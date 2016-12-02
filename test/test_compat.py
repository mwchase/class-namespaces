from abc import abstractmethod
import abc as abc_main
from inspect import isabstract
import sys

import pytest


def test_import_compat(compat):
    """Test the module is importable. See conftest.py for the actual import."""
    assert compat


def test_import_abc(abc):
    """Test the module is importable. See conftest.py for the actual import."""
    assert abc


def test_has_class(abc):
    assert abc.NamespaceableABC


def test_ABC_helper(abc):
    # create an ABC using the helper class and perform basic checks
    class C(abc.NamespaceableABC):
        @classmethod
        @abstractmethod
        def foo(cls):
            return cls.__name__
    assert isinstance(C, type(abc.NamespaceableABC))
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        @classmethod
        def foo(cls):
            return super().foo()
    assert D.foo() == 'D'


def test_abstractmethod_basics(abc):
    @abstractmethod
    def foo(self):
        pass
    assert foo.__isabstractmethod__

    def bar(self):
        pass
    assert not hasattr(bar, "__isabstractmethod__")


def test_abstractproperty_basics(abc):
    @property
    @abstractmethod
    def foo(self):
        pass
    assert foo.__isabstractmethod__

    def bar(self):
        pass
    assert not getattr(bar, "__isabstractmethod__", False)

    class C(metaclass=type(abc.NamespaceableABC)):
        @property
        @abstractmethod
        def foo(self):
            return 3
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        @C.foo.getter
        def foo(self):
            return super().foo
    assert D().foo == 3


def test_abstractproperty_namespaced(abc, namespace):

    class C(metaclass=type(abc.NamespaceableABC)):
        with namespace() as ns:
            @property
            @abstractmethod
            def foo(self):
                return 3
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        with namespace() as ns:
            @C.ns.foo.getter
            def foo(self):
                return super().ns.foo
    assert D().ns.foo == 3


def test_abstractclassmethod_basics(abc):
    @classmethod
    @abstractmethod
    def foo(cls):
        pass
    assert foo.__isabstractmethod__

    @classmethod
    def bar(cls):
        pass
    assert not getattr(bar, "__isabstractmethod__", False)

    class C(metaclass=type(abc.NamespaceableABC)):
        @classmethod
        @abstractmethod
        def foo(cls):
            return cls.__name__
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        @classmethod
        def foo(cls):
            return super().foo()
    assert D.foo() == 'D'
    assert D().foo() == 'D'


def test_abstractclassmethod_namespaced(abc, namespace):
    class C(metaclass=type(abc.NamespaceableABC)):
        with namespace() as ns:
            @classmethod
            @abstractmethod
            def foo(cls):
                return cls.__name__
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        with namespace() as ns:
            @classmethod
            def foo(cls):
                return super().ns.foo()
    assert D.ns.foo() == 'D'
    assert D().ns.foo() == 'D'


def test_abstractstaticmethod_basics(abc):
    @staticmethod
    @abstractmethod
    def foo():
        pass
    assert foo.__isabstractmethod__

    @staticmethod
    def bar():
        pass
    assert not (getattr(bar, "__isabstractmethod__", False))

    class C(metaclass=type(abc.NamespaceableABC)):
        @staticmethod
        @abstractmethod
        def foo():
            return 3
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        @staticmethod
        def foo():
            return 4
    assert D.foo() == 4
    assert D().foo() == 4


def test_abstractstaticmethod_namespaced(abc, namespace):
    class C(metaclass=type(abc.NamespaceableABC)):
        with namespace() as ns:
            @staticmethod
            @abstractmethod
            def foo():
                return 3
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        with namespace() as ns:
            @staticmethod
            def foo():
                return 4
    assert D.ns.foo() == 4
    assert D().ns.foo() == 4


