

class Bunch(object):
  def __init__(self, **kwargs):
    for k, v in kwargs.items():
      setattr(self, k, v)


def group_by(values, by):
  """
  Given an list of dicts:
  groups them by the given key
  """

  groups = {}

  for value in values:
    key = value.get(by)

    groups[key] = groups.get(key, []) + [value]

  return groups