"""Namespaceable Abstract Base Classes."""

import abc

from .. import namespaces


class NamespaceableABCMeta(abc.ABCMeta, namespaces.NamespaceableMeta):
    """Metaclass for Namespaceable classes that are also ABCs."""


class NamespaceableABC(metaclass=NamespaceableABCMeta):
    """Optional convenience class. Inherit from it to get the metaclass."""
