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


def _mro_to_chained(mro, dct):
    """Return a chained map of lookups for the given namespace and mro."""
    return collections.ChainMap(*[
        dct.get_namespace(cls, dct.path) for cls in
        itertools.takewhile(
            functools.partial(dct.no_blocker, dct.path),
            (cls for cls in mro if isinstance(cls, NamespaceableMeta))) if
        dct.namespace_exists(dct.path, cls)])


def _instance_map(ns_proxy):
    """Return a map, possibly chained, of lookups for the given instance."""
    dct, instance, _ = _PROXY_INFOS[ns_proxy]
    if instance is not None:
        try:
            if isinstance(instance, NamespaceableMeta):
                return _mro_to_chained(instance.__mro__, dct)
            else:
                return dct.get_namespace(instance, dct.path)
        except TypeError:
            return {}
    else:
        return {}


def _instance_namespace(instance, dct, name):
    """Return a Namespace associated with the instance, if possible."""
    try:
        return dct.get_namespace(instance, dct.path)
    except TypeError:
        raise AttributeError(name)


def _mro_map(ns_proxy):
    """Return a chained map of lookups for the given owner class."""
    dct, _, owner = _PROXY_INFOS[ns_proxy]
    mro = owner.__mro__
    parent_object = dct.parent_object
    index = mro.index(parent_object)
    mro = mro[index:]
    return _mro_to_chained(mro, dct)


def _retarget(ns_proxy):
    """Convert a class lookup to an instance lookup, if needed."""
    dct, instance, owner = _PROXY_INFOS[ns_proxy]
    if instance is None and isinstance(type(owner), NamespaceableMeta):
        instance, owner = owner, type(owner)
        dct = dct.get_namespace(owner, dct.path)
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
        if ops.is_data(mro_value) and ops.has_get(mro_value):
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
            real_map = dct.get_namespace(owner, dct.path)
            real_map[name] = value
            return
        mro_map = _mro_map(self)
        target_value = ops.get_data(mro_map, name)
        if target_value is not None:
            target_value.set(instance, value)
            return
        _instance_namespace(instance, dct, name)[name] = value

    def __delattr__(self, name):
        self = _retarget(self)
        dct, instance, owner = _PROXY_INFOS[self]
        real_map = dct.get_namespace(owner, dct.path)
        if instance is None:
            ops.delete(real_map, name)
            return
        value = ops.get_data(real_map, name)
        if value is not None:
            value.delete(instance)
            return
        ops.delete(_instance_namespace(instance, dct, name), name)


_NAMESPACE_INFOS = weakref.WeakKeyDictionary()


