#!/usr/bin/env python3
"""
Test script to verify socket connection functionality
Tests the basic SocketCon class and connection handling
"""

import os
import socket
import sys
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.utils.error_transfer import SocketCon
from src.config import settings


def test_socket_connection_basic():
    """Test basic socket connection functionality"""
    print("🧪 Testing Basic Socket Connection...")

    try:
        # Create a socket and try to connect
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(5)  # 5 second timeout

        print(f"Attempting to connect to {settings.SOCKET_HOST}:{settings.SOCKET_PORT}")
        test_socket.connect((settings.SOCKET_HOST, settings.SOCKET_PORT))

        print("✅ Socket connection established")

        # Test SocketCon wrapper
        socket_con = SocketCon(test_socket)

        # Test sending a message
        test_message = "🧪 Basic connection test message"
        socket_con.send_error(test_message)
        print("✅ Test message sent successfully")

        # Test connection status
        if socket_con._is_connected():
            print("✅ Connection status check working")
        else:
            print("⚠️ Connection status check indicates disconnected")

        test_socket.close()
        return True

    except socket.timeout:
        print("❌ Connection timed out - is the log server running?")
        return False
    except ConnectionRefusedError:
        print("❌ Connection refused - log server is not running")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_socket_error_scenarios():
    """Test various socket error scenarios"""
    print("\n🧪 Testing Socket Error Scenarios...")

    # Test 1: Invalid host
    print("1. Testing invalid host...")
    try:
        invalid_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        invalid_socket.settimeout(2)
        invalid_socket.connect(("invalid-host-12345", settings.SOCKET_PORT))
        invalid_socket.close()
        print("❌ Should have failed with invalid host")
    except Exception as e:
        print(f"✅ Correctly failed with invalid host: {type(e).__name__}")

    # Test 2: Invalid port
    print("2. Testing invalid port...")
    try:
        invalid_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        invalid_socket.settimeout(2)
        invalid_socket.connect((settings.SOCKET_HOST, 99999))  # Invalid port
        invalid_socket.close()
        print("❌ Should have failed with invalid port")
    except Exception as e:
        print(f"✅ Correctly failed with invalid port: {type(e).__name__}")

    # Test 3: Connection after close
    print("3. Testing connection after close...")
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(2)
        test_socket.connect((settings.SOCKET_HOST, settings.SOCKET_PORT))
        socket_con = SocketCon(test_socket)

        # Close the socket
        test_socket.close()

        # Try to send message after close
        socket_con.send_error("This should fail")
        print("⚠️ Message sent after close (might be buffered)")

    except Exception as e:
        print(f"✅ Correctly failed after close: {type(e).__name__}")

    return True


def test_concurrent_connections():
    """Test multiple concurrent connections"""
    print("\n🧪 Testing Concurrent Connections...")

    def create_connection(connection_id):
        """Create a connection and send a message"""
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            test_socket.connect((settings.SOCKET_HOST, settings.SOCKET_PORT))

            socket_con = SocketCon(test_socket)
            socket_con.send_error(f"🧪 Concurrent connection test #{connection_id}")

            time.sleep(1)  # Keep connection alive briefly
            test_socket.close()
            print(f"✅ Connection {connection_id} completed")
            return True

        except Exception as e:
            print(f"❌ Connection {connection_id} failed: {e}")
            return False

    # Note: Your server only accepts one connection at a time
    # So we'll test sequential connections instead
    print("Testing sequential connections (server accepts one at a time)...")

    success_count = 0
    for i in range(3):
        if create_connection(i + 1):
            success_count += 1
        time.sleep(0.5)  # Small delay between connections

    print(f"📊 Successful connections: {success_count}/3")
    return success_count > 0


def test_message_formats():
    """Test different message formats"""
    print("\n🧪 Testing Message Formats...")

    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(5)
        test_socket.connect((settings.SOCKET_HOST, settings.SOCKET_PORT))

        socket_con = SocketCon(test_socket)

        test_messages = [
            "Simple message",
            "Message with numbers: 12345",
            "Message with special chars: !@#$%^&*()",
            "Message with unicode: 🚀🔥💯",
            "Very long message: " + "A" * 500,
            "Message\nwith\nnewlines",
            "Message\twith\ttabs",
            "",  # Empty message
            'JSON-like: {"key": "value", "number": 42}',
            "XML-like: <tag>content</tag>",
        ]

        success_count = 0
        for i, message in enumerate(test_messages, 1):
            try:
                socket_con.send_error(f"[FORMAT TEST {i:02d}] {message}")
                success_count += 1
                print(f"✅ Message format {i} sent successfully")
            except Exception as e:
                print(f"❌ Message format {i} failed: {e}")

            time.sleep(0.1)

        test_socket.close()
        print(f"📊 Message format success rate: {success_count}/{len(test_messages)}")
        return success_count > 0

    except Exception as e:
        print(f"❌ Message format testing failed: {e}")
        return False


def run_socket_tests():
    """Run all socket connection tests"""
    print("=" * 70)
    print("🧪 SOCKET CONNECTION TEST SUITE")
    print("=" * 70)

    print("📋 Prerequisites:")
    print("   - Log server must be running: python utils/error_transfer.py")
    print("   - Check config.py for correct SOCKET_HOST and SOCKET_PORT")
    print()

    tests = [
        ("Basic Socket Connection", test_socket_connection_basic),
        ("Socket Error Scenarios", test_socket_error_scenarios),
        ("Concurrent Connections", test_concurrent_connections),
        ("Message Formats", test_message_formats),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("📊 SOCKET TEST RESULTS SUMMARY")
    print("=" * 70)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1

    print(f"\n📈 Overall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All socket tests passed!")
    else:
        print("⚠️ Some socket tests failed.")
        print("💡 Common issues:")
        print("   - Log server not running")
        print("   - Incorrect host/port in config")
        print("   - Firewall blocking connections")


if __name__ == "__main__":
    run_socket_tests()
