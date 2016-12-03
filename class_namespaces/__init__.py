"""Class Namespaces.

Class namespaces implemented using metaclasses and context managers.
Classes that contain namespaces need to have NamespaceableMeta as a metaclass.
Namespaces are context managers within a class definition. They can be
manipulated after they're defined.

"""

from . import namespaces

NamespaceableMeta = namespaces.NamespaceableMeta
Namespaceable = namespaces.Namespaceable
Namespace = namespaces.Namespace
