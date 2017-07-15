"""Test the integration of namespaces with abstract base classes."""

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
    """Test the convenience class exists."""
    assert abc.NamespaceableABC


def test_abc_helper(abc):
    """Test the convenience class works as expected."""
    # create an ABC using the helper class and perform basic checks
    class CClass(abc.NamespaceableABC):
        """A throwaway test class."""
        @classmethod
        @abstractmethod
        def footer(cls):
            """Return the class's name. Abstract."""
            return cls.__name__
    assert isinstance(CClass, abc.NamespaceableABCMeta)
    with pytest.raises(TypeError):
        print(CClass())

    class DClass(CClass):
        """A throwaway test class."""
        @classmethod
        def footer(cls):
            """Return the class's name. Concrete."""
            return super().footer()
    assert DClass.footer() == 'DClass'


def test_abstractmethod_basics():
    """Test abstractmethod works as expected.

    Adapted from Python's test suite.
    """
    @abstractmethod
    def footer(self):
        """Return self. Abstract."""
        return self
    assert footer.__isabstractmethod__

    def barter(self):
        """Return self. Concrete."""
        return self
    assert not hasattr(barter, "__isabstractmethod__")


# IT IS TOO USED.
def test_abstractproperty_basics(abc):
    """Test abstract property works as expected.

    Adapted from Python's test suite.
    """
    @property
    @abstractmethod
    def footer(self):
        """Return nothing. Abstract."""
    assert footer.__isabstractmethod__

    def barter(self):
        """Return nothing. Concrete."""
    assert not getattr(barter, "__isabstractmethod__", False)

    class CClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        @property
        @abstractmethod
        def footer(self):
            """Return 3. Abstract."""
            return 3
    with pytest.raises(TypeError):
        print(CClass())

    class DClass(CClass):
        """A throwaway test class."""
        @CClass.footer.getter
        def footer(self):
            """Return 3. Concrete."""
            return super().footer
    assert DClass().footer == 3


def test_abstractproperty_namespaced(abc, namespace):
    """Test interaction between namespaces and abstract properties."""
    class CClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        with namespace() as namespace_:
            @property
            @abstractmethod
            def footer(self):
                """Return 3. Abstract."""
                return 3
    with pytest.raises(TypeError):
        print(CClass())

    class DClass(CClass):
        """A throwaway test class."""
        with namespace() as namespace_:
            @CClass.namespace_.footer.getter
            def footer(self):
                """Return 3. Concrete."""
                return super().namespace_.footer
    assert DClass().namespace_.footer == 3


def test_abstractclassmethod_basics(abc):
    """Test abstract classmethod works as expected.

    Adapted from Python's test suite.
    """
    @classmethod
    @abstractmethod
    def footer(cls):
        """Return cls. Abstract."""
        return cls
    assert footer.__isabstractmethod__

    @classmethod
    def barter(cls):
        """Return cls. Concrete."""
        return cls
    assert not getattr(barter, "__isabstractmethod__", False)

    class CClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        @classmethod
        @abstractmethod
        def footer(cls):
            """Return class name. Abstract."""
            return cls.__name__
    with pytest.raises(TypeError):
        print(CClass())

    class DClass(CClass):
        """A throwaway test class."""
        @classmethod
        def footer(cls):
            """Return class name. Concrete."""
            return super().footer()
    assert DClass.footer() == 'DClass'
    assert DClass().footer() == 'DClass'


def test_abstractclassmethod_namespaced(abc, namespace):
    """Test interaction between namespaces and abstract classmethods."""
    class CClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        with namespace() as namespace_:
            @classmethod
            @abstractmethod
            def footer(cls):
                """Return class name. Abstract."""
                return cls.__name__
    with pytest.raises(TypeError):
        print(CClass())

    class DClass(CClass):
        """A throwaway test class."""
        with namespace() as namespace_:
            @classmethod
            def footer(cls):
                """Return class name. Concrete."""
                return super().namespace_.footer()
    assert DClass.namespace_.footer() == 'DClass'
    assert DClass().namespace_.footer() == 'DClass'


