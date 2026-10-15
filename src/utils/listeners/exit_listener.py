"""
the slash command of the exit  is not working as it assumed because the exit is handled up on the next message send by the user if user
used the /exit command so the value of the exist flag is set to true but the actual handled above the setting it so the part which could trigger the exit is not aware of the flag
so when user send the next message to the llm could be anything the application will exit because the flag is evaluated now .... which is the actual problem
we can fix this by creating event listener which could listen to the change of the exit flag and then trigger the exit when it is set to true

but I am creating this to not the exit application instant after user type /exit command i want that llm could display a message like "exiting application" and then exit
which is more graceful way to exit the application

"""

from src.utils.listeners.event_listener import EventListener
from src.config import settings
from src.ui.diagnostics.debug_helpers import debug_critical, debug_info

class ExitListener:
    """
    🎯 TWO-EMIT EXIT SYSTEM

    Listener to handle application exit when BOTH exit tickets are received:
    - Ticket 1: Graph completion emits exit event
    - Ticket 2: /exit slash command emits exit event

    Only exits when both tickets are collected.
    """
    manager: EventListener.EventManager = None

    def __init__(self):
        # Track exit tickets received
        self.exit_tickets_received = 0
        self.required_tickets = 2  # Must receive 2 tickets to exit
        self.ticket_sources = []  # Track where tickets came from

        # Initialize previous flag state
        self.previous_exit_flag = settings.exit_flag
        ExitListener.manager = EventListener.EventManager()

    def check_condition(self, event_data) -> bool:
        """
        🎫 Check if this is a valid exit ticket.

        A valid ticket is when:
        - Variable name is 'exit_flag'
        - Value changes from False to True (new ticket)
        - Or True to True (repeat ticket - also valid)
        """
        if not event_data.meta_data:
            return False

        variable_name = event_data.meta_data.get("variable_name")
        new_value = event_data.meta_data.get("new_value")

        # Only process exit_flag changes that set it to True
        return variable_name == "exit_flag" and new_value is True

    def on_event(self):
        """🚪 Actually exit the application with graceful message."""
        print("\n🎫 Both exit tickets collected!")
        print("✅ Exiting application gracefully...")
        import sys
        sys.exit(0)

    def register(self):
        """📝 Register the exit listener."""
        ExitListener.manager.register_listener(
            EventListener.EventType.VARIABLE_CHANGED,
            self.on_variable_change,
            priority=10,
            filter_func=self.check_condition
        )

        debug_info(
            heading="EXIT_LISTENER • REGISTERED",
            body="Two-emit exit system registered successfully",
            metadata={
                "required_tickets": self.required_tickets,
                "listener_id": id(self)
            }
        )

    def unregister(self):
        """📝 Unregister the exit listener."""
        ExitListener.manager.unregister_listener(
            EventListener.EventType.VARIABLE_CHANGED,
            self.on_variable_change  # ✅ Fixed: Use correct callback
        )

    def emit_exit_ticket(self, source_class: type, source_name: str = "Unknown"):
        """
        🎫 Emit an exit ticket (standardized method).

        Args:
            source_class: The class emitting the ticket
            source_name: Human-readable name for the source
        """
        # Get current flag state for proper old_value
        current_flag = settings.exit_flag

        # Always set flag to True when issuing ticket
        settings.exit_flag = True

        event_data = EventListener.EventData(
            event_type=EventListener.EventType.VARIABLE_CHANGED,
            source_class=source_class,
            meta_data={
                "id": id(self),
                "old_value": current_flag,  # ✅ Correct: Use actual current state
                "new_value": True,          # ✅ Correct: Always True for tickets
                "variable_name": "exit_flag",
                "ticket_source": source_name,
            },
        )

        debug_info(
            heading="EXIT_LISTENER • TICKET_ISSUED",
            body=f"Exit ticket issued by {source_name}",
            metadata={
                "source": source_name,
                "old_flag": current_flag,
                "new_flag": True,
                "tickets_so_far": self.exit_tickets_received
            }
        )

        ExitListener.manager.emit_event(event_data)

    def emit_on_variable_change(self, source_class: type, variable_name: str, old_value: bool, new_value: bool):
        """
        🔄 Legacy method - now routes to emit_exit_ticket for consistency.
        """
        if variable_name == "exit_flag" and new_value is True:
            source_name = getattr(source_class, '__name__', str(source_class))
            self.emit_exit_ticket(source_class, source_name)

    def on_variable_change(self, event_data: EventListener.EventData):
        """
        🎫 Handle exit ticket collection.

        Logic:
        - Collect each valid exit ticket
        - Track ticket sources
        - Only exit when required number of tickets collected
        """
        if event_data.meta_data.get("variable_name") == "exit_flag":
            old_value = event_data.meta_data.get("old_value")
            new_value = event_data.meta_data.get("new_value")
            ticket_source = event_data.meta_data.get("ticket_source", "Unknown")

            # Increment ticket counter
            self.exit_tickets_received += 1
            self.ticket_sources.append(ticket_source)

            debug_critical(
                heading="EXIT_LISTENER • TICKET_COLLECTED",
                body=f"Exit ticket #{self.exit_tickets_received}/{self.required_tickets} from {ticket_source}",
                metadata={
                    "ticket_number": self.exit_tickets_received,
                    "required_tickets": self.required_tickets,
                    "ticket_source": ticket_source,
                    "all_sources": self.ticket_sources,
                    "old_value": old_value,
                    "new_value": new_value,
                    "ready_to_exit": self.exit_tickets_received >= self.required_tickets
                },
            )

            # ✅ Only exit when we have enough tickets
            if self.exit_tickets_received >= self.required_tickets:
                debug_critical(
                    heading="EXIT_LISTENER • EXIT_TRIGGERED",
                    body=f"All {self.required_tickets} tickets collected! Exiting application.",
                    metadata={
                        "total_tickets": self.exit_tickets_received,
                        "ticket_sources": self.ticket_sources
                    }
                )
                self.on_event()
            else:
                remaining = self.required_tickets - self.exit_tickets_received
                debug_info(
                    heading="EXIT_LISTENER • WAITING",
                    body=f"Waiting for {remaining} more ticket(s) before exit",
                    metadata={
                        "tickets_collected": self.exit_tickets_received,
                        "tickets_remaining": remaining
                    }
                )
