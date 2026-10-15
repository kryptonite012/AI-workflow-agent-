from __future__ import annotations

import asyncio
import sys
from enum import Enum
from queue import Queue
from typing import TYPE_CHECKING, Callable, Awaitable
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

if TYPE_CHECKING:
    from .runner import Runner


class HandlerEnums(Enum):
    ON_PRE_REQUIREMENTS = 'on_pre_requirements'
    SET_UP = 'set_up'
    ON_START = 'on_start'
    ON_RUNNING = 'on_running'
    ON_COMPLETE = 'on_complete'
    ON_EXCEPTION = 'on_exception'
    TEAR_DOWN = 'tear_down'


class HandlerMeta(type):
    enum_driver_map: dict[HandlerEnums, type['Handler'] | None] = {}

    @classmethod
    def __prepare__(metacls, name, bases):
        return super().__prepare__(name, bases)

    # why we need metaclass because to evaluate the class Handler that it can get the event from valid driver which is registered into the enum
    # check that does that enum is also registered into other driver or not if yes return exception from HandlerExceptionRaises

    # the concept is ::::----
    """
    handler must be parent of all the driver events
    driver events must have class attribute enum_value which must be of type HandlerEnums
    we have to check that one on one relation between the driver event class and the HandlerEnums
    if any HandlerEnums is registered more than once in the driver event raise exception from HandlerExceptionRaises.DriverEventAlreadyRegistered
    if no Enum is found in the driver event raise exception from HandlerExceptionRaises.DriverEventNotFound
    if all good while creating the Handler class
    we have to insert enum_driver_map attribute into handler class which would be dictionary of HandlerEnums to driver event class
    
    """

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        if name == 'Handler':
            enum_driver_map = mcs.enum_driver_map
            for enum_class in HandlerEnums:
                enum_driver_map[enum_class] = None

            cls.enum_driver_map = enum_driver_map
        return cls

    def __init__(cls, name, bases, namespace):
        """
        Register driver classes in the enum_driver_map.

        This runs when a class using HandlerMeta is created.
        For the base Handler class, we skip validation.
        For driver classes (PreRequirementsCustomEvent, SetupDriver, etc.),
        we register them in enum_driver_map based on their enum_value.
        """
        # Skip validation for base Handler class itself
        if name == 'Handler':
            super().__init__(name, bases, namespace)
            return

        # For driver classes: check if THIS class has enum_value
        if hasattr(cls, 'enum_value'):
            enum_value = getattr(cls, 'enum_value')

            # Validate it's a HandlerEnums member
            if not isinstance(enum_value, HandlerEnums):
                raise TypeError(
                    f"The 'enum_value' attribute of {cls.__name__} must be "
                    f"a {HandlerEnums.__class__.__name__} member, got {type(enum_value)}"
                )

            # Check if this enum is already registered
            if Handler.enum_driver_map[enum_value] is not None:
                existing = Handler.enum_driver_map[enum_value].__name__
                raise HandlerExceptionRaises.DriverEventAlreadyRegistered(
                    f"{enum_value.name} (already registered to {existing}, "
                    f"can't register {cls.__name__})"
                )

            # Register this driver class for this enum
            Handler.enum_driver_map[enum_value] = cls

            # Inject execute method into this driver class
            setattr(cls, 'execute', Handler.execute_method)

            print(f"[MetaClass] ✅ Registered {cls.__name__} for {enum_value.name}")

        super().__init__(name, bases, namespace)


class HandlerExceptionRaises(Exception):
    """Base exception for Handler errors."""

    class CustomEventNotFound(RuntimeError):
        """Raised when a custom event is not found in the handler enum."""

        def __init__(self, missing_events: list[str] = None):
            if missing_events is None:
                super().__init__(f"The custom event you are trying to access is not found in the {HandlerEnums}.")
                return
            super().__init__(f"provided event are not registered :- " + ", ".join(missing_events))

    class DriverEventAlreadyRegistered(RuntimeError):
        """Raised when a driver event is already registered."""

        def __init__(self, event_name: str):
            super().__init__(f"The driver event '{event_name}' is already registered in the {HandlerEnums}.")


class Handler(metaclass=HandlerMeta):
    """
    this class use to have our own custom events, hookups and there logic during the browser tool lifecycle
    """

    # Type hint for IDE - execute is injected by metaclass at runtime
    execute: 'Callable[[Queue], Awaitable[dict]]'

    async def execute_method(self, moving_forward_bus: Queue, *args, **kwargs):
        """
        Execute all callable methods in the driver class instance.

        This method is injected into driver classes by the metaclass.
        It finds all non-private, non-special methods and executes them.

        :param moving_forward_bus: Queue bus to share data between events
        :return: Dictionary of {method_name: result}
        """

        results = {}
        driver_class_name = self.__class__.__name__

        print(f"[Handler] 🚀 Executing {driver_class_name}")

        # Get methods defined ONLY in the driver class, not inherited from Handler
        driver_attributes : list[str] = [k for k in self.__class__.__dict__.keys() if k not in Handler.__dict__.keys()]  # get all attributes of all drivers class

        # Get all callable methods from the driver instance
        for attr_name in driver_attributes:
            # Skip private/magic methods, execute_method itself, and enum_value
            if attr_name.startswith('_') or attr_name in ['execute', 'execute_method', 'enum_value']:
                continue

            attr_value = getattr(self, attr_name)

            # Only execute callable methods
            if not callable(attr_value):
                continue

            print(f"[Handler]   → Running {attr_name}()", flush=True)
            sys.stdout.flush()

            try:
                # Check if it's async or sync
                if asyncio.iscoroutinefunction(attr_value):
                    # It's async - await it
                    result = await attr_value()
                else:
                    # It's sync - run in thread
                    result = await asyncio.to_thread(attr_value)

                results[attr_name] = result
                moving_forward_bus.put({'attr_name': attr_name, 'result': result, 'error': None})
                print(f"[Handler]   ✅ {attr_name} completed")

            except Exception as e:
                print(f"[Handler]   ❌ {attr_name} raised an exception: {e}")
                # check if that attr class does have huge error or not if it is true stop the execution raise the error !!
                if hasattr(self, "huge_error") and getattr(self, "huge_error"):
                    print(f"[Handler]   ⛔ Huge error detected in {attr_name}, stopping execution.")
                    raise e
                moving_forward_bus.put({'attr_name': attr_name, 'result': None, 'error': str(e)})

        print(f"[Handler] 🎉 {driver_class_name} completed with {len(results)} methods executed")
        return results

    def get(self, runner_self: 'Runner', enum_event: HandlerEnums) -> Handler:
        """
        Get the driver instance for a specific lifecycle event.

        :param runner_self: Runner instance to inject into driver
        :param enum_event: Which lifecycle event to get driver for
        :return: Driver instance (subclass of Handler)
        """
        driver_class = self.enum_driver_map.get(enum_event)
        if driver_class is None:
            raise HandlerExceptionRaises.CustomEventNotFound(
                [f"{enum_event.name} (driver class not registered - ensure events_drivers is imported)"]
            )
        return driver_class(runner_self)
