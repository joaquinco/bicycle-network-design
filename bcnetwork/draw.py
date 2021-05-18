import networkx as nx
import matplotlib.pyplot as plt

from .read import read_graph_files_as_graph

def draw_graph(
  graph,
  position_param='pos',
  with_labels=True,
  arrows=False,
  node_color='black',
  font_color='white',
  **kwargs):
  """
  Draw graph using matplotlib.
  """
  f = plt.figure()

  positions = None

  if position_param:
    positions = nx.get_node_attributes(graph, position_param)

  nx.draw(
    graph,
    positions,
    with_labels=with_labels,
    arrows=arrows,
    node_color=node_color,
    font_color=font_color,
    **kwargs
  )

def draw_graph_to_file(filename, *args, dpi=300, **kwargs):
  draw_graph(*args, **kwargs)
  plt.savefig(filename, dpi=dpi)


def main_draw(args):
  graph = read_graph_files_as_graph(args.nodes_csv, args.arcs_csv)
  draw_graph_to_file(args.output, graph)
