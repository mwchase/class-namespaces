"""Namespaceable Abstract Base Classes."""

import abc

from .. import NamespaceableMeta


class NamespaceableABCMeta(abc.ABCMeta, NamespaceableMeta):

    """Metaclass for Namespaceable classes that are also ABCs."""


class NamespaceableABC(metaclass=NamespaceableABCMeta):

    """Optional convenience class. Inherit from it to get the metaclass."""
