def get_edge_list(nodes, neighbours_by_node):
    """
    Return list of edges given the neightbour data by node.
    """
    return [(node, other_node)
            for (node, edge_list) in enumerate(neighbours_by_node, min(nodes))
            for other_node in edge_list]