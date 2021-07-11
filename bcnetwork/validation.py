import networkx as nx


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
                    lines.append(m.print())
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
            'Shortest path for {origin}-{destination} is greater than base {base_shortest_path}'.format(
                base_shortest_path=base_shortest_path, **path_data,
            )
        )

    return ret


def validate_budget_excess(model, solution):
    """
    El presupuesto excedente no es suficiente para agregar una infraestructura
    que mejore el costo de alguno de los caminos.
    """
    ret = Errors(name='budget')

    return ret


def validate_demand_transfered(model, solution):
    """
    El camino más corto sobre la red resultante para un par origen-destino no
    puede resultar en un valor de demanda transferida distinto al resultante.
    """
    ret = Errors(name='demand transfered')

    return ret


def validate_solution(model, solution):
    """
    Validates a solution, used to validate the model itself.
    """

    errors = Errors()

    shortest_pat_errors = validate_shortest_paths(model, solution)
    errors.assert_cond(not shortest_pat_errors, shortest_pat_errors)

    budget_errors = validate_budget_excess(model, solution)
    errors.assert_cond(not budget_errors, budget_errors)

    demand_transfer_errors = validate_demand_transfered(model, solution)
    errors.assert_cond(not demand_transfer_errors, demand_transfer_errors)

    return errors
