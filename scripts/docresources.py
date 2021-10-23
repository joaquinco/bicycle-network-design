import numpy as np
from matplotlib import pyplot as plt

import bcnetwork as bc
from functions import linear, inv_logit, exp, log


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
        log,
        exp,
    ]
    names = [
        'Lineal',
        'Logistic',
        'Logarithmic',
        'Exponential',
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


def main():
    draw_f_shapes()


main()
