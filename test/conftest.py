import pytest


@pytest.fixture
def namespaces():
    import class_namespaces
    return class_namespaces


@pytest.fixture
def namespace(namespaces):
    return namespaces.Namespace


@pytest.fixture(params=['main', 'abc'])
def namespaceable(request, namespaces, abc):
    if request.param == 'main':
        return namespaces.Namespaceable
    else:
        return abc.NamespaceableABC


@pytest.fixture
def compat():
    import class_namespaces.compat
    return class_namespaces.compat


@pytest.fixture
def abc():
    import class_namespaces.compat.abc
    return class_namespaces.compat.abc
