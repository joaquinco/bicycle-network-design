def calculate_user_cost(weight, infra):
    """
    C*(-3*(i+1)+28)/25
    """
    return weight * (-3 * (infra + 1) + 28) / 25


def calculate_construction_cost(weight, infra):
    """
    2 * construction cost of (infra -1)
    """
    return 2 * infra * weight


def get_construction_cost(edge_data, infra=0):
    """
    Return construction cost on edge

    Edge data must provide 'construction_cost' attribute but it can be overriden by 'construction_cost_<infra>' 
    """
    return edge_data.get(f'construction_cost_{infra}') or calculate_construction_cost(
        edge_data['construction_cost'], int(infra)
    )


def get_user_cost(edge_data, infra=0):
    """
    Return construction cost on edge.

    Edge data must provide 'user_cost' attribute but it can be overriden by 'user_cost_<infra>'
    """
    return edge_data.get(f'infra_user_cost_{infra}') or calculate_user_cost(
        edge_data['user_cost'], int(infra)
    )
