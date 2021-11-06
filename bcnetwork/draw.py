import networkx as nx
import matplotlib.pyplot as plt

import networkx as nx

from .misc import group_by
from .colors import colors


def get_fig_scale(node_count):
    if node_count < 30:
        return 1

    if node_count < 200:
        return 1.5

    if node_count < 1000:
        return 3

    if node_count < 10000:
        return 5

    return 8


def calc_fig_size(positions):
    """
    Calculates fig size depending on nodes' positions.

    Returns a tuple (height, width)
    """
    def get_x(p):
        return p[1]

    def get_y(p):
        return p[0]

    axis = list(map(get_x, positions))
    absis = list(map(get_y, positions))
    max_x, min_x = max(axis), min(axis)
    max_y, min_y = max(absis), min(absis)

    delta_x = max_x - min_x
    delta_y = max_y - min_y

    base_size = 5
    if delta_x > delta_y:
        size = (base_size, base_size * delta_y / delta_x)
    else:
        size = (base_size * delta_y / delta_x, base_size)

    scale = get_fig_scale(len(positions))

    return tuple(map(lambda x: x * scale, size))


def get_draw_config(graph):
    """
    Return graph drawing configuration based on node count.
    Except from dpi, the keys are the ones defined in
    nx.draw_networkx function.
    """
    config = dict(
        node_size=300,
        font_size=12,
        dpi=300,
        width=1,
    )

    number_of_nodes = graph.number_of_nodes()

    if number_of_nodes < 30:
        return config

    if number_of_nodes < 200:
        return {
            **config,
            'node_size': 100,
            'font_size': 6,
            'dpi': 400,
            'width': 1,
        }

    return {
        **config,
        'node_size': 5,
        'font_size': 0.2,
        'dpi': 400,
        'width': 1,
    }


# TODO: set this properly
default_infra_edge_colors = [
    colors.orange,
    colors.yellow,
    colors.green,
]


def draw(
        model,
        solution=None,
        odpairs=True,
        infrastructures=True,
        flows=False,
        position_param='pos',
        with_labels=True,
        arrows=False,
        node_color=colors.gray_light,
        od_node_color=colors.blue,
        font_color='black',
        edge_color=colors.gray_dark,
        infra_edge_colors=None,
        figsize=None,
        infrastructure_scale_factor=2,
        odpair_scale_factor=2,
        **kwargs):
    """
    Draw a model's graph and its solution if applies.
    """
    is_graph = isinstance(model, nx.Graph)

    if is_graph:
        graph = model
    else:
        graph = model.graph

    positions = None
    calculated_fig_size = None

    draw_config = get_draw_config(graph)
    draw_config.update(kwargs)
    draw_config.pop('dpi')

    if position_param:
        positions = nx.get_node_attributes(graph, position_param)
        if not figsize:
            calculated_fig_size = calc_fig_size(positions.values())

    plt.figure(figsize=figsize or calculated_fig_size)

    if odpairs and not is_graph:
        odpairs = [(o, d) for o, d, _ in model.odpairs]
        origins, destinations = zip(*odpairs)

        odpair_draw_config = draw_config.copy()
        odpair_draw_config.update({
            'node_size': draw_config.get('node_size') * odpair_scale_factor,
        })

        for node_list, shape in [(origins, 'v'), (destinations, '^')]:
            nx.draw_networkx(
                graph,
                positions,
                nodelist=node_list,
                edgelist=[],
                node_color=od_node_color,
                with_labels=False,
                node_shape=shape,
                **odpair_draw_config,
            )

    if solution and not is_graph:
        solution_graph = model.apply_solution_to_graph(solution)

        if infrastructures:
            infra_colors = infra_edge_colors or default_infra_edge_colors
            infra_edges = [
                dict(edge=e, infra=v)
                for e, v in nx.get_edge_attributes(solution_graph, 'effective_infrastructure').items()
            ]
            edges_by_infra = group_by(infra_edges, 'infra')

            infra_draw_config = draw_config.copy()
            infra_draw_config.update({
                'width': draw_config.get('width') * infrastructure_scale_factor,
            })

            for infra, infra_edges in edges_by_infra.items():
                if str(infra) == '0':
                    continue

                nx.draw_networkx(
                    graph,
                    positions,
                    nodelist=[],
                    edgelist=[d['edge'] for d in infra_edges],
                    edge_color=infra_colors[int(infra) - 1],  # 0 is not drawn
                    with_labels=False,
                    **infra_draw_config,
                )

    # Draw final network
    nx.draw(
        graph,
        positions,
        with_labels=with_labels,
        arrows=arrows,
        node_color=node_color,
        font_color=font_color,
        edge_color=edge_color,
        **draw_config
    )


def draw_graph_to_file(filename, graph, *args, **kwargs):
    draw_config = get_draw_config(graph)
    draw_config.update(kwargs)

    dpi = draw_config.pop('dpi')

    draw(graph, *args, **draw_config)

    plt.savefig(filename, dpi=dpi)


def main(graph, args):
    draw_graph_to_file(args.output, graph)
