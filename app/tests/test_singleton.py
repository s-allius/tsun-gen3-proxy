# test_with_pytest.py
import pytest
from singleton import Singleton

class Test(metaclass=Singleton):
    def __init__(self):
        pass  # is a dummy test class

def test_singleton_metaclass():
    Singleton._instances.clear()
    a = Test()
    assert 1 == len(Singleton._instances)
    b = Test()
    assert 1 == len(Singleton._instances)
    assert a is  b
    del a
    assert 1 == len(Singleton._instances)
    del b
    assert 0 == len(Singleton._instances)
