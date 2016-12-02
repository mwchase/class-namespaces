import sys

import pytest


def test_import(namespaces):
    """Test the module is importable. See conftest.py for the actual import."""
    assert namespaces


def test_meta_basic(namespaceable):
    """Make a namespaceable class by subclassing from Namespaceable."""
    class Test(namespaceable):
        """A throwaway test class."""
    assert Test


def test_basic_namespace(namespaceable, namespace):
    """Define an attribute within a namespace.

    Attributes in a Namespace live in that Namespace, and are accessible from
    both the class, and any instance of the class.
    """
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            a = 1
        assert ns
    assert Test
    assert Test().ns
    assert Test.ns.a == 1
    assert Test().ns.a == 1


def test_delete(namespaceable, namespace):
    """Delete attributes from a namespace, at various points.

    Inside a Namespace context, you can delete a variable from the current
    Namespace.

    You cannot delete an attribute in a class Namespace, from an instance
    namespace.

    Missing attributes have proper exception behavior.
    """
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            a = 1
            del a
            b = 2
        assert ns
    assert Test
    assert Test().ns
    assert Test.ns.b == 2
    assert Test().ns.b == 2
    with pytest.raises(AttributeError, message='b'):
        del Test().ns.b
    del Test.ns.b
    with pytest.raises(AttributeError, message='b'):
        print(Test.ns.b)
    with pytest.raises(AttributeError, message='b'):
        print(Test().ns.b)


def test_set(namespaceable, namespace):
    """Set attributes on a namespace, at various points.

    You can set attributes on a Namespace after the class definition. The
    changes will be visible on both the class, and on instances.

    You can set attributes on an instance Namespace. This will not propagate up
    to the class Namespace.
    """
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            a = 1
            del a
        assert ns
    assert Test
    assert Test().ns
    Test.ns.b = 2
    assert Test.ns.b == 2
    assert Test().ns.b == 2
    test = Test()
    test.ns.b = 3
    assert Test.ns.b == 2
    assert test.ns.b == 3
    test2 = Test()
    test2.ns.c = 3
    with pytest.raises(AttributeError, message='c'):
        print(Test.ns.c)
    with pytest.raises(AttributeError, message='c'):
        print(test.ns.c)
    assert test2.ns.c == 3


@pytest.mark.xfail(sys.version_info < (3, 4),
                   reason="python3.4 api changes?", strict=True)
def test_dir(namespaceable, namespace):
    """Confirm the shape of dir.

    Dir provides a view of what's accessible from a single Namespace.

    There is some kind of interaction between Python, the libraries, and the
    Namespace code that reliably occurs on 3.3. I believe it's not really a
    problem.
    """
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            a = 1
        assert ns
        assert dir(ns) == ['a']
    assert dir(Test.ns) == ['a']
    assert dir(Test().ns) == ['a']


def test_shadow(namespaceable, namespace):
    """Define several attributes with the same name, in different scopes.

    Namespaces divide a class up into distinct pieces. A name defined in one
    place doesn't interfere with using the same name elsewhere.
    """
    class Test(namespaceable):
        """A throwaway test class."""
        footer = 1
        with namespace() as ns:
            footer = 2
            assert footer == 2
        assert footer == 1
    assert Test().footer == 1
    assert Test().ns.footer == 2


def test_resume(namespaceable, namespace):
    """Enter the same namespace multiple times.

    Namespaces are not only context managers, but reusable context managers.
    A resumed Namespace is truly the same scope.
    """
    class Test(namespaceable):
        """A throwaway test class."""
        footer = 1
        with namespace() as ns:
            footer = 2
            assert footer == 2
        assert footer == 1
        footer = 3
        with ns:
            assert footer == 2
            footer = 4
        assert footer == 3
    assert Test().footer == 3
    assert Test().ns.footer == 4


def assert_equals(a, b):
    """Compare a and b in a predictable scope.

    pytest can get confused inside a Namespaceable class definition.
    """
    assert a == b


def test_recursive_get_in_definition(namespaceable, namespace):
    """Look at namespace attributes during class definition.

    Clearly, this should just work, yet it did not always, so now there is a
    test.
    """
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            with namespace() as ns:
                footer = 1
        assert_equals(ns.ns.footer, 1)


def test_basic_inherit(namespaceable, namespace):
    """Make a subclass of a Namespaceable class.

    The Namespace resolution hooks into Python's existing systems, so any kind
    of inheritance structure should work (equally well as without namespacing).
    """
    class Test(namespaceable):
        """A throwaway test class."""
        footer = 1
        with namespace() as ns:
            footer = 2

    class Subclass(Test):
        """A throwaway test class."""
    assert Subclass().footer == 1
    assert Subclass().ns.footer == 2


