"""Common operations. Some assume use of _DescriptorInspector."""


from .descriptor_inspector import _DescriptorInspector


def get(a_map, name):
    """Return a _DescriptorInspector around the attribute, or None."""
    try:
        value = a_map[name]
    except KeyError:
        return None
    else:
        return _DescriptorInspector(value)


def delete(dct, name):
    """Attempt to delete `name` from `dct`. Raise AttributeError if missing."""
    try:
        del dct[name]
    except KeyError:
        raise AttributeError(name)


def has_get(value):
    """Return whether the value is a wrapped getter descriptor."""
    return value is not None and value.has_get


def is_data(value):
    """Return whether the value is a wrapped data descriptor."""
    return value is not None and value.is_data


def get_data(dct, name):
    """Return the data descriptor associated with `name` in `dct`, if any."""
    value = get(dct, name)
    if is_data(value):
        return value
