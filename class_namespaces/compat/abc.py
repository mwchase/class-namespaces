import abc

from .. import namespaces


class _NamespaceableABC(abc.ABCMeta, namespaces._Namespaceable):

    pass


class NamespaceableABC(namespaces.Namespaceable, metaclass=_NamespaceableABC):

    pass
