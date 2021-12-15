import math


def plane_distance(p1, p2):
    """
    Euclidean distance between two points,
    represented as tuples.
    """
    x, y = p1
    x1, y1 = p2

    return math.sqrt(
        (x - x1) ** 2 + (y - y1) ** 2
    )
