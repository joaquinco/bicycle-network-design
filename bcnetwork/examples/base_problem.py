import pdb
import networkx as nx
from pyomo.environ import ConcreteModel, Var, Param, Set, Objective, Constraint, \
                          NonNegativeReals, summation, minimize, SolverFactory


def get_base_model(graph, demand):
  """
  Builds a pyomo model given a graph and a demand dictionary.

  The model is a basic multi Origin-destination minimun cost flow problem.
  """
  model = ConcreteModel('Multiple Shortest Path')

  model.nodes = Set(initialize=list(graph.nodes()), doc='Nodes')

  is_simple_graph = isinstance(graph, nx.Graph)
  edges = list(graph.edges())

  if is_simple_graph:
    edges.extend(map(lambda x: (x[1], x[0]), edges[:]))

  model.edges = Set(
    initialize=edges, within=model.nodes * model.nodes, doc='Arcs'
  )

  model.od = Set(
    initialize=demand.keys(),
    within=model.nodes * model.nodes,
    doc='Origin destinations'
  )

  def get_inbound_edges(model, node):
    if is_simple_graph:
      return [(node, adj) for adj in graph.adj[node]]

    return [(adj, n) for adj, n in graph.edges() if n == node]

  def get_outbound_edges(model, node):
    return [(node, adj) for adj in graph.adj[node]]

  model.inbound = Set(model.nodes, initialize=get_inbound_edges, within=model.edges)
  model.outbound = Set(model.nodes, initialize=get_outbound_edges, within=model.edges)

  def get_flow_value(model, source, dest, node):
    od = (source, dest)
    if node == source:
      return demand[od]
    elif node == dest:
      return - demand[od]

    return 0

  model.b = Param(model.od, model.nodes, initialize=get_flow_value)

  def get_edge_weight(model, n1, n2):
    return graph.edges[n1, n2]['weight']

  model.cost = Param(model.edges, initialize=get_edge_weight)

  model.flow = Var(model.od, model.edges, domain=NonNegativeReals)

  def get_flow_conservation(model, source, dest, node):
    return sum(model.flow[source, dest, n1, n2] for n1, n2 in model.outbound[node]) - \
          sum(model.flow[source, dest, n1, n2] for n1, n2 in model.inbound[node]) - \
          model.b[source, dest, node] == 0

  model.flow_conservation = Constraint(
    model.od, model.nodes, rule=get_flow_conservation
  )

  def get_objective(model):
    return sum(
      model.cost[n1, n2] * sum(
        model.flow[source, dest, n1, n2] for source, dest in model.od
      )
      for n1, n2 in model.edges
    )

  model.user_cost = Objective(rule=get_objective, sense=minimize)

  return model
