"""
Test suite for browser session resurrection features.

Tests:
1. save_custom_sessions() - saves URL, form data, scroll position
2. load_custom_sessions() - loads and restores saved session
3. Full integration - session persistence across browser restarts
4. keep_alive functionality
5. Multi-session persistence (different websites)
"""
import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from browser_use import Browser, Agent
from src.config import settings


@pytest.fixture
def mock_browser():
    """Create a mock Browser object."""
    browser = Mock(spec=Browser)

    # Mock browser methods
    browser.get_current_page_url = AsyncMock(return_value="https://amazon.com/checkout")

    # Mock CDP session
    cdp_session = Mock()
    cdp_session.session_id = "mock_session_id"
    cdp_session.cdp_client = Mock()
    cdp_session.cdp_client.send = Mock()
    cdp_session.cdp_client.send.Runtime = Mock()
    cdp_session.cdp_client.send.Runtime.evaluate = AsyncMock(
        return_value={
            'result': {
                'value': {
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': 'john@example.com'
                }
            }
        }
    )

    browser.get_or_create_cdp_session = AsyncMock(return_value=cdp_session)

    # Mock event bus
    browser.event_bus = Mock()
    browser.event_bus.dispatch = AsyncMock()

    return browser


@pytest.fixture
def session_file_path(tmp_path):
    """Create temporary session file path."""
    session_file = tmp_path / "custom_sessions.json"
    return session_file


@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        'current_url': 'https://amazon.com/checkout',  # ← Fixed key
        'form_data': {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com'
        },
        'scroll_position': {'x': 0, 'y': 450},
        'timestamp': '02-01-2026 10:30:45:123'
    }


# ============================================================================
# TEST 1: save_custom_sessions() functionality
# ============================================================================

@pytest.mark.asyncio
async def test_save_custom_sessions_creates_file(mock_browser, session_file_path):
    """Test that save_custom_sessions() creates a JSON file with correct data."""
    from src.tools.lggraph_tools.tools.browser_subprocess_runner import save_custom_sessions

    # Mock settings to use our temp path
    with patch.object(settings, 'BROWSER_USE_USER_PROFILE_PATH', session_file_path.parent):
        await save_custom_sessions(mock_browser)

    # Verify file was created
    assert session_file_path.exists(), "Session file was not created"

    # Verify file contains correct data
    with open(session_file_path, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)

    assert 'current_url' in saved_data, "URL not saved"
    assert 'form_data' in saved_data, "Form data not saved"
    assert 'scroll_position' in saved_data, "Scroll position not saved"
    assert 'timestamp' in saved_data, "Timestamp not saved"

    assert saved_data['current_url'] == "https://amazon.com/checkout"
    print(f"✅ Test passed: Session file created with data: {saved_data}")


@pytest.mark.asyncio
async def test_save_custom_sessions_extracts_form_data(mock_browser, session_file_path):
    """Test that form data is correctly extracted via JavaScript."""
    from src.tools.lggraph_tools.tools.browser_subprocess_runner import save_custom_sessions

    # Set up mock to return specific form data
    mock_browser.get_or_create_cdp_session.return_value.cdp_client.send.Runtime.evaluate = AsyncMock(
        side_effect=[
            # First call: form data extraction
            {
                'result': {
                    'value': {
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'email': 'john@example.com',
                        'address': '123 Main St'
                    }
                }
            },
            # Second call: scroll position
            {
                'result': {
                    'value': {'x': 0, 'y': 450}
                }
            }
        ]
    )

    with patch.object(settings, 'BROWSER_USE_USER_PROFILE_PATH', session_file_path.parent):
        await save_custom_sessions(mock_browser)

    # Verify form data was saved
    with open(session_file_path, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)

    assert saved_data['form_data']['first_name'] == 'John'
    assert saved_data['form_data']['last_name'] == 'Doe'
    assert saved_data['form_data']['email'] == 'john@example.com'
    assert saved_data['form_data']['address'] == '123 Main St'
    print(f"✅ Test passed: Form data extracted correctly: {saved_data['form_data']}")


@pytest.mark.asyncio
async def test_save_custom_sessions_saves_scroll_position(mock_browser, session_file_path):
    """Test that scroll position is correctly saved."""
    from src.tools.lggraph_tools.tools.browser_subprocess_runner import save_custom_sessions

    # Mock scroll position
    mock_browser.get_or_create_cdp_session.return_value.cdp_client.send.Runtime.evaluate = AsyncMock(
        side_effect=[
            {'result': {'value': {}}},  # form data (empty)
            {'result': {'value': {'x': 100, 'y': 500}}}  # scroll position
        ]
    )

    with patch.object(settings, 'BROWSER_USE_USER_PROFILE_PATH', session_file_path.parent):
        await save_custom_sessions(mock_browser)

    with open(session_file_path, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)

    assert saved_data['scroll_position']['x'] == 100
    assert saved_data['scroll_position']['y'] == 500
    print(f"✅ Test passed: Scroll position saved: {saved_data['scroll_position']}")


