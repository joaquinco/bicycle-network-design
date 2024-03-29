import networkx as nx

from .costs import get_construction_cost
from .model_utils import get_breakpoint_index


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
        base_shortest_path = model.base_shortest_path_costs[(
            path_data.origin, path_data.destination)]
        ret.assert_cond(
            path_data.shortest_path_cost <= base_shortest_path,
            'Shortest path for {origin}-{destination} (cost {shortest_path_cost}) is greater than base cost: {base_shortest_path}'.format(
                base_shortest_path=base_shortest_path, **path_data,
            )
        )

    return ret


def validate_budget_excess(model, solution, solution_graph, ignore_excess_threshold=1e-3):
    """
    El presupuesto excedente no es suficiente para agregar una infraestructura
    que mejore el costo de alguno de los caminos.
    """
    ret = Errors(name='budget')

    budget_excess = model.budget - solution.budget_used

    # Ignore small budget excess
    if budget_excess <= ignore_excess_threshold:
        return ret

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
                    'Path not optimized for OD {odpair} using path {path}. Infra {infra} can be set by ${cost_diff} on edge {edge}'.format(
                        odpair=(origin, destination), path=path, infra=next_infra, cost_diff=cost_diff, edge=(
                            n1, n2)
                    )
                )

    return ret


def validate_demand_transfered(model, solution, solution_graph, tolerance=1e-3):
    """
    El camino más corto sobre la red resultante para un par origen-destino no
    puede resultar en un valor de demanda transferida distinto al resultante.
    """
    ret = Errors(name='demand transfered')
    demand_transfered_by_od = {
        (d.origin, d.destination): d for d in solution.data.demand_transfered
    }
    shortest_path_per_od = {
        (d.origin, d.destination): d for d in solution.data.shortest_paths
    }

    p_factors, q_factors = list(zip(*model.breakpoints))
    expected_total_demand_transfered = 0

    for origin, destination, demand in model.odpairs:
        od = (origin, destination)
        demand_transfered_data = demand_transfered_by_od.get(od, None)
        shortest_path_data = shortest_path_per_od[od]

        shortest_path_cost = nx.astar_path_length(
            solution_graph, origin, destination, weight='effective_user_cost')
        base_shortest_path_cost = model.base_shortest_path_costs[(
            origin, destination)]

        shortest_path_breakpoints = list(
            map(lambda x: x * base_shortest_path_cost, q_factors))
        expected_j = get_breakpoint_index(
            shortest_path_cost,
            shortest_path_breakpoints
        )
        received_j = demand_transfered_data and demand_transfered_data.j_value or 0
        received_shortest_path_cost = shortest_path_data.shortest_path_cost

        expected_demand_transfered = p_factors[expected_j] * demand
        expected_total_demand_transfered += int(expected_demand_transfered)

        # Due to numerical problems, when the shortest path cost is equal to a breakpoint
        # sometimes the solver does not return the j calculated here.
        ret.assert_cond(
            received_j == expected_j or (
                abs(received_shortest_path_cost -
                    shortest_path_cost) <= tolerance
                and abs(expected_j - received_j) == 1
            ),
            (
                'On OD {odpair} expected j of {expected_j} but found {received_j} '
                '(received shortest path cost: {received_shortest_path_cost}, expected: {shortest_path_cost}) '
                '(received demand transferd: {received_demand_transfered}, expected: {expected_demand_transfered})'
            ).format(
                odpair=(origin, destination),
                expected_j=expected_j,
                received_j=received_j,
                received_shortest_path_cost=received_shortest_path_cost,
                shortest_path_cost=shortest_path_cost,
                received_demand_transfered=demand_transfered_data.demand_transfered,
                expected_demand_transfered=expected_demand_transfered,
            )
        )

    ret.assert_cond(
        solution.total_demand_transfered == expected_total_demand_transfered,
        f'Expected total demand transfer of {expected_total_demand_transfered} but found {solution.total_demand_transfered}'
    )

    return ret


def validate_solution(model, solution):
    """
    Validates a solution, used to validate the model itself.
    """
    errors = Errors(name=model.name)

    solution_graph = model.apply_solution_to_graph(solution)

    shortest_pat_errors = validate_shortest_paths(model, solution)
    errors.assert_cond(not shortest_pat_errors, shortest_pat_errors)

    budget_errors = validate_budget_excess(model, solution, solution_graph)
    errors.assert_cond(not budget_errors, budget_errors)

    demand_transfer_errors = validate_demand_transfered(
        model, solution, solution_graph)
    errors.assert_cond(not demand_transfer_errors, demand_transfer_errors)

    return errors
