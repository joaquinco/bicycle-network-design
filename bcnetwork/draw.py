from collections import defaultdict
import itertools
import logging

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm

import networkx as nx

from .colors import colors
from .misc import group_by
from .model import Model
from .solution import Solution

logger = logging.getLogger(__name__)


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


# We should not need more than 5 colors
default_infra_colors = [
    colors.orange,
    colors.yellow,
    colors.green,
    colors.violet,
    colors.gray_dark,
]

# Matplotlib marker shapes took from:
# https://matplotlib.org/stable/api/markers_api.html
shapes = [
    'o', 'v', '^', '>', '<', 's', 'p', '*', 'X', 'D', 'd', '|', '_',
]

odpair_colors = list(map(lambda c: [c], itertools.chain.from_iterable(
    cm.get_cmap(cmap_name).colors for cmap_name in ['Pastel1', 'Paired', 'Accent', 'Set2', 'Set3']
)))


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
        font_color='black',
        edge_color=colors.gray_light,
        infra_edge_colors=None,
        flow_color=colors.blue,
        figsize=None,
        infrastructure_scale_factor=2,
        odpair_scale_factor=2,
        odpair_filter=None,
        odpair_separate=False,
        edge_weight_label=None,
        flow_scale_factor=3,
        **kwargs):
    """
    Draw a model's graph and its solution if applies.

    Modes:
    1- graph only: pass in a model and or a graph.
    2- model and odpairs: pass in a model and set odpairs=True.
       They can be drawn in two ways: play around with odpair_separate
    3- model and solution: pass in a model and a solution. About the solution, the infrastructures
      and flows can be drawn.

    Filtering odparis:
    On modes 2 and 3, if odpair_filter is passed it must be a container to filter odpairs that belongs to that
    container using the in python keyword.

    In order to draw labels for edges, use the :edge_weight_label: by specifying one
    attribute of the edges to use as lable.
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

    ax = kwargs.get('ax')
    fig = ax.figure if ax else plt.figure()
    fig.set(size_inches=figsize or calculated_fig_size, clip_on=True)

    def include_odpair(
        odpair): return not odpair_filter or odpair in odpair_filter

    if odpairs and not is_graph:
        odpairs = [(o, d)
                   for o, d, _ in model.odpairs if include_odpair((o, d))]

        odpair_draw_config = draw_config.copy()
        odpair_draw_config.update({
            'node_size': draw_config.get('node_size') * odpair_scale_factor,
        })

        if odpair_separate:
            # Draw each origin destination pair with its own style: color and shape
            logger.warning('Can draw up to %s distinct od pair color/shapes',
                           len(shapes) * len(odpair_colors))
            odpair_shapes_colors = itertools.product(
                shapes, odpair_colors, repeat=1)

            for o, d in odpairs:
                od_shape, od_color = next(odpair_shapes_colors)
                nx.draw_networkx(
                    graph,
                    positions,
                    nodelist=[o, d],
                    edgelist=[],
                    node_color=od_color,
                    with_labels=False,
                    node_shape=od_shape,
                    **odpair_draw_config,
                )
        else:
            # Draw all origins with the same shape and all destinations with another same shape.
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
                    node_color=odpair_colors[0],
                    with_labels=False,
                    node_shape=shape,
                    **odpair_draw_config,
                )

    if solution and not is_graph:
        solution_graph = model.apply_solution_to_graph(solution)

        if infrastructures:
            infra_colors = infra_edge_colors or default_infra_colors
            infra_edges = [
                dict(edge=e, infra=v)
                for e, v in nx.get_edge_attributes(solution_graph, 'effective_infrastructure').items()
            ]
            edges_by_infra = group_by(infra_edges, 'infra')

            infra_draw_config = {
                **draw_config,
                'width': draw_config.get('width') * infrastructure_scale_factor,
            }

            edges_by_infra = sorted(
                edges_by_infra.items(), key=lambda entry: entry[0])

            for infra, infra_edges in edges_by_infra:
                if str(infra) == '0':
                    continue

                infra_color = infra_colors[int(infra) - 1]  # 0 is not drawn

                nx.draw_networkx(
                    graph,
                    positions,
                    edgelist=[d['edge'] for d in infra_edges],
                    edge_color=infra_color,
                    with_labels=False,
                    **infra_draw_config,
                )

        if flows and solution.data.flows:
            sol_flows = solution.data.flows
            arcs_by_id = {graph.edges[o, d]['key']                          : (o, d) for o, d in graph.edges()}
            demand_transfered_by_od = {
                (e.origin, e.destination): e.demand_transfered
                for e in solution.data.demand_transfered
            }

            flow_by_edge = defaultdict(lambda: 0)
            for flow in sol_flows:
                # Must convert to string because I forgot to set the schema for flows
                # when loading solutions
                if not include_odpair((str(flow.origin), str(flow.destination))):
                    continue
                flow_by_edge[arcs_by_id[flow.arc]] += (
                    flow.flow *
                    demand_transfered_by_od[(flow.origin, flow.destination)]
                )

            flow_edges, weights = zip(*flow_by_edge.items())

            max_flow = max(weights)
            min_flow = min(weights)
            min_flow_width = draw_config.get('width')
            max_flow_width = min_flow_width * flow_scale_factor

            if min_flow == max_flow:
                def normalize_flow(w): return 1
            else:
                def normalize_flow(w): return (
                    w - min_flow) / max(1, max_flow - min_flow)

            def get_flow_width(z): return z * (max_flow_width -
                                               min_flow_width) + min_flow_width

            weights = list(map(
                get_flow_width,
                map(normalize_flow, weights),
            ))

            flow_draw_config = draw_config.copy()
            flow_draw_config['width'] = weights

            nx.draw_networkx(
                graph,
                positions,
                nodelist=[],
                edgelist=flow_edges,
                edge_color=flow_color,  # 0 is not drawn
                with_labels=False,
                **flow_draw_config,
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

    if edge_weight_label:
        edge_labels = {
            (n1, n2): graph.edges[n1, n2][edge_weight_label]
            for n1, n2 in graph.edges()
        }

        nx.draw_networkx_edge_labels(
            graph,
            positions,
            edge_labels=edge_labels,
        )


def main(args):
    """
    Draw subcommand entrypoint
    """
    if args.model.endswith('yaml') or args.model.endswith('yml'):
        model = Model.load_yaml(args.model)
    else:
        model = Model.load(args.model)
    solution = Solution.load(args.solution) if args.solution else None

    draw_config = get_draw_config(model.graph)
    dpi = draw_config.pop('dpi')

    draw(
        model,
        solution=solution,
        odpairs=args.odpairs,
        infrastructures=args.infrastructures,
        flows=args.flows,
    )

    plt.savefig(args.output, dpi=dpi)
