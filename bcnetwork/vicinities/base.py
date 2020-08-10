from bcnetwork.misc import Bunch

class Vicinity(object):
  def __init__(self, solution, model, **kwargs):
    """
    Builds a vicinity from a solution.
    Then it's capable of transforming it possibly several times in order
    to obtain better solutions.
    """
    self.solution = solution
    self.model = model
    self.config = Bunch({ **self.get_default_config(), **kwargs })

  def get_default_config(self, **config):
    return {}

  def get_neighbors(self):
    """
    Returns iterable where each entry corresponds to a solution which is neighbor
    to the initial one. They should be in descending order of importance.
    """
    raise NotImplementedError()
