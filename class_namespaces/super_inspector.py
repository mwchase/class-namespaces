"""Super Inspector.

Wrapper around objects, helps expose super protocol.

"""

from .inspector import _Inspector


class _SuperInspector(_Inspector):

    """Wrapper around objects. Provides access to super protocol."""

    __slots__ = ()

    def __new__(cls, super_obj):
        thisclass, self_class = super_obj.thisclass, super_obj.self_class
        mro = self_class.__mro__[self_class.__mro__.index(thisclass) + 1:]
        return super().__new__(cls, super_obj, mro)

    def getattribute(self, name):
        return self.get_as_attribute('__getattribute__')(self.object, name)

    def setattr(self, name, value):
        self.get_as_attribute('__setattr__')(self.object, name, value)

    def delattr(self, name):
        self.get_as_attribute('__delattr__')(self.object, name)
