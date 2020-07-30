import math

def plane_distance(g, n1, n2, key='pos'):
  x, y = g.nodes[n1][key]
  x1, y1 = g.nodes[n2][key]

  return math.sqrt(
    (x - x1) ** 2 + (y - y1) ** 2
  )
