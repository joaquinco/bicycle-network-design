import graphutils as gu

graph = gu.generate_graph(150)

edge_weights = { 'length': 'small' }

gu.randomize_weights(graph, edge_weights=edge_weights)

with open('graph.json', 'w') as graph_file:
  gu.save(graph, graph_file)