def test_abstractstaticmethod_basics(abc):
    """Test abstract staticmethod works as expected.

    Adapted from Python's test suite.
    """
    @staticmethod
    @abstractmethod
    def footer():
        """Do nothing. Abstract."""
    assert footer.__isabstractmethod__

    @staticmethod
    def barter():
        """Do nothing. Concrete."""
    assert not getattr(barter, "__isabstractmethod__", False)

    class CClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        @staticmethod
        @abstractmethod
        def footer():
            """Return 3. Abstract."""
            return 3
    with pytest.raises(TypeError):
        print(CClass())

    class DClass(CClass):
        """A throwaway test class."""
        @staticmethod
        def footer():
            """Return 4. Concrete."""
            return 4
    assert DClass.footer() == 4
    assert DClass().footer() == 4


def test_abstractstaticmethod_namespaced(abc, namespace):
    """Test interaction between namespaces and abstract staticmethods."""
    class CClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        with namespace() as namespace_:
            @staticmethod
            @abstractmethod
            def footer():
                """Return 3. Abstract."""
                return 3
    with pytest.raises(TypeError):
        print(CClass())

    class DClass(CClass):
        """A throwaway test class."""
        with namespace() as namespace_:
            @staticmethod
            def footer():
                """Return 4. Concrete."""
                return 4
    assert DClass.namespace_.footer() == 4
    assert DClass().namespace_.footer() == 4


def test_abstractmethod_integration(abc):
    """Test abstract shortcut decorators work as expected.

    Adapted from Python's test suite.
    """
    for abstractthing in [abstractmethod, abc_main.abstractproperty,
                          abc_main.abstractclassmethod,
                          abc_main.abstractstaticmethod]:
        class CClass(metaclass=abc.NamespaceableABCMeta):
            """A throwaway test class."""
            @abstractthing
            def footer(self):
                """Do nothing. Abstract."""

            def barter(self):
                """Do nothing. Concrete."""
        assert CClass.__abstractmethods__ == {"footer"}
        with pytest.raises(TypeError):
            print(CClass())  # because footer is abstract
        assert isabstract(CClass)

        class DClass(CClass):
            """A throwaway test class."""

            def barter(self):
                pass  # concrete override of concrete
        assert DClass.__abstractmethods__ == {"footer"}
        with pytest.raises(TypeError):
            print(DClass())  # because footer is still abstract
        assert isabstract(DClass)

        class EClass(DClass):
            """A throwaway test class."""

            def footer(self):
                pass
        assert EClass.__abstractmethods__ == set()
        EClass()  # now footer is concrete, too
        assert not isabstract(EClass)

        class FClass(EClass):
            """A throwaway test class."""
            @abstractthing
            def barter(self):
                pass  # abstract override of concrete
        assert FClass.__abstractmethods__ == {"barter"}
        with pytest.raises(TypeError):
            print(FClass())  # because barter is abstract now
        assert isabstract(FClass)


def test_abstractmethod_integration_namespaced(abc, namespace):
    """Test abstract shortcut decorators work as expected, under a namespace.

    Adapted from Python's test suite.
    """
    for abstractthing in [abstractmethod, abc_main.abstractproperty,
                          abc_main.abstractclassmethod,
                          abc_main.abstractstaticmethod]:
        class CClass(metaclass=abc.NamespaceableABCMeta):
            """A throwaway test class."""
            with namespace() as namespace_:
                @abstractthing
                def footer(self):
                    """Do nothing. Abstract."""

                def barter(self):
                    """Do nothing. Concrete."""
        assert CClass.__abstractmethods__ == {"namespace_.footer"}
        with pytest.raises(TypeError):
            print(CClass())  # because footer is abstract
        assert isabstract(CClass)

        class DClass(CClass):
            """A throwaway test class."""
            with namespace() as namespace_:
                def barter(self):
                    pass  # concrete override of concrete
        assert DClass.__abstractmethods__ == {"namespace_.footer"}
        with pytest.raises(TypeError):
            print(DClass())  # because footer is still abstract
        assert isabstract(DClass)

        class EClass(DClass):
            """A throwaway test class."""
            with namespace() as namespace_:
                def footer(self):
                    pass
        assert EClass.__abstractmethods__ == set()
        EClass()  # now footer is concrete, too
        assert not isabstract(EClass)

        class FClass(EClass):
            """A throwaway test class."""
            with namespace() as namespace_:
                @abstractthing
                def barter(self):
                    pass  # abstract override of concrete
        assert FClass.__abstractmethods__ == {"namespace_.barter"}
        with pytest.raises(TypeError):
            print(FClass())  # because barter is abstract now
        assert isabstract(FClass)


