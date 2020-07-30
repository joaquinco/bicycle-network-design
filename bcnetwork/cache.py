

class cached_property(object):
  def __init__(self, fn, name=None):
    self.fn = fn
    self.__doc__ = getattr(fn, '__doc__')
    self.name = name or fn.__name__

  def __get__(self, instance, cls=None):
    res = instance.__dict__[self.name] = self.fn(instance)
    return res

