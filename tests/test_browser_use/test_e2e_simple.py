"""
Simple end-to-end test to verify current setup works.

This test will reveal what's actually working vs what needs fixing.
"""
import asyncio
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("=" * 70)
print("🧪 BROWSER TOOL E2E TEST")
print("=" * 70)

# Step 1: Import Handler
print("\n1️⃣ Importing Handler...")
try:
    from src.tools.lggraph_tools.tools.browser_tool.Handler import Handler, HandlerEnums
    print("   ✅ Handler imported")
except Exception as e:
    print(f"   ❌ Failed to import Handler: {e}")
    sys.exit(1)

# Step 2: Check enum_driver_map
print("\n2️⃣ Checking enum_driver_map...")
print(f"   Handler.enum_driver_map = {Handler.enum_driver_map}")
for enum_member, driver_class in Handler.enum_driver_map.items():
    status = "✅" if driver_class is not None else "❌"
    driver_name = driver_class.__name__ if driver_class else "None"
    print(f"   {status} {enum_member.name}: {driver_name}")

# Step 3: Import drivers
print("\n3️⃣ Importing drivers...")
try:
    from src.tools.lggraph_tools.tools.browser_tool.utils import events_drivers
    print("   ✅ events_drivers imported")
except Exception as e:
    print(f"   ❌ Failed to import events_drivers: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Check if drivers registered
print("\n4️⃣ Checking registration after import...")
for enum_member, driver_class in Handler.enum_driver_map.items():
    status = "✅" if driver_class is not None else "❌"
    driver_name = driver_class.__name__ if driver_class else "None"
    print(f"   {status} {enum_member.name}: {driver_name}")

# Step 5: Test get() method
print("\n5️⃣ Testing Handler.get()...")
from src.tools.lggraph_tools.tools.browser_tool.config import BrowserRequiredConfig
from src.tools.lggraph_tools.tools.browser_tool.runner import Runner

config = BrowserRequiredConfig(query="test", file_path=Path("test.json"))
runner = Runner(config)
handler = Handler()

try:
    driver = handler.get(runner, HandlerEnums.ON_PRE_REQUIREMENTS)
    print(f"   ✅ get() returned: {type(driver).__name__}")
    print(f"   ✅ Driver instance: {driver}")
except Exception as e:
    print(f"   ❌ get() failed: {e}")
    import traceback
    traceback.print_exc()

# Step 6: Test execute() injection
print("\n6️⃣ Testing execute() method injection...")
try:
    has_execute = hasattr(driver, 'execute')
    print(f"   has execute: {has_execute}")

    if has_execute:
        print(f"   execute method: {driver.execute}")
        print(f"   is coroutine function: {asyncio.iscoroutinefunction(driver.execute)}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Step 7: Run execute()
print("\n7️⃣ Running execute()...")
async def test_execute():
    from queue import Queue
    bus = Queue()

    try:
        result = await driver.execute(bus)
        print(f"   ✅ execute() completed!")
        print(f"   Result: {result}")
        return result
    except Exception as e:
        print(f"   ❌ execute() failed: {e}")
        import traceback
        traceback.print_exc()
        return None

result = asyncio.run(test_execute())

print("\n" + "=" * 70)
print("🎉 TEST COMPLETE")
print("=" * 70)

if result:
    print("✅ All systems working!")
else:
    print("⚠️  Some issues found - check output above")