def test_descriptors_with_abstractmethod(abc):
    """Test abstract property methods work as expected.

    Adapted from Python's test suite.
    """
    class CClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        @property
        @abstractmethod
        def footer(self):
            """Return 3. Abstract."""
            return 3

        @footer.setter
        @abstractmethod
        def footer(self, val):
            """Discard input value. Abstract."""
    with pytest.raises(TypeError):
        print(CClass())

    class DClass(CClass):
        """A throwaway test class."""
        @CClass.footer.getter
        def footer(self):
            """Return 3. Concrete."""
            return super().footer
    with pytest.raises(TypeError):
        print(DClass())

    class EClass(DClass):
        """A throwaway test class."""
        @DClass.footer.setter
        def footer(self, val):
            """Discard input value. Concrete."""
    assert EClass().footer == 3
    # check that the property's __isabstractmethod__ descriptor does the
    # right thing when presented with a value that fails truth testing:

    class NotBool(object):
        """A pathological class for test purposes."""

        def __bool__(self):
            raise ValueError()
        __len__ = __bool__
    with pytest.raises(ValueError):
        class FClass(CClass):
            """A throwaway test class."""

            def barter(self):
                """Do nothing."""
            barter.__isabstractmethod__ = NotBool()
            footer = property(barter)


def test_descriptors_with_abstractmethod_namespaced(abc, namespace):
    """Test abstract property methods work as expected under a namespace.

    Adapted from Python's test suite.
    """
    class CClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        with namespace() as namespace_:
            @property
            @abstractmethod
            def footer(self):
                """Return 3. Abstract."""
                return 3

            @footer.setter
            @abstractmethod
            def footer(self, val):
                """Discard input value. Abstract."""
    with pytest.raises(TypeError):
        print(CClass())

    class DClass(CClass):
        """A throwaway test class."""
        with namespace() as namespace_:
            @CClass.namespace_.footer.getter
            def footer(self):
                """Return 3. Concrete."""
                return super().namespace_.footer
    with pytest.raises(TypeError):
        print(DClass())

    class EClass(DClass):
        """A throwaway test class."""
        with namespace() as namespace_:
            @DClass.namespace_.footer.setter
            def footer(self, val):
                """Discard input value. Concrete"""
    assert EClass().namespace_.footer == 3
    # check that the property's __isabstractmethod__ descriptor does the
    # right thing when presented with a value that fails truth testing:

    class NotBool(object):
        """A pathological class for test purposes."""

        def __bool__(self):
            raise ValueError()
        __len__ = __bool__
    with pytest.raises(ValueError):
        class FClass(CClass):
            """A throwaway test class."""
            with namespace() as namespace_:
                def barter(self):
                    """Do nothing."""
                barter.__isabstractmethod__ = NotBool()
                footer = property(barter)


def test_customdescriptors_with_abstractmethod(abc):
    """Test abstract custom descriptors work as expected.

    Adapted from Python's test suite.
    """
    class Descriptor:
        """A descriptor class integrated some with the ABC protocol."""

        def __init__(self, fget, fset=None):
            self._fget = fget
            self._fset = fset

        def getter(self, callable):
            """Replace self._fget with callable."""
            return Descriptor(callable, self._fset)

        def setter(self, callable):
            """Replace self._fset with callable."""
            return Descriptor(self._fget, callable)

        @property
        def __isabstractmethod__(self):
            """Return whether the descriptor is abstract."""
            return (getattr(self._fget, '__isabstractmethod__', False) or
                    getattr(self._fset, '__isabstractmethod__', False))

    class CClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        @Descriptor
        @abstractmethod
        def footer(self):
            """Return 3. Abstract."""
            return 3

        @footer.setter
        @abstractmethod
        def footer(self, val):
            """Discard input value. Abstract."""
    with pytest.raises(TypeError):
        print(CClass())

    class DClass(CClass):
        """A throwaway test class."""
        @CClass.footer.getter
        def footer(self):
            """Return 3. Concrete."""
            return super().footer
    with pytest.raises(TypeError):
        print(DClass())

    class EClass(DClass):
        """A throwaway test class."""
        @DClass.footer.setter
        def footer(self, val):
            """Discard input value. Concrete."""
    assert not EClass.footer.__isabstractmethod__


