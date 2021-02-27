import abc


class classproperty(object):
    def __init__(self, f):
        self.f = f
    def __get__(self, obj, owner):
        return self.f(owner)


def abstractproperty(func):
    return property(abc.abstractmethod(func))
