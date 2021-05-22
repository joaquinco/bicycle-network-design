import networkx as nx
import matplotlib.pyplot as plt


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
    Caluclates fig size depending on shape and node count
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


def draw_graph(
        graph,
        position_param='pos',
        with_labels=True,
        arrows=False,
        node_color='#67ccfc',
        font_color='black',
        edge_color='#9e9e9e',
        figsize=None,
        **kwargs):
    """
    Draw graph using matplotlib.
    """
    positions = None
    calculated_fig_size = None

    if position_param:
        positions = nx.get_node_attributes(graph, position_param)
        if not figsize:
            calculated_fig_size = calc_fig_size(positions.values())

    f = plt.figure(figsize=figsize or calculated_fig_size)

    nx.draw(
        graph,
        positions,
        with_labels=with_labels,
        arrows=arrows,
        node_color=node_color,
        font_color=font_color,
        edge_color=edge_color,
        **kwargs
    )


def draw_graph_to_file(filename, graph, *args, **kwargs):
    config = get_draw_config(graph)
    dpi = config.pop('dpi')

    draw_graph(graph, *args, **{**config, **kwargs})

    plt.savefig(filename, dpi=dpi)


def main(graph, args):
    draw_graph_to_file(args.output, graph)
