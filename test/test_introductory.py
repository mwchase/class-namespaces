import sys

import pytest


def test_import(namespaces):
    """Test the module is importable. See conftest.py for the actual import."""
    assert namespaces


def test_meta_basic(namespaces):
    """Make a namespaceable class by subclassing from Namespaceable."""
    class Test(namespaces.Namespaceable):
        """A throwaway test class."""
    assert Test


def test_basic_namespace(namespaces):
    """Define an attribute within a namespace.

    Attributes in a Namespace live in that Namespace, and are accessible from
    both the class, and any instance of the class.
    """
    class Test(namespaces.Namespaceable):
        """A throwaway test class."""
        with namespaces.Namespace() as ns:
            a = 1
        assert ns
    assert Test
    assert Test().ns
    assert Test.ns.a == 1
    assert Test().ns.a == 1


def test_delete(namespaces):
    """Delete attributes from a namespace, at various points.

    Inside a Namespace context, you can delete a variable from the current
    Namespace.

    You cannot delete an attribute in a class Namespace, from an instance
    namespace.

    Missing attributes have proper exception behavior.
    """
    class Test(namespaces.Namespaceable):
        """A throwaway test class."""
        with namespaces.Namespace() as ns:
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


def test_set(namespaces):
    """Set attributes on a namespace, at various points.

    You can set attributes on a Namespace after the class definition. The
    changes will be visible on both the class, and on instances.

    You can set attributes on an instance Namespace. This will not propagate up
    to the class Namespace.
    """
    class Test(namespaces.Namespaceable):
        """A throwaway test class."""
        with namespaces.Namespace() as ns:
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
def test_dir(namespaces):
    """Confirm the shape of dir.

    Dir provides a view of what's accessible from a single Namespace.

    There is some kind of interaction between Python, the libraries, and the
    Namespace code that reliably occurs on 3.3. I believe it's not really a
    problem.
    """
    class Test(namespaces.Namespaceable):
        """A throwaway test class."""
        with namespaces.Namespace() as ns:
            a = 1
        assert ns
        assert dir(ns) == ['a']
    assert dir(Test.ns) == ['a']
    assert dir(Test().ns) == ['a']


def test_shadow(namespaces):
    """Define several attributes with the same name, in different scopes.

    Namespaces divide a class up into distinct pieces. A name defined in one
    place doesn't interfere with using the same name elsewhere.
    """
    class Test(namespaces.Namespaceable):
        """A throwaway test class."""
        foo = 1
        with namespaces.Namespace() as ns:
            foo = 2
            assert foo == 2
        assert foo == 1
    assert Test().foo == 1
    assert Test().ns.foo == 2


def test_resume(namespaces):
    """Enter the same namespace multiple times.

    Namespaces are not only context managers, but reusable context managers.
    A resumed Namespace is truly the same scope.
    """
    class Test(namespaces.Namespaceable):
        """A throwaway test class."""
        foo = 1
        with namespaces.Namespace() as ns:
            foo = 2
            assert foo == 2
        assert foo == 1
        foo = 3
        with ns:
            assert foo == 2
            foo = 4
        assert foo == 3
    assert Test().foo == 3
    assert Test().ns.foo == 4
