import numpy as np

from .costs import calculate_user_cost


def normalize(y):
    """
    Normalize numpy vector to be between 0 and 1
    """
    return (y - y.min()) / (y.max() - y.min())


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
    y = normalize(y)

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


def get_breakpoint_index(w, breakpoints):
    """
    Given a decreasing list of breakpoints q_j
    returns the minimun index where q_j >= w or 0 otherwise.

    Note: This follows the definition of f_k
    """
    candidates = list(filter(lambda x: x[1] >= w, enumerate(breakpoints)))

    if not candidates:
        return 0

    return min(candidates, key=lambda x: x[1])[0]
