import networkx as nx

serializable_types = [int, float, bool, str]

def _is_serializable(value):
  if isinstance(value, list):
    return all(map(_is_serializable, value))
  
  return any(map(lambda t: isinstance(value, t), serializable_types))

def as_serializable(graph):
  """
  Return an osm graph but just including serializable attributes.
  """
  ret = graph.copy()

  for n in ret.nodes():
    for k, v in list(ret.nodes[n].items()):
      if not _is_serializable(v):
        del ret.nodes[n][k]

  if ret.is_multigraph():
    edges = ret.edges(keys=True)
  else:
    edges = ret.edges()

  for e in edges:
    for k, v in list(ret.edges[e].items()):
      if not _is_serializable(v):
        del ret.edges[e][k]

  return ret


def normalize_osm(g):
  """
  Put coordinates x, y into pos attribute for each node.
  Transform node ids to string
  """
  nodes = list(g.nodes())
  for node in nodes:
    data = g.nodes[node]
    g.nodes[node]['pos'] = [data['x'], data['y']]

  mapping = { n:str(n) for n in nodes }

  return nx.relabel_nodes(g, mapping)


def draw_solution(graph, solution, cmap=['orange', 'blue', 'green', 'black'], location_key='pos'):
    import osmnx as ox
    """
    Draw solution obtained by a solver
    """
    # TODO: add references to figure

    def get_xy(graph, n1, n2):
        return list(zip(graph.nodes[n1][location_key], graph.nodes[n2][location_key]))
    
    fig, ax = ox.plot_graph(graph, fig_height=15, show=False, close=False)
    for odpair, data in solution.shortest_paths.items():
        path = data['path']
        for n1, n2 in zip(path[:-1], path[1:]):
            ax.plot(*get_xy(graph, n1, n2), 'r--', linewidth=2)
        
        for edge in solution.modifications[odpair].keys():
            n1, n2, infra = edge
            if infra > 0:
                ax.plot(*get_xy(graph, n1, n2), c=cmap[infra], linewidth=4)
    
        source, target = odpair
        ax.scatter(*graph.nodes[source][location_key], s=100, c='red', zorder=4)
        ax.scatter(*graph.nodes[target][location_key], s=100, c='red', zorder=4)
            
    return fig, ax
