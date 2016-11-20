"""Class Namespaces

Class namespaces implemented using metaclasses and context managers.
Classes that contain namespaces need to have Namespaceable as a metaclass.
Namespaces are context managers within a class definition. They can be
manipulated after they're defined.

"""

from . import namespaces

Namespaceable = namespaces.Namespaceable
Namespace = namespaces.Namespace