def test_customdescriptors_with_abstractmethod_namespaced(abc, namespace):
    """Test abstract custom descriptors work as expected under a namespace.

    Adapted from Python's test suite.
    """
    class Descriptor:
        """A descriptor class integrated some with the ABC protocol."""

        def __init__(self, fget, fset=None):
            self._fget = fget
            self._fset = fset

        def getter(self, callable):
            """Replace self._fget with callable."""
            return Descriptor(callable, self._fset)

        def setter(self, callable):
            """Replace self._fset with callable."""
            return Descriptor(self._fget, callable)

        @property
        def __isabstractmethod__(self):
            """Return whether the descriptor is abstract."""
            return (getattr(self._fget, '__isabstractmethod__', False) or
                    getattr(self._fset, '__isabstractmethod__', False))

    class CClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        with namespace() as namespace_:
            @Descriptor
            @abstractmethod
            def footer(self):
                """Return 3. Abstract."""
                return 3

            @footer.setter
            @abstractmethod
            def footer(self, val):
                """Discard the input value. Abstract."""
    with pytest.raises(TypeError):
        print(CClass())

    class DClass(CClass):
        """A throwaway test class."""
        with namespace() as namespace_:
            @CClass.namespace_.footer.getter
            def footer(self):
                """Return 3. Concrete."""
                return super().namespace_.footer
    with pytest.raises(TypeError):
        print(DClass())

    class EClass(DClass):
        """A throwaway test class."""
        with namespace() as namespace_:
            @DClass.namespace_.footer.setter
            def footer(self, val):
                """Discard the input value. Concrete."""
    assert not EClass.namespace_.footer.__isabstractmethod__


def test_metaclass_abc(abc):
    """Test abstract metaclasses work as expected.

    Adapted from Python's test suite.
    """
    # Metaclasses can be ABCs, too.
    class AClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        @abstractmethod
        def x_m(self):
            """Do nothing. Abstract."""
    assert AClass.__abstractmethods__ == {"x_m"}

    class Meta(type, AClass):
        """A throwaway test metaclass."""

        def x_m(self):
            """Return 1. Concrete."""
            return 1

    class CClass(metaclass=Meta):
        """A throwaway test class."""


def test_metaclass_abc_namespaced(abc, namespace):
    """Test abstract metaclasses work as expected, with namespaces.

    Adapted from Python's test suite.
    """
    # Metaclasses can be ABCs, too.
    class AClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
        with namespace() as namespace_:
            @abstractmethod
            def x_m(self):
                """Do nothing. Abstract."""
    assert AClass.__abstractmethods__ == {"namespace_.x_m"}

    class Meta(type, AClass):
        """A throwaway test metaclass."""
        with namespace() as namespace_:
            def x_m(self):
                """Return 1. Concrete."""
                return 1

    class CClass(metaclass=Meta):
        """A throwaway test class."""


def test_registration_basics(abc):
    """Test ABC registration.

    Adapted from Python's test suite.
    """
    class AClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""

    class BClass(object):
        """A throwaway test class."""
    b = BClass()
    assert not (issubclass(BClass, AClass))
    assert not (issubclass(BClass, (AClass,)))
    assert not isinstance(b, AClass)
    assert not isinstance(b, (AClass,))
    BClass1 = AClass.register(BClass)
    assert issubclass(BClass, AClass)
    assert issubclass(BClass, (AClass,))
    assert isinstance(b, AClass)
    assert isinstance(b, (AClass,))
    assert BClass1 is BClass

    class CClass(BClass):
        """A throwaway test class."""
    c = CClass()
    assert issubclass(CClass, AClass)
    assert issubclass(CClass, (AClass,))
    assert isinstance(c, AClass)
    assert isinstance(c, (AClass,))


def test_register_as_class_deco(abc):
    """Test ABC registration decorator.

    Adapted from Python's test suite.
    """
    class AClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""

    @AClass.register
    class BClass(object):
        """A throwaway test class."""
    b = BClass()
    assert issubclass(BClass, AClass)
    assert issubclass(BClass, (AClass,))
    assert isinstance(b, AClass)
    assert isinstance(b, (AClass,))

    @AClass.register
    class CClass(BClass):
        """A throwaway test class."""
    c = CClass()
    assert issubclass(CClass, AClass)
    assert issubclass(CClass, (AClass,))
    assert isinstance(c, AClass)
    assert isinstance(c, (AClass,))
    assert CClass is AClass.register(CClass)


