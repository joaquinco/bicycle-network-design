import networkx as nx
import matplotlib.pyplot as plt

def get_draw_config(graph):
  config = dict(
    node_size=300,
    font_size=12,
    dpi=300,
    width=1,
  )

  number_of_nodes = graph.number_of_nodes()

  if number_of_nodes < 30:
    return config
  
  if number_of_nodes < 100:
    return {
      **config,
      'node_size': 100,
      'font_size': 6,
      'dpi': 600,
      'width': 0.8,
    }

  return {
    **config,
    'node_size': 1,
    'font_size': 0.2,
    'dpi': 900,
    'width': 0.3,
  }

def draw_graph(
  graph,
  position_param='pos',
  with_labels=True,
  arrows=False,
  node_color='#67ccfc',
  font_color='black',
  edge_color='#9e9e9e',
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
    edge_color=edge_color,
    **kwargs
  )

def draw_graph_to_file(filename, graph, *args, **kwargs):
  config = get_draw_config(graph)
  dpi = config.pop('dpi')

  draw_graph(graph, *args, **{**config, **kwargs})

  plt.savefig(filename, dpi=dpi)

def main(graph, args):
  draw_graph_to_file(args.output, graph)