def test_basic_super(namespaceable, namespace):
    """Use super() inside a method defined in a Namespace.

    Everything Python gives you to deal with inheritance should work equally
    well. That includes super().
    """
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            def hello(self):
                """Return a predictable constant."""
                return 1

    class Subclass(Test):
        """A throwaway test class."""
        with namespace() as ns:
            def hello(self):
                """Return the superclass's hello."""
                return super().ns.hello()

    assert Test().ns.hello() == 1
    assert Subclass().ns.hello() == 1


def test_private(namespaceable, namespace):
    """Use name mangling and subclassing together.

    Name mangling is meant to protect an implementation from being overridden
    by subclasses. Because it occurs before the Namespace code sees it, this
    happens for free, and is automatically correct.
    """
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as __ns:
            footer = 2

        def footer(self):
            """Access a private namespace."""
            return self.__ns.footer

    class Subclass(Test):
        """A throwaway test class."""

        def my_footer(self):
            """Access a non-existent private namespace."""
            return self.__ns.footer

    assert Test().footer() == 2
    assert Subclass().footer() == 2
    with pytest.raises(
            AttributeError, message="object has no attribute '_Subclass__ns'"):
        print(Subclass().my_footer())


def test_nested_namespace(namespaceable, namespace):
    """Define a Namespace in a Namespace."""
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            with namespace() as ns:
                a = 1
    assert Test().ns.ns.a == 1


def test_basic_shadow(namespaceable, namespace):
    """Define an attribute over a Namespace."""
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            footer = 2

    class Subclass(Test):
        """A throwaway test class."""
        ns = 1
    assert Subclass().ns == 1


def test_double_shadow(namespaceable, namespace):
    """Define an attribute over a Namespace, then a Namespace over that.

    Non-namespace attributes block the visibility of Namespaces in parent
    classes.
    """
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            footer = 2

    class Subclass(Test):
        """A throwaway test class."""
        ns = 1

    class DoubleSubclass(Subclass):
        """A throwaway test class."""
        with namespace() as ns:
            barter = 1
    assert not hasattr(DoubleSubclass().ns, 'footer')


def test_overlap(namespaceable, namespace):
    """Define different attributes in the same Namespace in a subclass.

    Namespaces delegate to parent classes, if not blocked.
    """
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            footer = 2

    class Subclass(Test):
        """A throwaway test class."""
        with namespace() as ns:
            barter = 3
    assert Subclass().ns.footer == 2
    assert Subclass().ns.barter == 3


def test_advanced_overlap(namespaceable, namespace):
    """Do the same things as in test_overlap, but with a little nesting."""
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            footer = 2
            with namespace() as ns:
                qux = 4

    class Subclass(Test):
        """A throwaway test class."""
        with namespace() as ns:
            barter = 3
    assert Subclass().ns.footer == 2
    assert Subclass().ns.barter == 3
    assert Subclass().ns.ns.qux == 4


def test_use_namespace(namespaceable, namespace):
    """Interact with a namespace's attributes."""
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            footer = 1
            qux = 3
        assert ns.footer == 1
        ns.barter = 2
        assert ns.barter == 2
        del ns.qux
        # I tried to add a message to this one. It broke. ¯\_(ツ)_/¯
        with pytest.raises(AttributeError):
            del ns.qux
    assert Test.ns.footer == 1
    assert Test.ns.barter == 2


def test_basic_prop(namespaceable, namespace):
    """Define a property in a Namespace.

    Data descriptors work.
    """
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            @property
            def footer(self):
                return 1
    assert Test().ns.footer == 1


def test_complicated_prop(namespaceable, namespace):
    """Define a property with all methods.

    @property.method works.
    """
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            @property
            def var(self):
                return self.__private.var

            @var.setter
            def var(self, value):
                self.__private.var = value + 1

            @var.deleter
            def var(self):
                del self.__private.var

        with namespace() as __private:
            var = None

    test = Test()
    assert test.ns.var is None
    test.ns.var = 1
    assert test.ns.var == 2
    del test.ns.var
    assert test.ns.var is None


def test_override_method(namespaceable, namespace):
    """Define a function, then overwrite it.

    Non-data descriptors work.
    """
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            def footer(self):
                return 1
    test = Test()
    assert test.ns.footer() == 1
    test.ns.footer = 2
    print(vars(test))
    assert test.ns.footer == 2
    del test.ns.footer
    assert test.ns.footer() == 1
    Test.ns.footer = 3
    assert Test.ns.footer == 3
    assert test.ns.footer == 3