def test_abstractmethod_integration(abc):
    for abstractthing in [abstractmethod, abc_main.abstractproperty,
                          abc_main.abstractclassmethod,
                          abc_main.abstractstaticmethod]:
        class C(metaclass=type(abc.NamespaceableABC)):
            @abstractthing
            def foo(self):
                pass  # abstract

            def bar(self):
                pass  # concrete
        assert C.__abstractmethods__ == {"foo"}
        with pytest.raises(TypeError):
            print(C())  # because foo is abstract
        assert isabstract(C)

        class D(C):
            def bar(self):
                pass  # concrete override of concrete
        assert D.__abstractmethods__ == {"foo"}
        with pytest.raises(TypeError):
            print(D())  # because foo is still abstract
        assert isabstract(D)

        class E(D):
            def foo(self):
                pass
        assert E.__abstractmethods__ == set()
        E()  # now foo is concrete, too
        assert not isabstract(E)

        class F(E):
            @abstractthing
            def bar(self):
                pass  # abstract override of concrete
        assert F.__abstractmethods__ == {"bar"}
        with pytest.raises(TypeError):
            print(F())  # because bar is abstract now
        assert isabstract(F)


def test_descriptors_with_abstractmethod(abc):
    class C(metaclass=type(abc.NamespaceableABC)):
        @property
        @abstractmethod
        def foo(self):
            return 3

        @foo.setter
        @abstractmethod
        def foo(self, val):
            pass
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        @C.foo.getter
        def foo(self):
            return super().foo
    with pytest.raises(TypeError):
        print(D())

    class E(D):
        @D.foo.setter
        def foo(self, val):
            pass
    assert E().foo == 3
    # check that the property's __isabstractmethod__ descriptor does the
    # right thing when presented with a value that fails truth testing:

    class NotBool(object):
        def __bool__(self):
            raise ValueError()
        __len__ = __bool__
    with pytest.raises(ValueError):
        class F(C):
            def bar(self):
                pass
            bar.__isabstractmethod__ = NotBool()
            foo = property(bar)


def test_customdescriptors_with_abstractmethod(abc):
    class Descriptor:
        def __init__(self, fget, fset=None):
            self._fget = fget
            self._fset = fset

        def getter(self, callable):
            return Descriptor(callable, self._fget)

        def setter(self, callable):
            return Descriptor(self._fget, callable)

        @property
        def __isabstractmethod__(self):
            return (getattr(self._fget, '__isabstractmethod__', False) or
                    getattr(self._fset, '__isabstractmethod__', False))

    class C(metaclass=type(abc.NamespaceableABC)):
        @Descriptor
        @abstractmethod
        def foo(self):
            return 3

        @foo.setter
        @abstractmethod
        def foo(self, val):
            pass
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        @C.foo.getter
        def foo(self):
            return super().foo
    with pytest.raises(TypeError):
        print(D())

    class E(D):
        @D.foo.setter
        def foo(self, val):
            pass
    assert not (E.foo.__isabstractmethod__)


def test_metaclass_abc(abc):
    # Metaclasses can be ABCs, too.
    class A(metaclass=type(abc.NamespaceableABC)):
        @abstractmethod
        def x(self):
            pass
    assert A.__abstractmethods__ == {"x"}

    class meta(type, A):
        def x(self):
            return 1

    class C(metaclass=meta):
        pass


def test_registration_basics(abc):
    class A(metaclass=type(abc.NamespaceableABC)):
        pass

    class B(object):
        pass
    b = B()
    assert not (issubclass(B, A))
    assert not (issubclass(B, (A,)))
    assert not isinstance(b, A)
    assert not isinstance(b, (A,))
    B1 = A.register(B)
    assert issubclass(B, A)
    assert issubclass(B, (A,))
    assert isinstance(b, A)
    assert isinstance(b, (A,))
    assert B1 is B

    class C(B):
        pass
    c = C()
    assert issubclass(C, A)
    assert issubclass(C, (A,))
    assert isinstance(c, A)
    assert isinstance(c, (A,))


