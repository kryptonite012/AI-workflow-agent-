# 🎯 Event Listener System

A complete event-driven system for Python applications with Rich.status integration.

## 📁 **File Structure**

```
examples/event_listener/
├── main.py                    # Main demo with Rich.status integration
├── event_listener.py          # Core event system (EventListener, EventManager)
├── rich_status_listener.py    # Rich.status integration
├── event_helpers.py           # Helper functions for manual events
├── README.md                  # This file
└── simple/
    └── event_listener.py      # Simple example without Rich complexity
```

## 🚀 **Quick Start**

### **1. Run the Full Demo**
```bash
cd examples/event_listener
python main.py
```

### **2. Run Quick Test**
```bash
python main.py quick
```

### **3. Run Simple Example**
```bash
cd simple
python event_listener.py
```

## 🧠 **Core Concepts**

### **Event Types**
- `VARIABLE_CHANGED` - When any variable changes value
- `STATUS_CHANGED` - When system status updates occur  
- `ERROR_OCCURRED` - When errors need to be reported

### **Key Components**

1. **EventListener** - Main class containing EventType, EventData, EventManager
2. **EventManager** - Singleton that manages listeners and dispatches events
3. **RichStatusListener** - Automatically updates Rich.status when events occur
4. **Event Helpers** - Functions for manually emitting events

## 📊 **How It Works**

### **Automatic Variable Change Detection**
```python
class MyClass:
    def __init__(self):
        self._status = "idle"
    
    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, value):
        old_value = self._status
        self._status = value
        
        # Emit event when value changes
        if old_value != value:
            event_data = EventListener.EventData(
                event_type=EventListener.EventType.VARIABLE_CHANGED,
                source_class=self.__class__,
                variable_name="status",
                old_value=old_value,
                new_value=value,
                time_stamp=time.time()
            )
            event_manager.emit_event(event_data)

# Usage
obj = MyClass()
obj.status = "processing"  # 🎯 Rich.status updates automatically!
```

### **Manual Event Emission**
```python
from event_helpers import emit_status_event, emit_variable_event

# Emit status updates
emit_status_event(MyClass, "🚀 Processing started...")

# Emit variable changes
emit_variable_event(MyClass, "progress", 50, 75)
```

### **Rich.status Integration**
```python
from rich_status_listener import rich_status_listener

# Start Rich.status display
rich_status_listener.start_status_display("🚀 System starting...")

# Now all events automatically update the Rich.status spinner!
# Variable changes show as: "🔄 MyClass.status = processing"
# Status events show as: "📊 Processing started..."
```

## 🎯 **Features**

✅ **Automatic Event Detection** - Variables emit events when changed  
✅ **Rich.status Integration** - Live status updates with spinning indicator  
✅ **Thread-Safe** - Safe for multi-threaded applications  
✅ **Event Filtering** - Priority-based event handling  
✅ **Memory Management** - Automatic cleanup of old events  
✅ **Event History** - Track and display event statistics  
✅ **Multiple Listeners** - Multiple handlers per event type  
✅ **Async Support** - Non-blocking event emission  

## 🧪 **Examples**

### **File Processing with Auto-Updates**
```python
processor = FileProcessor()
processor.status = "processing"     # Rich.status: "🔄 FileProcessor.status = processing"
processor.progress = 50             # Rich.status: "🔄 FileProcessor.progress = 50"
processor.emit_status("✅ Done!")   # Rich.status: "📊 ✅ Done!"
```

### **Database Operations**
```python
db = DatabaseManager()
db.connection_count = 5             # Rich.status: "🔄 DatabaseManager.connection_count = 5"
db.emit_status("🔌 Connected!")     # Rich.status: "📊 🔌 Connected!"
```

## 📊 **Event Flow**

```
Variable Change → Property Setter → Event Emission → Event Manager → Rich Status Listener → Rich.status Update
```

## 🔧 **Customization**

### **Add Custom Listeners**
```python
def my_custom_listener(event_data):
    print(f"Custom: {event_data.variable_name} = {event_data.new_value}")

event_manager.register_listener(
    EventListener.EventType.VARIABLE_CHANGED,
    my_custom_listener,
    priority=5
)
```

### **Create Event-Aware Classes**
Use the property pattern shown in the examples to make any class automatically emit events when its attributes change.

## 🎉 **Benefits**

- **Loose Coupling** - Classes don't need to know about each other
- **Real-time Updates** - Rich.status updates immediately when variables change
- **Scalable** - Easy to add new listeners and event types
- **Maintainable** - Clean separation of concerns
- **Testable** - Easy to unit test event flows
- **Professional** - Enterprise-grade patterns and thread safety

## 🚀 **Integration**

To integrate this system into your project:

1. Copy the core files (`event_listener.py`, `rich_status_listener.py`, `event_helpers.py`)
2. Import and use the components in your classes
3. Start the Rich.status listener in your main application
4. Make your classes event-aware using the property pattern
5. Enjoy automatic Rich.status updates!

The system is designed to be lightweight, fast, and easy to integrate into existing codebases.