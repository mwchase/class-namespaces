"""Class Namespaces (internal module).

All of the guts of the class namespace implementation.

"""


# See https://blog.ionelmc.ro/2015/02/09/understanding-python-metaclasses/

import collections.abc
import functools
import itertools
import weakref

from . import ops
from .descriptor_inspector import _DescriptorInspector
from .flags import ENABLE_SET_NAME
from .proxy import _Proxy
from .scope_proxy import _ScopeProxy


_PROXY_INFOS = weakref.WeakKeyDictionary()


def _mro_to_chained(mro, path):
    """Return a chained map of lookups for the given namespace and mro."""
    return collections.ChainMap(*[
        Namespace.get_namespace(cls, path) for cls in
        itertools.takewhile(
            functools.partial(Namespace.no_blocker, path),
            (cls for cls in mro if isinstance(cls, _Namespaceable))) if
        Namespace.namespace_exists(path, cls)])


def _instance_map(ns_proxy):
    """Return a map, possibly chained, of lookups for the given instance."""
    dct, instance, _ = _PROXY_INFOS[ns_proxy]
    if instance is not None:
        if isinstance(instance, _Namespaceable):
            return _mro_to_chained(instance.__mro__, dct.path)
        else:
            return Namespace.get_namespace(instance, dct.path)
    else:
        return {}


def _mro_map(ns_proxy):
    """Return a chained map of lookups for the given owner class."""
    dct, _, owner = _PROXY_INFOS[ns_proxy]
    mro = owner.__mro__
    parent_object = dct.parent_object
    index = mro.index(parent_object)
    mro = mro[index:]
    return _mro_to_chained(mro, dct.path)


def _retarget(ns_proxy):
    """Convert a class lookup to an instance lookup, if needed."""
    dct, instance, owner = _PROXY_INFOS[ns_proxy]
    if instance is None and isinstance(type(owner), _Namespaceable):
        instance, owner = owner, type(owner)
        dct = Namespace.get_namespace(owner, dct.path)
        ns_proxy = _NamespaceProxy(dct, instance, owner)
    return ns_proxy


class _NamespaceProxy(_Proxy):

    """Proxy object for manipulating and querying namespaces."""

    __slots__ = '__weakref__',

    def __init__(self, dct, instance, owner):
        _PROXY_INFOS[self] = dct, instance, owner

    def __dir__(self):
        return collections.ChainMap(_instance_map(self), _mro_map(self))

    def __getattribute__(self, name):
        self = _retarget(self)
        _, instance, owner = _PROXY_INFOS[self]
        instance_map = _instance_map(self)
        mro_map = _mro_map(self)
        instance_value = ops.get(instance_map, name)
        mro_value = ops.get(mro_map, name)
        if ops.is_data(mro_value):
            return mro_value.get(instance, owner)
        elif issubclass(owner, type) and ops.has_get(instance_value):
            return instance_value.get(None, instance)
        elif instance_value is not None:
            return instance_value.object
        elif ops.has_get(mro_value):
            return mro_value.get(instance, owner)
        elif mro_value is not None:
            return mro_value.object
        else:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self = _retarget(self)
        dct, instance, owner = _PROXY_INFOS[self]
        if instance is None:
            real_map = Namespace.get_namespace(owner, dct.path)
            real_map[name] = value
            return
        mro_map = _mro_map(self)
        target_value = ops.get_data(mro_map, name)
        if target_value is not None:
            # These lines will be called on a data descriptor.
            target_value.set(instance, value)
            return
        instance_map = Namespace.get_namespace(instance, dct.path)
        instance_map[name] = value

    def __delattr__(self, name):
        self = _retarget(self)
        dct, instance, owner = _PROXY_INFOS[self]
        real_map = Namespace.get_namespace(owner, dct.path)
        if instance is None:
            ops.delete(real_map, name)
            return
        value = ops.get_data(real_map, name)
        if value is not None:
            # These lines will be called on a data descriptor.
            value.delete(instance)
            return
        instance_map = Namespace.get_namespace(instance, dct.path)
        ops.delete(instance_map, name)


