import functools


sep = '  '

class MathprogWriter(object):
  def __init__(self, output):
    self.w = output.write

  def wparam(self, name):
    self.w(f"param {name} :=\n")

  def wset(self, name):
    self.w(f"set {name} := \n")

  def wset_values(self, values):
    for v in values:
      self.w(sep, v)
    if values:
      self.w(';\n')

  def wlist(self, values, evaluator, end_line=False):
    for v in values:
      self.w(sep, evaluator(v), end='')
    if end_line:
      self.w(';\n')
  
  def wmatrix(self, rows, colums, evaluator):
    for n1 in rows:
      self.w(sep, f"[{n1}, *]")
      self.wlist(colums, functools.partial(evaluator, n1))
      self.w(n1 == rows[-1] and ';' or '', end='\n')

  def wcomment(self, comment):
    self.w(f'/* {comment} */')

  def br(self):
    self.w('\n\n')


def export(graph, output):
  """
  Export networkx graph to marthprox syntax
  """

  def _get_all_keys(entries, dict_of_dicts):
    return [
      k for n in entries
      for k, _ in dict_of_dicts[n].items()
    ]

  writer = MathprogWriter(output)

  nodes = graph.nodes()
  edges = graph.edges()

  node_keys = _get_all_keys(nodes, graph.nodes)
  edge_keys = _get_all_keys(edges, graph.edges)

  if not nodes:
    return

  writer.wcomment('Node set')
  writer.wset('N')
  writer.wset_values(nodes)

  writer.wcomment("Graph adjacency matrix 1 is adjacent")
  writer.wparam('G')
  writer.wmatrix(
    nodes,
    nodes,
    lambda x, y: graph.edges[n1, n2] and 1 or 0,
  )
  writer.br()

  writer.wcomment('Node attributes')
  for key in node_keys:
    writer.wparam(f'node_{key}'.upper())
    writer.wlist(
      nodes,
      lambda x: graph.nodes[x][key],
      end_line=True
    )
    writer.br()

  writer.wcomment('Edge attributes')
  for key in edge_keys:
    writer.wparam(f'edge_{key}'.upper())
    writer.wmatrix(
      nodes,
      nodes,
      lambda x, y: graph.edges[x, y][key],
    )

  writer.br()
