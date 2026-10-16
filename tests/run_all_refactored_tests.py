"""
Master test runner - validates all refactored tests.

Run: python tests/run_all_refactored_tests.py
"""
import subprocess
import sys
from pathlib import Path

print("=" * 80)
print("🧪 RUNNING ALL REFACTORED TESTS")
print("=" * 80)

# Get project root
project_root = Path(__file__).parent.parent

# Test directories to run
test_dirs = [
    "tests/unit/",
    "tests/mcp/",
    "tests/logging/",
    "tests/api/",
    "tests/browser_tool/",
    "tests/integration/",
]

results = {}

for test_dir in test_dirs:
    full_path = project_root / test_dir
    if not full_path.exists():
        print(f"\n⚠️  {test_dir} does not exist, skipping...")
        continue

    print(f"\n{'='*60}")
    print(f"📁 Running: {test_dir}")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(full_path), "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=str(project_root)
    )

    # Parse output for summary
    output_lines = result.stdout.split('\n')
    for line in output_lines:
        if 'passed' in line or 'failed' in line or 'error' in line:
            print(f"  {line.strip()}")

    results[test_dir] = result.returncode

print("\n" + "=" * 80)
print("📊 SUMMARY")
print("=" * 80)

total_passed = 0
total_failed = 0

for test_dir, returncode in results.items():
    status = "✅ PASSED" if returncode == 0 else "❌ FAILED"
    print(f"  {test_dir}: {status}")
    if returncode == 0:
        total_passed += 1
    else:
        total_failed += 1

print(f"\nTotal: {total_passed} passed, {total_failed} failed")
print("=" * 80)

sys.exit(0 if total_failed == 0 else 1)
