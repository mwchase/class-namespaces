# See https://blog.ionelmc.ro/2015/02/09/understanding-python-metaclasses/

import collections.abc
import functools
import itertools
import weakref

import pytest


_PROXY_INFOS = weakref.WeakKeyDictionary()
_SENTINEL = object()


def _is_getter(descriptor):
    d_type_dict = vars(type(descriptor))
    return '__get__' in d_type_dict


def _is_data(descriptor):
    d_type_dict = vars(type(descriptor))
    return '__set__' in d_type_dict or '__delete__' in d_type_dict


def _is_non_data(descriptor):
    return _is_getter(descriptor) and not _is_data(descriptor)


def _get(descriptor, instance, owner):
    getter = getattr(type(descriptor), '__get__', _SENTINEL)
    if getter is _SENTINEL:
        return descriptor
    else:
        return getter(descriptor, instance, owner)


def _set(descriptor, instance, value):
    type(descriptor).__set__(descriptor, instance, value)


def _delete(descriptor, instance):
    type(descriptor).__delete__(descriptor, instance)


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
    dct, instance, owner = _PROXY_INFOS[ns_proxy]
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


class NamespaceProxy:

    def __init__(self, dct, instance, owner):
        _PROXY_INFOS[self] = dct, instance, owner

    def __dir__(self):
        return collections.ChainMap(_instance_map(self), _mro_map(self))

    def __getattribute__(self, name):
        dct, instance, owner = _PROXY_INFOS[self]
        if owner is None:
            return dct[name]
        instance_map = _instance_map(self)
        mro_map = _mro_map(self)
        if issubclass(owner, type):
            if name in mro_map and _is_data(mro_map[name]):
                return _get(mro_map[name], instance, owner)
            elif name in instance_map and _is_getter(instance_map[name]):
                return _get(instance_map[name], None, instance)
            elif name in instance_map:
                return instance_map[name]
            elif name in mro_map and _is_non_data(mro_map[name]):
                return _get(mro_map[name], instance, owner)
            elif name in mro_map:
                return mro_map[name]
            else:
                raise AttributeError(name)
        else:
            if name in mro_map and _is_data(mro_map[name]):
                return _get(mro_map[name], instance, owner)
            elif name in instance_map:
                return instance_map[name]
            elif name in mro_map and _is_non_data(mro_map[name]):
                return _get(mro_map[name], instance, owner)
            elif name in mro_map:
                return mro_map[name]
            else:
                raise AttributeError(name)

    def __setattr__(self, name, value):
        dct, instance, owner = _PROXY_INFOS[self]
        if owner is None:
            dct[name] = value
            return
        if instance is None:
            real_map = Namespace.get_namespace(owner, dct.path)
            real_map[name] = value
            return
        mro_map = _mro_map(self)
        target_value = mro_map.get(name)
        try:
            setter = type(target_value).__set__
        except AttributeError:
            instance_map = Namespace.get_namespace(instance, dct.path)
            instance_map[name] = value
            return
        setter(target_value, instance, value)

    def __delattr__(self, name):
        dct, instance, owner = _PROXY_INFOS[self]
        if owner is None:
            del dct[name]
            return
        real_map = Namespace.get_namespace(owner, dct.path)
        if instance is None:
            try:
                del real_map[name]
                return
            except KeyError:
                raise AttributeError(name)
        value = real_map.get(name)
        try:
            deleter = value.__delete__
        except AttributeError:
            instance_map = Namespace.get_namespace(instance, dct.path)
            try:
                del instance_map[name]
                return
            except KeyError:
                raise AttributeError(name)
        deleter(instance)

    def __enter__(self):
        dct, _, _ = _PROXY_INFOS[self]
        return dct.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        dct, _, _ = _PROXY_INFOS[self]
        return dct.__exit__(exc_type, exc_value, traceback)


class NamespaceException(Exception):
    pass


class Namespace(dict):

    name = None
    scope = None
    parent = None
    active = False
    parent_object = None

    __namespaces = {}

    @classmethod
    def premake(cls, name, parent):
        self = cls()
        self.name = name
        self.parent = parent
        return self

    def __enter__(self):
        self.activate()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.name is None:
            raise NamespaceException('Namespace must be named.')
        self.deactivate()

    @property
    def path(self):
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
        path_, namespaces = cls.__get_helper(target, path)
        return path_ in namespaces

    @classmethod
    def get_namespace(cls, target, path):
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
        path, namespaces = self.__get_helper(target, self.path)
        res = namespaces.setdefault(path, self)
        if res is self:
            self.parent_object = target
        return res

    def push(self, name, scope):
        if self.name is None:
            self.name = name
        if self.scope is None:
            self.scope = scope
        if self.parent is None:
            self.parent = scope.dicts[-1]
        if name != self.name:
            raise ValueError('Cannot rename namespace')
        if scope is not self.scope:
            raise ValueError('Cannot reuse namespace')
        if scope.dicts[-1] is not self.parent:
            raise ValueError('Cannot reparent namespace')
        self.scope.namespaces.append(self)
        self.activate()

    def activate(self):
        if self.scope is not None and not self.active:
            if self.scope.dicts[-1] is not self.parent:
                raise ValueError('Cannot reparent namespace')
            self.active = True
            self.scope.dicts.append(self)

    def deactivate(self):
        if self.scope is not None and self.active:
            self.active = False
            self.scope.dicts.pop()

    def __get__(self, instance, owner):
        return NamespaceProxy(self, instance, owner)


class NamespaceScope(collections.abc.MutableMapping):

    def __init__(self):
        self.dicts = [{}]
        self.namespaces = []

    def __getitem__(self, key):
        value = self.dicts[-1][key]
        if isinstance(value, Namespace):
            value = NamespaceProxy(value, None, None)
        return value

    def __setitem__(self, key, value):
        dct = self.dicts[-1]
        if isinstance(value, NamespaceProxy):
            value, _, _ = _PROXY_INFOS[value]
        if isinstance(value, Namespace) and value.name != key:
            value.push(key, self)
        dct[key] = value

    def __delitem__(self, key):
        del self.dicts[-1][key]

    def __iter__(self):
        return iter(collections.ChainMap(*self.dicts))

    def __len__(self):
        return len(collections.ChainMap(*self.dicts))


class Namespaceable(type):

    @classmethod
    def __prepare__(mcs, name, bases):
        return NamespaceScope()

    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct.dicts[-1])
        for namespace in dct.namespaces:
            namespace.add(cls)
        return cls
