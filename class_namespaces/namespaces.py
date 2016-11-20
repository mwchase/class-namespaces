"""Class Namespaces (internal module)

All of the guts of the class namespace implementation.

"""


# See https://blog.ionelmc.ro/2015/02/09/understanding-python-metaclasses/

import collections.abc
import functools
import itertools
import sys
import weakref


ENABLE_SET_NAME = sys.version_info >= (3, 6)


_PROXY_INFOS = weakref.WeakKeyDictionary()
_SENTINEL = object()


class _DescriptorInspector(collections.namedtuple('_DescriptorInspector',
                                                  ['object', 'dict'])):

    __slots__ = ()

    def __new__(cls, obj):
        dct = collections.ChainMap(*[vars(cls) for cls in type(obj).__mro__])
        return super().__new__(cls, obj, dct)

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
        """Returns whether self.object is a data descriptor."""
        return self.has_set or self.has_delete

    @property
    def is_non_data(self):
        """Returns whether self.object is a non-data descriptor."""
        return self.has_non_data and not self.is_data

    @property
    def is_descriptor(self):
        """Returns whether self.object is a descriptor."""
        return self.has_non_data or self.is_data

    def get_as_attribute(self, key):
        """Return attribute with the given name, or raise AttributeError."""
        try:
            return self.dict[key]
        except KeyError:
            raise AttributeError(key)

    def get(self, instance, owner):
        """Return the result of __get__, bypassing descriptor protocol."""
        return self.get_as_attribute('__get__')(self.object, instance, owner)

    def set(self, instance, value):
        """Call __set__, bypassing descriptor protocol."""
        self.get_as_attribute('__set__')(self.object, instance, value)

    def delete(self, instance):
        """Call __delete__, bypassing descriptor protocol."""
        self.get_as_attribute('__delete__')(self.object, instance)


def _no_blocker(dct, cls):
    try:
        namespace = vars(cls)
        for name in dct.path:
            namespace = namespace[name]
            if not isinstance(namespace, Namespace):
                return False
    except KeyError:
        pass
    return True


def _mro_to_chained(mro, dct):
    mro = (cls for cls in mro if isinstance(cls, Namespaceable))
    mro = itertools.takewhile(functools.partial(_no_blocker, dct), mro)
    mro = (cls for cls in mro if Namespace.namespace_exists(cls, dct.path))
    return collections.ChainMap(
        *[Namespace.get_namespace(cls, dct.path) for cls in mro])


def _instance_map(ns_proxy):
    dct, instance, _ = _PROXY_INFOS[ns_proxy]
    if instance is not None:
        if isinstance(instance, Namespaceable):
            return _mro_to_chained(instance.__mro__, dct)
        else:
            return Namespace.get_namespace(instance, dct.path)
    else:
        return {}


def _mro_map(ns_proxy):
    dct, _, owner = _PROXY_INFOS[ns_proxy]
    mro = owner.__mro__
    mro = mro[mro.index(dct.parent_object):]
    return _mro_to_chained(mro, dct)


def _retarget(ns_proxy):
    dct, instance, owner = _PROXY_INFOS[ns_proxy]
    if instance is None and isinstance(type(owner), Namespaceable):
        instance, owner = owner, type(owner)
        dct = Namespace.get_namespace(owner, dct.path)
        ns_proxy = _NamespaceProxy(dct, instance, owner)
    return ns_proxy


def _get(a_map, name):
    try:
        value = a_map[name]
    except KeyError:
        return None
    else:
        return _DescriptorInspector(value)


