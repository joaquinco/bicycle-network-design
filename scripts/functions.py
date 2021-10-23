import numpy as np

DEFAULT_M = 0.4


def linear(p, m=DEFAULT_M):
    """
    Linear version of f
    """
    return (p - 1) / (m - 1)


def inv_logit(p, m=DEFAULT_M, rate=15):
    """
    Logit version of f
    """
    p = p - (1 + m) / 2
    p *= rate

    return 1 - 1 / (1 + np.exp(-p))


def log(p, m=DEFAULT_M, rate=1):
    return 1 - np.log(p) * rate - np.log(m)


def exp(p, m=DEFAULT_M, rate=1):
    return 1 - np.exp2(p) * rate
