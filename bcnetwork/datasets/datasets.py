import math
from os import path
import pdb

import shapefile
import networkx as nx
import bcnetwork.graph as gu
from bcnetwork.conf import settings

eps = 1e-5

class Corner(object):
  def __init__(self, lat, lon, *streets):
    self.lat = lat
    self.lon = lon
    self.streets = set(streets)
    self.node = None

  @property
  def name(self):
    return ', '.join(map(lambda x: x.name, self.streets))

  def __or__(self, other):
    """
    Euclidean distance between coords
    """
    return math.sqrt(
      (self.lat - other.lat) ** 2 + (self.lon - other.lon) ** 2
    )

  def __repr__(self):
    return f'<Corner lat={self.lat} lon={self.lon}>'


def abs_lt(n1, n2):
  if n1 * n2 < 0:
    return False
  return abs(n1) < abs(n2)

class RelativeCoord(object):
  def __init__(self, origin_point, point):
    self.point = point
    self.origin = origin_point

  @property
  def lat(self):
    return self.point.lat - self.origin.lat
  
  @property
  def lon(self):
    return self.point.lon - self.origin.lon

  @property
  def offset(self):
    return self.point | self.origin

  def __lt__(self, other):
    """
    Return true if this coord is dominated by the other
    """
    return abs_lt(self.lat, other.lat) and abs_lt(self.lon, other.lon)

  def __repr__(self):
    return f'<RelativeCoord lat={self.lat} lon={self.lon} offset={self.offset}>'


class Street(object):
  def __init__(self, id, name):
    self.id = id
    self.name = name
    self.corners = []

  def add_corner(self, corner):
    for curr in self.corners:
      if curr | corner < eps:
        return
    self.corners.append(corner)

  def __repr__(self):
    return f'<Street {self.name}>'


def get_montevideo_data():
  """
  Given a shapefile of corners returns a graph
  """
  reader = shapefile.Reader(path.join(settings.dataset_path, 'montevideo/data.shp'))

  street_by_id = {}
  corners_by_ids = {}
  corners = []
  for entry in reader:
    record =  entry.record
    shape = entry.shape

    if shape.shapeTypeName.lower() != 'point':
      continue
  
    coords = shape.points[0]
    str_id1, str_id2, str_name1, str_name2 = tuple(record[:4])

    if not street_by_id.get(str_id1):
      street_by_id[str_id1] = Street(str_id1, str_name1)

    if not street_by_id.get(str_id2):
      street_by_id[str_id2] = Street(str_id2, str_name2)
    
    corner = corners_by_ids.get((str_id1, str_id2)) or corners_by_ids.get((str_id2, str_id1))
    if not corner:
      corner = Corner(*coords, *[street_by_id[str_id1], street_by_id[str_id2]])
      corners.append(corner)
      corners_by_ids[(str_id1, str_id2)] = corner

    street_by_id[str_id2].add_corner(corner)
    street_by_id[str_id2].add_corner(corner)

  return street_by_id, corners



def postprocess_graph(g):
  """
  Remove very large/very small edges.

  Keep with the largest connected component.
  """

  length_min = 1
  length_max = 2500

  for e in list(g.edges()):
    weight = g.edges[e]['weight']

    if weight > length_max or weight < length_min:
      g.remove_edge(*e)

  nodes = max(nx.connected_components(g), key=len)

  subg = g.subgraph(nodes)

  _, _, l = list(zip(*subg.edges.data('weight')))
  count = len(l)
  mean = sum(l) / count
  std = math.sqrt(sum(map(lambda x: (x - mean) ** 2 / (count - 1), l)))

  print(
    f"""
    count: {count}
    mean: {mean}
    std: {std}
    max: {max(l)}
    min: {min(l)}
    """
  )

  return subg


def get_montevideo_graph():
  """
  Returns a graph of montevideo.
  """
  street_by_id, corners = get_montevideo_data()

  graph = nx.Graph()

  already_processed = set()
  stack = corners[:]
  total_points = len(corners)

  def ensure_node_added(graph, corn):
    """
    Add corner node to graph if not already added
    """

    if corn.node:
      return

    node = str(graph.number_of_nodes() + 1)
    corn.node = node
    graph.add_node(
      node,
      pos=[corn.lat, corn.lon],
      name=corn.name
    )

  while True:
    if not stack:
      break

    current = stack.pop()
    ensure_node_added(graph, current)

    already_processed.add(current)
    ensure_node_added(graph, current)

    processed_count = len(already_processed)

    if processed_count % 1000 == 0:
      print('% {:.2f}'.format(processed_count * 100 / total_points))

    def filter_avail(x):
      ret = x | current

      return ret > eps

    for street in current.streets:
      added = list()
      corners_avail = sorted(map(
        lambda x: RelativeCoord(current, x),
        filter(lambda x: x | current > eps, street_by_id[street.id].corners[:])
      ), key=lambda x: x.offset, reverse=True)
      street_related = 0

      while True:
        if not corners_avail:
          break

        closest = corners_avail.pop()
        if any(map(lambda x: x < closest, added)):
          break

        added.append(closest)

        selected_corner = closest.point

        # Add edge between selected_corner and current
        ensure_node_added(graph, selected_corner)
        adj = graph.add_edge(
          current.node,
          selected_corner.node,
          weight=current | selected_corner
        )
        street_related += 1

  return postprocess_graph(graph)


def get_montevideo():
  graph_cache = path.join(settings.dataset_path, 'montevideo/graph.yml')

  if not path.isfile(graph_cache):
    graph = get_montevideo_graph()

    nx.write_yaml(graph, graph_cache)
  else:
    graph = nx.read_yaml(graph_cache)

  return graph


def get_transpurbanpasaj2019():
  """
  Load graph and demand from files under datasets
  """
  base_path = path.join(settings.dataset_path, 'transpurbanpasaj2019')
  demand = {}

  with open(path.join(base_path, 'demand.txt')) as f:
    for source, content in enumerate(f, start=1):
      if not f:
        continue

      numbers = map(int, content.split())
      for destination, d in enumerate(numbers, start=1):
        if d <= 0:
          continue

        demand[(str(source), str(destination))] = d

  graph = nx.read_yaml(path.join(base_path, 'graph.yml'))

  return graph, demand


