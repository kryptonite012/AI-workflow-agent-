# ⚠️ LEGACY TESTS - DO NOT RUN

These tests are from the old codebase and use deprecated APIs.

## Why They're Here

- Kept for reference
- Some may contain useful test patterns
- Can be migrated to new structure if needed

## Status

| File | Issue | Migration Status |
|------|-------|------------------|
| `test_agent_quick.py` | Uses old MCP API | ⏳ Migrated to tests/mcp/ |
| `test_handler_registration.py` | Not using pytest | ⏳ Migrated to tests/logging/ |
| `test_mcp_config.py` | Hardcoded paths | ⏳ Migrated to tests/mcp/ |
| `test_api_error_handling.py` | Not using fixtures | ⏳ Migrated to tests/api/ |
| `test_direct_logger.py` | Standalone script | ⏳ Migrated to tests/logging/ |
| `test_final_validation.py` | Integration test | ⏳ Migrated to tests/integration/ |
| `test_comprehensive_workflow.py` | Large integration | ⏳ Migrated to tests/integration/ |

## ❌ DO NOT RUN THESE TESTS

They will likely fail due to:
1. Missing imports
2. Changed APIs
3. Hardcoded paths
4. Not using pytest patterns

Use the new tests in:
- `tests/unit/`
- `tests/mcp/`
- `tests/logging/`
- `tests/api/`
- `tests/integration/`
- `tests/browser_tool/`