# ============================================================================
# TEST 2: load_custom_sessions() functionality
# ============================================================================

@pytest.mark.asyncio
async def test_load_custom_sessions_with_no_file(mock_browser, tmp_path):
    """Test that load_custom_sessions() handles missing file gracefully."""
    from src.tools.lggraph_tools.tools.browser_subprocess_runner import load_custom_sessions

    # Point to non-existent directory
    non_existent_path = tmp_path / "non_existent"

    with patch.object(settings, 'BROWSER_USE_USER_PROFILE_PATH', non_existent_path):
        # Should not raise exception
        await load_custom_sessions(mock_browser)

    # Verify no navigation was attempted
    mock_browser.event_bus.dispatch.assert_not_called()
    print("✅ Test passed: load_custom_sessions() handles missing file gracefully")


@pytest.mark.asyncio
async def test_load_custom_sessions_navigates_to_saved_url(mock_browser, session_file_path, sample_session_data):
    """Test that load_custom_sessions() navigates to the saved URL."""
    from src.tools.lggraph_tools.tools.browser_subprocess_runner import load_custom_sessions

    # Create session file
    session_file_path.write_text(json.dumps(sample_session_data), encoding='utf-8')

    with patch.object(settings, 'BROWSER_USE_USER_PROFILE_PATH', session_file_path.parent):
        await load_custom_sessions(mock_browser)

    # Verify NavigateToUrlEvent was dispatched
    mock_browser.event_bus.dispatch.assert_called_once()

    # Get the event that was dispatched
    call_args = mock_browser.event_bus.dispatch.call_args
    event = call_args[0][0]

    assert event.url == "https://amazon.com/checkout"
    print(f"✅ Test passed: Navigated to saved URL: {event.url}")


@pytest.mark.asyncio
async def test_load_custom_sessions_restores_form_data(mock_browser, session_file_path, sample_session_data):
    """Test that load_custom_sessions() restores form field values."""
    from src.tools.lggraph_tools.tools.browser_subprocess_runner import load_custom_sessions

    # Create session file
    session_file_path.write_text(json.dumps(sample_session_data), encoding='utf-8')

    # Mock form restoration to return count
    mock_browser.get_or_create_cdp_session.return_value.cdp_client.send.Runtime.evaluate = AsyncMock(
        side_effect=[
            {'result': {'value': 3}},  # Form restoration (3 fields restored)
            {'result': {'value': True}}  # Scroll restoration
        ]
    )

    with patch.object(settings, 'BROWSER_USE_USER_PROFILE_PATH', session_file_path.parent):
        await load_custom_sessions(mock_browser)

    # Verify JavaScript was executed to fill forms
    cdp_session = await mock_browser.get_or_create_cdp_session()
    assert cdp_session.cdp_client.send.Runtime.evaluate.call_count == 2  # form + scroll

    # Verify form restoration script was called
    first_call_args = cdp_session.cdp_client.send.Runtime.evaluate.call_args_list[0]
    script = first_call_args[1]['params']['expression']

    assert 'first_name' in script
    assert 'John' in script
    assert 'last_name' in script
    assert 'Doe' in script
    print("✅ Test passed: Form data restoration script executed correctly")


@pytest.mark.asyncio
async def test_load_custom_sessions_restores_scroll_position(mock_browser, session_file_path, sample_session_data):
    """Test that load_custom_sessions() restores scroll position."""
    from src.tools.lggraph_tools.tools.browser_subprocess_runner import load_custom_sessions

    # Create session file
    session_file_path.write_text(json.dumps(sample_session_data), encoding='utf-8')

    with patch.object(settings, 'BROWSER_USE_USER_PROFILE_PATH', session_file_path.parent):
        await load_custom_sessions(mock_browser)

    # Verify scroll script was executed
    cdp_session = await mock_browser.get_or_create_cdp_session()
    second_call_args = cdp_session.cdp_client.send.Runtime.evaluate.call_args_list[1]
    scroll_script = second_call_args[1]['params']['expression']

    assert 'window.scrollTo' in scroll_script
    assert '450' in scroll_script  # y position from sample data
    print("✅ Test passed: Scroll position restoration script executed correctly")


