from functools import partial
import math
import random

import networkx as nx


MAX_INT = 2 << 32

choice = random.choice


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


def generate_graph(
    node_count,
    directed=True,
    edge_percentage=0.6,
    ensure_connected=True
  ):
  """
  Generates random connected graph or digraph
  """

  graph = directed and nx.DiGraph() or nx.Graph()

  nodes = list(range(1, node_count + 1))

  graph.add_nodes_from(nodes)

  total_edges = sum(nodes) / (directed and 2 or 1)
  target_edges = total_edges * edge_percentage

  while (graph.number_of_edges() < target_edges) or (ensure_connected and not nx.is_connected(graph)):
    graph.add_edge(choice(nodes), choice(nodes))

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
    


