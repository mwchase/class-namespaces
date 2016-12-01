import sys

import pytest


def get_ns(ns):
    from class_namespaces import scope_proxy
    return scope_proxy._ns(ns)


def scope_dicts_length_equals(ns, length):
    scope = get_ns(ns).scope
    assert len(scope._dicts) == length


def test_finalization(namespaces):
    scopes = []

    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            with pytest.raises(ValueError,
                               message='Cannot finalize a pushed scope!'):
                print(get_ns(ns).scope.finalize())
        with pytest.raises(ValueError,
                           message='Cannot pop from a basal scope!'):
            print(get_ns(ns).scope.pop_())
        scopes.append(get_ns(ns).scope)
        with pytest.raises(
                ValueError,
                metaclass='Length not defined on unfinalized scope.'):
            print(len(get_ns(ns).scope))
        with pytest.raises(
                ValueError,
                message='Iteration not defined on unfinalized scope.'):
            print(next(iter(get_ns(ns).scope)))
    with pytest.raises(ValueError, message='Cannot push a finalized scope!'):
        print(scopes[0].push(None))


@pytest.mark.xfail(sys.version_info < (3, 4),
                   reason="python3.4 api changes?", strict=True)
def test_basic_scope_len(namespaces):
    scopes = {}

    class Test1(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            scopes[1] = get_ns(ns).scope

    class Test2(namespaces.Namespaceable):
        with namespaces.Namespace() as ns1:
            scopes[2] = get_ns(ns1).scope
        with namespaces.Namespace() as ns2:
            pass

    class Test3(namespaces.Namespaceable):
        with namespaces.Namespace() as ns1:
            foo = 1
            scopes[3] = get_ns(ns1).scope
        with namespaces.Namespace() as ns2:
            pass

    class Test4(namespaces.Namespaceable):
        with namespaces.Namespace() as ns1:
            with namespaces.Namespace() as ns:
                foo = 1
            scopes[4] = get_ns(ns1).scope
        with namespaces.Namespace() as ns2:
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
                   reason="python3.4 api changes?", strict=True)
