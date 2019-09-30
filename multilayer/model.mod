### Parameters ###

/* Nodes of graph */
set N;
set K;

/* Adjacency matrix: 1 if adjacent, 0 otherwise */
param G{N,N} binary;

/* Length of arcs */
param L{N, N} >= 0;

/* Maximum available network to build */
param LMAX{K} >= 0;

/* Cost modifier for each layer, layer 1 is 1 and layer N should be less */
param COSTMODIFIER{K};

/* User cost of traversing cycling infrastructure */
param C{k in K, i in N, j in N} := L[i, j] * COSTMODIFIER[k];

/* Origin destination pairs */
set OD within (N cross N);
param DEMAND{OD};

### Variables ###

/* Binary variable that tells on which layer the flows lays */
var X{k, N, N} binary;

/* Variable which models where the flow from origin to destination goes through */
var F{OD, N, N} >= 0;

### Objective ###

minimize user_cost:
  sum{(o, d) in OD} (
    sum{k in K} (
      sum{i in N, j in N} G[i, j] * F[o, d, i, j] * C[k, i, j] * X[k, i, j]
    );
  )

### Constraints ###

subject to at_most_one_layer_selected {i in N, j in N}: sum{k in K} X[k, i, j] <= 1;

subject to satisfy_demand {i in N, (o, d) in OD}:
  sum{j in N} F[o, d, i, j] - sum{l in N} F[o, d, l, i] =
    if i = o then DEMAND[o, d]
    else if i = d then -DEMAND[o, d]
    else 0;

subject to choose_one_layer {i in N, j in N}: sum{k in K} X[k, i, j] <= 1;

subject to respect_lmax {k in K}: sum{i in N, j in N} L[k, i, j] * X[k, i, j] <= LMAX[k];

subject to respect_graph_x {i in N, j in N, k in K}: X[k, i, j] <= G[i, j];

end;
