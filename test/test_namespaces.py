import sys

import pytest


def test_import(namespaces):
    assert namespaces


def test_meta_basic(namespaces):
    class Test(namespaces.Namespaceable):
        pass
    assert Test


def test_basic_namespace(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            a = 1
        assert ns
    assert Test
    assert Test().ns


def test_delete(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            a = 1
            del a
            b = 2
        assert ns
    assert Test
    assert Test().ns
    assert Test.ns.b == 2
    assert Test().ns.b == 2
    with pytest.raises(AttributeError):
        del Test().ns.b
    del Test.ns.b
    with pytest.raises(AttributeError):
        Test.ns.b
    with pytest.raises(AttributeError):
        Test().ns.b


def test_set(namespaces):
    class Test(namespaces.Namespaceable):
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
    with pytest.raises(AttributeError):
        Test.ns.c
    with pytest.raises(AttributeError):
        test.ns.c
    assert test2.ns.c == 3


@pytest.mark.xfail(sys.version_info < (3, 4),
                   reason="python3.4 api changes?", strict=True)
def test_dir(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            a = 1
        assert ns
        assert dir(ns) == ['a']
    assert dir(Test.ns) == ['a']
    assert dir(Test().ns) == ['a']


def test_shadow(namespaces):
    class Test(namespaces.Namespaceable):
        foo = 1
        with namespaces.Namespace() as ns:
            foo = 2
            assert foo == 2
        assert foo == 1
    assert Test().foo == 1
    assert Test().ns.foo == 2


def test_resume(namespaces):
    class Test(namespaces.Namespaceable):
        foo = 1
        with namespaces.Namespace() as ns:
            foo = 2
            assert foo == 2
        foo = 3
        with ns:
            foo = 4
        assert foo == 3
    assert Test().foo == 3
    assert Test().ns.foo == 4


def get_ns(ns):
    from class_namespaces import scope_proxy
    return scope_proxy._PROXY_INFOS[ns][ns]


def scope_dicts_length_equals(ns, length):
    scope = get_ns(ns).scope
    assert len(scope.dicts) == length


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


def test_basic_inherit(namespaces):
    class Test(namespaces.Namespaceable):
        foo = 1
        with namespaces.Namespace() as ns:
            foo = 2

    class Subclass(Test):
        pass
    assert Subclass().foo == 1
    assert Subclass().ns.foo == 2


def test_basic_super(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            def hello(self):
                return 1

    class Subclass(Test):
        with namespaces.Namespace() as ns:
            def hello(self):
                return super().ns.hello()

    assert Test().ns.hello() == 1
    assert Subclass().ns.hello() == 1


def test_private(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as __ns:
            foo = 2

        def foo(self):
            return self.__ns.foo

    class Subclass(Test):
        pass

    assert Test().foo() == 2
    assert Subclass().foo() == 2


def test_nested_namespace(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            with namespaces.Namespace() as ns:
                a = 1
    assert Test().ns.ns.a == 1


def test_basic_shadow(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            foo = 2

    class Subclass(Test):
        ns = 1
    assert Subclass().ns == 1


def test_double_shadow(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            foo = 2

    class Subclass(Test):
        ns = 1

    class DoubleSubclass(Subclass):
        with namespaces.Namespace() as ns:
            bar = 1
    assert not hasattr(DoubleSubclass().ns, 'foo')


def test_overlap(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            foo = 2

    class Subclass(Test):
        with namespaces.Namespace() as ns:
            bar = 3
    assert Subclass().ns.foo == 2
    assert Subclass().ns.bar == 3


def test_advanced_overlap(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            foo = 2
            with namespaces.Namespace() as ns:
                qux = 4

    class Subclass(Test):
        with namespaces.Namespace() as ns:
            bar = 3
    assert Subclass().ns.foo == 2
    assert Subclass().ns.bar == 3
    assert Subclass().ns.ns.qux == 4


def test_empty_nameless(namespaces):
    class Test(namespaces.Namespaceable):
        with pytest.raises(RuntimeError):
            with namespaces.Namespace():
                pass


def test_non_empty_nameless(namespaces):
    class Test(namespaces.Namespaceable):
        with pytest.raises(RuntimeError):
            with namespaces.Namespace():
                a = 1


def test_rename(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            pass
        with pytest.raises(ValueError):
            with ns as ns2:
                pass


def test_use_namespace(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            foo = 1
            qux = 3
        assert ns.foo == 1
        ns.bar = 2
        assert ns.bar == 2
        del ns.qux
        with pytest.raises(AttributeError):
            del ns.qux
    assert Test.ns.foo == 1
    assert Test.ns.bar == 2


def test_basic_prop(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            @property
            def foo(self):
                return 1
    assert Test().ns.foo == 1


def test_complicated_prop(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            @property
            def var(self):
                return self.__private.var

            @var.setter
            def var(self, value):
                self.__private.var = value + 1

            @var.deleter
            def var(self):
                del self.__private.var

        with namespaces.Namespace() as __private:
            var = None

    test = Test()
    assert test.ns.var is None
    test.ns.var = 1
    assert test.ns.var == 2
    del test.ns.var
    assert test.ns.var is None


def test_override_method(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            def foo(self):
                return 1
    test = Test()
    assert test.ns.foo() == 1
    test.ns.foo = 2
    print(vars(test))
    assert test.ns.foo == 2
    del test.ns.foo
    assert test.ns.foo() == 1
    Test.ns.foo = 3
    assert Test.ns.foo == 3
    assert test.ns.foo == 3


def test_can_t_preload_with_namespace(namespaces):
    with pytest.raises(ValueError):
        namespaces.Namespace(ns=namespaces.Namespace())


def test_add_later(namespaces):
    class Test(namespaces.Namespaceable):
        pass

    ns = namespaces.Namespace()
    Test.ns = ns
    print('ns props')
    for slot in namespaces.Namespace.__slots__:
        print(slot, getattr(ns, slot))
    ns2 = namespaces.Namespace()
    Test.ns.ns = ns2
    print('ns2 props')
    for slot in namespaces.Namespace.__slots__:
        print(slot, getattr(ns2, slot))
    Test.ns.value = 1
    assert Test.ns.value == 1
    Test.ns.ns.value = 2
    assert Test.ns.ns.value == 2
    assert Test.ns.value == 1


@pytest.mark.xfail(sys.version_info < (3, 6),
                   reason="python3.6 api changes", strict=True)
def test_3_6_descriptor(namespaces):
    class Descriptor:
        def __set_name__(self, owner, name):
            self.owner = owner
            self.name = name
    assert namespaces.namespaces._DescriptorInspector(
        Descriptor()).is_descriptor

    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            d = Descriptor()

    assert Test.ns.d.name == 'd'


def test_basic_meta(namespaces):
    class Meta(namespaces.Namespaceable, type(namespaces.Namespaceable)):
        with namespaces.Namespace() as ns:
            meta_var = 1

    class Test(namespaces.Namespaceable, metaclass=Meta):
        pass

    assert Meta.ns.meta_var == 1
    assert Test.ns.meta_var == 1
    with pytest.raises(AttributeError):
        Test().ns.meta_var


def test_somewhat_weirder_meta(namespaces):
    class Meta(namespaces.Namespaceable, type(namespaces.Namespaceable)):
        with namespaces.Namespace() as ns:
            meta_var = 1

    class Test(namespaces.Namespaceable, metaclass=Meta):
        with namespaces.Namespace() as ns:
            cls_var = 2

    assert Meta.ns.meta_var == 1
    assert Test.ns.meta_var == 1
    assert Test.ns.cls_var == 2
    assert Test().ns.cls_var == 2
    with pytest.raises(AttributeError):
        Test().ns.meta_var
    with pytest.raises(AttributeError):
        Test.ns.var
    with pytest.raises(AttributeError):
        Meta.ns.cls_var
    Test.var = 3
    assert Test.var == 3
    Meta.var = 4
    assert Meta.var == 4


def test_classmethod_basic(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            @classmethod
            def cls_mthd(cls):
                return 'called'

    assert Test.ns.cls_mthd() == 'called'
    assert Test().ns.cls_mthd() == 'called'


def test_meta_plus_classmethod(namespaces):
    class Meta(namespaces.Namespaceable, type(namespaces.Namespaceable)):
        with namespaces.Namespace() as ns:
            pass

    class Test(namespaces.Namespaceable, metaclass=Meta):
        with namespaces.Namespace() as ns:
            @classmethod
            def cls_mthd(cls):
                return 'called'

    assert Test().ns.cls_mthd() == 'called'
    assert Test.ns.cls_mthd() == 'called'


def test_get_through_namespace(namespaces):
    class Test(namespaces.Namespaceable):
        var = 1
        with namespaces.Namespace() as ns:
            var2 = var

    assert Test.var == 1
    assert Test.ns.var2 == 1


def test_multiple_inheritance(namespaces):
    class Test1(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            with namespaces.Namespace() as ns:
                var = 1

    class Test2(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            var = 2

    class Test3(Test2, Test1):
        pass

    assert Test3.ns.ns.var == 1
    assert Test3.ns.var == 2


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
    with pytest.raises(ValueError):
        class Test(metaclass=type(namespaces.Namespaceable)):
            pass


def test_regular_delete(namespaces):
    class Test(namespaces.Namespaceable):
        pass
    Test.var = 1
    assert Test.var == 1
    del Test.var


def test_too_deep(namespaces):
    class Test(namespaces.Namespaceable):
        var = None
    with pytest.raises(ValueError):
        getattr(Test, 'var.__str__')


def test_block_reparent(namespaces):
    shadow_ns1 = None
    shadow_ns2 = None
    class Test1(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            with pytest.raises(ValueError):
                with ns:
                    pass
            with pytest.raises(ValueError):
                ns.ns = ns
        with pytest.raises(ValueError):
            ns.ns = ns
        with namespaces.Namespace() as ns2:
            with pytest.raises(ValueError):
                with ns:
                    pass
        nonlocal shadow_ns1
        nonlocal shadow_ns2
        with ns as shadow_ns1:
            shadow_ns2 = ns

    class Test2(namespaces.Namespaceable):
        with pytest.raises(ValueError):
            ns = Test1.ns
        with pytest.raises(ValueError):
            ns = shadow_ns1
        with pytest.raises(ValueError):
            ns = shadow_ns2
        with namespaces.Namespace() as ns:
            pass

    with pytest.raises(ValueError):
        Test2.ns.ns = shadow_ns1
    with pytest.raises(ValueError):
        Test2.ns.ns = shadow_ns2


def test_can_t_get_path(namespaces):
    with pytest.raises(ValueError):
        namespaces.Namespace().path


def test_non_existent_attribute_during_creation(namespaces):
    class Test(namespaces.Namespaceable):
        with namespaces.Namespace() as ns:
            pass
        with pytest.raises(AttributeError):
            ns.var


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

    test = Test()
    with pytest.raises(AttributeError):
        test.ns.deleter = None
    with pytest.raises(AttributeError):
        del test.ns.setter
    with pytest.raises(AttributeError):
        test.deleter = None
    with pytest.raises(AttributeError):
        del test.setter


def test_namespace_is_truthy(namespaces):
    assert namespaces.Namespace()
