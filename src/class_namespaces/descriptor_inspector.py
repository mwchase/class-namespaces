"""Descriptor Inspector.

Wrapper around objects, helps expose descriptor protocol.

"""

from .flags import ENABLE_SET_NAME
from .inspector import _Inspector


class _DescriptorInspector(_Inspector):

    """Wrapper around objects. Provides access to descriptor protocol."""

    __slots__ = ()

    def __new__(cls, obj):
        return super().__new__(cls, obj, mro=type(obj).__mro__)

    @property
    def has_get(self):
        """Return whether self.object's mro provides __get__."""
        return '__get__' in self.dict

    @property
    def has_set(self):
        """Return whether self.object's mro provides __set__."""
        return '__set__' in self.dict

    @property
    def has_delete(self):
        """Return whether self.object's mro provides __delete__."""
        return '__delete__' in self.dict

    if ENABLE_SET_NAME:
        @property
        def has_set_name(self):
            """Return whether self.object's mro provides __set_name__."""
            return '__set_name__' in self.dict

        def set_name(self, owner, name):
            """Call __set_name__, bypassing descriptor protocol."""
            self.get_as_attribute('__set_name__')(self.object, owner, name)

        @property
        def has_non_data(self):
            """Return whether self.object's mro provides non-data methods."""
            return self.has_get or self.has_set_name
    else:
        has_non_data = has_get

    @property
    def is_data(self):
        """Return whether self.object is a data descriptor."""
        return self.has_set or self.has_delete

    # I guess I don't actually have a use for this property?
    @property
    def is_non_data(self):
        """Return whether self.object is a non-data descriptor."""
        return self.has_non_data and not self.is_data

    @property
    def is_descriptor(self):
        """Return whether self.object is a descriptor."""
        return self.has_non_data or self.is_data

    def get(self, instance, owner):
        """Return the result of __get__, bypassing descriptor protocol."""
        return self.get_as_attribute('__get__')(self.object, instance, owner)

    def set(self, instance, value):
        """Call __set__, bypassing descriptor protocol."""
        self.get_as_attribute('__set__')(self.object, instance, value)

    def delete(self, instance):
        """Call __delete__, bypassing descriptor protocol."""
        self.get_as_attribute('__delete__')(self.object, instance)
