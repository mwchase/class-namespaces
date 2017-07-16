"""Test the public behavior of namespaces."""

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
        """A throwaway test class, for testing get behavior."""
        with namespace() as namespace_:
            attribute = 1
        assert namespace_
    assert Test
    assert Test().namespace_
    assert Test.namespace_.attribute == 1
    assert Test().namespace_.attribute == 1


def test_delete(namespaceable, namespace):
    """Delete attributes from a namespace, at various points.

    Inside a Namespace context, you can delete a variable from the current
    Namespace.

    You cannot delete an attribute in a class Namespace, from an instance
    namespace.

    Missing attributes have proper exception behavior.
    """
    class Test(namespaceable):
        """A throwaway test class, for testing delete behavior."""
        with namespace() as namespace_:
            attribute = 1
            del attribute
            bttribute = 2
        assert namespace_
    assert Test
    assert Test().namespace_
    assert Test.namespace_.bttribute == 2
    assert Test().namespace_.bttribute == 2
    with pytest.raises(AttributeError, message='bttribute'):
        del Test().namespace_.bttribute
    del Test.namespace_.bttribute
    with pytest.raises(AttributeError, message='bttribute'):
        print(Test.namespace_.bttribute)
    with pytest.raises(AttributeError, message='bttribute'):
        print(Test().namespace_.bttribute)


def test_set(namespaceable, namespace):
    """Set attributes on a namespace, at various points.

    You can set attributes on a Namespace after the class definition. The
    changes will be visible on both the class, and on instances.

    You can set attributes on an instance Namespace. This will not propagate up
    to the class Namespace.
    """
    class Test(namespaceable):
        """A throwaway test class, for testing set behavior."""
        with namespace() as namespace_:
            attribute = 1
            del attribute
        assert namespace_
    assert Test
    assert Test().namespace_
    Test.namespace_.bttribute = 2
    assert Test.namespace_.bttribute == 2
    assert Test().namespace_.bttribute == 2
    test = Test()
    test.namespace_.bttribute = 3
    assert Test.namespace_.bttribute == 2
    assert test.namespace_.bttribute == 3
    test2 = Test()
    test2.namespace_.cttribute = 3
    with pytest.raises(AttributeError, message='cttribute'):
        print(Test.namespace_.cttribute)
    with pytest.raises(AttributeError, message='cttribute'):
        print(test.namespace_.cttribute)
    assert test2.namespace_.cttribute == 3


@pytest.mark.xfail(sys.version_info < (3, 4),
                   reason="python3.4 api changes?")
def test_dir(namespaceable, namespace):
    """Confirm the shape of dir.

    Dir provides a view of what's accessible from a single Namespace.

    There is some kind of interaction between Python, the libraries, and the
    Namespace code that reliably occurs on 3.3. I believe it's not really a
    problem.
    """
    class Test(namespaceable):
        """A throwaway test class, for testing dir behavior."""
        with namespace() as namespace_:
            attribute = 1
        assert namespace_
        assert dir(namespace_) == ['attribute']
    assert dir(Test.namespace_) == ['attribute']
    assert dir(Test().namespace_) == ['attribute']


def test_shadow(namespaceable, namespace):
    """Define several attributes with the same name, in different scopes.

    Namespaces divide a class up into distinct pieces. A name defined in one
    place doesn't interfere with using the same name elsewhere.
    """
    class Test(namespaceable):
        """A throwaway test class, for testing shadowing."""
        footer = 1
        with namespace() as namespace_:
            footer = 2
            assert footer == 2
        assert footer == 1
    assert Test().footer == 1
    assert Test().namespace_.footer == 2


def test_resume(namespaceable, namespace):
    """Enter the same namespace multiple times.

    Namespaces are not only context managers, but reusable context managers.
    A resumed Namespace is truly the same scope.
    """
    class Test(namespaceable):
        """A throwaway test class, for testing namespace resumption."""
        footer = 1
        with namespace() as namespace_:
            footer = 2
            assert footer == 2
        assert footer == 1
        footer = 3
        with namespace_:
            assert footer == 2
            footer = 4
        assert footer == 3
    assert Test().footer == 3
    assert Test().namespace_.footer == 4


def assert_equals(expected, actual):
    """Compare expected and actual in a predictable scope.

    pytest can get confused inside a Namespaceable class definition.
    """
    assert expected == actual


