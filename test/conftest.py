import pytest


@pytest.fixture
def namespaces():
    import class_namespaces
    return class_namespaces


@pytest.fixture
def namespace(namespaces):
    return namespaces.Namespace


@pytest.fixture
def namespaceable(namespaces):
    return namespaces.Namespaceable


@pytest.fixture
def compat():
    import class_namespaces.compat
    return class_namespaces.compat


@pytest.fixture
def abc():
    import class_namespaces.compat.abc
    return class_namespaces.compat.abc
