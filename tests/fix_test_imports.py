"""
Automated Import Fixer for All Test Files

This script automatically adds proper path setup to all Python test files
that import from 'src' package.
"""
import re
from pathlib import Path


def get_path_setup_code(file_path: Path) -> str:
    """
    Generate the appropriate path setup code based on file location.

    Args:
        file_path: Path to the test file

    Returns:
        String containing the path setup code
    """
    # Calculate how many levels up to get to project root
    # tests/ → 1 level
    # tests/subfolder/ → 2 levels
    # tests/subfolder/subsubfolder/ → 3 levels

    tests_dir = Path(__file__).parent
    relative_path = file_path.relative_to(tests_dir)
    levels_up = len(relative_path.parts) - 1  # -1 because we don't count the file itself

    if levels_up == 0:
        # File is directly in tests/
        parents_count = 1
    else:
        # File is in a subdirectory
        parents_count = levels_up + 1

    return f"""import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[{parents_count}]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
"""


def has_src_import(content: str) -> bool:
    """Check if file has imports from 'src' package."""
    return bool(re.search(r'from\s+src[.\w]*\s+import', content) or
                re.search(r'import\s+src[.\w]*', content))


def has_path_setup(content: str) -> bool:
    """Check if file already has proper path setup."""
    return 'sys.path' in content and 'project_root' in content


def fix_file_imports(file_path: Path, dry_run=False) -> tuple[bool, str]:
    """
    Fix imports in a single test file.

    Args:
        file_path: Path to the file to fix
        dry_run: If True, don't actually write changes

    Returns:
        (success, message) tuple
    """
    try:
        # Read file
        content = file_path.read_text(encoding='utf-8')

        # Check if file needs fixing
        if not has_src_import(content):
            return True, f"SKIP: No 'src' imports found"

        if has_path_setup(content):
            # Check if it's using the correct path setup
            if 'project_root = Path(__file__).resolve().parents[' in content:
                return True, f"SKIP: Already has proper path setup"

        # Generate path setup code
        path_setup = get_path_setup_code(file_path)

        # Find where to insert the path setup
        # Look for the first import statement or docstring
        lines = content.split('\n')
        insert_index = 0

        # Skip docstring if present
        in_docstring = False
        for i, line in enumerate(lines):
            stripped = line.strip()

            # Handle docstrings
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_docstring:
                    in_docstring = False
                    insert_index = i + 1
                    continue
                else:
                    in_docstring = True
                    continue

            if in_docstring:
                continue

            # Skip comments and empty lines
            if not stripped or stripped.startswith('#'):
                continue

            # Found first non-comment, non-docstring line
            insert_index = i
            break

        # Remove old path setup if exists
        cleaned_lines = []
        skip_next = 0
        for i, line in enumerate(lines):
            if skip_next > 0:
                skip_next -= 1
                continue

            # Skip old path setup patterns
            if 'sys.path.insert' in line or 'sys.path.append' in line:
                # Skip this line and look for related imports
                if i > 0 and ('import sys' in lines[i-1] or 'from pathlib import Path' in lines[i-1]):
                    cleaned_lines.pop()  # Remove previous import
                continue

            if 'project_root' in line and '=' in line:
                continue

            cleaned_lines.append(line)

        # Insert new path setup
        final_lines = cleaned_lines[:insert_index] + path_setup.split('\n') + [''] + cleaned_lines[insert_index:]

        new_content = '\n'.join(final_lines)

        if not dry_run:
            file_path.write_text(new_content, encoding='utf-8')

        return True, "FIXED: Added proper path setup"

    except Exception as e:
        return False, f"ERROR: {e}"


def fix_all_test_files(dry_run=False):
    """Fix all Python test files in the tests directory."""
    tests_dir = Path(__file__).parent

    print("="*80)
    print("AUTOMATED TEST IMPORT FIXER")
    print("="*80)
    print(f"\nScanning directory: {tests_dir}")
    print(f"Dry run: {dry_run}\n")

    # Find all Python files
    test_files = list(tests_dir.rglob('*.py'))

    # Exclude this script and __pycache__
    test_files = [f for f in test_files if '__pycache__' not in str(f) and f.name != Path(__file__).name]

    print(f"Found {len(test_files)} Python files\n")

    fixed_count = 0
    skipped_count = 0
    error_count = 0

    for file_path in sorted(test_files):
        relative_path = file_path.relative_to(tests_dir)
        success, message = fix_file_imports(file_path, dry_run=dry_run)

        status = "✅" if success else "❌"
        if "SKIP" in message:
            status = "⏭️"
            skipped_count += 1
        elif "FIXED" in message:
            fixed_count += 1
        elif "ERROR" in message:
            error_count += 1

        print(f"{status} {relative_path}")
        print(f"   {message}\n")

    print("="*80)
    print(f"SUMMARY:")
    print(f"  Fixed:   {fixed_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors:  {error_count}")
    print(f"  Total:   {len(test_files)}")
    print("="*80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Fix imports in all test files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    parser.add_argument('--apply', action='store_true', help='Actually apply the fixes')

    args = parser.parse_args()

    if args.apply:
        fix_all_test_files(dry_run=False)
    else:
        print("\n⚠️  Running in DRY RUN mode. Use --apply to make actual changes.\n")
        fix_all_test_files(dry_run=True)

