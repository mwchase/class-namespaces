"""Test the internal details of namespaces."""

import sys

import pytest


def get_ns(namespace_):
    """Return the namespace associated with a scope proxy."""
    from class_namespaces import scope_proxy
    return scope_proxy.namespace(namespace_)


def scope_dicts_length_equals(namespace_, length):
    """Check the length of the associated namespace's scope."""
    scope = get_ns(namespace_).scope
    assert len(scope._dicts) == length


def test_finalization(namespaceable, namespace):
    """Test error messages around finalization."""
    scopes = []

    class Test(namespaceable):
        """Throwaway test class, for testing scope finalization."""
        with namespace() as namespace_:
            with pytest.raises(ValueError,
                               message='Cannot finalize a pushed scope!'):
                print(get_ns(namespace_).scope.finalize())
        with pytest.raises(ValueError,
                           message='Cannot pop from a basal scope!'):
            print(get_ns(namespace_).scope.pop_())
        scopes.append(get_ns(namespace_).scope)
        with pytest.raises(
                ValueError,
                metaclass='Length not defined on unfinalized scope.'):
            print(len(get_ns(namespace_).scope))
        with pytest.raises(
                ValueError,
                message='Iteration not defined on unfinalized scope.'):
            print(next(iter(get_ns(namespace_).scope)))
    with pytest.raises(ValueError, message='Cannot push a finalized scope!'):
        print(scopes[0].push(None))


@pytest.mark.xfail(sys.version_info < (3, 4),
                   reason="python3.4 api changes?")
def test_basic_scope_len(namespaceable, namespace):
    """Test the overall length behavior of scopes, with various layouts."""
    scopes = {}

    class Test1(namespaceable):
        """Throwaway test class, for testing scope length."""
        with namespace() as namespace_:
            scopes[1] = get_ns(namespace_).scope

    class Test2(namespaceable):
        """Throwaway test class, for testing scope length."""
        with namespace() as namespace_1:
            scopes[2] = get_ns(namespace_1).scope
        with namespace() as namespace_2:
            pass

    class Test3(namespaceable):
        """Throwaway test class, for testing scope length."""
        with namespace() as namespace_1:
            footer = 1
            scopes[3] = get_ns(namespace_1).scope
        with namespace() as namespace_2:
            pass

    class Test4(namespaceable):
        """Throwaway test class, for testing scope length."""
        with namespace() as namespace_1:
            with namespace() as namespace_:
                footer = 1
            scopes[4] = get_ns(namespace_1).scope
        with namespace() as namespace_2:
            pass

    for scope in scopes.values():
        assert scope.finalized

    scope1 = scopes[1]
    scope2 = scopes[2]
    scope3 = scopes[3]
    scope4 = scopes[4]
    assert len(scope2) - len(scope1) == 1
    assert len(scope3) - len(scope2) == 1
    assert len(scope4) - len(scope3) == 1


@pytest.mark.xfail(sys.version_info < (3, 4),
                   reason="python3.4 api changes?")
def test_basic_scope_iter(namespaceable, namespace):
    """Test the overall iteration behavior of scopes, with various layouts."""
    scopes = {}

    class Test1(namespaceable):
        """Throwaway test class, for testing scope iteration."""
        with namespace() as namespace_:
            scopes[1] = get_ns(namespace_).scope

    class Test2(namespaceable):
        """Throwaway test class, for testing scope iteration."""
        with namespace() as namespace_1:
            scopes[2] = get_ns(namespace_1).scope
        with namespace() as namespace_2:
            pass

    class Test3(namespaceable):
        """Throwaway test class, for testing scope iteration."""
        with namespace() as namespace_1:
            footer = 1
            scopes[3] = get_ns(namespace_1).scope
        with namespace() as namespace_2:
            pass

    class Test4(namespaceable):
        """Throwaway test class, for testing scope iteration."""
        with namespace() as namespace_1:
            with namespace() as namespace_:
                footer = 1
            scopes[4] = get_ns(namespace_1).scope
        with namespace() as namespace_2:
            pass

    for scope in scopes.values():
        assert scope.finalized

    set1 = frozenset(scopes[1])
    set2 = frozenset(scopes[2])
    set3 = frozenset(scopes[3])
    set4 = frozenset(scopes[4])

    baseline = set1.difference({'namespace_'})
    assert set2.symmetric_difference(baseline) == frozenset({'namespace_1',
                                                             'namespace_2'})
    assert set3.symmetric_difference(set2) == frozenset({'namespace_1.footer'})
    assert set4.symmetric_difference(set2) == frozenset(
        {'namespace_1.namespace_', 'namespace_1.namespace_.footer'})


