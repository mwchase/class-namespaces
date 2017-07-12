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
        """A throwaway test class."""
        @classmethod
        @abstractmethod
        def footer(cls):
            return cls.__name__
    assert isinstance(C, abc.NamespaceableABCMeta)
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        """A throwaway test class."""
        @classmethod
        def footer(cls):
            return super().footer()
    assert D.footer() == 'D'


def test_abstractmethod_basics(abc):
    @abstractmethod
    def footer(self):
        pass
    assert footer.__isabstractmethod__

    def barter(self):
        pass
    assert not hasattr(barter, "__isabstractmethod__")


def test_abstractproperty_basics(abc):
    @property
    @abstractmethod
    def footer(self):
        pass
    assert footer.__isabstractmethod__

    def barter(self):
        pass
    assert not getattr(barter, "__isabstractmethod__", False)

    class C(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        @property
        @abstractmethod
        def footer(self):
            return 3
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        """A throwaway test class."""
        @C.footer.getter
        def footer(self):
            return super().footer
    assert D().footer == 3


def test_abstractproperty_namespaced(abc, namespace):

    class C(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        with namespace() as ns:
            @property
            @abstractmethod
            def footer(self):
                return 3
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        """A throwaway test class."""
        with namespace() as ns:
            @C.ns.footer.getter
            def footer(self):
                return super().ns.footer
    assert D().ns.footer == 3


def test_abstractclassmethod_basics(abc):
    @classmethod
    @abstractmethod
    def footer(cls):
        pass
    assert footer.__isabstractmethod__

    @classmethod
    def barter(cls):
        pass
    assert not getattr(barter, "__isabstractmethod__", False)

    class C(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        @classmethod
        @abstractmethod
        def footer(cls):
            return cls.__name__
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        """A throwaway test class."""
        @classmethod
        def footer(cls):
            return super().footer()
    assert D.footer() == 'D'
    assert D().footer() == 'D'


def test_abstractclassmethod_namespaced(abc, namespace):
    class C(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        with namespace() as ns:
            @classmethod
            @abstractmethod
            def footer(cls):
                return cls.__name__
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        """A throwaway test class."""
        with namespace() as ns:
            @classmethod
            def footer(cls):
                return super().ns.footer()
    assert D.ns.footer() == 'D'
    assert D().ns.footer() == 'D'


def test_abstractstaticmethod_basics(abc):
    @staticmethod
    @abstractmethod
    def footer():
        pass
    assert footer.__isabstractmethod__

    @staticmethod
    def barter():
        pass
    assert not (getattr(barter, "__isabstractmethod__", False))

    class C(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        @staticmethod
        @abstractmethod
        def footer():
            return 3
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        """A throwaway test class."""
        @staticmethod
        def footer():
            return 4
    assert D.footer() == 4
    assert D().footer() == 4


def test_abstractstaticmethod_namespaced(abc, namespace):
    class C(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        with namespace() as ns:
            @staticmethod
            @abstractmethod
            def footer():
                return 3
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        """A throwaway test class."""
        with namespace() as ns:
            @staticmethod
            def footer():
                return 4
    assert D.ns.footer() == 4
    assert D().ns.footer() == 4


def test_abstractmethod_integration(abc):
    for abstractthing in [abstractmethod, abc_main.abstractproperty,
                          abc_main.abstractclassmethod,
                          abc_main.abstractstaticmethod]:
        class C(metaclass=abc.NamespaceableABCMeta):
            """A throwaway test class."""
            @abstractthing
            def footer(self):
                pass  # abstract

            def barter(self):
                pass  # concrete
        assert C.__abstractmethods__ == {"footer"}
        with pytest.raises(TypeError):
            print(C())  # because footer is abstract
        assert isabstract(C)

        class D(C):
            """A throwaway test class."""

            def barter(self):
                pass  # concrete override of concrete
        assert D.__abstractmethods__ == {"footer"}
        with pytest.raises(TypeError):
            print(D())  # because footer is still abstract
        assert isabstract(D)

        class E(D):
            """A throwaway test class."""

            def footer(self):
                pass
        assert E.__abstractmethods__ == set()
        E()  # now footer is concrete, too
        assert not isabstract(E)

        class F(E):
            """A throwaway test class."""
            @abstractthing
            def barter(self):
                pass  # abstract override of concrete
        assert F.__abstractmethods__ == {"barter"}
        with pytest.raises(TypeError):
            print(F())  # because barter is abstract now
        assert isabstract(F)


def test_abstractmethod_integration_namespaced(abc, namespace):
    for abstractthing in [abstractmethod, abc_main.abstractproperty,
                          abc_main.abstractclassmethod,
                          abc_main.abstractstaticmethod]:
        class C(metaclass=abc.NamespaceableABCMeta):
            """A throwaway test class."""
            with namespace() as ns:
                @abstractthing
                def footer(self):
                    pass  # abstract

                def barter(self):
                    pass  # concrete
        assert C.__abstractmethods__ == {"ns.footer"}
        with pytest.raises(TypeError):
            print(C())  # because footer is abstract
        assert isabstract(C)

        class D(C):
            """A throwaway test class."""
            with namespace() as ns:
                def barter(self):
                    pass  # concrete override of concrete
        assert D.__abstractmethods__ == {"ns.footer"}
        with pytest.raises(TypeError):
            print(D())  # because footer is still abstract
        assert isabstract(D)

        class E(D):
            """A throwaway test class."""
            with namespace() as ns:
                def footer(self):
                    pass
        assert E.__abstractmethods__ == set()
        E()  # now footer is concrete, too
        assert not isabstract(E)

        class F(E):
            """A throwaway test class."""
            with namespace() as ns:
                @abstractthing
                def barter(self):
                    pass  # abstract override of concrete
        assert F.__abstractmethods__ == {"ns.barter"}
        with pytest.raises(TypeError):
            print(F())  # because barter is abstract now
        assert isabstract(F)


def test_descriptors_with_abstractmethod(abc):
    class C(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        @property
        @abstractmethod
        def footer(self):
            return 3

        @footer.setter
        @abstractmethod
        def footer(self, val):
            pass
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        """A throwaway test class."""
        @C.footer.getter
        def footer(self):
            return super().footer
    with pytest.raises(TypeError):
        print(D())

    class E(D):
        """A throwaway test class."""
        @D.footer.setter
        def footer(self, val):
            pass
    assert E().footer == 3
    # check that the property's __isabstractmethod__ descriptor does the
    # right thing when presented with a value that fails truth testing:

    class NotBool(object):
        """A pathological class for test purposes."""

        def __bool__(self):
            raise ValueError()
        __len__ = __bool__
    with pytest.raises(ValueError):
        class F(C):
            """A throwaway test class."""

            def barter(self):
                pass
            barter.__isabstractmethod__ = NotBool()
            footer = property(barter)


def test_descriptors_with_abstractmethod_namespaced(abc, namespace):
    class C(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        with namespace() as ns:
            @property
            @abstractmethod
            def footer(self):
                return 3

            @footer.setter
            @abstractmethod
            def footer(self, val):
                pass
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        """A throwaway test class."""
        with namespace() as ns:
            @C.ns.footer.getter
            def footer(self):
                return super().ns.footer
    with pytest.raises(TypeError):
        print(D())

    class E(D):
        """A throwaway test class."""
        with namespace() as ns:
            @D.ns.footer.setter
            def footer(self, val):
                pass
    assert E().ns.footer == 3
    # check that the property's __isabstractmethod__ descriptor does the
    # right thing when presented with a value that fails truth testing:

    class NotBool(object):
        """A pathological class for test purposes."""

        def __bool__(self):
            raise ValueError()
        __len__ = __bool__
    with pytest.raises(ValueError):
        class F(C):
            """A throwaway test class."""
            with namespace() as ns:
                def barter(self):
                    pass
                barter.__isabstractmethod__ = NotBool()
                footer = property(barter)


def test_customdescriptors_with_abstractmethod(abc):
    class Descriptor:
        """A descriptor class integrated some with the ABC protocol."""

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

    class C(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        @Descriptor
        @abstractmethod
        def footer(self):
            return 3

        @footer.setter
        @abstractmethod
        def footer(self, val):
            pass
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        """A throwaway test class."""
        @C.footer.getter
        def footer(self):
            return super().footer
    with pytest.raises(TypeError):
        print(D())

    class E(D):
        """A throwaway test class."""
        @D.footer.setter
        def footer(self, val):
            pass
    assert not (E.footer.__isabstractmethod__)


def test_customdescriptors_with_abstractmethod_namespaced(abc, namespace):
    class Descriptor:
        """A descriptor class integrated some with the ABC protocol."""

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

    class C(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        with namespace() as ns:
            @Descriptor
            @abstractmethod
            def footer(self):
                return 3

            @footer.setter
            @abstractmethod
            def footer(self, val):
                pass
    with pytest.raises(TypeError):
        print(C())

    class D(C):
        """A throwaway test class."""
        with namespace() as ns:
            @C.ns.footer.getter
            def footer(self):
                return super().ns.footer
    with pytest.raises(TypeError):
        print(D())

    class E(D):
        """A throwaway test class."""
        with namespace() as ns:
            @D.ns.footer.setter
            def footer(self, val):
                pass
    assert not (E.ns.footer.__isabstractmethod__)


def test_metaclass_abc(abc):
    # Metaclasses can be ABCs, too.
    class A(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        @abstractmethod
        def x(self):
            pass
    assert A.__abstractmethods__ == {"x"}

    class meta(type, A):
        """A throwaway test metaclass."""

        def x(self):
            return 1

    class C(metaclass=meta):
        """A throwaway test class."""


def test_metaclass_abc_namespaced(abc, namespace):
    # Metaclasses can be ABCs, too.
    class A(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        with namespace() as ns:
            @abstractmethod
            def x(self):
                pass
    assert A.__abstractmethods__ == {"ns.x"}

    class meta(type, A):
        """A throwaway test metaclass."""
        with namespace() as ns:
            def x(self):
                return 1

    class C(metaclass=meta):
        """A throwaway test class."""


def test_registration_basics(abc):
    class A(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""

    class B(object):
        """A throwaway test class."""
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
        """A throwaway test class."""
    c = C()
    assert issubclass(C, A)
    assert issubclass(C, (A,))
    assert isinstance(c, A)
    assert isinstance(c, (A,))


def test_register_as_class_deco(abc):
    class A(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""

    @A.register
    class B(object):
        """A throwaway test class."""
    b = B()
    assert issubclass(B, A)
    assert issubclass(B, (A,))
    assert isinstance(b, A)
    assert isinstance(b, (A,))

    @A.register
    class C(B):
        """A throwaway test class."""
    c = C()
    assert issubclass(C, A)
    assert issubclass(C, (A,))
    assert isinstance(c, A)
    assert isinstance(c, (A,))
    assert C is A.register(C)


@pytest.mark.xfail(sys.version_info < (3, 4),
                   reason="python3.4 api changes?", strict=True)
def test_isinstance_invalidation(abc):
    class A(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""

    class B:
        """A throwaway test class."""
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
    class A(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
    A.register(int)
    assert isinstance(42, A)
    assert isinstance(42, (A,))
    assert issubclass(int, A)
    assert issubclass(int, (A,))

    class B(A):
        """A throwaway test class."""
    B.register(str)

    class C(str):
        """A throwaway test class."""
    assert isinstance("", A)
    assert isinstance("", (A,))
    assert issubclass(str, A)
    assert issubclass(str, (A,))
    assert issubclass(C, A)
    assert issubclass(C, (A,))


def test_registration_edge_cases(abc):
    class A(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
    A.register(A)  # should pass silently

    class A1(A):
        """A throwaway test class."""
    with pytest.raises(RuntimeError):
        A1.register(A)  # cycles not allowed

    class B(object):
        """A throwaway test class."""
    A1.register(B)  # ok
    A1.register(B)  # should pass silently

    class C(A):
        """A throwaway test class."""
    A.register(C)  # should pass silently
    with pytest.raises(RuntimeError):
        C.register(A)  # cycles not allowed
    C.register(B)  # ok


def test_register_non_class(abc):
    class A(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
    with pytest.raises(TypeError, message="Can only register classes"):
        print(A.register(4))


def test_registration_transitiveness(abc):
    class A(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
    assert issubclass(A, A)
    assert issubclass(A, (A,))

    class B(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
    assert not (issubclass(A, B))
    assert not (issubclass(A, (B,)))
    assert not (issubclass(B, A))
    assert not (issubclass(B, (A,)))

    class C(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
    A.register(B)

    class B1(B):
        """A throwaway test class."""
    assert issubclass(B1, A)
    assert issubclass(B1, (A,))

    class C1(C):
        """A throwaway test class."""
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
        """A throwaway test class."""
    assert issubclass(MyInt, A)
    assert issubclass(MyInt, (A,))
    assert isinstance(42, A)
    assert isinstance(42, (A,))


def test_all_new_methods_are_called(abc):
    class A(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""

    class B(object):
        """A throwaway test class."""
        counter = 0

        def __new__(cls):
            B.counter += 1
            return super().__new__(cls)

    class C(A, B):
        """A throwaway test class."""
    assert B.counter == 0
    C()
    assert B.counter == 1
