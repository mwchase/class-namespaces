import abc
import sys

from .. import namespaces

if sys.version_info >= (3, 4):
    get_cache_token = abc.get_cache_token
abstractproperty = abc.abstractproperty
abstractclassmethod = abc.abstractclassmethod
abstractstaticmethod = abc.abstractstaticmethod


class _NamespaceableABC(abc.ABCMeta, namespaces._Namespaceable):

    pass


class NamespaceableABC(namespaces.Namespaceable, metaclass=_NamespaceableABC):

    pass
