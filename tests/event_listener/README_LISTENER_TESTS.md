# 🧪 Event Listener Test Suite

Comprehensive testing system for the RichStatusListener event system with realistic multi-threaded scenarios.

## 📁 Test Files

### `quick_validation.py`
**Purpose**: Quick validation to ensure basic functionality works
**Usage**: `python tests/quick_validation.py`
**What it tests**:
- Import validation
- Listener creation
- Status display start/stop
- Basic event emission

### `run_listener_test.py`
**Purpose**: Interactive test runner with multiple test modes
**Usage**: `python tests/run_listener_test.py`
**Test modes**:
1. **Basic Test** - Simple functionality check
2. **Realistic Test** - Multi-threaded request processing simulation
3. **Continuous Test** - Runs until working properly
4. **All Tests** - Runs everything

### `test_event_listener_realistic.py`
**Purpose**: Comprehensive realistic test with detailed validation
**Usage**: `python tests/test_event_listener_realistic.py`
**Features**:
- Multi-threaded status updates
- Request counting simulation
- Milestone-based status changes
- Comprehensive test result analysis
- Continuous testing mode

## 🎯 Test Scenario (As Requested)

The realistic test simulates this exact scenario:

1. **Main Thread**: Shows "generating heading..." status
2. **Background Thread**: Processes requests concurrently
3. **Status Updates**:
   - 0-9 requests: `"🔄 generating heading..."`
   - 10 requests: `"🔄 generating heading... (requests done 10)"`
   - 30 requests: `"🔄 generating heading... (requests done 30)"`
   - 40 requests: `"⏳ generating the request is 40 wait for sec"` (waits 2 seconds)
   - Final: `"✅ heading generation completed!"`

## 🚀 Quick Start

### Step 1: Validate System
```bash
python tests/quick_validation.py
```

### Step 2: Run Interactive Tests
```bash
python tests/run_listener_test.py
```

### Step 3: Run Comprehensive Test
```bash
python tests/test_event_listener_realistic.py
```

### Step 4: Continuous Testing (Until Working)
```bash
python tests/test_event_listener_realistic.py --continuous
```

## 🔍 What Gets Tested

### Thread Safety
- ✅ Concurrent status updates from multiple threads
- ✅ Thread-safe event emission
- ✅ Proper locking mechanisms

### Event System
- ✅ Event creation and emission
- ✅ Event filtering and targeting
- ✅ Metadata handling

### Status Display
- ✅ Rich.status integration
- ✅ Real-time status updates
- ✅ Status lifecycle management

### Realistic Behavior
- ✅ Timing that looks realistic
- ✅ Progressive status updates
- ✅ Milestone-based changes
- ✅ Background processing simulation

## 📊 Test Results

The comprehensive test provides:
- **Detailed timing analysis**
- **Event sequence validation**
- **Thread safety confirmation**
- **Visual status update verification**
- **Pass/fail validation for each milestone**

## 🎯 Success Criteria

A test passes when:
- ✅ All status milestones are reached correctly
- ✅ Thread-safe updates work without conflicts
- ✅ Timing appears realistic and smooth
- ✅ Event filtering works (only targeted listener updates)
- ✅ No exceptions or errors occur

## 🔧 Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Make sure you're running from the project root
cd /path/to/AI_llm
python tests/quick_validation.py
```

**Status Not Updating**:
- Check that the listener is properly created
- Verify event emission is working
- Ensure metadata filtering is correct

**Threading Issues**:
- Check for proper thread synchronization
- Verify status updates are thread-safe
- Look for race conditions in status updates

### Debug Mode

Add debug prints to see what's happening:
```python
# In your test, add:
print(f"Event emitted: {event_data}")
print(f"Listener ID: {id(listener)}")
print(f"Metadata: {event_data.meta_data}")
```

## 🎉 Expected Output

When working correctly, you should see:
1. **Status display** with spinning indicator
2. **Real-time updates** as requests are processed
3. **Milestone messages** in the console
4. **Smooth transitions** between status messages
5. **Final completion** message

The test will look and feel like a real application with realistic timing and behavior!

## 📝 Notes

- Tests are designed to run continuously until working properly
- Each test creates fresh listener instances to avoid conflicts
- Realistic timing makes the test feel like a real application
- Thread safety is thoroughly tested with concurrent operations
- All tests include comprehensive validation and reporting