class _NamespaceProxy:

    """Proxy object for manipulating and querying namespaces."""

    __slots__ = '__weakref__',

    def __init__(self, dct, instance, owner):
        _PROXY_INFOS[self] = dct, instance, owner

    def __dir__(self):
        return collections.ChainMap(_instance_map(self), _mro_map(self))

    def __getattribute__(self, name):
        self = _retarget(self)
        dct, instance, owner = _PROXY_INFOS[self]
        if owner is None:
            return dct[name]
        instance_map = _instance_map(self)
        mro_map = _mro_map(self)
        instance_value = _get(instance_map, name)
        mro_value = _get(mro_map, name)
        if mro_value is not None and mro_value.is_data:
            return mro_value.get(instance, owner)
        elif (issubclass(owner, type) and instance_value is not None and
              instance_value.has_get):
            return instance_value.get(None, instance)
        elif instance_value is not None:
            return instance_value.object
        elif mro_value is not None and mro_value.has_get:
            return mro_value.get(instance, owner)
        elif mro_value is not None:
            return mro_value.object
        else:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self = _retarget(self)
        dct, instance, owner = _PROXY_INFOS[self]
        if owner is None:
            dct[name] = value
            return
        if instance is None:
            real_map = Namespace.get_namespace(owner, dct.path)
            real_map[name] = value
            return
        mro_map = _mro_map(self)
        try:
            target_value = mro_map[name]
        except KeyError:
            pass
        else:
            target_value = _DescriptorInspector(target_value)
            if target_value.is_data:
                target_value.set(instance, value)
                return
        instance_map = Namespace.get_namespace(instance, dct.path)
        instance_map[name] = value

    def __delattr__(self, name):
        self = _retarget(self)
        dct, instance, owner = _PROXY_INFOS[self]
        if owner is None:
            try:
                del dct[name]
            except KeyError:
                raise AttributeError(name)
            return
        real_map = Namespace.get_namespace(owner, dct.path)
        if instance is None:
            try:
                del real_map[name]
                return
            except KeyError:
                raise AttributeError(name)
        try:
            value = real_map[name]
        except KeyError:
            pass
        else:
            value = _DescriptorInspector(value)
            if value.is_data:
                value.delete(instance)
                return
        instance_map = Namespace.get_namespace(instance, dct.path)
        try:
            del instance_map[name]
        except KeyError:
            raise AttributeError(name)

    def __enter__(self):
        dct, _, _ = _PROXY_INFOS[self]
        return dct.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        dct, _, _ = _PROXY_INFOS[self]
        return dct.__exit__(exc_type, exc_value, traceback)


class Namespace(dict):

    """Namespace."""

    __slots__ = 'name', 'scope', 'parent', 'active', 'parent_object'

    __namespaces = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bad_values = tuple(
            value for value in self.values() if
            isinstance(value, (Namespace, _NamespaceProxy)))
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
        if isinstance(target, Namespaceable):
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
    def namespace_exists(cls, target, path):
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

    def add(self, target):
        """Add self as a namespace under target."""
        path, namespaces = self.__get_helper(target, self.path)
        res = namespaces.setdefault(path, self)
        if res is self:
            self.parent_object = target

    def push(self, name, scope):
        """Bind self to the given name and scope, and activate."""
        if self.name is None:
            self.name = name
        if self.scope is None:
            self.scope = scope
        if self.parent is None:
            self.parent = scope.dicts[0]
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

    __slots__ = 'dicts', 'namespaces'

    def __init__(self):
        self.dicts = [{}]
        self.namespaces = []

    def __getitem__(self, key):
        value = collections.ChainMap(*self.dicts)[key]
        if isinstance(value, Namespace):
            value = _NamespaceProxy(value, None, None)
        return value

    def __setitem__(self, key, value):
        dct = self.dicts[0]
        if isinstance(value, _NamespaceProxy):
            value, _, _ = _PROXY_INFOS[value]
        if isinstance(value, Namespace) and value.name != key:
            value.push(key, self)
        dct[key] = value

    def __delitem__(self, key):
        del self.dicts[0][key]

    def __iter__(self):
        return iter(collections.ChainMap(*self.dicts))

    def __len__(self):
        return len(collections.ChainMap(*self.dicts))


class Namespaceable(type):

    """Metaclass for classes that can contain namespaces."""

    @classmethod
    def __prepare__(mcs, name, bases):
        return _NamespaceScope()

    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct.dicts[0])
        cls.__scope = dct
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
            value.push(name, cls.__scope)
            value.add(cls)
        if issubclass(cls, Namespaceable):
            super().__setattr__(cls, name, value)
        else:
            super().__setattr__(name, value)