def test_scope_namespaced_get(namespaceable, namespace):
    """Test scope get with nesting."""
    scopes = {}

    class Test(namespaceable):
        """Throwaway test class, for testing scope indexing."""
        with namespace() as namespace_:
            with namespace() as namespace_:
                footer = 1
                scopes[0] = get_ns(namespace_).scope

    assert scopes[0]['namespace_.namespace_.footer'] == 1


def test_scope_namespaced_set(namespaceable, namespace):
    """Test scope set with nesting."""
    scopes = {}

    class Test(namespaceable):
        """Throwaway test class, for testing scope setitem."""
        with namespace() as namespace_:
            with namespace() as namespace_:
                scopes[0] = get_ns(namespace_).scope

    scopes[0]['namespace_.namespace_.footer'] = 1
    assert scopes[0]['namespace_.namespace_.footer'] == 1
    assert Test.namespace_.namespace_.footer == 1


def test_scope_namespaced_del(namespaceable, namespace):
    """Test scope del with nesting."""
    scopes = {}

    class Test(namespaceable):
        """Throwaway test class, for testing scope delete."""
        with namespace() as namespace_:
            with namespace() as namespace_:
                footer = 1
                scopes[0] = get_ns(namespace_).scope

    assert Test.namespace_.namespace_.footer == 1
    del scopes[0]['namespace_.namespace_.footer']
    with pytest.raises(AttributeError, message='footer'):
        print(Test.namespace_.namespace_.footer)


def test_scope_namespaced_get_error(namespaceable, namespace):
    """Test getting a nonexistent member of a nested scope."""
    scopes = {}

    class Test(namespaceable):
        """Throwaway test class, for testing failing scope get."""
        with namespace() as namespace_:
            with namespace() as namespace_:
                footer = 1
                scopes[0] = get_ns(namespace_).scope

    scope = scopes[0]

    with pytest.raises(KeyError, message='namespace_.namespace_.barter'):
        print(scope['namespace_.namespace_.barter'])


def test_scope_namespaced_get_non_ns(namespaceable, namespace):
    """Test a nested get that goes too deep."""
    scopes = {}

    class Test(namespaceable):
        """Throwaway test class, for testing over-deep scope get."""
        with namespace() as namespace_:
            with namespace() as namespace_:
                footer = 1
                scopes[0] = get_ns(namespace_).scope

    scope = scopes[0]

    with pytest.raises(KeyError,
                       message='namespace_.namespace_.footer.__str__'):
        print(scope['namespace_.namespace_.footer.__str__'])


def test_scope_namespaced_get_non_existent(namespaceable, namespace):
    """Test a nested get that's missing the first level of nesting."""
    scopes = {}

    class Test(namespaceable):
        """Throwaway test class, for testing failing scope get."""
        with namespace() as namespace_:
            with namespace() as namespace_:
                footer = 1
                scopes[0] = get_ns(namespace_).scope

    scope = scopes[0]

    with pytest.raises(KeyError, message='namespace_.footer'):
        print(scope['namespace_.footer'])


def test_scope_namespaced_get_non_recursive(namespaceable, namespace):
    """Test a non-recursive scope get."""
    scopes = {}

    class Test(namespaceable):
        """Throwaway test class, for testing basic scope get."""
        with namespace() as namespace_:
            with namespace() as namespace_:
                footer = 1
                scopes[0] = get_ns(namespace_).scope

    scope = scopes[0]

    assert scope['namespace_'].namespace_.footer == 1