def test_basic_scope_iter(namespaces):
    scopes = {}

    class Test1(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            scopes[1] = get_ns(ns).scope

    class Test2(namespaces.Namespaceable):
        with namespaces.Namespace() as ns1:
            scopes[2] = get_ns(ns1).scope
        with namespaces.Namespace() as ns2:
            pass

    class Test3(namespaces.Namespaceable):
        with namespaces.Namespace() as ns1:
            foo = 1
            scopes[3] = get_ns(ns1).scope
        with namespaces.Namespace() as ns2:
            pass

    class Test4(namespaces.Namespaceable):
        with namespaces.Namespace() as ns1:
            with namespaces.Namespace() as ns:
                foo = 1
            scopes[4] = get_ns(ns1).scope
        with namespaces.Namespace() as ns2:
            pass

    for scope in scopes.values():
        assert scope.finalized

    set1 = frozenset(scopes[1])
    set2 = frozenset(scopes[2])
    set3 = frozenset(scopes[3])
    set4 = frozenset(scopes[4])

    baseline = set1.difference({'ns'})
    assert set2.symmetric_difference(baseline) == frozenset({'ns1', 'ns2'})
    assert set3.symmetric_difference(set2) == frozenset({'ns1.foo'})
    assert set4.symmetric_difference(set2) == frozenset(
        {'ns1.ns', 'ns1.ns.foo'})


def test_scope_namespaced_get(namespaces):
    scopes = {}

    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            with namespaces.Namespace() as ns:
                foo = 1
                scopes[0] = get_ns(ns).scope

    assert scopes[0]['ns.ns.foo'] == 1


def test_scope_namespaced_set(namespaces):
    scopes = {}

    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            with namespaces.Namespace() as ns:
                scopes[0] = get_ns(ns).scope

    scopes[0]['ns.ns.foo'] = 1
    assert scopes[0]['ns.ns.foo'] == 1
    assert Test.ns.ns.foo == 1


def test_scope_namespaced_del(namespaces):
    scopes = {}

    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            with namespaces.Namespace() as ns:
                foo = 1
                scopes[0] = get_ns(ns).scope

    assert Test.ns.ns.foo == 1
    del scopes[0]['ns.ns.foo']
    with pytest.raises(AttributeError, message='foo'):
        print(Test.ns.ns.foo)


def test_scope_namespaced_get_error(namespaces):
    scopes = {}

    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            with namespaces.Namespace() as ns:
                foo = 1
                scopes[0] = get_ns(ns).scope

    scope = scopes[0]

    with pytest.raises(KeyError, message='ns.ns.bar'):
        print(scope['ns.ns.bar'])


def test_scope_namespaced_get_non_ns(namespaces):
    scopes = {}

    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            with namespaces.Namespace() as ns:
                foo = 1
                scopes[0] = get_ns(ns).scope

    scope = scopes[0]

    with pytest.raises(KeyError, message='ns.ns.foo.__str__'):
        print(scope['ns.ns.foo.__str__'])


def test_scope_namespaced_get_non_existent(namespaces):
    scopes = {}

    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            with namespaces.Namespace() as ns:
                foo = 1
                scopes[0] = get_ns(ns).scope

    scope = scopes[0]

    with pytest.raises(KeyError, message='ns.foo'):
        print(scope['ns.foo'])


def test_scope_namespaced_get_non_recursive(namespaces):
    scopes = {}

    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            with namespaces.Namespace() as ns:
                foo = 1
                scopes[0] = get_ns(ns).scope

    scope = scopes[0]

    assert scope['ns'].ns.foo == 1


# I wanted this to be an intro test, but it has some paranoid checks in it.
def test_redundant_resume(namespaces):
    class Test(namespaces.Namespaceable):
        foo = 1
        with namespaces.Namespace() as ns:
            foo = 2
            assert foo == 2
        scope_dicts_length_equals(ns, 1)
        foo = 3
        ns = ns
        scope_dicts_length_equals(ns, 1)
        with ns as ns:
            foo = 4
        assert foo == 3
    assert Test().foo == 3
    assert Test().ns.foo == 4


def test_empty_nameless(namespaces):
    class Test(namespaces.Namespaceable):
        with pytest.raises(RuntimeError, message='Namespace must be named.'):
            with namespaces.Namespace():
                pass


def test_non_empty_nameless(namespaces):
    class Test(namespaces.Namespaceable):
        with pytest.raises(RuntimeError, message='Namespace must be named.'):
            with namespaces.Namespace():
                a = 1


def test_rename(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            pass
        with pytest.raises(ValueError, message='Cannot rename namespace'):
            with ns as ns2:
                pass


def test_can_t_preload_with_namespace(namespaces):
    with pytest.raises(ValueError, message='Bad values: {}'):
        print(namespaces.Namespace(ns=namespaces.Namespace()))


def test_star_attr_functions(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            with namespaces.Namespace() as ns:
                with namespaces.Namespace() as ns:
                    pass

    setattr(Test, 'ns.ns.ns.var', 1)
    assert hasattr(Test, 'ns.ns.ns.var')
    assert getattr(Test, 'ns.ns.ns.var') == 1
    assert Test.ns.ns.ns.var == 1
    delattr(Test, 'ns.ns.ns.var')
    assert not hasattr(Test, 'ns.ns.ns.var')


def test_must_inherit(namespaces):
    with pytest.raises(
            ValueError, message=(
                'Cannot create a _Namespaceable that does not inherit from '
                'Namespaceable')):
        class Test(metaclass=type(namespaces.Namespaceable)):
            pass
        print(Test)


def test_too_deep(namespaces):
    class Test(namespaces.Namespaceable):
        var = None
    with pytest.raises(
            ValueError, message='Given a dot attribute that went too deep.'):
        print(getattr(Test, 'var.__str__'))


def test_block_reparent(namespaces):
    shadow_ns1 = None
    shadow_ns2 = None

    class Test1(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            with pytest.raises(ValueError, message='Cannot double-activate.'):
                with ns:
                    pass
            with pytest.raises(
                    ValueError, message='Cannot reparent namespace'):
                ns.ns = ns
                print(ns, ns.ns)
        with pytest.raises(ValueError, message='Cannot reparent namespace'):
            ns.ns = ns
            print(ns, ns.ns)
        with namespaces.Namespace() as ns2:
            with pytest.raises(
                    ValueError, message='Cannot reparent namespace'):
                with ns:
                    pass
                print(ns)
        nonlocal shadow_ns1
        nonlocal shadow_ns2
        with ns as shadow_ns1:
            shadow_ns2 = ns

    assert isinstance(shadow_ns1, namespaces.Namespace)
    assert isinstance(shadow_ns2, shadow_ns1.scope.scope_proxy)

    class Test2(namespaces.Namespaceable):
        with pytest.raises(
                ValueError, message='Cannot move scopes between classes.'):
            ns = Test1.ns
        with pytest.raises(ValueError, message='Cannot reuse namespace'):
            ns = shadow_ns1
        with pytest.raises(
                ValueError, message='Cannot move scopes between classes.'):
            ns = shadow_ns2
        with namespaces.Namespace() as ns:
            pass

    with pytest.raises(ValueError, message='Cannot reuse namespace'):
        Test2.ns.ns = shadow_ns1
    with pytest.raises(
            ValueError, message='Cannot move scopes between classes.'):
        Test2.ns.ns = shadow_ns2


def test_can_t_get_path(namespaces):
    # This error currently doesn't have a message.
    with pytest.raises(ValueError):
        print(namespaces.Namespace().path)


def test_non_existent_attribute_during_creation(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            pass
        with pytest.raises(AttributeError, message='var'):
            print(ns.var)


def test_partial_descriptors(namespaces):
    class Setter:
        def __set__(self, instance, value):
            pass

    class Deleter:
        def __delete__(self, instance):
            pass

    class Test(namespaces.Namespaceable):
        setter = Setter()
        deleter = Deleter()
        with namespaces.Namespace() as ns:
            setter = Setter()
            deleter = Deleter()

    deleter_msg = '__set__'
    setter_msg = '__delete__'
    test = Test()
    with pytest.raises(AttributeError, message=deleter_msg):
        test.deleter = None
    with pytest.raises(AttributeError, message=setter_msg):
        del test.setter
    with pytest.raises(AttributeError, message=deleter_msg):
        test.ns.deleter = None
    with pytest.raises(AttributeError, message=setter_msg):
        del test.ns.setter


def test_namespace_is_truthy(namespaces):
    assert namespaces.Namespace()


def test_bad_del_in_definition(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            with pytest.raises(NameError, message="name 'foo' is not defined"):
                del foo


# Not 100% sure this is desired behavior. See Issue 12.
def test_subtle_bad_del_in_definition(namespaces):
    class Test(namespaces.Namespaceable):
        foo = 1
        with namespaces.Namespace() as ns:
            with pytest.raises(NameError, message="name 'foo' is not defined"):
                del foo
