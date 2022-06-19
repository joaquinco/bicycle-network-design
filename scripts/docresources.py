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
        'Linear',
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

    # fig.tight_layout()
    fig.suptitle(
        'Alternativas para el modelado de transferencia de demanda', y=0.98)
    fig.savefig(get_fig_output_path('f_catalog.png'), dpi=300)


def draw_f_example():
    """
    Draw an example of how functions are represented in the
    lineal formulation.
    """
    m = 0.4
    domain = np.linspace(m, 1, 30)
    demand = 750

    fig, ax = plt.subplots()

    func = inv_logit
    ax.plot(domain, func(domain, m=m), color=bc.colors.sky_blue, label='Real')

    breakpoints = bc.model_utils.build_breakpoints(func, 6, m)
    breakpoints.reverse()

    for i, point in enumerate(breakpoints):
        y, x = point
        label = None

        if i == 0:
            prev_x = m - 0.05
        else:
            prev_x = breakpoints[i - 1][1]

        if i == len(breakpoints) - 1:
            label = 'Repr.'

        ax.plot([prev_x, x], [y, y], color=bc.colors.gray_dark, label=label)

    ys, xs = zip(*breakpoints)

    ax.tick_params(axis='y', which='both', labelrotation=45)
    num_formatter = ticker.FormatStrFormatter('%.2f')
    ax.xaxis.set_major_formatter(num_formatter)

    ax.set_yticks(ys)
    ax.set_yticklabels([format(d, '.2f') for d in demand * np.array(ys)])
    ax.set_xticks(xs)

    ax.set_xlabel('Q - Proporción de mejoras sobre el costo del camino más corto base')
    ax.set_ylabel('P - Demanda transferida')
    ax.legend()

    fig.suptitle(
        f'f real y su representación para una demanda total de {demand}', y=0.98,
    )
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

    fig, ax = plt.subplots(figsize=(7, 8))

    bc.draw.draw(model.graph, ax=ax)
    draw_demand = functools.partial(
        bc.draw.draw_demand_weight, alpha=0.2, circle_factor=130)
    draw_demand(ax, model)

    ax.set_title('Orígenes y Destinos')
    ax.margins(0.3, 0.25)
    fig.savefig(
        get_fig_output_path('sioux_falls_demand.png'),
        dpi=300,
        bbox_inches='tight',
    )


def draw_montevideo_data():
    """
    Draw demand data of Montevideo instance and what we filtered out.
    """
    pass


def main():
    draw_f_shapes()
    draw_f_example()
    draw_sioux_falls()


main()
