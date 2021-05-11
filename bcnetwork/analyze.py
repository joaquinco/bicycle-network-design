from itertools import combinations
import networkx as nx

from .geo import plane_distance
from .read import read_graph_files_as_graph


section_separator = '---'

def main(nodes_csv, arcs_csv, weight_attribute):
  """
  Print statistics about a graph
  """
  graph = read_graph_files_as_graph(nodes_csv, arcs_csv)

  print(f'#nodes: {graph.number_of_nodes()}')
  print(f'#edges: {graph.number_of_edges()}')
  print(section_separator)

  print('source,destination,shortest_path')
  for n1, n2 in combinations(graph.nodes(), 2):
    shortest_path_cost = nx.astar_path_length(
      graph, n1, n2, heuristic=None, weight=weight_attribute
    )
    print(f'{n1},{n2},{shortest_path_cost}')

  print(section_separator)


def main_analyze(args):
  main(args.nodes_csv, args.arcs_csv, args.weight_attribute)