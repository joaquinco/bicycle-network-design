import numpy as np
from matplotlib import pyplot as plt, ticker

import bcnetwork as bc
from functions import linear, inv_logit, sad, happy


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
        'Logistic',
        'Concave down',
        'Concave up',
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
    fig.suptitle('Demand mode shift modeling alternatives', y=0.98)
    fig.savefig('f_catalog.png', dpi=300)


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

    ax.set_xlabel('Q - Base shortest path improvements')
    ax.set_ylabel('P - Demand transfered')
    ax.legend()

    fig.suptitle(
        f'Real f and its representation for a total demand of {demand}', y=0.98)
    fig.savefig('f_example.png', dpi=300)


def main():
    draw_f_shapes()
    draw_f_example()


main()
