import numpy as np
from matplotlib import pyplot as plt

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

    fig, axs = plt.subplots(2, 2)
    axs = axs.flatten()

    for index, func in enumerate(funcs):
        ax = axs[index]
        ax.plot(domain, func(domain, m=m))
        ax.set_title(names[index])
        ax.set_xticks([m, 1])
        ax.set_xticklabels(['m', '1'])

        # ax.set_yticks([1])

    fig.suptitle('Alternatives of f')
    fig.savefig('f_catalog.png', dpi=300)


def main():
    draw_f_shapes()

main()
