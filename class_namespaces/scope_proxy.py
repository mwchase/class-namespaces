"""Base class for Namespace proxies in class creation."""

import weakref

from . import ops
from .proxy import _Proxy

_PROXY_INFOS = weakref.WeakKeyDictionary()


class _ScopeProxy(_Proxy):

    """Proxy object for manipulating namespaces during class creation."""

    __slots__ = '__weakref__',

    def __init__(self, dct, container):
        _PROXY_INFOS[self] = container
        container[self] = dct

    def __dir__(self):
        # This line will fire if dir(ns) is done during class creation.
        return _PROXY_INFOS[self][self]

    def __getattribute__(self, name):
        # Have to add some dependencies back...
        from .namespaces import Namespace
        dct = _PROXY_INFOS[self][self]
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
        _PROXY_INFOS[self][self][name] = value

    def __delattr__(self, name):
        ops.delete(_PROXY_INFOS[self][self], name)

    def __enter__(self):
        return _PROXY_INFOS[self][self].__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        return _PROXY_INFOS[self][self].__exit__(
            exc_type, exc_value, traceback)
