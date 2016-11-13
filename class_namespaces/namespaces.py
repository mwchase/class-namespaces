# See https://blog.ionelmc.ro/2015/02/09/understanding-python-metaclasses/

import collections.abc
import functools
import itertools
import weakref


_PROXY_INFOS = weakref.WeakKeyDictionary()
_SENTINEL = object()


class DescriptorInspector(collections.namedtuple('DescriptorInspector',
                                                 ['object', 'dict'])):

    def __new__(cls, obj):
        dct = collections.ChainMap(*[vars(cls) for cls in type(obj).__mro__])
        return super().__new__(cls, obj, dct)

    @property
    def has_get(self):
        return '__get__' in self.dict

    @property
    def has_set(self):
        return '__set__' in self.dict

    @property
    def has_delete(self):
        return '__delete__' in self.dict

    @property
    def is_data(self):
        return self.has_set or self.has_delete

    @property
    def is_non_data(self):
        return self.has_get and not self.is_data

    @property
    def is_descriptor(self):
        return self.has_get or self.has_set or self.has_delete

    @property
    def get(self):
        return self.dict['__get__']

    @property
    def set(self):
        return self.dict['__set__']

    @property
    def delete(self):
        return self.dict['__delete__']


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
        try:
            instance_value = instance_map[name]
        except KeyError:
            instance_value = None
        else:
            instance_value = DescriptorInspector(instance_value)
        try:
            mro_value = mro_map[name]
        except KeyError:
            mro_value = None
        else:
            mro_value = DescriptorInspector(mro_value)
        if issubclass(owner, type):
            if mro_value is not None and mro_value.is_data:
                return mro_value.get(mro_value.object, instance, owner)
            elif instance_value is not None and instance_value.has_get:
                return instance_value.get(
                    instance_value.object, None, instance)
            elif instance_value is not None:
                return instance_value.object
            elif mro_value is not None and mro_value.is_non_data:
                return mro_value.get(mro_value.object, instance, owner)
            elif mro_value is not None:
                return mro_value.object
            else:
                raise AttributeError(name)
        else:
            if mro_value is not None and mro_value.is_data:
                return mro_value.get(mro_value.object, instance, owner)
            elif instance_value is not None:
                return instance_value.object
            elif mro_value is not None and mro_value.is_non_data:
                return mro_value.get(mro_value.object, instance, owner)
            elif mro_value is not None:
                return mro_value.object
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
        try:
            target_value = mro_map[name]
        except KeyError:
            pass
        else:
            target_value = DescriptorInspector(target_value)
            if target_value.has_set:
                target_value.set(target_value.object, instance, value)
                return
        instance_map = Namespace.get_namespace(instance, dct.path)
        instance_map[name] = value

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
        try:
            value = real_map[name]
        except KeyError:
            pass
        else:
            value = DescriptorInspector(value)
            if value.has_delete:
                value.delete(value.object, instance)
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
