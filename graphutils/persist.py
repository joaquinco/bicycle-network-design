
import json
import sys
import networkx as nx

from .mathprog import export as mathprog_export


def export_graph_to_fmt(graph, output_file, fmt=None):
  """
  Exports graph to specified format
  """
  fmt = fmt or 'mathprog'

  exporter = {
    'mathprog': mathprog_export,
  }.get(fmt)

  if not exporter:
    raise Exception('Invalid export format')

  exporter(graph, output_file)


def load_graph_from_file(input):
  """
  Opens file and call load_graph with json data
  """
  data = json.loads(input.read())

  return load_graph(data)


def load_and_export(input=None, output=None, fmt=None):
  """
  Loads graph definition and exports it to MathProg format.
  """

  input_close = output_close = True
  if not input or input == '-':
    finput = sys.stdin
    input_close = False
  else:
    finput = open(input, 'rb')

  if not output or output == '-':
    foutput = sys.stdout
    output_close = False
  else:
    foutput = open(output, 'wt')

  graph = load_graph_from_file(finput)

  export_graph_to_fmt(graph, foutput, fmt)

  if input_close:
    finput.close()
  
  if output_close:
    foutput.close()

def load_graph(data):
  """
  Transforms dict into networkx.Graph or whatever instance
  Specification:
  {
    type: string -> graph, digraph
    nodes: array -> list of nodes,
    adjacents: {
      node1: array -> array of adjacents,
      node2: {
        node3: { weight1: value, weight2: value }
      }
    }
  }  
  """
  validate_data(data)

  gtype = data.get('type', 'graph')
  if gtype == 'digraph':
    graph = nx.Digraph()
  else:
    graph = nx.Graph()

  graph.add_nodes_from(data.get('nodes', []))

  adj = data.get('adjacency', {})

  for node, node_adj in adj.items():
    if isinstance(node_adj, list):
      graph.add_edges_from([(node, other_node) for other_node in node_adj])
    else:
      for other_node, attributes in node_adj.items():
        graph.add_edge(node, other_node, **attributes)

  return graph


def save_graph(graph, output):
  """
  Writes json.dump to output stream
  """
  data = {
    "type": graph.__class__.__name__.lower(),
    "nodes": list(graph.nodes()),
  }

  adj = {}

  for node in graph.nodes():
    neightbours = {}

    for nei in graph.adj[node]:
      neightbours[nei] = dict(graph.edges[node, nei])

    adj[node] = neightbours

  data['adjacency'] = adj

  output.write(json.dumps(data))


def is_scalar(value):
  """
  Returns true if value is scalar
  """
  return not (isinstance(value, list) or isinstance(value, dict))


def validate_data(data):
  """
  Validates data structure
  """
  errors = {}

  gtype = data.get('type', None)
  nodes = data.get('nodes', [])
  adjacents = data.get('adjacents')
  
  if gtype and not isinstance(gtype, str):
    errors["type"] = "Expected 'graph' or 'digraph' but found #{gtype}"

  if nodes:
    if not isinstance(node, list):
      errors["nodes"] = "Expected array but found #{nodes}"
    else:
      node_errs = {}
      for index, elem in enumerate(nodes):
        if not elem and elem != 0:
          node_errs[index] = "Empty element found"
        elif not (isinstance(elem, str) or isinstance(elem, int)):
          node_errs[index] = "Expected string or integer but found #{elem}"
      
      if node_errs:
        errors["nodes"] = node_errs
  
  if adjacents:
    if not isinstance(adjacents, dict):
      errors["adjacents"] = "Expected dictionary but found #{adjacents}"
    else:
      for node, node_adj in adjacents.items():
        adj_err = {}
        if isinstance(node_adj, dict):
          for node, node_attrs in value.items():
            if not is_scalar(node):
              adj_err[node] = "Expected scalar attribute key"
        elif isinstance(node_adj, list):
          if not all(map(list, is_scalar)):
            adj_err[node] = "Node adjacency list should be a list of node names"
        else:
          adj_err["Node adjacency should be a list or a dictionary"]
      
      if adj_err:
        errors["adjacency"] = adj_err
    
  if errors:
    print_errors(errors)
    raise Exception("Data structure errors found")


def print_errors(errors, pad=0):
  """
  Print nested error dict
  """
  padding = ' ' * pad
  for key, value in errors.items():
    if isinstance(value, dict):
      print(padding, key, ':')
      print_errors(value, pad=2)
    else:
      print(padding, key, ": ", value)
