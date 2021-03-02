import abc
from collections import OrderedDict
from typing import NewType, Union, Dict, Any


FieldsValues = NewType('FieldsValues',
                       Union[OrderedDict[str, Any], Dict[str, Any]])


class classproperty(object):
    def __init__(self, f):
        self.f = f
    def __get__(self, obj, owner):
        return self.f(owner)


def abstractproperty(func):
    return property(abc.abstractmethod(func))


def camel_case_to_snake_case(text: str) -> str:
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', text).lower()


def ncycles(iterable, n):
    from itertools import chain, repeat
    "Returns the sequence elements n times"
    return chain.from_iterable(repeat(tuple(iterable), n))
