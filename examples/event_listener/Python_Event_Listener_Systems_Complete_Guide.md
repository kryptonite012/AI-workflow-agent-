# 🎯 Python Event Listener Systems: Complete Guide for Rich Status Updates

## 📚 **Table of Contents**
1. [Understanding Your Current Rich Status Architecture](#current-architecture)
2. [Event-Driven Programming Fundamentals](#fundamentals)
3. [Python Event Listener Patterns](#python-patterns)
4. [Android-Style Event Listeners in Python](#android-style)
5. [Advanced Event Systems & Libraries](#advanced-systems)
6. [Practical Implementation Strategies](#implementation)
7. [Performance & Best Practices](#best-practices)
8. [Real-World Examples & Code](#examples)

---

## 🏗️ **Understanding Your Current Rich Status Architecture** {#current-architecture}

### **Your Current Implementation Analysis**

Based on your codebase analysis, you have a sophisticated **RichTracebackManager** singleton that handles error display across 6+ files:

```python
# Your Current Architecture
RichTracebackManager (Singleton)
├── Error Handling & Display
├── Socket Integration  
├── Context-Aware Reporting
├── Performance Monitoring
└── Decorator Pattern (@rich_exception_handler)
```

### **The Challenge You're Facing**

You want to create a **responsive system** where:
1. **Class A** changes a variable
2. **Event Listener** detects the change automatically  
3. **Class B** gets notified without tight coupling
4. **Rich Status** updates immediately
5. **Listener** marks notification as "read"

### **Why Observer Pattern Isn't Ideal**

You mentioned Observer pattern is "too particular" - and you're absolutely right! Observer pattern requires:
- Direct subject-observer relationships
- Tight coupling between classes
- Manual subscription management
- Complex cleanup logic

**You need something more like Android's EventListener system!**

---

## 🧠 **Event-Driven Programming Fundamentals** {#fundamentals}

### **Core Concept: Decoupled Communication**

Think of event systems like a **radio station**:
- **Radio Station** (Event Source) broadcasts signals
- **Radio Receivers** (Event Listeners) tune in to specific frequencies  
- **No direct connection** between station and receivers
- **Multiple receivers** can listen to the same frequency
- **Receivers can tune in/out** dynamically

### **Event System Components**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Event Source  │───▶│  Event Manager  │───▶│ Event Listeners │
│  (Your Class)   │    │   (Dispatcher)  │    │ (Rich Status)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

1. **Event Source**: The class that changes variables
2. **Event Manager**: Central dispatcher (like Android's EventBus)
3. **Event Listeners**: Functions that respond to events
4. **Event Data**: Information passed with the event

### **Key Advantages Over Observer Pattern**

✅ **Loose Coupling**: Classes don't know about each other  
✅ **Dynamic Registration**: Add/remove listeners at runtime  
✅ **Type Safety**: Strongly typed event data  
✅ **Async Support**: Non-blocking event handling  
✅ **Filtering**: Listen to specific event types only  
✅ **Priority Handling**: Control execution order  

---

## 🐍 **Python Event Listener Patterns** {#python-patterns}

### **Pattern 1: Signal-Slot System (PyQt Style)**

This is the closest to Android EventListener in Python:

```python
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
import threading
from enum import Enum

class EventType(Enum):
    VARIABLE_CHANGED = "variable_changed"
    STATUS_UPDATE = "status_update"
    ERROR_OCCURRED = "error_occurred"

@dataclass
class EventData:
    event_type: EventType
    source_class: str
    variable_name: str
    old_value: Any
    new_value: Any
    timestamp: float
    metadata: Dict[str, Any] = None

class EventManager:
    """
    Central Event Manager - Like Android's EventBus
    Thread-safe, type-safe, and highly performant
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._listeners: Dict[EventType, List[Callable]] = {}
            self._listener_priorities: Dict[Callable, int] = {}
            self._listener_filters: Dict[Callable, Callable] = {}
            self._lock = threading.RLock()
            self._initialized = True
    
    def register_listener(self, 
                         event_type: EventType, 
                         listener: Callable[[EventData], None],
                         priority: int = 0,
                         filter_func: Callable[[EventData], bool] = None):
        """
        Register an event listener (like Android's @Subscribe)
        
        Args:
            event_type: Type of event to listen for
            listener: Function to call when event occurs
            priority: Higher numbers execute first (default: 0)
            filter_func: Optional filter to determine if listener should execute
        """
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            
            self._listeners[event_type].append(listener)
            self._listener_priorities[listener] = priority
            
            if filter_func:
                self._listener_filters[listener] = filter_func
            
            # Sort by priority (highest first)
            self._listeners[event_type].sort(
                key=lambda l: self._listener_priorities.get(l, 0), 
                reverse=True
            )
    
    def unregister_listener(self, event_type: EventType, listener: Callable):
        """Remove a listener (automatic cleanup)"""
        with self._lock:
            if event_type in self._listeners:
                if listener in self._listeners[event_type]:
                    self._listeners[event_type].remove(listener)
                
                # Cleanup priority and filter data
                self._listener_priorities.pop(listener, None)
                self._listener_filters.pop(listener, None)
    
    def emit_event(self, event_data: EventData):
        """
        Emit an event to all registered listeners
        This is like Android's EventBus.post()
        """
        with self._lock:
            listeners = self._listeners.get(event_data.event_type, []).copy()
        
        for listener in listeners:
            try:
                # Apply filter if exists
                filter_func = self._listener_filters.get(listener)
                if filter_func and not filter_func(event_data):
                    continue
                
                # Call the listener
                listener(event_data)
                
            except Exception as e:
                print(f"Error in event listener {listener.__name__}: {e}")
    
    def emit_async(self, event_data: EventData):
        """Emit event asynchronously (non-blocking)"""
        import threading
        thread = threading.Thread(target=self.emit_event, args=(event_data,))
        thread.daemon = True
        thread.start()

# Global event manager instance
event_manager = EventManager()
```

### **Pattern 2: Decorator-Based Event System**

This makes your classes automatically emit events:

```python
import time
from functools import wraps

def event_emitter(event_type: EventType, variable_name: str = None):
    """
    Decorator that automatically emits events when variables change
    This is like Android's @EventEmitter annotation
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get old value if it's a setter
            old_value = None
            if hasattr(self, variable_name) and variable_name:
                old_value = getattr(self, variable_name)
            
            # Execute the original function
            result = func(self, *args, **kwargs)
            
            # Get new value
            new_value = getattr(self, variable_name) if variable_name else args[0] if args else None
            
            # Emit event if value actually changed
            if old_value != new_value:
                event_data = EventData(
                    event_type=event_type,
                    source_class=self.__class__.__name__,
                    variable_name=variable_name or func.__name__,
                    old_value=old_value,
                    new_value=new_value,
                    timestamp=time.time(),
                    metadata={'method': func.__name__, 'args': args, 'kwargs': kwargs}
                )
                event_manager.emit_event(event_data)
            
            return result
        return wrapper
    return decorator

class EventAwareProperty:
    """
    Property descriptor that automatically emits events on change
    This is like Android's Observable fields
    """
    def __init__(self, initial_value=None, event_type: EventType = EventType.VARIABLE_CHANGED):
        self.value = initial_value
        self.event_type = event_type
        self.name = None
    
    def __set_name__(self, owner, name):
        self.name = name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self.value
    
    def __set__(self, obj, value):
        if self.value != value:
            old_value = self.value
            self.value = value
            
            # Emit event
            event_data = EventData(
                event_type=self.event_type,
                source_class=obj.__class__.__name__,
                variable_name=self.name,
                old_value=old_value,
                new_value=value,
                timestamp=time.time()
            )
            event_manager.emit_event(event_data)
```

---

## 📱 **Android-Style Event Listeners in Python** {#android-style}

### **Creating Android EventBus Equivalent**

Here's how to create the exact Android EventListener experience you want:

```python
from typing import TypeVar, Generic, Union
import inspect

T = TypeVar('T')

class EventListener(Generic[T]):
    """
    Android-style EventListener interface
    """
    def on_event(self, event_data: T) -> None:
        """Override this method to handle events"""
        pass

class VariableChangeListener(EventListener[EventData]):
    """Specific listener for variable changes"""
    def on_variable_changed(self, event_data: EventData) -> None:
        """Called when any variable changes"""
        pass
    
    def on_event(self, event_data: EventData) -> None:
        self.on_variable_changed(event_data)

class RichStatusEventListener(VariableChangeListener):
    """
    Your Rich Status Event Listener
    This will update Rich status when variables change
    """
    def __init__(self, rich_manager):
        self.rich_manager = rich_manager
        self.processed_events = set()  # Track "read" events
    
    def on_variable_changed(self, event_data: EventData) -> None:
        """Update Rich status when variables change"""
        event_id = f"{event_data.source_class}_{event_data.variable_name}_{event_data.timestamp}"
        
        if event_id not in self.processed_events:
            # Update Rich status
            status_message = f"🔄 {event_data.source_class}.{event_data.variable_name} changed: {event_data.old_value} → {event_data.new_value}"
            
            # Use your existing Rich system
            if hasattr(self.rich_manager, 'update_status'):
                self.rich_manager.update_status(status_message)
            else:
                print(status_message)  # Fallback
            
            # Mark as read
            self.processed_events.add(event_id)
            
            # Optional: Clean up old events to prevent memory leaks
            if len(self.processed_events) > 1000:
                # Keep only recent 500 events
                recent_events = list(self.processed_events)[-500:]
                self.processed_events = set(recent_events)

# Android-style registration
def register_event_listener(listener: EventListener, event_type: EventType = EventType.VARIABLE_CHANGED):
    """
    Register listener Android-style
    Usage: register_event_listener(MyListener(), EventType.VARIABLE_CHANGED)
    """
    event_manager.register_listener(event_type, listener.on_event)

def unregister_event_listener(listener: EventListener, event_type: EventType = EventType.VARIABLE_CHANGED):
    """Unregister listener Android-style"""
    event_manager.unregister_listener(event_type, listener.on_event)
```

### **Usage Example: Your Rich Status Integration**

```python
# Your existing Rich manager integration
class YourClass:
    """Example class that emits events when variables change"""
    
    # Method 1: Using property descriptor (automatic)
    status_message = EventAwareProperty("Initial Status", EventType.STATUS_UPDATE)
    error_count = EventAwareProperty(0, EventType.VARIABLE_CHANGED)
    
    # Method 2: Using decorator (manual)
    @event_emitter(EventType.VARIABLE_CHANGED, "processing_state")
    def set_processing_state(self, new_state):
        self.processing_state = new_state
    
    # Method 3: Manual event emission (full control)
    def update_complex_data(self, data):
        old_data = getattr(self, 'complex_data', None)
        self.complex_data = data
        
        # Emit custom event
        event_data = EventData(
            event_type=EventType.VARIABLE_CHANGED,
            source_class=self.__class__.__name__,
            variable_name="complex_data",
            old_value=old_data,
            new_value=data,
            timestamp=time.time(),
            metadata={'data_size': len(data) if data else 0}
        )
        event_manager.emit_event(event_data)

# Set up your Rich status listener
rich_listener = RichStatusEventListener(your_rich_traceback_manager)
register_event_listener(rich_listener, EventType.VARIABLE_CHANGED)
register_event_listener(rich_listener, EventType.STATUS_UPDATE)

# Now any variable change automatically updates Rich status!
your_instance = YourClass()
your_instance.status_message = "Processing started..."  # Automatically triggers Rich update
your_instance.error_count = 5  # Automatically triggers Rich update
your_instance.set_processing_state("RUNNING")  # Automatically triggers Rich update
```

---
## 🚀 **Advanced Event Systems & Libraries** {#advanced-systems}

### **1. PyQt/PySide Signal-Slot System**

The most mature event system in Python, used by millions of applications:

```python
from PySide6.QtCore import QObject, Signal, Slot

class VariableWatcher(QObject):
    """PyQt-style signal emitter"""
    variable_changed = Signal(str, object, object)  # variable_name, old_value, new_value
    status_updated = Signal(str)  # status_message
    
    def __init__(self):
        super().__init__()
        self._variables = {}
    
    def set_variable(self, name: str, value):
        """Set variable and emit signal if changed"""
        old_value = self._variables.get(name)
        if old_value != value:
            self._variables[name] = value
            self.variable_changed.emit(name, old_value, value)
    
    def update_status(self, message: str):
        """Update status and emit signal"""
        self.status_updated.emit(message)

class RichStatusUpdater(QObject):
    """Rich status updater using Qt signals"""
    
    def __init__(self, rich_manager):
        super().__init__()
        self.rich_manager = rich_manager
        self.processed_updates = set()
    
    @Slot(str, object, object)
    def on_variable_changed(self, variable_name: str, old_value, new_value):
        """Slot that receives variable change signals"""
        update_id = f"{variable_name}_{hash(str(new_value))}_{time.time()}"
        
        if update_id not in self.processed_updates:
            status_msg = f"🔄 Variable '{variable_name}' changed: {old_value} → {new_value}"
            
            # Update your Rich status here
            print(status_msg)  # Replace with your Rich manager call
            
            # Mark as processed
            self.processed_updates.add(update_id)
    
    @Slot(str)
    def on_status_updated(self, message: str):
        """Slot that receives status update signals"""
        print(f"📊 Status: {message}")

# Usage
watcher = VariableWatcher()
updater = RichStatusUpdater(your_rich_manager)

# Connect signals to slots (Android-style listener registration)
watcher.variable_changed.connect(updater.on_variable_changed)
watcher.status_updated.connect(updater.on_status_updated)

# Now variable changes automatically trigger Rich updates
watcher.set_variable("user_count", 150)
watcher.set_variable("error_rate", 0.02)
watcher.update_status("System running smoothly")
```

### **2. Blinker - Lightweight Signal Library**

Fast, simple, and widely used (Flask uses it internally):

```python
from blinker import Namespace

# Create namespace for your events
app_signals = Namespace()

# Define signals
variable_changed = app_signals.signal('variable-changed')
status_updated = app_signals.signal('status-updated')
error_occurred = app_signals.signal('error-occurred')

class EventEmittingClass:
    """Class that emits Blinker signals"""
    
    def __init__(self, name: str):
        self.name = name
        self._data = {}
    
    def set_data(self, key: str, value):
        """Set data and emit signal if changed"""
        old_value = self._data.get(key)
        if old_value != value:
            self._data[key] = value
            
            # Emit signal with data
            variable_changed.send(
                self,  # sender
                class_name=self.name,
                variable_name=key,
                old_value=old_value,
                new_value=value,
                timestamp=time.time()
            )
    
    def update_status(self, message: str):
        """Update status and emit signal"""
        status_updated.send(
            self,
            class_name=self.name,
            message=message,
            timestamp=time.time()
        )

# Rich status listener using Blinker
@variable_changed.connect
def handle_variable_change(sender, **kwargs):
    """Handle variable change events"""
    class_name = kwargs.get('class_name')
    variable_name = kwargs.get('variable_name')
    old_value = kwargs.get('old_value')
    new_value = kwargs.get('new_value')
    
    rich_message = f"🔄 {class_name}.{variable_name}: {old_value} → {new_value}"
    
    # Update your Rich status here
    print(rich_message)  # Replace with your Rich manager

@status_updated.connect
def handle_status_update(sender, **kwargs):
    """Handle status update events"""
    class_name = kwargs.get('class_name')
    message = kwargs.get('message')
    
    rich_message = f"📊 {class_name}: {message}"
    print(rich_message)  # Replace with your Rich manager

# Usage
emitter = EventEmittingClass("DataProcessor")
emitter.set_data("records_processed", 1000)
emitter.set_data("error_count", 3)
emitter.update_status("Processing completed successfully")
```

### **3. PyPubSub - Publisher-Subscriber Pattern**

Powerful message-based communication system:

```python
from pubsub import pub

class VariablePublisher:
    """Publisher that sends messages when variables change"""
    
    def __init__(self, name: str):
        self.name = name
        self._variables = {}
    
    def set_variable(self, var_name: str, value):
        """Set variable and publish message if changed"""
        old_value = self._variables.get(var_name)
        if old_value != value:
            self._variables[var_name] = value
            
            # Publish message
            pub.sendMessage(
                'variable.changed',
                class_name=self.name,
                variable_name=var_name,
                old_value=old_value,
                new_value=value,
                timestamp=time.time()
            )
    
    def publish_status(self, message: str):
        """Publish status update"""
        pub.sendMessage(
            'status.updated',
            class_name=self.name,
            message=message,
            timestamp=time.time()
        )

class RichStatusSubscriber:
    """Subscriber that updates Rich status"""
    
    def __init__(self, rich_manager):
        self.rich_manager = rich_manager
        self.processed_messages = set()
        
        # Subscribe to messages
        pub.subscribe(self.on_variable_changed, 'variable.changed')
        pub.subscribe(self.on_status_updated, 'status.updated')
    
    def on_variable_changed(self, class_name, variable_name, old_value, new_value, timestamp):
        """Handle variable change messages"""
        message_id = f"{class_name}_{variable_name}_{timestamp}"
        
        if message_id not in self.processed_messages:
            rich_message = f"🔄 {class_name}.{variable_name}: {old_value} → {new_value}"
            
            # Update Rich status
            print(rich_message)  # Replace with your Rich manager
            
            # Mark as processed
            self.processed_messages.add(message_id)
    
    def on_status_updated(self, class_name, message, timestamp):
        """Handle status update messages"""
        rich_message = f"📊 {class_name}: {message}"
        print(rich_message)  # Replace with your Rich manager

# Usage
publisher = VariablePublisher("DatabaseManager")
subscriber = RichStatusSubscriber(your_rich_manager)

# Variable changes automatically trigger Rich updates
publisher.set_variable("connection_count", 25)
publisher.set_variable("query_time", 0.045)
publisher.publish_status("Database optimization completed")
```

### **4. AsyncIO Event System**

For high-performance async applications:

```python
import asyncio
from typing import Dict, List, Callable, Any
from dataclasses import dataclass

@dataclass
class AsyncEventData:
    event_type: str
    source: str
    data: Dict[str, Any]
    timestamp: float

class AsyncEventManager:
    """Async event manager for high-performance applications"""
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._event_queue = asyncio.Queue()
        self._running = False
    
    async def start(self):
        """Start the event processing loop"""
        self._running = True
        await self._process_events()
    
    def stop(self):
        """Stop the event processing loop"""
        self._running = False
    
    def register_listener(self, event_type: str, listener: Callable):
        """Register async event listener"""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)
    
    async def emit_event(self, event_data: AsyncEventData):
        """Emit event asynchronously"""
        await self._event_queue.put(event_data)
    
    async def _process_events(self):
        """Process events from the queue"""
        while self._running:
            try:
                # Wait for event with timeout
                event_data = await asyncio.wait_for(
                    self._event_queue.get(), 
                    timeout=1.0
                )
                
                # Process event
                listeners = self._listeners.get(event_data.event_type, [])
                
                # Run all listeners concurrently
                if listeners:
                    await asyncio.gather(
                        *[self._safe_call_listener(listener, event_data) for listener in listeners],
                        return_exceptions=True
                    )
                
            except asyncio.TimeoutError:
                continue  # No events, continue loop
            except Exception as e:
                print(f"Error processing event: {e}")
    
    async def _safe_call_listener(self, listener: Callable, event_data: AsyncEventData):
        """Safely call listener with error handling"""
        try:
            if asyncio.iscoroutinefunction(listener):
                await listener(event_data)
            else:
                listener(event_data)
        except Exception as e:
            print(f"Error in listener {listener.__name__}: {e}")

# Async Rich status updater
class AsyncRichStatusUpdater:
    """Async Rich status updater"""
    
    def __init__(self, rich_manager):
        self.rich_manager = rich_manager
        self.processed_events = set()
    
    async def on_variable_changed(self, event_data: AsyncEventData):
        """Handle variable change events asynchronously"""
        event_id = f"{event_data.source}_{event_data.timestamp}"
        
        if event_id not in self.processed_events:
            # Simulate async Rich update
            await asyncio.sleep(0.01)  # Simulate async operation
            
            var_name = event_data.data.get('variable_name')
            old_value = event_data.data.get('old_value')
            new_value = event_data.data.get('new_value')
            
            rich_message = f"🔄 {event_data.source}.{var_name}: {old_value} → {new_value}"
            print(rich_message)  # Replace with your Rich manager
            
            # Mark as processed
            self.processed_events.add(event_id)

# Usage
async def main():
    event_manager = AsyncEventManager()
    rich_updater = AsyncRichStatusUpdater(your_rich_manager)
    
    # Register listener
    event_manager.register_listener('variable_changed', rich_updater.on_variable_changed)
    
    # Start event manager
    event_task = asyncio.create_task(event_manager.start())
    
    # Emit some events
    await event_manager.emit_event(AsyncEventData(
        event_type='variable_changed',
        source='AsyncClass',
        data={
            'variable_name': 'status',
            'old_value': 'idle',
            'new_value': 'processing'
        },
        timestamp=time.time()
    ))
    
    # Let events process
    await asyncio.sleep(2)
    
    # Stop event manager
    event_manager.stop()
    await event_task

# Run the async example
# asyncio.run(main())
```

---

## 💡 **Practical Implementation Strategies** {#implementation}

### **Strategy 1: Minimal Integration with Your Rich System**

Here's how to integrate with your existing `RichTracebackManager` with minimal changes:

```python
# Add this to your existing RichTracebackManager class
class RichTracebackManager:
    # ... your existing code ...
    
    @classmethod
    def create_status_updater(cls):
        """Create a status updater that integrates with event system"""
        def update_rich_status(event_data: EventData):
            """Update Rich status from event data"""
            if event_data.event_type == EventType.VARIABLE_CHANGED:
                status_message = f"🔄 {event_data.source_class}.{event_data.variable_name} changed"
                
                # Create Rich panel for status update
                from rich.panel import Panel
                status_panel = Panel(
                    f"Variable: {event_data.variable_name}\n"
                    f"Old Value: {event_data.old_value}\n"
                    f"New Value: {event_data.new_value}\n"
                    f"Source: {event_data.source_class}\n"
                    f"Time: {datetime.fromtimestamp(event_data.timestamp).strftime('%H:%M:%S')}",
                    title="🔄 Variable Changed",
                    border_style="blue"
                )
                
                if cls._console:
                    cls._console.print(status_panel)
                
                # Send to socket if available
                if settings.socket_con:
                    settings.socket_con.send_error(f"[STATUS] {status_message}")
        
        return update_rich_status
    
    @classmethod
    def register_with_event_system(cls):
        """Register Rich status updates with event system"""
        status_updater = cls.create_status_updater()
        event_manager.register_listener(EventType.VARIABLE_CHANGED, status_updater)
        event_manager.register_listener(EventType.STATUS_UPDATE, status_updater)
        
        if settings.socket_con:
            settings.socket_con.send_error("🎯 Rich status event listeners registered")

# Initialize event integration
RichTracebackManager.register_with_event_system()
```

### **Strategy 2: Decorator for Existing Classes**

Add event emission to your existing classes without modifying them:

```python
def make_event_aware(cls):
    """
    Class decorator that makes any class emit events on attribute changes
    This is like Android's @EventEmitter annotation
    """
    original_setattr = cls.__setattr__
    
    def event_aware_setattr(self, name, value):
        # Get old value
        old_value = getattr(self, name, None) if hasattr(self, name) else None
        
        # Set new value
        original_setattr(self, name, value)
        
        # Emit event if value changed
        if old_value != value:
            event_data = EventData(
                event_type=EventType.VARIABLE_CHANGED,
                source_class=self.__class__.__name__,
                variable_name=name,
                old_value=old_value,
                new_value=value,
                timestamp=time.time()
            )
            event_manager.emit_event(event_data)
    
    cls.__setattr__ = event_aware_setattr
    return cls

# Usage: Make any existing class event-aware
@make_event_aware
class YourExistingClass:
    def __init__(self):
        self.status = "idle"
        self.progress = 0
        self.error_count = 0

# Now this class automatically emits events!
instance = YourExistingClass()
instance.status = "processing"  # Automatically triggers Rich update
instance.progress = 50  # Automatically triggers Rich update
```

### **Strategy 3: Context Manager for Event Batching**

Batch multiple variable changes into single Rich update:

```python
from contextlib import contextmanager

class BatchEventManager:
    """Manager for batching events to reduce Rich update frequency"""
    
    def __init__(self):
        self.batched_events = []
        self.batching = False
    
    @contextmanager
    def batch_events(self):
        """Context manager for batching events"""
        self.batching = True
        self.batched_events.clear()
        
        try:
            yield self
        finally:
            # Process all batched events at once
            if self.batched_events:
                self._process_batched_events()
            
            self.batching = False
            self.batched_events.clear()
    
    def add_event(self, event_data: EventData):
        """Add event to batch or process immediately"""
        if self.batching:
            self.batched_events.append(event_data)
        else:
            event_manager.emit_event(event_data)
    
    def _process_batched_events(self):
        """Process all batched events as a single Rich update"""
        if not self.batched_events:
            return
        
        # Group events by source class
        grouped_events = {}
        for event in self.batched_events:
            source = event.source_class
            if source not in grouped_events:
                grouped_events[source] = []
            grouped_events[source].append(event)
        
        # Create Rich panel for batched updates
        from rich.panel import Panel
        from rich.table import Table
        
        table = Table(title="📊 Batched Variable Changes")
        table.add_column("Class", style="cyan")
        table.add_column("Variable", style="magenta")
        table.add_column("Old → New", style="green")
        
        for source_class, events in grouped_events.items():
            for event in events:
                table.add_row(
                    source_class,
                    event.variable_name,
                    f"{event.old_value} → {event.new_value}"
                )
        
        if RichTracebackManager._console:
            RichTracebackManager._console.print(table)

# Usage
batch_manager = BatchEventManager()

# Batch multiple changes into single Rich update
with batch_manager.batch_events():
    instance.status = "processing"
    instance.progress = 25
    instance.error_count = 1
    instance.progress = 50
    instance.progress = 75
    instance.status = "completed"
# Rich update happens here with all changes at once
```

---

## ⚡ **Performance & Best Practices** {#best-practices}

### **Performance Considerations**

#### **1. Event Filtering**
```python
# Filter events to reduce Rich update frequency
def important_changes_only(event_data: EventData) -> bool:
    """Only process important variable changes"""
    important_variables = {'status', 'error_count', 'progress', 'connection_state'}
    return event_data.variable_name in important_variables

# Register with filter
event_manager.register_listener(
    EventType.VARIABLE_CHANGED, 
    rich_status_updater,
    filter_func=important_changes_only
)
```

#### **2. Debouncing**
```python
import time
from collections import defaultdict

class DebouncedEventManager:
    """Event manager with debouncing to prevent spam"""
    
    def __init__(self, debounce_time: float = 0.1):
        self.debounce_time = debounce_time
        self.last_event_time = defaultdict(float)
        self.pending_events = {}
    
    def emit_debounced(self, event_data: EventData):
        """Emit event with debouncing"""
        event_key = f"{event_data.source_class}_{event_data.variable_name}"
        current_time = time.time()
        
        # Store the latest event
        self.pending_events[event_key] = event_data
        
        # Check if enough time has passed
        if current_time - self.last_event_time[event_key] >= self.debounce_time:
            # Emit the event
            event_manager.emit_event(event_data)
            self.last_event_time[event_key] = current_time
            
            # Remove from pending
            self.pending_events.pop(event_key, None)
        else:
            # Schedule delayed emission
            import threading
            def delayed_emit():
                time.sleep(self.debounce_time)
                if event_key in self.pending_events:
                    latest_event = self.pending_events.pop(event_key)
                    event_manager.emit_event(latest_event)
                    self.last_event_time[event_key] = time.time()
            
            thread = threading.Thread(target=delayed_emit)
            thread.daemon = True
            thread.start()

debounced_manager = DebouncedEventManager(debounce_time=0.2)
```

#### **3. Memory Management**
```python
class MemoryEfficientEventManager(EventManager):
    """Event manager with automatic cleanup"""
    
    def __init__(self, max_processed_events: int = 1000):
        super().__init__()
        self.max_processed_events = max_processed_events
        self.processed_events = set()
    
    def emit_event(self, event_data: EventData):
        """Emit event with memory management"""
        event_id = f"{event_data.source_class}_{event_data.variable_name}_{event_data.timestamp}"
        
        # Check if already processed
        if event_id in self.processed_events:
            return
        
        # Process event
        super().emit_event(event_data)
        
        # Track processed event
        self.processed_events.add(event_id)
        
        # Cleanup old events
        if len(self.processed_events) > self.max_processed_events:
            # Keep only recent events
            recent_events = list(self.processed_events)[-self.max_processed_events//2:]
            self.processed_events = set(recent_events)
```

### **Best Practices Summary**

✅ **Use Type Hints**: Always use type hints for better IDE support  
✅ **Error Handling**: Wrap listeners in try-catch blocks  
✅ **Thread Safety**: Use locks for multi-threaded applications  
✅ **Memory Management**: Clean up old events and listeners  
✅ **Performance**: Use filtering and debouncing for high-frequency events  
✅ **Testing**: Write unit tests for event flows  
✅ **Documentation**: Document event types and data structures  
✅ **Monitoring**: Log event statistics for debugging  

---

## 🎯 **Real-World Examples & Code** {#examples}

### **Complete Integration Example**

Here's a complete example showing how to integrate event listeners with your Rich status system:

```python
# complete_integration_example.py

import time
import threading
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# Your existing imports
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Event system classes (copy from above)
class EventType(Enum):
    VARIABLE_CHANGED = "variable_changed"
    STATUS_UPDATE = "status_update"
    ERROR_OCCURRED = "error_occurred"

@dataclass
class EventData:
    event_type: EventType
    source_class: str
    variable_name: str
    old_value: Any
    new_value: Any
    timestamp: float
    metadata: Dict[str, Any] = None

class EventManager:
    # ... (copy complete implementation from above)
    pass

# Your Rich integration
class RichStatusEventSystem:
    """
    Complete Rich status event system integration
    This replaces the Observer pattern with event listeners
    """
    
    def __init__(self, rich_console: Console = None):
        self.console = rich_console or Console()
        self.event_manager = EventManager()
        self.processed_events = set()
        self.status_history = []
        
        # Register listeners
        self._register_listeners()
    
    def _register_listeners(self):
        """Register all event listeners"""
        self.event_manager.register_listener(
            EventType.VARIABLE_CHANGED, 
            self._handle_variable_change,
            priority=10  # High priority
        )
        
        self.event_manager.register_listener(
            EventType.STATUS_UPDATE,
            self._handle_status_update,
            priority=5
        )
        
        self.event_manager.register_listener(
            EventType.ERROR_OCCURRED,
            self._handle_error,
            priority=15  # Highest priority
        )
    
    def _handle_variable_change(self, event_data: EventData):
        """Handle variable change events with Rich display"""
        event_id = f"{event_data.source_class}_{event_data.variable_name}_{event_data.timestamp}"
        
        if event_id not in self.processed_events:
            # Create Rich display
            change_table = Table(title=f"🔄 Variable Changed in {event_data.source_class}")
            change_table.add_column("Property", style="cyan")
            change_table.add_column("Value", style="magenta")
            
            change_table.add_row("Variable", event_data.variable_name)
            change_table.add_row("Old Value", str(event_data.old_value))
            change_table.add_row("New Value", str(event_data.new_value))
            change_table.add_row("Time", datetime.fromtimestamp(event_data.timestamp).strftime('%H:%M:%S'))
            
            # Display with Rich
            self.console.print(change_table)
            
            # Store in history
            self.status_history.append({
                'type': 'variable_change',
                'data': event_data,
                'timestamp': event_data.timestamp
            })
            
            # Mark as processed (your "read" functionality)
            self.processed_events.add(event_id)
            
            # Cleanup old events
            self._cleanup_old_events()
    
    def _handle_status_update(self, event_data: EventData):
        """Handle status update events"""
        status_panel = Panel(
            f"📊 Status Update from {event_data.source_class}\n\n"
            f"Message: {event_data.new_value}\n"
            f"Time: {datetime.fromtimestamp(event_data.timestamp).strftime('%H:%M:%S')}",
            title="Status Update",
            border_style="green"
        )
        
        self.console.print(status_panel)
    
    def _handle_error(self, event_data: EventData):
        """Handle error events with Rich display"""
        error_panel = Panel(
            f"🚨 Error in {event_data.source_class}\n\n"
            f"Error: {event_data.new_value}\n"
            f"Variable: {event_data.variable_name}\n"
            f"Time: {datetime.fromtimestamp(event_data.timestamp).strftime('%H:%M:%S')}",
            title="Error Occurred",
            border_style="red"
        )
        
        self.console.print(error_panel)
    
    def _cleanup_old_events(self):
        """Clean up old processed events to prevent memory leaks"""
        if len(self.processed_events) > 1000:
            # Keep only recent 500 events
            recent_events = list(self.processed_events)[-500:]
            self.processed_events = set(recent_events)
        
        # Clean up history
        if len(self.status_history) > 100:
            self.status_history = self.status_history[-50:]
    
    def get_event_manager(self) -> EventManager:
        """Get the event manager for registering custom listeners"""
        return self.event_manager
    
    def show_status_history(self):
        """Show Rich display of status history"""
        if not self.status_history:
            self.console.print("📋 No status history available")
            return
        
        history_table = Table(title="📊 Status History")
        history_table.add_column("Time", style="cyan")
        history_table.add_column("Type", style="magenta")
        history_table.add_column("Source", style="green")
        history_table.add_column("Details", style="yellow")
        
        for entry in self.status_history[-10:]:  # Show last 10 entries
            event_data = entry['data']
            timestamp = datetime.fromtimestamp(entry['timestamp']).strftime('%H:%M:%S')
            
            if entry['type'] == 'variable_change':
                details = f"{event_data.variable_name}: {event_data.old_value} → {event_data.new_value}"
            else:
                details = str(event_data.new_value)
            
            history_table.add_row(
                timestamp,
                entry['type'],
                event_data.source_class,
                details
            )
        
        self.console.print(history_table)

# Event-aware base class
class EventAwareClass:
    """
    Base class that automatically emits events when attributes change
    This is your Android-style EventEmitter
    """
    
    def __init__(self, class_name: str = None):
        self._class_name = class_name or self.__class__.__name__
        self._event_manager = None
        self._attributes = {}
    
    def set_event_manager(self, event_manager: EventManager):
        """Set the event manager for this class"""
        self._event_manager = event_manager
    
    def __setattr__(self, name: str, value: Any):
        # Handle internal attributes normally
        if name.startswith('_') or name in ['set_event_manager']:
            super().__setattr__(name, value)
            return
        
        # Get old value
        old_value = getattr(self, name, None) if hasattr(self, name) else None
        
        # Set new value
        super().__setattr__(name, value)
        
        # Emit event if value changed and event manager is set
        if old_value != value and self._event_manager:
            event_data = EventData(
                event_type=EventType.VARIABLE_CHANGED,
                source_class=self._class_name,
                variable_name=name,
                old_value=old_value,
                new_value=value,
                timestamp=time.time(),
                metadata={'change_type': 'attribute_set'}
            )
            self._event_manager.emit_event(event_data)
    
    def emit_status_update(self, message: str):
        """Manually emit a status update event"""
        if self._event_manager:
            event_data = EventData(
                event_type=EventType.STATUS_UPDATE,
                source_class=self._class_name,
                variable_name="status",
                old_value=None,
                new_value=message,
                timestamp=time.time(),
                metadata={'change_type': 'status_update'}
            )
            self._event_manager.emit_event(event_data)
    
    def emit_error(self, error_message: str, variable_name: str = "error"):
        """Manually emit an error event"""
        if self._event_manager:
            event_data = EventData(
                event_type=EventType.ERROR_OCCURRED,
                source_class=self._class_name,
                variable_name=variable_name,
                old_value=None,
                new_value=error_message,
                timestamp=time.time(),
                metadata={'change_type': 'error'}
            )
            self._event_manager.emit_event(event_data)

# Example usage classes
class DataProcessor(EventAwareClass):
    """Example class that processes data and emits events"""
    
    def __init__(self):
        super().__init__("DataProcessor")
        self.status = "idle"
        self.records_processed = 0
        self.error_count = 0
        self.processing_speed = 0.0
    
    def start_processing(self):
        """Start processing and emit status updates"""
        self.status = "starting"
        self.emit_status_update("Data processing started")
        
        # Simulate processing
        for i in range(1, 101, 10):
            time.sleep(0.1)  # Simulate work
            self.records_processed = i
            self.processing_speed = i / 10.0
            
            if i == 50:
                self.status = "halfway"
                self.emit_status_update("Processing halfway complete")
        
        self.status = "completed"
        self.emit_status_update("Data processing completed successfully")

class DatabaseManager(EventAwareClass):
    """Example database manager that emits connection events"""
    
    def __init__(self):
        super().__init__("DatabaseManager")
        self.connection_count = 0
        self.query_time = 0.0
        self.last_error = None
    
    def connect(self):
        """Simulate database connection"""
        self.connection_count += 1
        self.emit_status_update(f"Database connected (connections: {self.connection_count})")
    
    def execute_query(self, query: str):
        """Simulate query execution"""
        import random
        
        # Simulate query time
        query_time = random.uniform(0.01, 0.5)
        time.sleep(query_time)
        self.query_time = query_time
        
        # Simulate occasional errors
        if random.random() < 0.1:  # 10% chance of error
            error_msg = f"Query failed: {query[:50]}..."
            self.last_error = error_msg
            self.emit_error(error_msg, "query_execution")
        else:
            self.emit_status_update(f"Query executed successfully in {query_time:.3f}s")

# Complete usage example
def main():
    """Complete example of event-driven Rich status updates"""
    
    # Create Rich status event system
    rich_status_system = RichStatusEventSystem()
    event_manager = rich_status_system.get_event_manager()
    
    # Create event-aware classes
    processor = DataProcessor()
    db_manager = DatabaseManager()
    
    # Connect classes to event system
    processor.set_event_manager(event_manager)
    db_manager.set_event_manager(event_manager)
    
    # Demonstrate the system
    print("🚀 Starting Event-Driven Rich Status Demo")
    print("=" * 50)
    
    # Database operations
    db_manager.connect()
    db_manager.execute_query("SELECT * FROM users WHERE active = 1")
    db_manager.execute_query("UPDATE users SET last_login = NOW()")
    
    # Data processing
    processor.start_processing()
    
    # Show history
    print("\n" + "=" * 50)
    rich_status_system.show_status_history()
    
    print("\n🎉 Demo completed! All variable changes were automatically detected and displayed with Rich formatting.")

if __name__ == "__main__":
    main()
```

### **Integration with Your Existing RichTracebackManager**

```python
# Add this method to your existing RichTracebackManager class
class RichTracebackManager:
    # ... your existing code ...
    
    @classmethod
    def create_event_integration(cls):
        """Create event system integration for automatic Rich status updates"""
        
        # Create event system
        rich_event_system = RichStatusEventSystem(cls._console)
        event_manager = rich_event_system.get_event_manager()
        
        # Store reference for cleanup
        cls._event_system = rich_event_system
        cls._event_manager = event_manager
        
        # Log integration
        if settings.socket_con:
            settings.socket_con.send_error("🎯 Rich Event System integrated successfully")
        
        return event_manager
    
    @classmethod
    def make_class_event_aware(cls, target_class):
        """Make any existing class emit events for Rich status updates"""
        
        # Get event manager
        if not hasattr(cls, '_event_manager'):
            cls.create_event_integration()
        
        # Add event awareness to class
        original_setattr = target_class.__setattr__
        
        def event_aware_setattr(self, name, value):
            old_value = getattr(self, name, None) if hasattr(self, name) else None
            original_setattr(self, name, value)
            
            if old_value != value and cls._event_manager:
                event_data = EventData(
                    event_type=EventType.VARIABLE_CHANGED,
                    source_class=self.__class__.__name__,
                    variable_name=name,
                    old_value=old_value,
                    new_value=value,
                    timestamp=time.time()
                )
                cls._event_manager.emit_event(event_data)
        
        target_class.__setattr__ = event_aware_setattr
        return target_class

# Usage with your existing classes
# Make any class automatically update Rich status when variables change
@RichTracebackManager.make_class_event_aware
class YourExistingClass:
    def __init__(self):
        self.status = "idle"
        self.progress = 0

# Now variable changes automatically trigger Rich updates!
instance = YourExistingClass()
instance.status = "processing"  # Rich status updates automatically
instance.progress = 50  # Rich status updates automatically
```

---

## 🎓 **Summary & Recommendations**

### **For Your Rich Status Use Case, I Recommend:**

1. **Primary Choice**: **Custom Event Manager** (Pattern 1) - Most flexible and Android-like
2. **Secondary Choice**: **Blinker Library** - Lightweight and battle-tested
3. **Advanced Choice**: **PyQt Signals** - If you need maximum performance

### **Implementation Steps:**

1. **Start Simple**: Implement the basic EventManager class
2. **Add Rich Integration**: Connect to your RichTracebackManager
3. **Make Classes Event-Aware**: Use decorators or base classes
4. **Add Performance Features**: Debouncing, filtering, batching
5. **Test & Optimize**: Monitor performance and memory usage

### **Key Benefits You'll Get:**

✅ **Loose Coupling**: Classes don't need to know about each other  
✅ **Automatic Updates**: Rich status updates happen automatically  
✅ **Scalable**: Easy to add new listeners and event types  
✅ **Maintainable**: Clean separation of concerns  
✅ **Testable**: Easy to unit test event flows  
✅ **Android-like**: Familiar pattern from Android development  

### **Next Steps:**

1. Copy the `EventManager` and `EventData` classes
2. Integrate with your `RichTracebackManager`
3. Make your existing classes event-aware using decorators
4. Test with a few variable changes
5. Expand to cover all classes that need Rich status updates

This event-driven approach will make your software much more responsive and maintainable than the Observer pattern, while giving you the Android-style EventListener experience you wanted!

---

*📝 This guide provides multiple approaches to event-driven programming in Python, specifically tailored for Rich status updates. Choose the approach that best fits your project's complexity and performance requirements.*