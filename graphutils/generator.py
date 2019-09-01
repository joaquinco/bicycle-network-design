from functools import partial
import math
import random

import networkx as nx
from networkx.algorithms.planarity import check_planarity

MAX_INT = 2 << 32


def int_generator(min, max):
  return random.randint(min, max)


big_int_generator = partial(int_generator, 0, MAX_INT)
small_int_generator = partial(int_generator, 0, 256)
binary_generator = partial(int_generator, 0, 1)


def get_random_value(value_type):
  """
  Generates random value of type v.
  """
  allowed_types = [
    'int', 'small', 'float', 'binary'
  ]

  assert value_type in allowed_types, "Invalid type value, must be one of: " + ', '.join(allowed_types)

  generator = {
    'int': big_int_generator,
    'small': small_int_generator,
    'float': random.random,
    'binary': binary_generator,
  }.get(value_type)

  return generator()


def add_weights(data, weights):
  """
  Add random node weights
  """
  for k, v in weights.items():
    data[k] = get_random_value(v)


class _NodePool(object):
  def __init__(self, start=0):
    self.current = 0

  def get(self):
    self.current += 1
    return self.current


def fix_planarity(graph):
  """
  Remove edges from graph until it's planar.

  Returns: planar graph
  """
  # copy graph
  graph = nx.Graph(graph)

  edges = list(graph.edges())
  random.shuffle(edges)

  print(
    'Fixing planarity of graph ',
    graph.number_of_nodes(),
    ' nodes, ',
    graph.number_of_edges(),
    ' edges.'
  )

  for e in edges:
    graph.remove_edge(*e)
    if check_planarity(graph)[0]:
      lonely_nodes = [n for n in graph.nodes() if graph.degree[n] == 0]
      graph.remove_nodes_from(lonely_nodes)
      return graph


def generate_graph(node_count, directed=False):
  """
  Generates random connected planar graph or digraph
  """
  graph = directed and nx.DiGraph() or nx.Graph()

  pool = _NodePool()

  while graph.number_of_nodes() < node_count:
    candidates = [n for n in graph.nodes() if graph.degree[n] < 5]

    if not candidates:
      edge = (pool.get(), pool.get())
    else:
      n1 = random.choice(candidates)
      # From time to time generate new nodes
      if random.random() < 0.2 or len(candidates) == 1:
        n2 = pool.get()
      else:
        n2 = random.choice(
          list(filter(lambda x: x != n1, candidates))
        )

      # Random orientation
      edge = random.random() < 0.5 and (n1, n2) or (n2, n1)

    graph.add_edge(*edge)

    # From time to time or on edge conditions check planarity which
    # will remove edges randomly if it's not
    if (graph.number_of_nodes() >= node_count) and \
      not check_planarity(graph)[0]:
        graph = fix_planarity(graph)

  return graph


def randomize_weights(graph, node_weights=None, edge_weights=None):
  """
  Add random weights to graph
  """
  if node_weights:
    for node in graph.nodes():
      add_weights(graph.nodes[node], node_weights)

  if edge_weights:
    for edge in graph.edges():
      add_weights(graph.edges[edge], edge_weights)
    


