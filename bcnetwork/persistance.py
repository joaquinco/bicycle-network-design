import csv

import networkx as nx
import yaml

from bcnetwork.geo import plane_distance
from bcnetwork import osm


def strip_str(value):
  return value.strip()

def parse_with_schema(data, schema):
  """
  Parse data values according to the schema dictionary
  """
  if not schema:
    return data

  complete_schema = {key: schema.get(key, strip_str) for key in data.keys()}

  return {key: complete_schema[key](value) for (key, value) in data.items()}

def get_csv_rows(arcs_file, schema=None):
  with open(arcs_file, 'r') as f:
    reader = csv.DictReader(f)

    return [parse_with_schema(row, schema) for row in reader]

def format_arc_key(source, destination):
  """
  Creates unique key for the arc
  """
  return f'arc_{source}_{destination}'

def read_graph_files(nodes_file, arcs_file):
  """
  Arcs csv must have:
  - source
  - destination
  - user_weight
  - construction_weight
  - infra_user_weight

  Nodes csv must have:
  - id
  - x
  - y

  return a tuple with nodes data and arcs data as dictionaries.
  """

  nodes = get_csv_rows(
    nodes_file,
    schema=dict(x=float, y=float)
  )
  arcs = get_csv_rows(
    arcs_file,
    schema=dict(
      user_weight=float,
      construction_weight=float,
      infra_user_weight=float,
    )
  )

  nodes_dict = {n['id']: n for n in nodes}

  # Add pos tuple to nodes
  for node_data in nodes_dict.values():
    node_data.update(dict(
      pos=(node_data['x'], node_data['y'])
    ))

  # Add weights and key to arcs
  for arc_data in arcs:
    distance = plane_distance(
      nodes_dict[arc_data['source']],
      nodes_dict[arc_data['destination']]
    )
    arc_data.update(dict(
      distance=distance,
      key=format_arc_key(arc_data['source'], arc_data['destination'])
    ))

  arcs_dict = {a['key']: a for a in arcs}

  return nodes_dict, arcs_dict

def read_graph_from_csvs(nodes_file, arcs_file, graph_class=nx.DiGraph):
  """
  Read graph files and return a nx.Graph or nx.DiGraph object
  """
  nodes, arcs = read_graph_files(nodes_file, arcs_file)

  graph = graph_class()

  graph.add_nodes_from(nodes.items())
  graph.add_edges_from([
    (a['source'], a['destination'], a) for a in arcs.values()
  ])

  return graph


def convert_to_simple_graph(graph):
  """
  Converts a multigraph to a simple graph
  """
  ret = nx.DiGraph()

  for node in graph.nodes():
    ret.add_node(node, **graph.nodes[node])

    for nbr, edges in graph.adj[node].items():
      # Pick just the first edge
      
      key = list(edges.keys())[0]
      ret.add_edge(node, nbr, **edges[key])

  return ret

def normalize_graph_shape(graph):
  """
  Normalize the graph instance with attributes used in this project.
  Also, if it's a multigraph convert it to a simple graph

  For arcs:
  - key
  - distance
  For nodes:
  - pos
  """
  graph_is_osm = osm.is_osm(graph)
  if graph_is_osm:
    osm.normalize_osm(graph)

  if graph.is_multigraph():
    ret = convert_to_simple_graph(graph)
    ret.graph.update(graph.graph)
  else:
    ret = graph.copy()


  for n1, n2 in ret.edges():
    if graph_is_osm:
      distance = ret.edges[n1, n2]['length']
    else:
      distance = plane_distance(ret.nodes[n1], ret.nodes[n2])

    ret.edges[n1, n2].update({
      'key': format_arc_key(n1, n2),
      'distance': distance
    })

  return ret

def read_graph_from_yaml(yaml_file, normalize=False):
  """
  Returns whatever is saved in the yaml, that should be a nx.Graph instance
  """
  with open(yaml_file, 'r') as file:
    graph = yaml.load(file.read(), Loader=yaml.Loader)

  if normalize:
    graph = normalize_graph_shape(graph)

  return graph

def write_graph_to_yaml(graph, yaml_file):
  """
  Writes a an graph object to a yaml file
  """
  with open(yaml_file, 'w') as file:
    file.write(yaml.dump(graph))