@pytest.mark.xfail(sys.version_info < (3, 4),
                   reason="python3.4 api changes?", strict=True)
def test_isinstance_invalidation(abc):
    """Test after-the-fact registration behavior.

    Adapted from Python's test suite.
    """
    class AClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""

    class BClass:
        """A throwaway test class."""
    b = BClass()
    assert not (isinstance(b, AClass))
    assert not (isinstance(b, (AClass,)))
    token_old = abc_main.get_cache_token()
    AClass.register(BClass)
    token_new = abc_main.get_cache_token()
    assert token_old != token_new
    assert isinstance(b, AClass)
    assert isinstance(b, (AClass,))


def test_registration_builtins(abc):
    """Test making builtin classes into registered subclasses.

    Adapted from Python's test suite.
    """
    class AClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
    AClass.register(int)
    assert isinstance(42, AClass)
    assert isinstance(42, (AClass,))
    assert issubclass(int, AClass)
    assert issubclass(int, (AClass,))

    class BClass(AClass):
        """A throwaway test class."""
    BClass.register(str)

    class CClass(str):
        """A throwaway test class."""
    assert isinstance("", AClass)
    assert isinstance("", (AClass,))
    assert issubclass(str, AClass)
    assert issubclass(str, (AClass,))
    assert issubclass(CClass, AClass)
    assert issubclass(CClass, (AClass,))


def test_registration_edge_cases(abc):
    """Test edge cases in registration: reflexive, cyclic, repeated...

    Adapted from Python's test suite.
    """
    class AClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
    AClass.register(AClass)  # should pass silently

    class AClass1(AClass):
        """A throwaway test class."""
    with pytest.raises(RuntimeError):
        AClass1.register(AClass)  # cycles not allowed

    class BClass(object):
        """A throwaway test class."""
    AClass1.register(BClass)  # ok
    AClass1.register(BClass)  # should pass silently

    class CClass(AClass):
        """A throwaway test class."""
    AClass.register(CClass)  # should pass silently
    with pytest.raises(RuntimeError):
        CClass.register(AClass)  # cycles not allowed
    CClass.register(BClass)  # ok


def test_register_non_class(abc):
    """Test that non-classes cannot be registered.

    Adapted from Python's test suite.
    """
    class AClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
    with pytest.raises(TypeError, message="Can only register classes"):
        print(AClass.register(4))


def test_registration_transitiveness(abc):
    """Test that chains of registration hold.

    Adapted from Python's test suite.
    """
    class AClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
    assert issubclass(AClass, AClass)
    assert issubclass(AClass, (AClass,))

    class BClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
    assert not (issubclass(AClass, BClass))
    assert not (issubclass(AClass, (BClass,)))
    assert not (issubclass(BClass, AClass))
    assert not (issubclass(BClass, (AClass,)))

    class CClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""
    AClass.register(BClass)

    class BClass1(BClass):
        """A throwaway test class."""
    assert issubclass(BClass1, AClass)
    assert issubclass(BClass1, (AClass,))

    class CClass1(CClass):
        """A throwaway test class."""
    BClass1.register(CClass1)
    assert not issubclass(CClass, BClass)
    assert not issubclass(CClass, (BClass,))
    assert not issubclass(CClass, BClass1)
    assert not issubclass(CClass, (BClass1,))
    assert issubclass(CClass1, AClass)
    assert issubclass(CClass1, (AClass,))
    assert issubclass(CClass1, BClass)
    assert issubclass(CClass1, (BClass,))
    assert issubclass(CClass1, BClass1)
    assert issubclass(CClass1, (BClass1,))
    CClass1.register(int)

    class MyInt(int):
        """A throwaway test class."""
    assert issubclass(MyInt, AClass)
    assert issubclass(MyInt, (AClass,))
    assert isinstance(42, AClass)
    assert isinstance(42, (AClass,))


def test_all_new_methods_are_called(abc):
    """Test that super delegation still works using abstract classes.

    Adapted from Python's test suite.
    """
    class AClass(metaclass=abc.NamespaceableABCMeta):
        """A throwaway test class."""

    class BClass(object):
        """A throwaway test class."""
        counter = 0

        def __new__(cls):
            BClass.counter += 1
            return super().__new__(cls)

    class CClass(AClass, BClass):
        """A throwaway test class."""
    assert BClass.counter == 0
    CClass()
    assert BClass.counter == 1
