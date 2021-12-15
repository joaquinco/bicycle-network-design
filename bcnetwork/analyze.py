from itertools import permutations, combinations
import networkx as nx


section_separator = '---'


def main(graph, args):
    """
    Print statistics about a graph
    """
    generate_node_pairs = permutations if graph.is_directed() else combinations
    weight_attribute = args.weight_attribute

    print(f'#nodes: {graph.number_of_nodes()}')
    print(f'#edges: {graph.number_of_edges()}')
    print(section_separator)

    print('source,destination,shortest_path')
    for n1, n2 in generate_node_pairs(graph.nodes(), 2):
        shortest_path_cost = nx.astar_path_length(
            graph, n1, n2, heuristic=None, weight=weight_attribute
        )
        print(f'{n1},{n2},{shortest_path_cost}')

    print(section_separator)
