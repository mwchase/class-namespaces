import pytest


@pytest.fixture
def namespaces():
    import class_namespaces
    return class_namespaces
