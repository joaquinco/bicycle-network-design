import csv
import logging
import sys

import networkx as nx

from .mathprog import MathprogWriter
from .misc import group_by


logger = logging.getLogger('bcnetwork.transform')


def get_user_cost(weight, infra):
    """
    C*(-3*(i+1)+28)/25
    """
    return weight * (-3 * (infra + 1) + 28) / 25


def get_construction_cost(weight, infra):
    """
    2 * construction cost of (infra -1)
    """
    return 2 * infra * weight


def graph_to_mathprog(graph, output, infrastructure_count=2):
    """
    Export nodes and arcs into MathProg format according to exact.mod model definition
    """
    nodes_ids = list(graph.nodes())
    arcs_by_id = {graph.edges[n1, n2]['key']: (
        n1, n2) for (n1, n2) in graph.edges()}
    arcs_ids = list(arcs_by_id.keys())

    writer = MathprogWriter(output)

    writer.wcomment('Set of nodes')
    writer.wset('N')
    writer.wset_values(nodes_ids)
    writer.br()

    writer.wcomment('Set of arcs')
    writer.wset('A')
    writer.wset_values(arcs_ids)
    writer.br()

    # TODO: find a better way to handle infrastructures and user cost (currently distance)
    infrastructures = list(map(str, range(infrastructure_count)))
    infrastructures_costs_factor = {
        infra: int(infra) for infra in infrastructures}

    def get_infrastructure_user_cost(arc_id, infra):
        n1, n2 = arcs_by_id[arc_id]

        return graph.edges[n1, n2].get(f'construction_weight_{infra}') or \
            get_user_cost(graph.edges[n1, n2]
                          ['construction_weight'], int(infra))

    def get_infrastructure_construction_cost(arc_id, infra):
        n1, n2 = arcs_by_id[arc_id]

        return graph.edges[n1, n2].get(f'infra_user_weight_{infra}') or \
            get_construction_cost(
                graph.edges[n1, n2]['infra_user_weight'], int(infra))

    reversed_graph = graph.reverse()

    writer.wcomment('Graph adjacency')
    for node in graph.nodes():
        writer.wset(f'A_OUT[{node}]')
        writer.wset_values(
            [adj['key'] for adj in graph.adj[node].values()]
        )

        writer.wset(f'A_IN[{node}]')
        writer.wset_values(
            [adj['key'] for adj in reversed_graph.adj[node].values()]
        )
    writer.br()

    writer.wcomment('Set of infrastrucutres')
    writer.wset('I')
    writer.wset_values(infrastructures)
    writer.br()

    writer.wcomment('User cost')
    writer.wparam('C')
    writer.wmatrix(
        list(arcs_ids),
        infrastructures,
        get_infrastructure_user_cost
    )
    writer.br()

    writer.wcomment('Construction cost')
    writer.wparam('M')
    writer.wmatrix(
        list(arcs_ids),
        infrastructures,
        get_infrastructure_construction_cost
    )
    writer.br()


def origin_destination_pairs_to_mathprog(
    graph,
    odpairs,
    breakpoints,
    output,
    weight='distance'
):
    """
    Write OD pairs to mathprog format (according to the model definitoin)

    @param :graph: networkx.DiGraph
    @param :odparis: list((str, str, int)) (source, destination, demand)
    @param :breakpoints: list((float, float)) (demand transfered percentage, improvement needed)
    @param :output: stream

    @return None

    set OD := main   secondary1 secondary2;

    /* Origin and destinations nodes */
    param ORIGIN :=
    [main] 1
    [secondary1] 9
    [secondary2] 10;

    param DESTINATION :=
    [main] 3
    [secondary1] 4
    [secondary2] 13;

    /* Construction Budget */
    param B := 20;

    set J := 1 2 3;

    /* Demand transfer (P) and breakpoint (Q) parameters */
    param P :=
    [main, *] 1 0 2 20 3 200
    [secondary1, *] 1 0 2 30 3 50
    [secondary2, *] 1 0 2 20 3 80;

    param Q :=
    [main, *] 1 20 2 11 3 9.21
    [secondary1, *] 1 20 2 12 3 10
    [secondary2, *] 1 20 2 9 3 8;

    end;
    """

    writer = MathprogWriter(output)
    odpair_data = [(f'od_{idx}', *odpairs[idx]) for idx in range(len(odpairs))]
    odpair_ids = list(map(lambda x: x[0], odpair_data))
    origins = {x[0]: x[1] for x in odpair_data}
    destinations = {x[0]: x[2] for x in odpair_data}
    demand = {x[0]: x[3] for x in odpair_data}

    shortest_path_costs = {
        id: nx.astar_path_length(graph, o, d, weight=weight)
        for (id, o, d, *_rest) in odpair_data
    }

    writer.wcomment('OD Pairs')
    writer.wset('OD')
    writer.wset_values(odpair_ids)
    writer.wcomment('Shortest path cost per OD')
    for odpair_id, shortest_path_cost in shortest_path_costs.items():
        writer.wcomment(f'{odpair_id}: {shortest_path_cost}')
    writer.br()

    writer.wparam('ORIGIN')
    writer.wlist(
        odpair_ids,
        lambda x: origins[x],
    )
    writer.br()

    writer.wparam('DESTINATION')
    writer.wlist(
        odpair_ids,
        lambda x: destinations[x],
    )
    writer.br()

    j_values = [str(i) for i in range(len(breakpoints))]

    writer.wset('J')
    writer.wset_values(j_values)
    writer.br()

    def get_demand_transfered(od_id, j):
        od_demand = demand[od_id]
        index = int(j)

        return int(od_demand * breakpoints[index][0])

    def get_shortest_path_breakpoint(od_id, j):
        path_cost = shortest_path_costs[od_id]
        index = int(j)

        return path_cost * breakpoints[index][1]

    writer.wparam('P')
    writer.wmatrix(
        odpair_ids,
        j_values,
        get_demand_transfered,
    )
    writer.br()

    writer.wparam('Q')
    writer.wmatrix(
        odpair_ids,
        j_values,
        get_shortest_path_breakpoint,
    )
    writer.br()


def main(graph, *args):
    output = sys.stdout
    graph_to_mathprog(graph, output)
