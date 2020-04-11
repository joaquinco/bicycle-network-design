import networkx as nx
import matplotlib.pyplot as plt


def draw_graph(
  graph,
  position_param='pos',
  with_labels=True,
  arrows=False,
  node_color='black',
  font_color='white'):
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
    font_color=font_color
  )
