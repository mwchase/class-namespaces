"""Common test fixtures."""


import pytest


@pytest.fixture
def namespaces():
    """Return the top-level class_namespaces module."""
    import class_namespaces
    return class_namespaces


@pytest.fixture
def namespace(namespaces):
    """Return the Namespace class."""
    return namespaces.Namespace


@pytest.fixture(params=['main', 'abc'])
def namespaceable(request, namespaces, abc):
    """Return either helper class."""
    if request.param == 'main':
        return namespaces.Namespaceable
    else:
        return abc.NamespaceableABC


@pytest.fixture
def compat():
    """Return the top-level metaclasses module."""
    import class_namespaces.compat
    return class_namespaces.compat


@pytest.fixture
def abc():
    """Return the ABC compatibility module."""
    import class_namespaces.compat.abc
    return class_namespaces.compat.abc
