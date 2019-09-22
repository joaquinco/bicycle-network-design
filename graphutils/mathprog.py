import functools
import numbers


sep = '  '

def get_empty_weight(sample):
  if isinstance(sample, numbers.Number):
    return 0
  else:
    return sep


class MathprogWriter(object):
  def __init__(self, output):
    self.w = output.write

  def wparam(self, name):
    self.w(f"param {name} :=\n")

  def wset(self, name):
    self.w(f"set {name} := \n")

  def wset_values(self, values):
    for v in values:
      self.w(sep + v)
    if values:
      self.w(';\n')

  def wlist(self, values, evaluator, end_line=False):
    for v in values:
      self.w(sep + v + sep + str(evaluator(v)))
    if end_line:
      self.w(';\n')
  
  def wmatrix(self, rows, colums, evaluator):
    for n1 in rows:
      self.w(sep + f"[{n1}, *]")
      self.wlist(colums, functools.partial(evaluator, n1))
      self.w(n1 == rows[-1] and ';' or '' + '\n')

  def wcomment(self, comment):
    self.w(f'/* {comment} */\n')

  def br(self):
    self.w('\n\n')

  def wdata(self):
    self.w('data;\n')

  def wend(self):
    self.w('end;\n')


def export(graph, output):
  """
  Export networkx graph to marthprox syntax
  """

  def _get_all_keys(entries, dict_of_dicts):
    return {
      k for n in entries
      for k, _ in dict_of_dicts[n].items()
    }

  writer = MathprogWriter(output)

  nodes = list(graph.nodes())
  edges = list(graph.edges())

  node_keys = _get_all_keys(nodes, graph.nodes)
  edge_keys = _get_all_keys(edges, graph.edges)

  if not nodes:
    return

  writer.wdata()
  writer.br()

  writer.wcomment('Node set')
  writer.wset('N')
  writer.wset_values(nodes)
  writer.br()

  writer.wcomment("Graph adjacency matrix 1 is adjacent")
  writer.wparam('G')
  writer.wmatrix(
    nodes,
    nodes,
    lambda x, y: (x, y) in graph.edges and 1 or 0,
  )
  writer.br()

  if node_keys:
    writer.wcomment('Node attributes')
    for key in node_keys:
      writer.wparam(f'node_{key}'.upper())
      writer.wlist(
        nodes,
        lambda x: graph.nodes[x][key],
        end_line=True
      )
      writer.br()

  if edge_keys:
    writer.wcomment('Edge attributes')
    for key in edge_keys:
      _, _, sample = list(graph.edges.data(key))[0]
      default_value = get_empty_weight(sample)

      writer.wparam(f'edge_{key}'.upper())
      writer.wmatrix(
        nodes,
        nodes,
        lambda x, y: (x, y) in graph.edges and graph.edges[x, y][key] or default_value,
      )
      writer.br()

  writer.wend()