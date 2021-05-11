import csv
import logging
import sys

from .mathprog import MathprogWriter
from .misc import group_by
from .read import read_graph_files


logger = logging.getLogger('bcnetwork.transform')

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
  writer.br()

  writer.wcomment('Set of infrastrucutres')
  writer.wset('I')
  writer.wset_values(infrastructures)
  writer.br()

  writer.wcomment('User cost')
  writer.wparam('C')
  writer.wmatrix(
    list(arcs.keys()),
    infrastructures,
    get_infrastructure_user_cost
  )
  writer.br()

  writer.wcomment('Construction cost')
  writer.wparam('M')
  writer.wmatrix(
    list(arcs.keys()),
    infrastructures,
    get_infrastructure_construction_cost
  )
  writer.br()

def transform(nodes_csv, arcs_csv):
  logger.debug(f'Reading nodes from {nodes_csv} and arcs from {arcs_csv}')

  nodes, arcs = read_graph_files(
    nodes_csv,
    arcs_csv
  )

  output = sys.stdout
  export_data(nodes, arcs, output)

def main_transform(args):
  return transform(args.nodes_csv, args.arcs_csv)