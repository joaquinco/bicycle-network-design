import csv
import logging
import sys

from .geo import plane_distance
from .mathprog import MathprogWriter
from .misc import group_by


logger = logging.getLogger('bcnetwork.transform')

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

def parse_files(nodes_file, arcs_file):
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


def export_data(nodes, arcs, output):
  """
  Export nodes and arcs into MathProg format according to exact.mod model definition
  """
  writer = MathprogWriter(output)

  writer.wcomment('Set of nodes')
  writer.wset('N')
  writer.wset_values(nodes.keys())
  writer.br()

  writer.wcomment('Set of arcs')
  writer.wset('A')
  writer.wset_values(arcs.keys())
  writer.br()

  outbound = group_by(arcs.values(), 'source')
  inbound = group_by(arcs.values(), 'destination')

  # TODO: find a better way to handle infrastructures
  infrastructures = ['none', 'basic']
  def get_infrastructure_user_cost(arc_id, infra):
    if infra == 'none':
      return arcs[arc_id]['user_cost']
    elif infra == 'basic':
      return arcs[arc_id]['infra_user_cost']

  def get_infrastructure_construction_cost(arc_id, infra):
    if infra == 'none':
      return 0.0
    elif infra == 'basic':
      return arcs[arc_id]['construction_cost']

  writer.wcomment('Graph adjacency')
  for node in nodes.keys():
    writer.wset(f'A_OUT[{node}]')
    writer.wset_values([a['name'] for a in outbound.get(node, [])])

    writer.wset(f'A_IN[{node}]')
    writer.wset_values([a['name'] for a in inbound.get(node, [])])

  writer.wcomment('Set of infrastrucutres')
  writer.wset('I')
  writer.wset_values(infrastructures)

  writer.wcomment('User cost')
  writer.wparam('C')
  writer.wmatrix(
    list(arcs.keys()),
    infrastructures,
    get_infrastructure_user_cost
  )

  writer.wcomment('Construction cost')
  writer.wparam('M')
  writer.wmatrix(
    list(arcs.keys()),
    infrastructures,
    get_infrastructure_construction_cost
  )

def transform(nodes_csv, arcs_csv):
  logger.debug(f'Reading nodes from {nodes_csv} and arcs from {arcs_csv}')

  nodes, arcs = parse_files(
    nodes_csv,
    arcs_csv
  )

  output = sys.stdout
  export_data(nodes, arcs, output)


def main_transform(args):
  return transform(args.nodes_csv, args.arcs_csv)