class Namespace(dict):

    """Namespace.

    Namespace() -> new empty namespace
    Namespace(mapping) -> new namespace initialized from a mapping object's
        (key, value) pairs
    Namespace(iterable) -> new namespace initialized as if via:
        d = {}
        for k, v in iterable:
            d[k] = v
        ns = Namespace(d)
    Namespace(**kwargs) -> new namespace initialized with the name=value pairs
        in the keyword argument list.  For example:  Namespace(one=1, two=2)

    Namespaces implement the context manager protocol. When the context is
    entered in an appropriate class creation scope, the Namespace shadows the
    currently visible scope.

    Namespaces can be re-entered after they are exited, provided they're in the
    same parent scope.
    """

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
        if (
                self.scope is not None and
                isinstance(value, self.scope.scope_proxy)):
            value = self.scope.proxies[value]
        if isinstance(value, _Proxy):
            raise ValueError('Cannot move scopes between classes.')
        if isinstance(value, Namespace):
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
            raise ValueError
        if isinstance(self.parent, Namespace):
            parent_path = self.parent.path
        else:
            parent_path = ()
        return parent_path + (self.name,)

    @classmethod
    def __get_helper(cls, target, path):
        """Return the namespace for `target` at `path`, create if needed."""
        if isinstance(target, NamespaceableMeta):
            path_ = target, path
            namespaces = cls.__namespaces
        else:
            path_ = path
            try:
                namespaces = _NAMESPACE_INFOS[target]
            except KeyError:
                namespaces = {}
                _NAMESPACE_INFOS[target] = namespaces
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
        if target is not None:
            path, namespaces = self.__get_helper(target, self.path)
            res = namespaces.setdefault(path, self)
            if res is self:
                self.parent_object = target

    def set_if_none(self, name, value):
        """Set the attribute `name` to `value`, if it's initially None."""
        if getattr(self, name) is None:
            setattr(self, name, value)

    def validate_assignment(self, name, scope):
        """Confirm the instance can be assigned to the given name and scope."""
        if name != self.name:
            raise ValueError('Cannot rename namespace')
        if scope is not self.scope:
            raise ValueError('Cannot reuse namespace')

    def validate_parent(self, parent):
        """Confirm that the instance has the correct parent dict."""
        if parent is not self.parent:
            raise ValueError('Cannot reparent namespace')

    def push(self, name, scope, parent):
        """Bind self to the given name and scope, and activate."""
        self.set_if_none('name', name)
        self.set_if_none('scope', scope)
        self.set_if_none('parent', parent)
        self.validate_assignment(name, scope)
        self.validate_parent(parent)
        self.scope.namespaces.append(self)
        if self.needs_setup:
            self.activate()

    def activate(self):
        """Take over as the scope for the target."""
        if self.active:
            raise ValueError('Cannot double-activate.')
        if self.scope is not None:
            self.validate_parent(self.scope.head)
            self.active = True
            self.scope.push(self)
            self.needs_setup = False

    def deactivate(self):
        """Stop being the scope for the target."""
        if self.scope is not None and self.active:
            self.active = False
            self.scope.pop_()

    def total_length(self):
        """Return the total number of elements in the Namespace tree."""
        return len(self) + sum(
            ns.total_length() for ns in self.values() if
            isinstance(ns, Namespace))

    def iter_all(self, prefix):
        """Iterate over all elements in the Namespace tree."""
        for key, value in self.items():
            qualified_name = prefix + key
            yield qualified_name
            if isinstance(value, Namespace):
                yield from value.iter_all(qualified_name + '.')

    def __get__(self, instance, owner):
        return _NamespaceProxy(self, instance, owner)

    def __bool__(self):
        return True


class _NamespaceScope(collections.abc.MutableMapping):

    """The class creation namespace for NamespaceableMetas."""

    __slots__ = '_dicts', 'namespaces', 'proxies', 'scope_proxy', 'finalized'

    def __init__(self, dct):
        self._dicts = [dct]
        self.namespaces = []
        self.proxies = weakref.WeakKeyDictionary()
        self.finalized = False

        self_ = self

        class ScopeProxy(_ScopeProxy):

            """Local version of ScopeProxy for this scope."""

            __slots__ = ()

            def __init__(self, dct):
                super().__init__(dct, self_)

        self.scope_proxy = ScopeProxy

    @property
    def head(self):
        """The innermost Namespace scope."""
        return self._dicts[0]

    def finalize(self):
        """Mark the scope as no longer active, and return the head."""
        if len(self._dicts) != 1:
            raise ValueError('Cannot finalize a pushed scope!')
        self.finalized = True
        return self.head

    def push(self, dct):
        """Add a new active Namespace to the scope."""
        if self.finalized:
            raise ValueError('Cannot push a finalized scope!')
        self._dicts.insert(0, dct)

    def pop_(self):
        """Remove the current active Namespace from the scope."""
        if len(self._dicts) == 1:
            raise ValueError('Cannot pop from a basal scope!')
        self._dicts.pop(0)

    def _raw_get(self, parent, key):
        """Return the item under the given path, without wrapping."""
        dct = self.head
        try:
            for element in parent.split('.'):
                dct = dct[element]
                if not isinstance(dct, Namespace):
                    raise KeyError
            return dct
        except KeyError:
            raise KeyError(key)

    def wrap(self, value):
        """If `value` is a Namespace, wrap it in a proxy."""
        if isinstance(value, Namespace):
            value = self.scope_proxy(value)
        return value

    def __getitem__(self, key):
        if self.finalized:
            parent, is_namespace, name = key.rpartition('.')
            if is_namespace:
                namespace = self._raw_get(parent, key)
                try:
                    value = namespace[name]
                except KeyError:
                    raise KeyError(key)
            else:
                value = self.head[key]
        else:
            value = collections.ChainMap(*self._dicts)[key]
        return self.wrap(value)

    def _store(self, key, value, dct):
        """Return the rebased value and target dict."""
        # We just entered the context successfully.
        if not self.finalized:
            if value is dct:
                dct = self._dicts[1]
            if isinstance(value, Namespace):
                value.push(key, self, dct)
        if isinstance(value, self.scope_proxy):
            value = self.proxies[value]
            value.validate_parent(dct)
            value.validate_assignment(key, self)
        return value, dct

    def __setitem__(self, key, value):
        dct = self.head
        value, dct = self._store(key, value, dct)
        if isinstance(value, _Proxy):
            raise ValueError('Cannot move scopes between classes.')
        parent, is_namespace, name = key.rpartition('.')
        if self.finalized and is_namespace:
            # Look for parent, not key.
            namespace = self._raw_get(parent, parent)
            namespace[name] = value
        else:
            dct[key] = value

    def __delitem__(self, key):
        parent, is_namespace, name = key.rpartition('.')
        if self.finalized and is_namespace:
            # Look for parent, not key.
            namespace = self._raw_get(parent, parent)
            del namespace[name]
        else:
            del self.head[key]

    def __iter__(self):
        if not self.finalized:
            raise ValueError('Iteration not defined on unfinalized scope.')
        for key, value in self.head.items():
            yield key
            if isinstance(value, Namespace):
                yield from value.iter_all(prefix=key + '.')

    def __len__(self):
        if not self.finalized:
            raise ValueError('Length not defined on unfinalized scope.')
        return len(self.head) + sum(
            ns.total_length() for ns in self.head.values() if
            isinstance(ns, Namespace))