# I wanted this to be an intro test, but it has some paranoid checks in it.
def test_redundant_resume(namespaceable, namespace):
    """Test the various forms of namespace reuse."""
    class Test(namespaceable):
        """Throwaway test class, for testing namespace reuse."""
        footer = 1
        with namespace() as namespace_:
            footer = 2
            assert footer == 2
        scope_dicts_length_equals(namespace_, 1)
        footer = 3
        namespace_ = namespace_
        scope_dicts_length_equals(namespace_, 1)
        with namespace_ as namespace_:
            footer = 4
        assert footer == 3
    assert Test().footer == 3
    assert Test().namespace_.footer == 4


def test_empty_nameless(namespaceable, namespace):
    """Test an unnamed namespace with nothing in it."""
    class Test(namespaceable):
        """Throwaway test class, for testing nameless namespace."""
        with pytest.raises(RuntimeError, message='Namespace must be named.'):
            with namespace():
                pass


def test_non_empty_nameless(namespaceable, namespace):
    """Test an unnamed namespace with something in it."""
    class Test(namespaceable):
        """Throwaway test class, for testing nameless namespace."""
        with pytest.raises(RuntimeError, message='Namespace must be named.'):
            with namespace():
                attribute = 1


def test_rename(namespaceable, namespace):
    """Test renaming a namespace."""
    class Test(namespaceable):
        """Throwaway test class, for testing namespace rename."""
        with namespace() as namespace_:
            pass
        with pytest.raises(ValueError, message='Cannot rename namespace'):
            with namespace_ as namespace_2:
                pass


def test_can_t_preload_with_namespace(namespace):
    """Test using a namespace as an initial value."""
    with pytest.raises(ValueError, message='Bad values: {}'):
        print(namespace(namespace_=namespace()))


def test_star_attr_functions(namespaceable, namespace):
    """Test the *attr functions on a nested namespace."""
    class Test(namespaceable):
        """Throwaway test class, for testing *attr functions with nesting."""
        with namespace() as namespace_:
            with namespace() as namespace_:
                with namespace() as namespace_:
                    pass

    setattr(Test, 'namespace_.namespace_.namespace_.var', 1)
    assert hasattr(Test, 'namespace_.namespace_.namespace_.var')
    assert getattr(Test, 'namespace_.namespace_.namespace_.var') == 1
    assert Test.namespace_.namespace_.namespace_.var == 1
    delattr(Test, 'namespace_.namespace_.namespace_.var')
    assert not hasattr(Test, 'namespace_.namespace_.namespace_.var')


def test_dont_need_to_inherit(
        namespaceable):  # pylint: disable=unused-argument
    """Test using the metaclass without the convenience class."""
    class Test(metaclass=type(namespaceable)):
        """Throwaway test class, for testing the metaclass."""


def test_too_deep(namespaceable):
    """Test trying to do nested access through a non-namespace attribute."""
    class Test(namespaceable):
        """Throwaway test class, for testing too-deep get."""
        var = None
    with pytest.raises(
            ValueError, message='Given a dot attribute that went too deep.'):
        print(getattr(Test, 'var.__str__'))


def test_block_reparent(namespaceable, namespace):
    """Test trying to give one namespace multiple parents."""
    shadow_ns1 = None
    shadow_ns2 = None

    class Test1(namespaceable):
        """Throwaway test class, for testing reparenting."""
        with namespace() as namespace_:
            with pytest.raises(ValueError, message='Cannot double-activate.'):
                with namespace_:
                    pass
            with pytest.raises(
                    ValueError, message='Cannot reparent namespace'):
                namespace_.namespace_ = namespace_
                print(namespace_, namespace_.namespace_)
        with pytest.raises(ValueError, message='Cannot reparent namespace'):
            namespace_.namespace_ = namespace_
            print(namespace_, namespace_.namespace_)
        with namespace() as namespace_2:
            with pytest.raises(
                    ValueError, message='Cannot reparent namespace'):
                with namespace_:
                    pass
                print(namespace_)
        nonlocal shadow_ns1  # pylint: disable=nonlocal-without-binding
        nonlocal shadow_ns2  # pylint: disable=nonlocal-without-binding
        with namespace_ as shadow_ns1:
            shadow_ns2 = namespace_

    assert isinstance(shadow_ns1, namespace)
    assert isinstance(shadow_ns2, shadow_ns1.scope.scope_proxy)

    class Test2(namespaceable):
        """Throwaway test class, for testing reparenting."""
        with pytest.raises(
                ValueError, message='Cannot move scopes between classes.'):
            namespace_ = Test1.namespace_
        with pytest.raises(ValueError, message='Cannot reuse namespace'):
            namespace_ = shadow_ns1
        with pytest.raises(
                ValueError, message='Cannot move scopes between classes.'):
            namespace_ = shadow_ns2
        with namespace() as namespace_:
            pass

    with pytest.raises(ValueError, message='Cannot reuse namespace'):
        Test2.namespace_.namespace_ = shadow_ns1
    with pytest.raises(
            ValueError, message='Cannot move scopes between classes.'):
        Test2.namespace_.namespace_ = shadow_ns2


