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
    mro = mro[mro.index(dct.parent_object):]
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
            value.delete(instance)
            return
        instance_map = Namespace.get_namespace(instance, dct.path)
        ops.delete(instance_map, name)


class Namespace(dict):

    """Namespace."""

    __slots__ = 'name', 'scope', 'parent', 'active', 'parent_object'

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

    @classmethod
    def premake(cls, name, parent):
        """Return an empty namespace with the given name and parent."""
        self = cls()
        self.name = name
        self.parent = parent
        return self

    def __setitem__(self, key, value):
        if (
                self.parent_object is not None and
                isinstance(value, Namespace) and value.name != key):
            value.push(key, self.scope)
            value.add(self.parent_object)
        super().__setitem__(key, value)

    def __enter__(self):
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

    def push(self, name, scope):
        """Bind self to the given name and scope, and activate."""
        self.set_if_none('name', name)
        self.set_if_none('scope', scope)
        self.set_if_none('parent', scope.dicts[0])
        if name != self.name:
            raise ValueError('Cannot rename namespace')
        if scope is not self.scope:
            raise ValueError('Cannot reuse namespace')
        if scope.dicts[0] is not self.parent:
            raise ValueError('Cannot reparent namespace')
        self.scope.namespaces.append(self)
        self.activate()

    def activate(self):
        """Take over as the scope for the target."""
        if self.scope is not None and not self.active:
            if self.scope.dicts[0] is not self.parent:
                raise ValueError('Cannot reparent namespace')
            self.active = True
            self.scope.dicts.insert(0, self)

    def deactivate(self):
        """Stop being the scope for the target."""
        if self.scope is not None and self.active:
            self.active = False
            self.scope.dicts.pop(0)

    def __get__(self, instance, owner):
        return _NamespaceProxy(self, instance, owner)


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

    def __getitem__(self, key):
        value = collections.ChainMap(*self.dicts)[key]
        if isinstance(value, Namespace):
            value = self.scope_proxy(value)
        return value

    def __setitem__(self, key, value):
        dct = self.dicts[0]
        if isinstance(value, self.scope_proxy):
            value = self.proxies[value]
        if isinstance(value, Namespace) and value.name != key:
            value.push(key, self)
        dct[key] = value

    def __delitem__(self, key):
        del self.dicts[0][key]

    def __iter__(self):
        return iter(collections.ChainMap(*self.dicts))

    def __len__(self):
        return len(collections.ChainMap(*self.dicts))


_NAMESPACE_SCOPES = weakref.WeakKeyDictionary()


class _NamespaceBase:

    """Common base class for Namespaceable and its metaclass."""

    __slots__ = ()

    def __getattribute__(self, name):
        parent, is_namespace, name_ = name.rpartition('.')
        if is_namespace:
            self_ = self
            for element in parent.split('.'):
                self_ = getattr(self_, element)
            return getattr(getattr(self, parent), name_)
        return super(_NamespaceBase, type(self)).__getattribute__(self, name)

    def __setattr__(self, name, value):
        parent, is_namespace, name_ = name.rpartition('.')
        if is_namespace:
            setattr(getattr(self, parent), name_, value)
            return
        super(_NamespaceBase, type(self)).__setattr__(self, name, value)

    def __delattr__(self, name):
        parent, is_namespace, name_ = name.rpartition('.')
        if is_namespace:
            delattr(getattr(self, parent), name_)
            return
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
        if isinstance(value, Namespace) and value.name != name:
            value.push(name, _NAMESPACE_SCOPES[cls])
            value.add(cls)
        super(_Namespaceable, type(cls)).__setattr__(cls, name, value)


_DEFINED = False


class Namespaceable(_NamespaceBase, metaclass=_Namespaceable):

    """Base class for classes that can contain namespaces."""

    def __maps(self, parent):
        path = tuple(parent.split('.'))
        instance_namespace = Namespace.get_namespace(self, path)
        if isinstance(type(self), _Namespaceable):
            owner_namespace = Namespace.get_namespace(type(self), path)
            instance_value = ops.get(instance_map, name)
        else:
            owner_namespace = None

    def __getattribute__(self, name):
        parent, is_namespace, name = name.rpartition('.')
        if is_namespace:
            maps = self.__maps(parent)
        return super(Namespaceable, type(self)).__getattribute__(self, name)


_DEFINED = True
