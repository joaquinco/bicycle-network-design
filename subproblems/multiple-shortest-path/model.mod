### Parameters ###

/* Nodes of graph */
set N;

/* Adjacency matrix: 1 if adjacent, 0 otherwise */
param G{N,N} binary;

/* Variable cost */
param C{i in N, j in N};

/* Origin destination pairs */
set OD := N cross N;
param DEMAND{OD};

### Variables ###

/* Flow on each arc for each OD pair */
var X{OD, N, N} >= 0;

### Objective ###

minimize user_cost:
  sum{(o, d) in OD} (
    sum{i in N, j in N} G[i, j] * C[i, j] * X[o, d, i, j]
  );

### Constraints ###

subject to flow_conservation {i in N, (o, d) in OD}:
  sum{j in N} X[o, d, i, j] - sum{l in N} X[o, d, l, i] = if i = o then DEMAND[o, d]
                                                          else if i = d then -DEMAND[o, d]
                                                          else 0;

subject to respect_graph {(o, d) in OD, i in N, j in N}: X[o, d, i, j] <= G[i, j] * DEMAND[o, d];

end;
