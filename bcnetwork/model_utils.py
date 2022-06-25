import numpy as np

from .costs import calculate_user_cost


def build_breakpoints(func, count, m=None, infrastructure_count=None):
    """
    Return list of breakpoints by evaluating func
    :count: times between m and 1.

    :param func: a function [0, 1] -> [m, 1]
    :param count: must be at least 2
    """

    if infrastructure_count is None and m is None:
        raise ValueError('Must provide m or infrastructure_count')

    m = m or calculate_user_cost(1, infrastructure_count - 1)

    x = np.linspace(m, 1, 10000)
    y = func(x)

    # Normalize y to [0,1].
    y = (y - y.min()) / (y.max() - y.min())

    interval = (y.max() - y.min()) / (count - 1)
    breakpoints = []

    # this should be close to 1, if not 1
    curr_threshold = y.max()
    for x_val, y_val in zip(x, y):
        if y_val <= curr_threshold:
            breakpoints.append((y_val, x_val))
            curr_threshold -= interval

    if len(breakpoints) < count:
        breakpoints.append((y[-1], x[-1]))

    breakpoints.reverse()

    return breakpoints
