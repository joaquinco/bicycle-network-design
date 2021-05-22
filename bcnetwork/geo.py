import math


def plane_distance(n1, n2, key='pos'):
    x, y = n1[key]
    x1, y1 = n2[key]

    return math.sqrt(
        (x - x1) ** 2 + (y - y1) ** 2
    )