def test_rec_get_in_definition(namespaceable, namespace):
    """Look at namespace attributes during class definition.

    Clearly, this should just work, yet it did not always, so now there is a
    test.
    """
    # The class just exists as a means of creating the values that are
    # asserted about.
    class Test(namespaceable):  # pylint: disable=unused-variable
        """A throwaway test class, for testing nested resolution."""
        with namespace() as namespace_:
            with namespace() as namespace_:
                footer = 1
        assert_equals(1, namespace_.namespace_.footer)


def test_basic_inherit(namespaceable, namespace):
    """Make a subclass of a Namespaceable class.

    The Namespace resolution hooks into Python's existing systems, so any kind
    of inheritance structure should work (equally well as without namespacing).
    """
    class Test(namespaceable):
        """A throwaway test class, for testing inheritance."""
        footer = 1
        with namespace() as namespace_:
            footer = 2

    class Subclass(Test):
        """A throwaway test class, for testing inheritance."""
    assert Subclass().footer == 1
    assert Subclass().namespace_.footer == 2


def test_basic_super(namespaceable, namespace):
    """Use super() inside a method defined in a Namespace.

    Everything Python gives you to deal with inheritance should work equally
    well. That includes super().
    """
    class Test(namespaceable):
        """A throwaway test class, for testing super()."""
        with namespace() as namespace_:
            def hello(self):
                """Return a predictable constant."""
                return 1

    class Subclass(Test):
        """A throwaway test class, for testing super()."""
        with namespace() as namespace_:
            def hello(self):
                """Return the superclass's hello."""
                return super().namespace_.hello()

    assert Test().namespace_.hello() == 1
    assert Subclass().namespace_.hello() == 1


def test_private(namespaceable, namespace):
    """Use name mangling and subclassing together.

    Name mangling is meant to protect an implementation from being overridden
    by subclasses. Because it occurs before the Namespace code sees it, this
    happens for free, and is automatically correct.
    """
    class Test(namespaceable):
        """A throwaway test class, for testing name mangling."""
        with namespace() as __namespace_:
            footer = 2

        def footer(self):  # pylint: disable=function-redefined
            """Access a private namespace."""
            return self.__namespace_.footer

    class Subclass(Test):
        """A throwaway test class, for testing name mangling."""

        def my_footer(self):
            """Access a non-existent private namespace."""
            return self.__namespace_.footer

    assert Test().footer() == 2
    assert Subclass().footer() == 2
    with pytest.raises(AttributeError,
                       message="object has no attribute "
                               "'_Subclass__namespace_'"):
        print(Subclass().my_footer())


def test_nested_namespace(namespaceable, namespace):
    """Define a Namespace in a Namespace."""
    class Test(namespaceable):
        """A throwaway test class, for testing nesting."""
        with namespace() as namespace_:
            with namespace() as namespace_:
                attribute = 1
    assert Test().namespace_.namespace_.attribute == 1


def test_basic_shadow(namespaceable, namespace):
    """Define an attribute over a Namespace."""
    class Test(namespaceable):
        """A throwaway test class, for testing shadowing via inheritance."""
        with namespace() as namespace_:
            footer = 2

    class Subclass(Test):
        """A throwaway test class, for testing shadowing via inheritance."""
        namespace_ = 1
    assert Subclass().namespace_ == 1


def test_double_shadow(namespaceable, namespace):
    """Define an attribute over a Namespace, then a Namespace over that.

    Non-namespace attributes block the visibility of Namespaces in parent
    classes.
    """
    class Test(namespaceable):
        """A throwaway test class, for testing advanced shadowing."""
        with namespace() as namespace_:
            footer = 2

    class Subclass(Test):
        """A throwaway test class, for testing advanced shadowing."""
        namespace_ = 1

    class DoubleSubclass(Subclass):
        """A throwaway test class, for testing advanced shadowing."""
        with namespace() as namespace_:
            barter = 1
    assert not hasattr(DoubleSubclass().namespace_, 'footer')


def test_overlap(namespaceable, namespace):
    """Define different attributes in the same Namespace in a subclass.

    Namespaces delegate to parent classes, if not blocked.
    """
    class Test(namespaceable):
        """A throwaway test class, for testing delegation."""
        with namespace() as namespace_:
            footer = 2

    class Subclass(Test):
        """A throwaway test class, for testing delegation."""
        with namespace() as namespace_:
            barter = 3
    assert Subclass().namespace_.footer == 2
    assert Subclass().namespace_.barter == 3