def test_can_t_get_path(namespace):
    """Test that a free namespace doesn't have a well-defined path."""
    # This error currently doesn't have a message.
    with pytest.raises(ValueError):
        print(namespace().path)


def test_non_existent_attribute_during_creation(namespaceable, namespace):
    """Test that looking for a non-existent attribute raises AttributeError."""
    class Test(namespaceable):
        """Throwaway test class, for testing nonexistent attribute get."""
        with namespace() as namespace_:
            pass
        with pytest.raises(AttributeError, message='var'):
            print(namespace_.var)


def test_partial_descriptors(namespaceable, namespace):
    """Test that descriptor behavior is consistent with non-namespaced classes.

    I hate trying to get these lines to wrap properly, sometimes.
    """
    class Setter:
        """Descriptor that can only be set."""

        def __set__(self, instance, value):
            """Allow for setting, but don't actually do anything."""

    class Deleter:
        """Descriptor that can only be deleted."""

        def __delete__(self, instance):
            """Allow for deleting, but don't actually do anything."""

    class Test(namespaceable):
        """Throwaway test class, for testing descriptors."""
        setter = Setter()
        deleter = Deleter()
        with namespace() as namespace_:
            setter = Setter()
            deleter = Deleter()

    deleter_msg = '__set__'
    setter_msg = '__delete__'
    test = Test()
    assert isinstance(test.setter, Setter)
    assert isinstance(test.deleter, Deleter)
    vars(test)['setter'] = None
    vars(test)['deleter'] = None
    assert test.setter is None
    assert test.deleter is None
    assert isinstance(test.namespace_.setter, Setter)
    assert isinstance(test.namespace_.deleter, Deleter)
    with pytest.raises(AttributeError, message=deleter_msg):
        test.deleter = None
    with pytest.raises(AttributeError, message=setter_msg):
        del test.setter
    with pytest.raises(AttributeError, message=deleter_msg):
        test.namespace_.deleter = None
    with pytest.raises(AttributeError, message=setter_msg):
        del test.namespace_.setter


def test_namespace_is_truthy(namespace):
    """Test that namespaces are always considered truthy."""
    assert namespace()


def test_bad_del_in_definition(namespaceable, namespace):
    """Test that deletes of nonexistent attributes still raise NameError."""
    class Test(namespaceable):
        """Throwaway test class, for testing failing delete."""
        with namespace() as namespace_:
            with pytest.raises(
                    NameError, message="name 'footer' is not defined"):
                del footer


# Not 100% sure this is desired behavior. See Issue 12.
def test_subtle_bad_del_in_definition(namespaceable, namespace):
    """Test that deletes of nonexistent attributes still raise NameError."""
    class Test(namespaceable):
        """Throwaway test class, for testing failing delete."""
        footer = 1
        with namespace() as namespace_:
            with pytest.raises(
                    NameError, message="name 'footer' is not defined"):
                del footer


def test_tuple_subclass(namespaceable, namespace):
    """Test that tuple subclasses have immutable namespaces."""
    meta = type(namespaceable)

    class Test(tuple, metaclass=meta):
        """Throwaway test class, for testing immutable namespaceables."""
        __slots__ = ()
        with namespace() as namespace_:
            var = 1

    assert Test().namespace_.var == 1
    with pytest.raises(AttributeError):
        Test().namespace_.var = 2
    assert Test().namespace_.var == 1
    with pytest.raises(AttributeError):
        del Test().namespace_.var
