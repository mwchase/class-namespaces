"""Inspector.

Wrapper around objects, helps expose protocols.

"""

import collections


class _Inspector(collections.namedtuple('_Inspector', ['object', 'dict'])):

    """Wrapper around objects. Provides access to protocold."""

    __slots__ = ()

    def __new__(cls, obj, *, mro):
        dct = collections.ChainMap(*[vars(cls) for cls in mro])
        return super().__new__(cls, obj, dct)

    def get_as_attribute(self, key):
        """Return attribute with the given name, or raise AttributeError."""
        try:
            return self.dict[key]
        except KeyError:
            raise AttributeError(key)
