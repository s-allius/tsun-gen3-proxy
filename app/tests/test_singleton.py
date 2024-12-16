# test_with_pytest.py
import pytest
from singleton import Singleton

class Example(metaclass=Singleton):
    def __init__(self):
        pass  # is a dummy test class

def test_singleton_metaclass():
    Singleton._instances.clear()
    a = Example()
    assert 1 == len(Singleton._instances)
    b = Example()
    assert 1 == len(Singleton._instances)
    assert a is  b
    del a
    assert 1 == len(Singleton._instances)
    del b
    assert 0 == len(Singleton._instances)
