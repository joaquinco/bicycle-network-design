import networkx as nx

from .costs import get_construction_cost


class Errors:
    def __init__(self, name=None):
        self.messages = []
        self.name = name

    def add(self, message):
        self.messages.append(message)

    def assert_cond(self, success_condition, message):
        if not success_condition:
            self.add(message)

    def __bool__(self):
        return bool(self.messages)

    def __str__(self):
        lines = [f'Errors for {self.name}:']
        for m in self.messages:
            if isinstance(m, Errors):
                if m:
                    lines.append(str(m))
            else:
                lines.append(f'- {m}')

        return '\n'.join(lines)


def validate_shortest_paths(model, solution):
    """
    El costo de los caminos entre pares origen-destino sobre la red resultante
    es menor o igual al costo sobre la red sin infraestructuras.
    """
    ret = Errors(name='shortest paths')

    for path_data in solution.data.shortest_paths:
        base_shortest_path = nx.astar_path_length(
            model.graph, path_data.origin, path_data.destination, weight=model.user_cost_weight
        )
        ret.assert_cond(
            path_data.shortest_path_cost <= base_shortest_path,
            'Shortest path for {origin}-{destination} (cost {shortest_path_cost}) is greater than base cost: {base_shortest_path}'.format(
                base_shortest_path=base_shortest_path, **path_data,
            )
        )

    return ret


def validate_budget_excess(model, solution, ignore_excess_threshold=1e-3):
    """
    El presupuesto excedente no es suficiente para agregar una infraestructura
    que mejore el costo de alguno de los caminos.
    """
    ret = Errors(name='budget')

    budget_excess = model.budget - solution.budget_used

    # Ignore small budget excess
    if budget_excess <= ignore_excess_threshold:
        return ret

    solution_graph = model.apply_solution_to_graph(solution)

    for path_data in solution.data.shortest_paths:
        origin, destination = path_data.origin, path_data.destination

        for path in nx.all_shortest_paths(solution_graph, origin, destination, weight='effective_user_cost'):
            for n1, n2 in zip(path[:-1], path[1:]):
                infra = int(solution_graph[n1][n2]['effective_infrastructure'])
                # Infra can't be upgraded
                if infra == model.infrastructure_count - 1:
                    continue

                next_infra = infra + 1
                edge_data = model.graph[n1][n2]
                cost_diff = get_construction_cost(
                    edge_data, next_infra) - get_construction_cost(edge_data, infra)
                # Try with minimum purchasable infrastructure
                ret.assert_cond(
                    cost_diff > budget_excess,
                    'Path not improved for OD {odpair} using path {path} and setting infra {infra} by ${cost_diff} on edge {edge}'.format(
                        odpair=(origin, destination), path=path, infra={next_infra}, cost_diff=cost_diff, edge=(n1, n2)
                    )
                )

    return ret


def _get_interval_index(w, breakpoints):
    """
    Given a decreasing list of breakpoints q_j
    returns the minimun index where q_j >= w or 0 otherwise.

    Note: This follows the definition of f_k
    """

    for index, q in enumerate(breakpoints):
        if q >= w:
            return index
    return 0


def validate_demand_transfered(model, solution):
    """
    El camino más corto sobre la red resultante para un par origen-destino no
    puede resultar en un valor de demanda transferida distinto al resultante.
    """
    ret = Errors(name='demand transfered')
    shortest_path_data_by_od = {
        (d.origin, d.destination): d for d in solution.data.shortest_paths
    }

    demand_transfered_by_od = {
        (d.origin, d.destination): d for d in solution.data.demand_transfered
    }

    p_factors, q_factors = list(zip(*model.breakpoints))

    for origin, destination, demand in model.odpairs:
        path_data = shortest_path_data_by_od[(origin, destination)]
        demand_transfered_data = demand_transfered_by_od[(origin, destination)]
        shortest_path_cost = nx.astar_path_length(
            model.graph, origin, destination, weight=model.user_cost_weight)

        expected_j = _get_interval_index(
            shortest_path_cost,
            list(map(lambda x: x * shortest_path_cost, q_factors))
        )

        expected_demand_transfered = demand * p_factors[expected_j]

        ret.assert_cond(
            expected_demand_transfered != demand_transfered_data.demand_transfered,
            'On OD {odpair} expected seldemand transfere of {expected_demand_transfered} but found {demand_transfered}'.format(
                odpair=(origin, destination),
                expected_demand_transfered=expected_demand_transfered,
                demand_transfered=demand_transfered_data.demand_transfered,
            )
        )


def validate_solution(model, solution):
    """
    Validates a solution, used to validate the model itself.
    """
    errors = Errors(name=model.name)

    shortest_pat_errors = validate_shortest_paths(model, solution)
    errors.assert_cond(not shortest_pat_errors, shortest_pat_errors)

    budget_errors = validate_budget_excess(model, solution)
    errors.assert_cond(not budget_errors, budget_errors)

    demand_transfer_errors = validate_demand_transfered(model, solution)
    errors.assert_cond(not demand_transfer_errors, demand_transfer_errors)

    return errors
