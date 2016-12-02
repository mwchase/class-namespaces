def test_import_compat(compat):
    """Test the module is importable. See conftest.py for the actual import."""
    assert compat


def test_import_abc(abc):
    """Test the module is importable. See conftest.py for the actual import."""
    assert abc


def test_has_class(abc):
    assert abc.NamespaceableABC