class Namespace(dict):

    """Namespace."""

    __slots__ = (
        'name', 'scope', 'parent', 'active', 'parent_object', 'needs_setup')

    __namespaces = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bad_values = tuple(
            value for value in self.values() if
            isinstance(value, (Namespace, _Proxy)))
        if bad_values:
            raise ValueError('Bad values: {}'.format(bad_values))
        self.name = None
        self.scope = None
        self.parent = None
        self.active = False
        self.parent_object = None
        self.needs_setup = False

    @classmethod
    def premake(cls, name, parent):
        """Return an empty namespace with the given name and parent."""
        self = cls()
        self.name = name
        self.parent = parent
        return self

    # Hold up. Do we need a symmetric addon to __delitem__?
    # I forget how this works.
    def __setitem__(self, key, value):
        if isinstance(value, Namespace):
            if self.parent_object is not None:
                value.push(key, self.scope, self)
                value.add(self.parent_object)
        super().__setitem__(key, value)

    def __enter__(self):
        self.needs_setup = True
        self.activate()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.name is None:
            raise RuntimeError('Namespace must be named.')
        self.deactivate()

    @property
    def path(self):
        """Return the full path of the namespace."""
        if self.name is None or self.parent is None:
            # This line can be hit by Namespace().path.
            raise ValueError
        if isinstance(self.parent, Namespace):
            parent_path = self.parent.path
        else:
            parent_path = ()
        return parent_path + (self.name,)

    @classmethod
    def __get_helper(cls, target, path):
        """Return the namespace for `target` at `path`, create if needed."""
        if isinstance(target, _Namespaceable):
            path_ = target, path
            namespaces = cls.__namespaces
        else:
            path_ = path
            try:
                namespaces = target.__namespaces
            except AttributeError:
                namespaces = {}
                target.__namespaces = namespaces
        return path_, namespaces

    @classmethod
    def namespace_exists(cls, path, target):
        """Return whether the given namespace exists."""
        path_, namespaces = cls.__get_helper(target, path)
        return path_ in namespaces

    @classmethod
    def get_namespace(cls, target, path):
        """Return a namespace with given target and path, create if needed."""
        path_, namespaces = cls.__get_helper(target, path)
        try:
            return namespaces[path_]
        except KeyError:
            if len(path) == 1:
                parent = {}
            else:
                parent = cls.get_namespace(target, path[:-1])
            return namespaces.setdefault(path_, cls.premake(path[-1], parent))

    @classmethod
    def no_blocker(cls, path, cls_):
        """Return False if there's a non-Namespace object in the path."""
        try:
            namespace = vars(cls_)
            for name in path:
                namespace = namespace[name]
                if not isinstance(namespace, cls):
                    return False
        except KeyError:
            pass
        return True

    def add(self, target):
        """Add self as a namespace under target."""
        path, namespaces = self.__get_helper(target, self.path)
        res = namespaces.setdefault(path, self)
        if res is self:
            self.parent_object = target

    def set_if_none(self, name, value):
        """Set the attribute `name` to `value`, if it's initially None."""
        if getattr(self, name) is None:
            setattr(self, name, value)

    def validate_assignment(self, name, scope):
        if name != self.name:
            raise ValueError('Cannot rename namespace')
        if scope is not self.scope:
            # It should be possible to hit this line by assigning a namespace
            # into another class. It may not be, however.
            raise ValueError('Cannot reuse namespace')

    def validate_parent(self, scope, parent=None):
        if (parent or scope.dicts[0]) is not self.parent:
            # This line can be hit by assigning a namespace into another
            # namespace.
            raise ValueError('Cannot reparent namespace')

    def push(self, name, scope, parent=None):
        """Bind self to the given name and scope, and activate."""
        self.set_if_none('name', name)
        self.set_if_none('scope', scope)
        self.set_if_none('parent', parent or scope.dicts[0])
        self.validate_assignment(name, scope)
        self.validate_parent(scope, parent)
        self.scope.namespaces.append(self)
        if self.needs_setup:
            self.activate()

    def activate(self):
        """Take over as the scope for the target."""
        if self.active:
            raise ValueError('Cannot double-activate.')
        if self.scope is not None:
            self.validate_parent(self.scope)
            self.active = True
            self.scope.dicts.insert(0, self)
            self.needs_setup = False

    def deactivate(self):
        """Stop being the scope for the target."""
        if self.scope is not None and self.active:
            self.active = False
            self.scope.dicts.pop(0)

    def __get__(self, instance, owner):
        return _NamespaceProxy(self, instance, owner)

    def __bool__(self):
        return True


