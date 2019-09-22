from matplotlib import pyplot as plt
import networkx as nx

import graphutils as gu

graph = gu.generate_graph(150)

edge_weights = { 'length': 'short' }

gu.randomize_weights(graph, edge_weights=edge_weights)

with open('graph.json', 'w') as graph_file:
  gu.save(graph, graph_file)

nx.drawing.nx_pylab.draw_planar(graph)
plt.savefig('graph.svg')

