import csv
import logging
import sys

import networkx as nx

from .mathprog import MathprogWriter
from .misc import group_by


logger = logging.getLogger('bcnetwork.transform')

def graph_to_mathprog(graph, output):
  """
  Export nodes and arcs into MathProg format according to exact.mod model definition
  """
  nodes_ids = list(graph.nodes())
  arcs_by_id = {graph.edges[n1, n2]['key']:(n1, n2) for (n1, n2) in graph.edges()}
  arcs_ids = list(arcs_by_id.keys())

  writer = MathprogWriter(output)

  writer.wcomment('Set of nodes')
  writer.wset('N')
  writer.wset_values(nodes_ids)
  writer.br()

  writer.wcomment('Set of arcs')
  writer.wset('A')
  writer.wset_values(arcs_ids)
  writer.br()

  # TODO: find a better way to handle infrastructures and user cost (currently distance)
  infrastructures = ['none', 'basic']
  infrastructures_improvements = dict(none=1, basic=0.8)
  infrastructures_costs = dict(none=0.0, basic=1.8)

  def get_infrastructure_user_cost(arc_id, infra):
    n1, n2 = arcs_by_id[arc_id]

    return graph.edges[n1, n2]['distance'] * infrastructures_improvements[infra]

  def get_infrastructure_construction_cost(arc_id, infra):
    n1, n2 = arcs_by_id[arc_id]

    return graph.edges[n1, n2]['distance'] * infrastructures_costs[infra]

  reversed_graph = graph.reverse()

  writer.wcomment('Graph adjacency')
  for node in graph.nodes():
    writer.wset(f'A_OUT[{node}]')
    writer.wset_values([adj['key'] for adj in graph.adj[node].values()])

    writer.wset(f'A_IN[{node}]')
    writer.wset_values([adj['key'] for adj in reversed_graph.adj[node].values()])
  writer.br()

  writer.wcomment('Set of infrastrucutres')
  writer.wset('I')
  writer.wset_values(infrastructures)
  writer.br()

  writer.wcomment('User cost')
  writer.wparam('C')
  writer.wmatrix(
    list(arcs_ids),
    infrastructures,
    get_infrastructure_user_cost
  )
  writer.br()

  writer.wcomment('Construction cost')
  writer.wparam('M')
  writer.wmatrix(
    list(arcs_ids),
    infrastructures,
    get_infrastructure_construction_cost
  )
  writer.br()

def main(graph, *args):
  output = sys.stdout
  graph_to_mathprog(graph, output)