def test_advanced_overlap(namespaceable, namespace):
    """Do the same things as in test_overlap, but with a little nesting."""
    class Test(namespaceable):
        """A throwaway test class, for testing delegation."""
        with namespace() as namespace_:
            footer = 2
            with namespace() as namespace_:
                qux = 4

    class Subclass(Test):
        """A throwaway test class, for testing delegation."""
        with namespace() as namespace_:
            barter = 3
    assert Subclass().namespace_.footer == 2
    assert Subclass().namespace_.barter == 3
    assert Subclass().namespace_.namespace_.qux == 4


def test_use_namespace(namespaceable, namespace):
    """Interact with a namespace's attributes."""
    class Test(namespaceable):
        """A throwaway test class, for testing creation-time interfaces."""
        with namespace() as namespace_:
            footer = 1
            qux = 3
        assert namespace_.footer == 1
        namespace_.barter = 2
        assert namespace_.barter == 2
        del namespace_.qux
        # I tried to add a message to this one. It broke. ¯\_(ツ)_/¯
        with pytest.raises(AttributeError):
            del namespace_.qux
    assert Test.namespace_.footer == 1
    assert Test.namespace_.barter == 2


def test_basic_prop(namespaceable, namespace):
    """Define a property in a Namespace.

    Data descriptors work.
    """
    class Test(namespaceable):
        """A throwaway test class, for testing properties."""
        with namespace() as namespace_:
            @property
            def footer(self):
                """Return 1."""
                return 1
    assert Test().namespace_.footer == 1


def test_complicated_prop(namespaceable, namespace):
    """Define a property with all methods.

    @property.method works.
    """
    class Test(namespaceable):
        """A throwaway test class, for testing advanced properties."""
        with namespace() as namespace_:
            @property
            def var(self):
                """Return a value from the private namespace."""
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
    assert test.namespace_.var is None
    test.namespace_.var = 1
    assert test.namespace_.var == 2
    del test.namespace_.var
    assert test.namespace_.var is None


def test_override_method(namespaceable, namespace):
    """Define a function, then overwrite it.

    Non-data descriptors work.
    """
    class Test(namespaceable):
        """A throwaway test class, for testing method overrides."""
        with namespace() as namespace_:
            def footer(self):
                """Return 1."""
                return 1
    test = Test()
    assert test.namespace_.footer() == 1
    test.namespace_.footer = 2
    print(vars(test))
    assert test.namespace_.footer == 2
    del test.namespace_.footer
    assert test.namespace_.footer() == 1
    Test.namespace_.footer = 3
    assert Test.namespace_.footer == 3
    assert test.namespace_.footer == 3


def test_add_later(namespaceable, namespace):
    """Add a Namespace to a class, post-creation."""
    class Test(namespaceable):
        """A throwaway test class, for testing post-creation injection."""

    namespace_ = namespace()
    Test.namespace_ = namespace_
    print('namespace_ props')
    for slot in namespace.__slots__:
        print(slot, getattr(namespace_, slot))
    namespace_2 = namespace()
    Test.namespace_.namespace_ = namespace_2
    print('namespace_2 props')
    for slot in namespace.__slots__:
        print(slot, getattr(namespace_2, slot))
    Test.namespace_.value = 1
    assert Test.namespace_.value == 1
    Test.namespace_.namespace_.value = 2
    assert Test.namespace_.namespace_.value == 2
    assert Test.namespace_.value == 1


@pytest.mark.xfail(sys.version_info < (3, 6),
                   reason="python3.6 api changes", strict=True)
def test_3_6_descriptor(namespaces, namespaceable, namespace):
    """Create a descriptor that implements __set_name__, confirm it works.

    This test is invalid before 3.6.
    """
    class Descriptor:
        """A descriptor that only sets its name."""

        owner = None
        name = None

        def __set_name__(self, owner, name):
            self.owner = owner
            self.name = name
    assert namespaces.namespaces.DescriptorInspector(
        Descriptor()).is_descriptor

    class Test(namespaceable):
        """A throwaway test class, for testing __set_name__."""
        with namespace() as namespace_:
            descriptor = Descriptor()

    assert Test.namespace_.descriptor.name == 'descriptor'