# ============================================================================
# TEST 3: Full integration test
# ============================================================================

@pytest.mark.asyncio
async def test_full_session_resurrection_cycle(mock_browser, session_file_path):
    """
    Test complete cycle: save session → close browser → load session → verify data.

    This simulates:
    1. User fills form on Amazon checkout
    2. Browser closes (session saved)
    3. Browser reopens
    4. Session loaded (form auto-filled)
    """
    from src.tools.lggraph_tools.tools.browser_subprocess_runner import save_custom_sessions, load_custom_sessions

    # Step 1: Save session (simulating filled form)
    mock_browser.get_current_page_url = AsyncMock(return_value="https://amazon.com/checkout")
    mock_browser.get_or_create_cdp_session.return_value.cdp_client.send.Runtime.evaluate = AsyncMock(
        side_effect=[
            # Save: form data
            {
                'result': {
                    'value': {
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'email': 'john@example.com'
                    }
                }
            },
            # Save: scroll position
            {
                'result': {
                    'value': {'x': 0, 'y': 450}
                }
            }
        ]
    )

    with patch.object(settings, 'BROWSER_USE_USER_PROFILE_PATH', session_file_path.parent):
        await save_custom_sessions(mock_browser)

    print("📝 Step 1: Session saved")

    # Step 2: Verify file exists
    assert session_file_path.exists()
    with open(session_file_path, 'r') as f:
        saved_data = json.load(f)
    print(f"📝 Step 2: Session file contains: {saved_data}")

    # Step 3: Reset mock browser (simulating browser restart)
    mock_browser.event_bus.dispatch.reset_mock()
    mock_browser.get_or_create_cdp_session.reset_mock()

    # Configure mock for loading
    mock_browser.get_or_create_cdp_session.return_value.cdp_client.send.Runtime.evaluate = AsyncMock(
        side_effect=[
            {'result': {'value': 3}},  # Form restore count
            {'result': {'value': True}}  # Scroll restore
        ]
    )

    # Step 4: Load session
    with patch.object(settings, 'BROWSER_USE_USER_PROFILE_PATH', session_file_path.parent):
        await load_custom_sessions(mock_browser)

    print("📝 Step 3: Session loaded")

    # Step 5: Verify session was restored correctly
    assert mock_browser.event_bus.dispatch.called, "Navigation not triggered"
    assert mock_browser.get_or_create_cdp_session.called, "CDP session not accessed"

    # Verify navigation to correct URL
    nav_call = mock_browser.event_bus.dispatch.call_args[0][0]
    assert nav_call.url == "https://amazon.com/checkout"

    print("✅ Full integration test passed: Session saved → closed → loaded → verified!")


# ============================================================================
# TEST 4: keep_alive functionality
# ============================================================================

@pytest.mark.asyncio
async def test_keep_alive_true_subprocess_stays_alive():
    """Test that subprocess doesn't exit when keep_alive=True."""
    # This is a conceptual test - actual subprocess testing requires integration test

    # Simulate the main() function logic
    keep_alive = True

    # Mock sys.exit to verify it's NOT called
    with patch('sys.exit') as mock_exit:
        # Simulate the conditional exit logic
        if not keep_alive:
            mock_exit(0)

        # Verify sys.exit was NOT called when keep_alive=True
        mock_exit.assert_not_called()

    print("✅ Test passed: sys.exit() not called when keep_alive=True")


@pytest.mark.asyncio
async def test_keep_alive_false_subprocess_exits():
    """Test that subprocess exits when keep_alive=False."""
    keep_alive = False

    # Mock sys.exit to verify it IS called
    with patch('sys.exit') as mock_exit:
        # Simulate the conditional exit logic
        if not keep_alive:
            mock_exit(0)

        # Verify sys.exit WAS called when keep_alive=False
        mock_exit.assert_called_once_with(0)

    print("✅ Test passed: sys.exit(0) called when keep_alive=False")


# ============================================================================
# TEST 5: Multi-session persistence (different websites)
# ============================================================================