class _NamespaceScope(collections.abc.MutableMapping):

    """The class creation namespace for _Namespaceables."""

    __slots__ = 'dicts', 'namespaces', 'proxies', 'scope_proxy'

    def __init__(self, dct):
        self.dicts = [dct]
        self.namespaces = []
        self.proxies = proxies = weakref.WeakKeyDictionary()

        class ScopeProxy(_ScopeProxy):

            """Local version of ScopeProxy for this scope."""

            __slots__ = ()

            def __init__(self, dct):
                super().__init__(dct, proxies)

        self.scope_proxy = ScopeProxy

    # Mapping methods need to know about the dot syntax.
    # Possibly namespaces themselves should know. Would simplify some things.

    def __getitem__(self, key):
        value = collections.ChainMap(*self.dicts)[key]
        if isinstance(value, Namespace):
            value = self.scope_proxy(value)
        return value

    def __setitem__(self, key, value):
        dct = self.dicts[0]
        if isinstance(value, self.scope_proxy):
            value = self.proxies[value]
        if isinstance(value, Namespace):
            if value.needs_setup:
                value.push(key, self)
            else:
                value.validate_parent(self, dct)
            value.validate_assignment(key, self)
        dct[key] = value

    def __delitem__(self, key):
        del self.dicts[0][key]

    # These functions are incorrect and need to be rewritten.
    def __iter__(self):
        return iter(collections.ChainMap(*self.dicts))

    def __len__(self):
        return len(collections.ChainMap(*self.dicts))


_NAMESPACE_SCOPES = weakref.WeakKeyDictionary()


class _NamespaceBase:

    """Common base class for Namespaceable and its metaclass."""

    __slots__ = ()

    # Note: the dot format of invocation can "escape" self into other objects.
    # This is not intended behavior, and the result of using dots "too deeply"
    # should be considered undefined.
    # I would like it to be an error, if I can figure out how.

    @staticmethod
    def __is_proxy(value):
        if not isinstance(value, _NamespaceProxy):
            # This line can be hit by doing what the error message says.
            raise ValueError('Given a dot attribute that went too deep.')
        return value

    def __getattribute__(self, name):
        parent, is_namespace, name_ = name.rpartition('.')
        if is_namespace:
            self_ = self
            for element in parent.split('.'):
                self_ = self.__is_proxy(getattr(self_, element))
            return getattr(getattr(self, parent), name_)
        return super(_NamespaceBase, type(self)).__getattribute__(self, name)

    def __setattr__(self, name, value):
        parent, is_namespace, name_ = name.rpartition('.')
        if is_namespace:
            setattr(self.__is_proxy(getattr(self, parent)), name_, value)
            return
        super(_NamespaceBase, type(self)).__setattr__(self, name, value)

    def __delattr__(self, name):
        parent, is_namespace, name_ = name.rpartition('.')
        if is_namespace:
            delattr(self.__is_proxy(getattr(self, parent)), name_)
            return
        # This line can be hit by deleting an attribute that isn't a namespace.
        super(_NamespaceBase, type(self)).__delattr__(self, name)


class _Namespaceable(_NamespaceBase, type):

    """Metaclass for classes that can contain namespaces.

    Using the metaclass directly is a bad idea. Use a base class instead.
    """

    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        return _NamespaceScope(super().__prepare__(name, bases, **kwargs))

    def __new__(mcs, name, bases, dct, **kwargs):
        cls = super().__new__(mcs, name, bases, dct.dicts[0], **kwargs)
        if _DEFINED and not issubclass(cls, Namespaceable):
            # This line can be hit with class(metaclass=type(Namespaceable)):
            raise ValueError(
                'Cannot create a _Namespaceable that does not inherit from '
                'Namespaceable')
        _NAMESPACE_SCOPES[cls] = dct
        for namespace in dct.namespaces:
            namespace.add(cls)
            if ENABLE_SET_NAME:
                for name, value in namespace.items():
                    wrapped = _DescriptorInspector(value)
                    if wrapped.has_set_name:
                        wrapped.set_name(cls, name)
        return cls

    def __setattr__(cls, name, value):
        if (
                '.' not in name and isinstance(value, Namespace) and
                value.name != name):
            value.push(name, _NAMESPACE_SCOPES[cls])
            value.add(cls)
        super(_Namespaceable, type(cls)).__setattr__(cls, name, value)


_DEFINED = False


class Namespaceable(_NamespaceBase, metaclass=_Namespaceable):

    """Base class for classes that can contain namespaces.

    A note for people extending the functionality:
    The base class for Namespaceable and its metaclass uses a non-standard
    super() invocation in its definitions of several methods. This was the only
    way I could find to mitigate some bugs I encountered with a standard
    invocation. If you override any of methods defined on built-in types, I
    recommend this form for maximal reusability:

    super(class, type(self)).__method__(self, ...)

    This avoids confusing error messages in case self is a subclass of class,
    in addition to being an instance.

    If you're not delegating above Namespaceable, you can probably use the
    standard invocation, unless you bring about the above situation on your own
    types.
    """


_DEFINED = True