_NAMESPACE_SCOPES = weakref.WeakKeyDictionary()


class NamespaceableMeta(type):

    """Metaclass for classes that can contain namespaces.

    A note for people extending the functionality:
    The base class for NamespaceableMeta uses a non-standard super() invocation
    in its definitions of several methods. This was the only way I could find
    to mitigate some bugs I encountered with a standard invocation. If you
    override any of methods defined on built-in types, I recommend this form
    for maximal reusability:

    super(class, type(self)).__method__(self, ...)
    """

    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        return _NamespaceScope(super().__prepare__(name, bases, **kwargs))

    def __new__(mcs, name, bases, dct, **kwargs):
        cls = super().__new__(mcs, name, bases, dct.finalize(), **kwargs)
        _NAMESPACE_SCOPES[cls] = dct
        for namespace in dct.namespaces:
            namespace.add(cls)
            if ENABLE_SET_NAME:
                for name, value in namespace.items():
                    wrapped = _DescriptorInspector(value)
                    if wrapped.has_set_name:
                        wrapped.set_name(cls, name)
        return cls

    @staticmethod
    def __is_proxy(value):
        """Return whether the value is a _NamespaceProxy."""
        if not isinstance(value, _NamespaceProxy):
            raise ValueError('Given a dot attribute that went too deep.')
        return value

    def __getattribute__(cls, name):
        parent, is_namespace, name_ = name.rpartition('.')
        if is_namespace:
            cls_ = cls
            for element in parent.split('.'):
                cls_ = cls.__is_proxy(getattr(cls_, element))
            return getattr(cls_, name_)
        return super(NamespaceableMeta, type(cls)).__getattribute__(cls, name)

    def __setattr__(cls, name, value):
        if (
                '.' not in name and isinstance(value, Namespace) and
                value.name != name):
            scope = _NAMESPACE_SCOPES[cls]
            value.push(name, scope, scope.head)
            value.add(cls)
        parent, is_namespace, name_ = name.rpartition('.')
        if is_namespace:
            setattr(cls.__is_proxy(getattr(cls, parent)), name_, value)
            return
        super(NamespaceableMeta, type(cls)).__setattr__(cls, name, value)

    def __delattr__(cls, name):
        parent, is_namespace, name_ = name.rpartition('.')
        if is_namespace:
            delattr(cls.__is_proxy(getattr(cls, parent)), name_)
            return
        super(NamespaceableMeta, type(cls)).__delattr__(cls, name)


class Namespaceable(metaclass=NamespaceableMeta):

    """Optional convenience class. Inherit from it to get the metaclass."""