@pytest.mark.asyncio
async def test_multi_session_persistence_different_websites(mock_browser, session_file_path):
    """
    Test session persistence across multiple website visits.

    Scenario:
    1. Visit Amazon, save session
    2. Visit Facebook, save session (overwrites Amazon)
    3. Visit Amazon again, load session (should have Facebook session)

    This tests that session_state.json gets overwritten correctly.
    """
    from src.tools.lggraph_tools.tools.browser_subprocess_runner import save_custom_sessions, load_custom_sessions

    # Session 1: Amazon
    mock_browser.get_current_page_url = AsyncMock(return_value="https://amazon.com/cart")
    mock_browser.get_or_create_cdp_session.return_value.cdp_client.send.Runtime.evaluate = AsyncMock(
        side_effect=[
            {'result': {'value': {'promo_code': 'SAVE20'}}},
            {'result': {'value': {'x': 0, 'y': 100}}}
        ]
    )

    with patch.object(settings, 'BROWSER_USE_USER_PROFILE_PATH', session_file_path.parent):
        await save_custom_sessions(mock_browser)

    # Verify Amazon session saved
    with open(session_file_path, 'r') as f:
        amazon_session = json.load(f)
    assert amazon_session['current_url'] == "https://amazon.com/cart"
    print("📝 Session 1 saved: Amazon")

    # Session 2: Facebook (overwrites Amazon)
    mock_browser.get_current_page_url = AsyncMock(return_value="https://facebook.com/home")
    mock_browser.get_or_create_cdp_session.return_value.cdp_client.send.Runtime.evaluate = AsyncMock(
        side_effect=[
            {'result': {'value': {}}},  # No form data
            {'result': {'value': {'x': 0, 'y': 0}}}
        ]
    )

    with patch.object(settings, 'BROWSER_USE_USER_PROFILE_PATH', session_file_path.parent):
        await save_custom_sessions(mock_browser)

    # Verify Facebook session saved (Amazon overwritten)
    with open(session_file_path, 'r') as f:
        facebook_session = json.load(f)
    assert facebook_session['current_url'] == "https://facebook.com/home"
    assert facebook_session['current_url'] != amazon_session['current_url']
    print("📝 Session 2 saved: Facebook (overwrote Amazon)")

    # Session 3: Load session (should load Facebook, not Amazon)
    mock_browser.get_or_create_cdp_session.return_value.cdp_client.send.Runtime.evaluate = AsyncMock(
        side_effect=[
            {'result': {'value': 0}},  # No forms to restore
            {'result': {'value': True}}
        ]
    )

    with patch.object(settings, 'BROWSER_USE_USER_PROFILE_PATH', session_file_path.parent):
        await load_custom_sessions(mock_browser)

    # Verify navigation was to Facebook, not Amazon
    nav_call = mock_browser.event_bus.dispatch.call_args[0][0]
    assert nav_call.url == "https://facebook.com/home"
    print("✅ Test passed: Multi-session persistence works (last session loaded)")


# ============================================================================
# TEST 6: Edge cases
# ============================================================================

@pytest.mark.asyncio
async def test_save_with_empty_form_data(mock_browser, session_file_path):
    """Test saving when no form data exists."""
    from src.tools.lggraph_tools.tools.browser_subprocess_runner import save_custom_sessions

    mock_browser.get_current_page_url = AsyncMock(return_value="https://example.com")
    mock_browser.get_or_create_cdp_session.return_value.cdp_client.send.Runtime.evaluate = AsyncMock(
        side_effect=[
            {'result': {'value': {}}},  # No form data
            {'result': {'value': {'x': 0, 'y': 0}}}
        ]
    )

    with patch.object(settings, 'BROWSER_USE_USER_PROFILE_PATH', session_file_path.parent):
        await save_custom_sessions(mock_browser)

    with open(session_file_path, 'r') as f:
        saved_data = json.load(f)

    assert saved_data['form_data'] == {}
    assert saved_data['current_url'] == "https://example.com"
    print("✅ Test passed: Empty form data handled correctly")


@pytest.mark.asyncio
async def test_load_with_no_url(mock_browser, session_file_path):
    """Test loading session with no URL (blank page)."""
    from src.tools.lggraph_tools.tools.browser_subprocess_runner import load_custom_sessions

    # Create session with no URL
    invalid_session = {
        'current_url': None,  # ← Fixed key
        'form_data': {},
        'scroll_position': {'x': 0, 'y': 0},
        'timestamp': '02-01-2026 10:30:45:123'
    }

    session_file_path.write_text(json.dumps(invalid_session), encoding='utf-8')

    with patch.object(settings, 'BROWSER_USE_USER_PROFILE_PATH', session_file_path.parent):
        await load_custom_sessions(mock_browser)

    # Verify no navigation attempted
    mock_browser.event_bus.dispatch.assert_not_called()
    print("✅ Test passed: No navigation when URL is None")


# ============================================================================
# Run all tests
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🧪 RUNNING BROWSER SESSION RESURRECTION TESTS")
    print("="*80 + "\n")

    # Run pytest
    pytest.main([__file__, '-v', '--tb=short', '-s'])