def test_basic_meta(namespaceable, namespace):
    """Test the basic interactions between Namespaceable and metaclasses."""
    class Meta(namespaceable, type(namespaceable)):
        """A throwaway test metaclass."""
        with namespace() as namespace_:
            meta_var = 1

    class Test(namespaceable, metaclass=Meta):
        """A throwaway test class, for testing metaclasses."""

    assert Meta.namespace_.meta_var == 1
    assert Test.namespace_.meta_var == 1
    with pytest.raises(AttributeError, message='meta_var'):
        print(Test().namespace_.meta_var)


def test_somewhat_weirder_meta(namespaceable, namespace):
    """Test that attribute visibility works with Namespaceable, metaclasses."""
    class Meta(namespaceable, type(namespaceable)):
        """A throwaway test metaclass."""
        with namespace() as namespace_:
            meta_var = 1

    class Test(namespaceable, metaclass=Meta):
        """A throwaway test class, for testing advanced metaclass interactions.

        The same as above, but with an attribute.
        """
        with namespace() as namespace_:
            cls_var = 2

    assert Meta.namespace_.meta_var == 1
    assert Test.namespace_.meta_var == 1
    assert Test.namespace_.cls_var == 2
    assert Test().namespace_.cls_var == 2
    with pytest.raises(AttributeError, message='meta_var'):
        print(Test().namespace_.meta_var)
    with pytest.raises(AttributeError, message='var'):
        print(Test.namespace_.var)
    with pytest.raises(AttributeError, message='cls_var'):
        print(Meta.namespace_.cls_var)
    Test.var = 3
    assert Test.var == 3
    Meta.var = 4
    assert Meta.var == 4


def test_classmethod_basic(namespaceable, namespace):
    """Test using a classmethod in a Namespace."""
    class Test(namespaceable):
        """A throwaway test class, for testing classmethods."""
        with namespace() as namespace_:
            @classmethod
            def cls_mthd(cls):
                """Return that a call occurred."""
                return 'called'

    assert Test.namespace_.cls_mthd() == 'called'
    assert Test().namespace_.cls_mthd() == 'called'


def test_meta_plus_classmethod(namespaceable, namespace):
    """Test using a classmethod in a Namespace, while messing with metaclasses.

    This might have been purely for coverage of some kind? I forget.
    """
    class Meta(namespaceable, type(namespaceable)):
        """A throwaway test metaclass."""
        with namespace() as namespace_:
            pass

    class Test(namespaceable, metaclass=Meta):
        """A throwaway test class, for testing classmethods."""
        with namespace() as namespace_:
            @classmethod
            def cls_mthd(cls):
                """Return that a call occurred."""
                return 'called'

    assert Test().namespace_.cls_mthd() == 'called'
    assert Test.namespace_.cls_mthd() == 'called'


def test_get_through_namespace(namespaceable, namespace):
    """Define a variable in a Namespace in terms of a variable in parent scope.

    Like other scopes in Python, Namespaces allow you to get variables from
    outer scopes.
    """
    class Test(namespaceable):
        """A throwaway test class, for testing chained get."""
        var = 1
        with namespace() as namespace_:
            var2 = var

    assert Test.var == 1
    assert Test.namespace_.var2 == 1


def test_multiple_inheritance(namespaceable, namespace):
    """Define some base classes with Namespaces, inherit, confirm they merged.

    Everything Python gives you to deal with inheritance should work equally
    well. That includes multiple inheritance.
    """
    class Test1(namespaceable):
        """A throwaway test class, for testing multiple inheritance."""
        with namespace() as namespace_:
            with namespace() as namespace_:
                var = 1

    class Test2(namespaceable):
        """A throwaway test class, for testing multiple inheritance."""
        with namespace() as namespace_:
            var = 2

    class Test3(Test2, Test1):
        """A throwaway test class, for testing multiple inheritance."""

    assert Test3.namespace_.namespace_.var == 1
    assert Test3.namespace_.var == 2


def test_regular_delete(namespaceable):
    """Define and delete a variable in a Namespaceable class.

    This isn't too exciting, but if we don't prove this works, there's a
    coverage gap.
    """
    class Test(namespaceable):
        """A throwaway test class, for testing vanilla get, set, delete."""
    Test.var = 1
    assert Test.var == 1
    del Test.var