def test_add_later(namespaceable, namespace):
    """Add a Namespace to a class, post-creation."""
    class Test(namespaceable):
        """A throwaway test class."""

    ns = namespace()
    Test.ns = ns
    print('ns props')
    for slot in namespace.__slots__:
        print(slot, getattr(ns, slot))
    ns2 = namespace()
    Test.ns.ns = ns2
    print('ns2 props')
    for slot in namespace.__slots__:
        print(slot, getattr(ns2, slot))
    Test.ns.value = 1
    assert Test.ns.value == 1
    Test.ns.ns.value = 2
    assert Test.ns.ns.value == 2
    assert Test.ns.value == 1


@pytest.mark.xfail(sys.version_info < (3, 6),
                   reason="python3.6 api changes", strict=True)
def test_3_6_descriptor(namespaces, namespaceable, namespace):
    """Create a descriptor that implements __set_name__, confirm it works.

    This test is invalid before 3.6.
    """
    class Descriptor:
        """A descriptor that only sets its name."""

        def __set_name__(self, owner, name):
            self.owner = owner
            self.name = name
    assert namespaces.namespaces._DescriptorInspector(
        Descriptor()).is_descriptor

    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            d = Descriptor()

    assert Test.ns.d.name == 'd'


def test_basic_meta(namespaceable, namespace):
    """Test the basic interactions between Namespaceable and metaclasses."""
    class Meta(namespaceable, type(namespaceable)):
        """A throwaway test metaclass."""
        with namespace() as ns:
            meta_var = 1

    class Test(namespaceable, metaclass=Meta):
        """A throwaway test class."""

    assert Meta.ns.meta_var == 1
    assert Test.ns.meta_var == 1
    with pytest.raises(AttributeError, message='meta_var'):
        print(Test().ns.meta_var)


def test_somewhat_weirder_meta(namespaceable, namespace):
    """Test that attribute visibility works with Namespaceable, metaclasses."""
    class Meta(namespaceable, type(namespaceable)):
        """A throwaway test metaclass."""
        with namespace() as ns:
            meta_var = 1

    class Test(namespaceable, metaclass=Meta):
        """A throwaway test class."""
        with namespace() as ns:
            cls_var = 2

    assert Meta.ns.meta_var == 1
    assert Test.ns.meta_var == 1
    assert Test.ns.cls_var == 2
    assert Test().ns.cls_var == 2
    with pytest.raises(AttributeError, message='meta_var'):
        print(Test().ns.meta_var)
    with pytest.raises(AttributeError, message='var'):
        print(Test.ns.var)
    with pytest.raises(AttributeError, message='cls_var'):
        print(Meta.ns.cls_var)
    Test.var = 3
    assert Test.var == 3
    Meta.var = 4
    assert Meta.var == 4


def test_classmethod_basic(namespaceable, namespace):
    """Test using a classmethod in a Namespace."""
    class Test(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            @classmethod
            def cls_mthd(cls):
                """Return that a call occurred."""
                return 'called'

    assert Test.ns.cls_mthd() == 'called'
    assert Test().ns.cls_mthd() == 'called'


def test_meta_plus_classmethod(namespaceable, namespace):
    """Test using a classmethod in a Namespace, while messing with metaclasses.

    This might have been purely for coverage of some kind? I forget.
    """
    class Meta(namespaceable, type(namespaceable)):
        """A throwaway test metaclass."""
        with namespace() as ns:
            pass

    class Test(namespaceable, metaclass=Meta):
        """A throwaway test class."""
        with namespace() as ns:
            @classmethod
            def cls_mthd(cls):
                """Return that a call occurred."""
                return 'called'

    assert Test().ns.cls_mthd() == 'called'
    assert Test.ns.cls_mthd() == 'called'


def test_get_through_namespace(namespaceable, namespace):
    """Define a variable in a Namespace in terms of a variable in parent scope.

    Like other scopes in Python, Namespaces allow you to get variables from
    outer scopes.
    """
    class Test(namespaceable):
        """A throwaway test class."""
        var = 1
        with namespace() as ns:
            var2 = var

    assert Test.var == 1
    assert Test.ns.var2 == 1


def test_multiple_inheritance(namespaceable, namespace):
    """Define some base classes with Namespaces, inherit, confirm they merged.

    Everything Python gives you to deal with inheritance should work equally
    well. That includes multiple inheritance.
    """
    class Test1(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            with namespace() as ns:
                var = 1

    class Test2(namespaceable):
        """A throwaway test class."""
        with namespace() as ns:
            var = 2

    class Test3(Test2, Test1):
        """A throwaway test class."""

    assert Test3.ns.ns.var == 1
    assert Test3.ns.var == 2


def test_regular_delete(namespaceable):
    """Define and delete a variable in a Namespaceable class.

    This isn't too exciting, but if we don't prove this works, there's a
    coverage gap.
    """
    class Test(namespaceable):
        """A throwaway test class."""
    Test.var = 1
    assert Test.var == 1
    del Test.var
