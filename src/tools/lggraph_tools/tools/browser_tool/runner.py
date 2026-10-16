"""
this only contains the orchestration logic for the browser tool to run as subprocess
"""
from __future__ import annotations
import asyncio
from queue import Queue
from threading import Thread

from .config import BrowserRequiredConfig
from .Handler import HandlerEnums, HandlerExceptionRaises, Handler

# IMPORTANT: Import events_drivers to register driver classes with the metaclass
# Without this import, Handler.enum_driver_map will have None for all events
from .utils import events_drivers  # noqa: F401 - triggers metaclass registration

class Runner:
    """
    this is not optimized for performance and parallelism yet
    """
    config: BrowserRequiredConfig
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(Runner, cls).__new__(cls)
        return cls.instance

    def __init__(self, config: BrowserRequiredConfig):
        # Check if already initialized (not just if instance exists)
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.config = config
        self.browser_process = None
        self.running = False
        self.agent = None
        self.result = None  # Initialize result attribute
        self.final_result = None  # Initialize final_result attribute
        self.last_exception = None  # Initialize last_exception attribute
        self.agent_result = None  # Initialize agent_result attribute
        self.browser = None  # Initialize browser attribute
        self.llm = None  # Initialize llm attribute for SetupDriver
        self.monitor_queue = None  # Initialize monitor_queue attribute
        self.monitor_thread = None  # Initialize monitor_thread attribute
        self.monitering = None
        self.event_handler = None

    async def run(self):
        moving_forward_bus = Queue()
        all_results = []  # Collect all results from drivers

        try:
            # initial check ups for requirements and environment
            self.event_handler = Handler()

            #### get returns the class of driver and then the execute method runs the class methods one by one and update the queue bus
            await self.event_handler.get(self, HandlerEnums.ON_PRE_REQUIREMENTS).execute(moving_forward_bus)
            # setup phase and custom logic during setup
            await self.event_handler.get(self, HandlerEnums.SET_UP).execute(moving_forward_bus)
            # start the agent and the browser process
            await self.event_handler.get(self, HandlerEnums.ON_START).execute(moving_forward_bus)

            await self.event_handler.get(self, HandlerEnums.ON_RUNNING).execute(moving_forward_bus)

            await self.event_handler.get(self, HandlerEnums.ON_COMPLETE).execute(moving_forward_bus)

        except asyncio.CancelledError:
            raise
        except (HandlerExceptionRaises.CustomEventNotFound, HandlerExceptionRaises.DriverEventAlreadyRegistered) as e:
            # Store exception for ON_EXCEPTION driver to access
            self.last_exception = e
            await self.event_handler.get(self, HandlerEnums.ON_EXCEPTION).execute(moving_forward_bus)
            moving_forward_bus.put({"error": str(e)})
        except Exception as e:
            # Store exception for ON_EXCEPTION driver to access
            self.last_exception = e
            # Catch any other exception and run ON_EXCEPTION handler
            await self.event_handler.get(self, HandlerEnums.ON_EXCEPTION).execute(moving_forward_bus)
            moving_forward_bus.put({"error": str(e), "type": type(e).__name__})
        finally:
            await self.event_handler.get(self, HandlerEnums.TEAR_DOWN).execute(moving_forward_bus)

            # Collect ALL results from the queue (non-blocking)
            while not moving_forward_bus.empty():
                try:
                    item = moving_forward_bus.get_nowait()
                    all_results.append(item)
                except Exception:
                    break

            print(f"[Runner] All results collected: {all_results}", flush=True)

            self.result = {
                "status": "completed",
                "results": all_results,
                "final_result": self.final_result,
                "count": len(all_results)
            }
            return self.result
