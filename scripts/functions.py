import numpy as np

DEFAULT_M = 0.4


def get_logit_rate(m):
    """
    Logit function rate varies with m
    so that edges are close to 0 and 1
    """
    return 5 / (1 - m)


def linear(p, m=DEFAULT_M):
    """
    Linear version of f
    """
    return (p - 1) / (m - 1)


def inv_logit(p, m=DEFAULT_M):
    """
    Logit version of f
    """
    rate = get_logit_rate(m)
    p = p - (1 + m) / 2
    p *= rate * 2

    return 1 / (1 + np.exp(p))


def sad(p, m=DEFAULT_M):
    """
    One part of the logit function
    """
    rate = get_logit_rate(m)
    p = p - 1
    p *= rate

    return 2 / (1 + np.exp(p)) - 1


def happy(p, m=DEFAULT_M):
    """
    One part of the logit function
    """
    rate = get_logit_rate(m)
    p = p - m
    p *= rate

    return 2 / (1 + np.exp(p))
