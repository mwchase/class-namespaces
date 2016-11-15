"""Class Namespaces (internal module)

All of the guts of the class namespace implementation.

"""


# See https://blog.ionelmc.ro/2015/02/09/understanding-python-metaclasses/

import collections.abc
import functools
import itertools
import weakref


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

    @property
    def is_data(self):
        """Returns whether self.object is a data descriptor."""
        return self.has_set or self.has_delete

    @property
    def is_non_data(self):
        """Returns whether self.object is a non-data descriptor."""
        return self.has_get and not self.is_data

    @property
    def is_descriptor(self):
        """Returns whether self.object is a descriptor."""
        return self.has_get or self.has_set or self.has_delete

    def get_as_attribute(self, key):
        """Return attribute with the given name, or raise AttributeError."""
        try:
            return self.dict[key]
        except KeyError:
            raise namespace_exception(AttributeError)(key)

    def get(self, instance, owner):
        """Return the result of __get__, bypassing descriptor protocol."""
        return self.get_as_attribute('__get__')(self.object, instance, owner)

    def set(self, instance, value):
        """Return the result of __set__, bypassing descriptor protocol."""
        self.get_as_attribute('__set__')(self.object, instance, value)

    def delete(self, instance):
        """Return the result of __delete__, bypassing descriptor protocol."""
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


class _NamespaceProxy:

    """Proxy object for manipulating and querying namespaces."""

    __slots__ = '__weakref__',

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
            instance_value = _DescriptorInspector(instance_value)
        try:
            mro_value = mro_map[name]
        except KeyError:
            mro_value = None
        else:
            mro_value = _DescriptorInspector(mro_value)
        if issubclass(owner, type):
            if mro_value is not None and mro_value.is_data:
                return mro_value.get(instance, owner)
            elif instance_value is not None and instance_value.has_get:
                return instance_value.get(None, instance)
            elif instance_value is not None:
                return instance_value.object
            elif mro_value is not None and mro_value.is_non_data:
                return mro_value.get(instance, owner)
            elif mro_value is not None:
                return mro_value.object
            else:
                raise namespace_exception(AttributeError)(name)
        else:
            if mro_value is not None and mro_value.is_data:
                return mro_value.get(instance, owner)
            elif instance_value is not None:
                return instance_value.object
            elif mro_value is not None and mro_value.is_non_data:
                return mro_value.get(instance, owner)
            elif mro_value is not None:
                return mro_value.object
            else:
                raise namespace_exception(AttributeError)(name)

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
            target_value = _DescriptorInspector(target_value)
            if target_value.is_data:
                target_value.set(instance, value)
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
                raise namespace_exception(AttributeError)(name)
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
            raise namespace_exception(AttributeError)(name)

    def __enter__(self):
        dct, _, _ = _PROXY_INFOS[self]
        return dct.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        dct, _, _ = _PROXY_INFOS[self]
        return dct.__exit__(exc_type, exc_value, traceback)


class NamespaceException(Exception):
    """Base class for exceptions thrown from Class Namespaces."""


_EXCEPTIONS = weakref.WeakKeyDictionary()


def namespace_exception(exception):
    """Return a subclass of the given exception type. Results are cached."""
    return _EXCEPTIONS.setdefault(
        exception,
        type('Namespace' + exception.__name__,
             (NamespaceException, exception),
             {}))


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
            raise namespace_exception(ValueError)(
                'Bad values: {}'.format(bad_values))
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

    def __enter__(self):
        self.activate()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.name is None:
            raise namespace_exception(RuntimeError)('Namespace must be named.')
        self.deactivate()

    @property
    def path(self):
        """Return the full path of the namespace."""
        if self.name is None or self.parent is None:
            raise namespace_exception(ValueError)
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
        return res

    def push(self, name, scope):
        """Bind self to the given name and scope, and activate."""
        if self.name is None:
            self.name = name
        if self.scope is None:
            self.scope = scope
        if self.parent is None:
            self.parent = scope.dicts[-1]
        if name != self.name:
            raise namespace_exception(ValueError)('Cannot rename namespace')
        if scope is not self.scope:
            raise namespace_exception(ValueError)('Cannot reuse namespace')
        if scope.dicts[-1] is not self.parent:
            raise namespace_exception(ValueError)('Cannot reparent namespace')
        self.scope.namespaces.append(self)
        self.activate()

    def activate(self):
        """Take over as the scope for the target."""
        if self.scope is not None and not self.active:
            if self.scope.dicts[-1] is not self.parent:
                raise namespace_exception(ValueError)(
                    'Cannot reparent namespace')
            self.active = True
            self.scope.dicts.append(self)

    def deactivate(self):
        """Stop being the scope for the target."""
        if self.scope is not None and self.active:
            self.active = False
            self.scope.dicts.pop()

    def __get__(self, instance, owner):
        return _NamespaceProxy(self, instance, owner)


class _NamespaceScope(collections.abc.MutableMapping):

    __slots__ = 'dicts', 'namespaces'

    def __init__(self):
        self.dicts = [{}]
        self.namespaces = []

    def __getitem__(self, key):
        value = self.dicts[-1][key]
        if isinstance(value, Namespace):
            value = _NamespaceProxy(value, None, None)
        return value

    def __setitem__(self, key, value):
        dct = self.dicts[-1]
        if isinstance(value, _NamespaceProxy):
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

    """Metaclass for classes that can contain namespaces."""

    __slots__ = ()

    @classmethod
    def __prepare__(mcs, name, bases):
        return _NamespaceScope()

    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct.dicts[-1])
        for namespace in dct.namespaces:
            namespace.add(cls)
        return cls
