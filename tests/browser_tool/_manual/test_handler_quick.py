
"""Quick test to verify Handler system works."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("🧪 HANDLER SYSTEM TEST")
print("=" * 70)

# Import drivers to trigger registration
print("\n1️⃣ Importing drivers...")
from src.tools.lggraph_tools.tools.browser_tool.utils import events_drivers
from src.tools.lggraph_tools.tools.browser_tool.Handler import Handler, HandlerEnums
from src.tools.lggraph_tools.tools.browser_tool.config import BrowserRequiredConfig
from src.tools.lggraph_tools.tools.browser_tool.runner import Runner

print("   ✅ Imports successful")

# Check registration
print("\n2️⃣ Checking driver registration...")
all_registered = True
for enum_member, driver_class in Handler.enum_driver_map.items():
    status = "✅" if driver_class else "❌"
    name = driver_class.__name__ if driver_class else "None"
    print(f"   {status} {enum_member.name}: {name}")
    if driver_class is None:
        all_registered = False

if all_registered:
    print("   ✅ All drivers registered!")
else:
    print("   ❌ Some drivers missing!")
    sys.exit(1)

# Test get() method
print("\n3️⃣ Testing Handler.get()...")
config = BrowserRequiredConfig(query="test", file_path=Path("test.json"))
runner = Runner(config)
handler = Handler()

driver = handler.get(runner, HandlerEnums.ON_PRE_REQUIREMENTS)
print(f"   ✅ Got driver: {type(driver).__name__}")

# Test execute() injection
print("\n4️⃣ Testing execute() method...")
print(f"   Has execute: {hasattr(driver, 'execute')}")
print(f"   Is async: {asyncio.iscoroutinefunction(driver.execute)}")

# Run execute()
print("\n5️⃣ Running execute()...")
async def test_run():
    from queue import Queue
    bus = Queue()
    try:
        result = await driver.execute(bus)
        print(f"   ✅ Execute completed!")
        print(f"   Result keys: {list(result.keys())}")
        return True
    except Exception as e:
        print(f"   ❌ Execute failed: {e}")
        import traceback
        traceback.print_exc()
        return False

success = asyncio.run(test_run())

print("\n" + "=" * 70)
if success:
    print("✅ ALL TESTS PASSED!")
else:
    print("❌ TESTS FAILED!")
print("=" * 70)
