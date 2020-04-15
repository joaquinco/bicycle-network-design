import math
from os import path

import shapefile
import networkx as nx
import bcnetwork.graph as gu
from bcnetwork.conf import settings


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

  def __lt__(self, other):
    """
    Return true if this coord is dominated by the other
    """
    return self.lat < other.lat and self.lon < other.lon
  
  def __gt__(self, other):
    """
    Return true if this coord dominates the other
    """
    return self.lat > other.lat and self.lon > other.lon


class Street(object):
  def __init__(self, id, name):
    self.id = id
    self.name = name
    self.corners = []

  def add_corner(self, corner):
    self.corners.append(corner)


def get_montevideo_data():
  """
  Given a shapefile of corners returns a graph
  """
  reader = shapefile.Reader(path.join(settings.dataset_path, 'montevideo/data.shp'))

  street_by_id = {}
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
    
    corner = Corner(*coords, *[street_by_id[str_id1], street_by_id[str_id2]])

    street_by_id[str_id2].add_corner(corner)
    street_by_id[str_id2].add_corner(corner)

    corners.append(corner)

  return street_by_id, corners


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

    already_processed.add(current)
    ensure_node_added(graph, current)

    processed_count = len(already_processed)

    if processed_count % 1000 == 0:
      print(f'% {processed_count / total_points} processed')

    corners_by_str_id = {}
    for street in current.streets:
      corners = street_by_id[street.id].corners[:]
      added = set()
      while True:
        corners_avail = list(filter(lambda x: x not in added, corners))

        if not corners_avail:
          break

        closest = min(
          corners_avail,
          key=lambda x: x | current
        )
        if any(map(lambda x: x < closest, added)):
          break

        added.add(closest)
        # Add edge between closest and current
        ensure_node_added(graph, closest)
        adj = graph.add_edge(
          current.node,
          closest.node,
          weight=current | closest
        )

  return graph


def get_montevideo():
  graph_cache = path.join(settings.dataset_path, 'montevideo/graph.json')

  if not path.isfile(graph_cache):
    graph = get_montevideo_graph()

    with open(graph_cache, 'w') as f:
      gu.save(graph, f)
  else:
    with open(graph_cache, 'r') as f:
      graph = gu.load(f)

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


  with open(path.join(base_path, 'graph.json')) as f:
    graph = gu.load(f)

  return graph, demand


