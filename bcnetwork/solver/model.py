import networkx as nx
from bcnetwork.networkx import astar_path
from bcnetwork.misc import Bunch
from bcnetwork.geo import plane_distance


class Model(object):
  def __init__(self, graph, odpairs, config=None):
    """
    Initializes the model. Required params are a conected graph and a list of od pairs.
    Graph MUST have the following data:
      - edges: weight_key
    And CAN have the following:
      - nodes: position_key, not required if astar is not used

    od pairs are a list of tuples where the tuples have the following form:
      (source, target, demand)
    """
    self.graph = graph
    self.odpairs = odpairs
    self.config = None
    self.update_config(**(config or {}))
    self.config_locked = False

  def update_config(self, **kwargs):
    """
    Model configuration handling
    """
    if self.config_locked:
      raise Exception('Cannot update config after computation has started')

    if self.config is None:
      self.config = Bunch(self.default_config)

    self.config.update(kwargs)
    self.config.update(
      original_weight_key=f'{self.config.weight_key}_current'
    )

  def objective(self):
    """
    Computes objective function
    """
    heuristic = None if self.config.use_astar else self._astar_heuristic
    ac = 0

    for source, target, demand in self.odpairs:
      _, distance = astar_path(
        self.current_graph, source, target, heuristic=heuristic, weight=self.config.weight_key
      )
      ac += distance * demand

    return ac

  def _astar_heuristic(self, n1, n2):
    """
    A* heuristic
    """
    return plane_distance(self.current_graph, n1, n2, key=self.config.position_key)

  @cached_property
  def current_graph(self):
    """
    Builds the graph used to make the computations
    """
    ret = self.graph.copy()
    original_weight_key = f'{self.config.weigth_key}_original'

    nx.

    self.config_locked = True

    return self.run_construction_phase(ret)

  def run_construction_phase(self, graph):
    """
    Run construction phase if any
    """
    return graph

  @property
  def default_config(self):
    """
    Return default_props
    """
    return dict(
      weight_key='weight',
      position_key='pos',
      use_astar=False,
    )