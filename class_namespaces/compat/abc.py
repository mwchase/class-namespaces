import abc

from .. import namespaces


class NamespaceableABCMeta(abc.ABCMeta, namespaces.NamespaceableMeta):

    pass


class NamespaceableABC(metaclass=NamespaceableABCMeta):

    pass
