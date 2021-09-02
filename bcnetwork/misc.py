

class Bunch(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _get_group_key(value, by):
    if hasattr(by, '__call__'):
        return by(value)
    else:
        return value[by]


def group_by(values, by):
    """
    Given an iterable of items:
    groups them by the given key, by default items are
    assumed to be dicts and :by: is one of its keys.
    """

    groups = {}

    for value in values:
        key = _get_group_key(value, by)

        groups[key] = groups.get(key, []) + [value]

    return groups
