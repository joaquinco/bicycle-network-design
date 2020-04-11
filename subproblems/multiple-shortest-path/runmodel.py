import pdb
from pyomo.environ import ConcreteModel, Var, Param, Set, Objective, Constraint, \
                          NonNegativeReals, summation, minimize, SolverFactory
import bcnetwork.graph as gu


def get_model(graph, demand):
  """
  Builds a pyomo model given a graph and a demand dictionary
  """
  model = ConcreteModel()

  model.nodes = Set(initialize=graph.nodes(), doc='Nodes')
  model.edges = Set(
    initialize=graph.edges(), within=model.nodes * model.nodes, doc='Arcs'
  )

  model.od = Set(
    initialize=demand.keys(),
    within=model.nodes * model.nodes,
    doc='Origin destinations'
  )

  def get_inbound_edges(model, node):
    return [(adj, n) for adj, n in graph.edges() if n == node]

  def get_outbound_edges(model, node):
    return [(node, adj) for adj in graph.adj[node]]

  model.inbound = Set(model.nodes, initialize=get_inbound_edges, within=model.edges)
  model.outbound = Set(model.nodes, initialize=get_outbound_edges, within=model.edges)

  def get_demand(model, source, dest, node):
    od = (source, dest)
    if node == source:
      return demand[od]
    elif node == dest:
      return - demand[od]
    
    return 0

  model.b = Param(model.od, model.nodes, initialize=get_demand)

  edge_weights = { e: graph.edges[e]['weight'] for e in graph.edges()}
  model.cost = Param(model.edges, initialize=edge_weights)

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


def run_transpurbanpasaj2019():
  """
  Runs model with transpurbanpasaj dataset
  """

  with open('transpurbanpasaj2019/graph.json') as f:
    graph = gu.load(f)

  demand = {
    ('1', '9'): 300,
    ('1', '11'): 400,
    ('13', '1'): 100,
    ('11', '13'): 100,
    ('2', '15'): 250,
    ('7', '5'): 50,
  }

  model = get_model(graph, demand)

  solver = SolverFactory('glpk')

  solver.solve(model, tee=True)


run_transpurbanpasaj2019()
