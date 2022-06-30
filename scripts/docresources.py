import functools
import os

import numpy as np
from matplotlib import pyplot as plt, ticker

import bcnetwork as bc
from functions import linear, inv_logit, sad, happy


def get_fig_output_path(filename):
    return os.path.join('thesis/resources', filename)


def draw_f_shapes():
    """
    Draw the functions that will be used to pick
    breakpoints.
    """
    m = 0.4
    domain = np.linspace(m, 1, 30)

    funcs = [
        linear,
        inv_logit,
        sad,
        happy,
    ]
    names = [
        'Lineal',
        'Logística',
        'Concavidad negativa',
        'Concavidad positiva',
    ]
    colors = [
        bc.colors.blue,
        bc.colors.orange,
        bc.colors.yellow,
        bc.colors.green,
    ]

    fig, axs = plt.subplots(2, 2)
    # Make room for the figure title
    fig.subplots_adjust(top=0.85)
    axs = axs.flatten()

    for index, func in enumerate(funcs):
        ax = axs[index]
        ax.plot(domain, func(domain, m=m), color=colors[index])
        ax.set_title(names[index], size='small')
        ax.set_xticks([m, 1])
        ax.set_xticklabels(['m', '1'])
        ax.set_yticks([1])

    fig.savefig(get_fig_output_path('f_catalog.png'), dpi=300)


def draw_f_example():
    """
    Draw an example of how functions are represented in the
    lineal formulation.
    """
    m = 0.4
    demand = 750
    base_shortet_path = 1000
    domain = np.linspace(m, 1, 30)

    fig, ax = plt.subplots()

    func = functools.partial(inv_logit, m=m)

    ax.plot(
        domain * base_shortet_path,
        bc.model_utils.normalize(func(domain)) * demand,
        color=bc.colors.sky_blue, label='Real',
    )

    breakpoints = bc.model_utils.build_breakpoints(func, 6, m)
    breakpoints.reverse()
    ys, xs = zip(*breakpoints)
    transfers = np.array(ys) * demand
    improvements = np.array(xs) * base_shortet_path

    absolute_breakpoints = list(zip(transfers, improvements))

    for i, point in enumerate(absolute_breakpoints):
        y, x = point
        label = None

        if i == 0:
            prev_x = (m - 0.05) * base_shortet_path
        else:
            prev_x = absolute_breakpoints[i - 1][1]

        if i == len(absolute_breakpoints) - 1:
            label = 'Repr.'

        ax.plot([prev_x, x], [y, y], color=bc.colors.gray_dark, label=label)

    ax.tick_params(axis='y', which='both', labelrotation=45)

    num_formatter = ticker.FormatStrFormatter('%.2f')
    ax.xaxis.set_major_formatter(num_formatter)

    transfers.sort()
    ax.set_yticks(transfers)
    ax.set_yticklabels([format(d, '.1f') for d in transfers])
    ax.set_xticks(improvements)
    ax.set_xticklabels([format(d, '.1f') for d in improvements])

    ax.set_xlabel(
        'Q - Costo del camino más corto')
    ax.set_ylabel('P - Demanda transferida')
    ax.legend()

    # f'Real f and its representation for a total demand of {demand}', y=0.98)
    fig.savefig(get_fig_output_path('f_example.png'), dpi=300)


def draw_sioux_falls():
    """
    Draw basic sioux falls network
    """
    base_path = 'instances/sioux-falls'
    nodes_file = os.path.join(base_path, 'nodes.csv')
    arcs_file = os.path.join(base_path, 'arcs.csv')
    demands_file = os.path.join(base_path, 'origin_destination.csv')
    model = bc.model.Model(nodes_file=nodes_file,
                           arcs_file=arcs_file, odpairs_file=demands_file)

    fig, ax = plt.subplots(figsize=(7, 8))

    for n1, n2 in model.graph.edges():
        model.graph.edges[n1, n2]['user_cost'] = int(
            model.graph.edges[n1, n2]['user_cost'])

    bc.draw.draw(model, ax=ax, edge_weight_label='user_cost',
                 legend_location='lower right')

    fig.savefig(get_fig_output_path('sioux_falls_odpairs.png'),
                dpi=300, bbox_inches='tight')

    fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(
        10, 6), constrained_layout=True)
    ax1, ax2 = axs

    draw_demand = functools.partial(
        bc.draw.draw_demand_weight, alpha=0.2, circle_factor=130)
    margins = (0.32, 0.25)

    bc.draw.draw(model.graph, ax=ax1, margins=margins)
    draw_demand(ax1, model, destination_color=None)

    bc.draw.draw(model.graph, ax=ax2, margins=margins)
    draw_demand(ax2, model, origin_color=None)

    fig.savefig(
        get_fig_output_path('sioux_falls_demand.png'),
        dpi=300,
    )


def draw_montevideo_data():
    """
    Draw demand data of Montevideo instance and what we filtered out.
    """
    model = bc.model.Model(
        nodes_file='instances/montevideo/nodes.csv',
        arcs_file='instances/montevideo/arcs.csv',
    )

    fig, ax = plt.subplots(constrained_layout=True)
    bc.draw.draw(model.graph, ax=ax, node_size=0.5, width=1, with_labels=False)

    fig.savefig(get_fig_output_path('montevideo_simple.png'), dpi=300)


def main():
    draw_f_shapes()
    draw_f_example()
    draw_sioux_falls()
    draw_montevideo_data()


main()
