#!/usr/bin/env python3
"""
Unit tests demonstrating classes, objects, and design patterns
Educational examples for understanding OOP concepts
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# Regular class - creates new objects each time
class RegularManager:
    def __init__(self):
        self.connection_id = id(self)  # Unique ID for each object
        print(f"Created RegularManager with ID: {self.connection_id}")

    def get_id(self):
        return self.connection_id


# Singleton class - always returns the same object
class SingletonManager:
    _instance = None
    _connection_id = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SingletonManager, cls).__new__(cls)
            cls._connection_id = id(cls._instance)
            print(f"Created SingletonManager with ID: {cls._connection_id}")
        else:
            print(f"Returning existing SingletonManager with ID: {cls._connection_id}")
        return cls._instance

    def get_id(self):
        return self._connection_id


def test_regular_class():
    """Test regular class behavior - creates multiple objects"""
    print("🧪 Testing Regular Class (Multiple Objects)")
    print("-" * 50)

    regular1 = RegularManager()
    regular2 = RegularManager()
    regular3 = RegularManager()

    print(f"regular1 ID: {regular1.get_id()}")
    print(f"regular2 ID: {regular2.get_id()}")
    print(f"regular3 ID: {regular3.get_id()}")
    print(f"Are they the same object? {regular1 is regular2}")

    # Verify they're different
    assert regular1 is not regular2, "Regular objects should be different"
    assert regular2 is not regular3, "Regular objects should be different"
    assert regular1.get_id() != regular2.get_id(), (
        "Regular objects should have different IDs"
    )

    print("✅ Regular class test passed - creates different objects")
    return True


def test_singleton_class():
    """Test singleton class behavior - always returns same object"""
    print("\n🧪 Testing Singleton Class (Same Object)")
    print("-" * 50)

    singleton1 = SingletonManager()
    singleton2 = SingletonManager()
    singleton3 = SingletonManager()

    print(f"singleton1 ID: {singleton1.get_id()}")
    print(f"singleton2 ID: {singleton2.get_id()}")
    print(f"singleton3 ID: {singleton3.get_id()}")
    print(f"Are they the same object? {singleton1 is singleton2}")

    # Verify they're the same
    assert singleton1 is singleton2, "Singleton objects should be the same"
    assert singleton2 is singleton3, "Singleton objects should be the same"
    assert singleton1.get_id() == singleton2.get_id(), (
        "Singleton objects should have same ID"
    )

    print("✅ Singleton class test passed - returns same object")
    return True


def test_class_vs_instance_variables():
    """Test understanding of class vs instance variables"""
    print("\n🧪 Testing Class vs Instance Variables")
    print("-" * 50)

    class TestClass:
        class_variable = "shared"  # Class variable - shared by all instances

        def __init__(self, name):
            self.instance_variable = name  # Instance variable - unique to each object

        def show_variables(self):
            return f"Class: {self.class_variable}, Instance: {self.instance_variable}"

    # Create two instances
    obj1 = TestClass("Object1")
    obj2 = TestClass("Object2")

    print(f"obj1: {obj1.show_variables()}")
    print(f"obj2: {obj2.show_variables()}")

    # Change class variable - affects all instances
    TestClass.class_variable = "modified"
    print(f"After changing class variable:")
    print(f"obj1: {obj1.show_variables()}")
    print(f"obj2: {obj2.show_variables()}")

    # Verify behavior
    assert obj1.class_variable == obj2.class_variable, (
        "Class variables should be shared"
    )
    assert obj1.instance_variable != obj2.instance_variable, (
        "Instance variables should be different"
    )

    print("✅ Class vs instance variables test passed")
    return True


def test_method_types():
    """Test different types of methods in classes"""
    print("\n🧪 Testing Method Types")
    print("-" * 50)

    class MethodDemo:
        class_counter = 0

        def __init__(self, name):
            self.name = name
            MethodDemo.class_counter += 1

        def instance_method(self):
            """Regular method - needs an instance"""
            return f"Instance method called by {self.name}"

        @classmethod
        def class_method(cls):
            """Class method - works with the class itself"""
            return f"Class method called, counter: {cls.class_counter}"

        @staticmethod
        def static_method():
            """Static method - independent of class and instances"""
            return "Static method called - no class or instance needed"

    # Test instance method
    obj = MethodDemo("TestObject")
    print(f"Instance method: {obj.instance_method()}")

    # Test class method
    print(f"Class method: {MethodDemo.class_method()}")

    # Test static method
    print(f"Static method: {MethodDemo.static_method()}")

    # Create another instance to test class counter
    obj2 = MethodDemo("TestObject2")
    print(f"Class method after second object: {MethodDemo.class_method()}")

    print("✅ Method types test passed")
    return True


def run_all_class_tests():
    """Run all class and object tests"""
    print("=" * 70)
    print("🧪 CLASS AND OBJECT CONCEPTS TEST SUITE")
    print("=" * 70)

    tests = [
        ("Regular Class Behavior", test_regular_class),
        ("Singleton Pattern", test_singleton_class),
        ("Class vs Instance Variables", test_class_vs_instance_variables),
        ("Method Types", test_method_types),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("📊 CLASS CONCEPTS TEST RESULTS")
    print("=" * 70)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1

    print(f"\n📈 Overall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All class concept tests passed!")
        print("   You now understand the basics of classes and objects!")
    else:
        print("⚠️ Some tests failed - review the concepts above")


if __name__ == "__main__":
    run_all_class_tests()