def test_register_as_class_deco(abc):
    class A(metaclass=type(abc.NamespaceableABC)):
        pass

    @A.register
    class B(object):
        pass
    b = B()
    assert issubclass(B, A)
    assert issubclass(B, (A,))
    assert isinstance(b, A)
    assert isinstance(b, (A,))

    @A.register
    class C(B):
        pass
    c = C()
    assert issubclass(C, A)
    assert issubclass(C, (A,))
    assert isinstance(c, A)
    assert isinstance(c, (A,))
    assert C is A.register(C)


@pytest.mark.xfail(sys.version_info < (3, 4),
                   reason="python3.4 api changes?", strict=True)
def test_isinstance_invalidation(abc):
    class A(metaclass=type(abc.NamespaceableABC)):
        pass

    class B:
        pass
    b = B()
    assert not (isinstance(b, A))
    assert not (isinstance(b, (A,)))
    token_old = abc_main.get_cache_token()
    A.register(B)
    token_new = abc_main.get_cache_token()
    assert token_old != token_new
    assert isinstance(b, A)
    assert isinstance(b, (A,))


def test_registration_builtins(abc):
    class A(metaclass=type(abc.NamespaceableABC)):
        pass
    A.register(int)
    assert isinstance(42, A)
    assert isinstance(42, (A,))
    assert issubclass(int, A)
    assert issubclass(int, (A,))

    class B(A):
        pass
    B.register(str)

    class C(str):
        pass
    assert isinstance("", A)
    assert isinstance("", (A,))
    assert issubclass(str, A)
    assert issubclass(str, (A,))
    assert issubclass(C, A)
    assert issubclass(C, (A,))


def test_registration_edge_cases(abc):
    class A(metaclass=type(abc.NamespaceableABC)):
        pass
    A.register(A)  # should pass silently

    class A1(A):
        pass
    with pytest.raises(RuntimeError):
        A1.register(A)  # cycles not allowed

    class B(object):
        pass
    A1.register(B)  # ok
    A1.register(B)  # should pass silently

    class C(A):
        pass
    A.register(C)  # should pass silently
    with pytest.raises(RuntimeError):
        C.register(A)  # cycles not allowed
    C.register(B)  # ok


def test_register_non_class(abc):
    class A(metaclass=type(abc.NamespaceableABC)):
        pass
    with pytest.raises(TypeError, message="Can only register classes"):
        print(A.register(4))


def test_registration_transitiveness(abc):
    class A(metaclass=type(abc.NamespaceableABC)):
        pass
    assert issubclass(A, A)
    assert issubclass(A, (A,))

    class B(metaclass=type(abc.NamespaceableABC)):
        pass
    assert not (issubclass(A, B))
    assert not (issubclass(A, (B,)))
    assert not (issubclass(B, A))
    assert not (issubclass(B, (A,)))

    class C(metaclass=type(abc.NamespaceableABC)):
        pass
    A.register(B)

    class B1(B):
        pass
    assert issubclass(B1, A)
    assert issubclass(B1, (A,))

    class C1(C):
        pass
    B1.register(C1)
    assert not issubclass(C, B)
    assert not issubclass(C, (B,))
    assert not issubclass(C, B1)
    assert not issubclass(C, (B1,))
    assert issubclass(C1, A)
    assert issubclass(C1, (A,))
    assert issubclass(C1, B)
    assert issubclass(C1, (B,))
    assert issubclass(C1, B1)
    assert issubclass(C1, (B1,))
    C1.register(int)

    class MyInt(int):
        pass
    assert issubclass(MyInt, A)
    assert issubclass(MyInt, (A,))
    assert isinstance(42, A)
    assert isinstance(42, (A,))


def test_all_new_methods_are_called(abc):
    class A(metaclass=type(abc.NamespaceableABC)):
        pass

    class B(object):
        counter = 0

        def __new__(cls):
            B.counter += 1
            return super().__new__(cls)

    class C(A, B):
        pass
    assert B.counter == 0
    C()
    assert B.counter == 1
