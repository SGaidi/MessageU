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


def abstractproperty(func: object) -> object:
    return property(abc.abstractmethod(func))  # noqa


def camel_case_to_snake_case(text: str) -> str:
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', text).lower()


def islice(iterable, stop):
    it = iter(range(stop))
    nexti = next(it)

    try:
        for i, element in enumerate(iterable):
            if i == nexti:
                yield element
                nexti = next(it)
    except StopIteration:
        # Consume to *stop*.
        for i, element in zip(range(i + 1, stop), iterable):
            pass