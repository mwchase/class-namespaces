"""Base class for Namespace proxies in class creation."""

import weakref

from . import ops
from .proxy import _Proxy

_NAMESPACES = weakref.WeakKeyDictionary()
_OWNERS = weakref.WeakKeyDictionary()


def namespace(self):
    """Return the associated Namespace."""
    return _owner(self).proxies[self]


def _owner(self):
    """Return the associated scope."""
    return _OWNERS[self]


class _ScopeProxy(_Proxy):

    """Proxy object for manipulating namespaces during class creation."""

    __slots__ = ('__weakref__',)

    def __init__(self, dct, owner):
        _OWNERS[self] = owner
        owner.proxies[self] = dct

    def __dir__(self):
        return namespace(self)

    def __getattribute__(self, name):
        dct = namespace(self)
        try:
            value = dct[name]
        except KeyError:
            raise AttributeError(name)
        return _owner(self).wrap(value)

    def __setattr__(self, name, value):
        namespace(self)[name] = value

    def __delattr__(self, name):
        ops.delete(namespace(self), name)

    def __enter__(self):
        return namespace(self).__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        return namespace(self).__exit__(exc_type, exc_value, traceback)
