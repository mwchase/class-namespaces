"""Base class for Namespace proxies in class creation."""

import weakref

from . import ops
from .proxy import _Proxy

_PROXY_INFOS = weakref.WeakKeyDictionary()


def _ns(self):
    return _PROXY_INFOS[self][self]


class _ScopeProxy(_Proxy):

    """Proxy object for manipulating namespaces during class creation."""

    __slots__ = '__weakref__',

    def __init__(self, dct, container, owner):
        _PROXY_INFOS[self] = container
        container[self] = dct

    def __dir__(self):
        # This line will fire if dir(ns) is done during class creation.
        return _ns(self)

    def __getattribute__(self, name):
        # Have to add some dependencies back...
        from .namespaces import Namespace
        dct = _ns(self)
        try:
            value = dct[name]
        # These lines will fire if a non-existent namespace attribute is gotten
        # during class creation.
        except KeyError:
            raise AttributeError(name)
        if isinstance(value, Namespace):
            value = type(self)(value)
        return value

    def __setattr__(self, name, value):
        _ns(self)[name] = value

    def __delattr__(self, name):
        ops.delete(_ns(self), name)

    def __enter__(self):
        return _ns(self).__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        return _ns(self).__exit__(exc_type, exc_value, traceback)
