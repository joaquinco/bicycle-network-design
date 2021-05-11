import csv

import networkx as nx

from .geo import plane_distance


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

def format_arc_name(arc_data):
  """
  Creates unique name for the arc
  """
  source = arc_data['source']
  destination = arc_data['destination']

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

  # Add weights and name to arcs
  for arc_data in arcs:
    distance = plane_distance(
      nodes_dict[arc_data['source']],
      nodes_dict[arc_data['destination']]
    )
    arc_data.update(dict(
      user_cost=distance * arc_data['user_weight'],
      construction_cost=distance * arc_data['construction_weight'],
      infra_user_cost=distance * arc_data['infra_user_weight'],
      distance=distance,
      name=format_arc_name(arc_data)
    ))

  arcs_dict = {a['name']: a for a in arcs}

  return nodes_dict, arcs_dict


def read_graph_files_as_graph(nodes_file, arcs_file, graph_class=nx.DiGraph):
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
