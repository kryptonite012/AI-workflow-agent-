# 🏭 Step 1: Create a metaclass (inherits from type)
from threading import Thread

from networkx.generators.small import bull_graph

from src.tools.lggraph_tools.tools.browser_tool.Handler import HandlerEnums


class MyMeta(type):

    @classmethod
    def __prepare__(metacls, name, bases):
        from collections import OrderedDict
        print(f"🔧 Preparing class: {name}")
        return OrderedDict(super().__prepare__(name, bases))

    def __new__(mcs, name, bases, namespace):
        print(f"🏭 Creating class: {name}")
        # Call parent's __new__ to actually create the class
        if '__doc__' not in namespace:
            namespace['__doc__'] = f"This is the {name} class created with MyMeta metaclass."
        return super().__new__(mcs, name, bases, namespace)

    def __init__(cls ,name, bases, namespace):
        print(f"🚀 Initializing class: {name}")
        super().__init__(name, bases, namespace)



class Animal:
    _physical = ["head", "body", "legs", "tail"]

# 🐕 Step 2: Use the metaclass
class Dog(Animal, metaclass=MyMeta):
    name = HandlerEnums.ON_PRE_REQUIREMENTS
    hand = 5

    def __new__(cls, *args, **kwargs):
        cls.field_order = cls.__dict__.keys()
        print(f"🐶 Creating instance of: {cls.__name__}")
        return super().__new__(cls)


    def __init__(self, daku= True):
        self.daku = daku
        self.name = "doggggesh"
        self.joy = True

    def bark(self):
        return "Woof!"

# # Output when Python reads this code:
# # 🏭 Creating class: Dog
#
# # The class is created BEFORE you even make any instances!
# buddy = Dog()  # This doesn't print anything from MyMeta
# # print(type(buddy.name))
# #
# print(buddy.__class__)
# # print(dir(Dog()))
# numbers = [1, 5, 15, 20]
# print(any([n > 10 for n in numbers]))
# print(any(n > 10 for n in numbers))  # This is more efficient, it doesn't create a list in memory

t = Thread(target=lambda: print("Hello from a thread!"))
t.is_alive()
