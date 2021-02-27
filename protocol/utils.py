import abc
import re


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