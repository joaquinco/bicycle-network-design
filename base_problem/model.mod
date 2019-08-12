### Parameters ###

/* Nodes of graph */
set N;

/* Adjacency matrix: 1 if adjacent, 0 otherwise */
param G{N,N};

/* Length of arcs */
param L{N, N};

/* Maximum available network to build */
param LMAX >= 0;

/* User cost of traversing cycling infrastructure */
param CI{i in N, j in N} := L[i, j] * 0.5;

/* User cost of traversing non cycling infrastructure */
param CN{i in N, j in N} := L[i, j] * 2.5;

/* Origin destination pairs */
set OD within (N cross N);
param DEMAND{OD};

### Variables ###

/* Binary variable which is 1 if there is flow of bikes over each arch */
var X{N, N} binary;

/* Binary variable which is 1 if cycling infrastructure is built on each arch */
var Y{N, N} binary;

/* Variable which models the flow of users per OD pair on each arch where cycling
  infrastructure is built
 */
var FI{OD, N, N};

/* Variable which models the flow of users per OD pair on each arch where cycling
  infrastructure is not built
*/
var FN{OD, N, N};

### Objective ###

minimize user_cost:
  sum{(o, d) in OD} (
    sum{i in N, j in N} G[i, j] * (CI[i, j] * FI[o, d, i, j] + CN[i, j] * FN[o, d, i, j])
  );

### Constraints ###

subject to build_or_not_build {i in N, j in N}: X[i, j] + Y[i, j] <= 1;
subject to constraint_y {i in N, j in N}:
  sum{(o, d) in OD} FI[o, d, i, j] <= Y[i, j] * sum{(o, d) in OD} DEMAND[o, d];
subject to constraint_x {i in N, j in N}:
  sum{(o, d) in OD} FN[o, d, i, j] <= X[i, j] * sum{(o, d) in OD} DEMAND[o, d];
subject to satisfy_demand {i in N, (o, d) in OD}:
  sum{j in N} (FI[o, d, i, j] + FN[o, d, i, j]) - sum{l in N} (FI[o, d, l, i] + FN[o, d, l, i]) =
    if i = o then DEMAND[o, d]
    else if i = d then -DEMAND[o, d]
    else 0;

subject to respect_lmax: sum{i in N, j in N} L[i, j] * Y[i, j] <= LMAX;
subject to positive_fi {i in N, j in N, (o, d) in OD}: FI[o, d, i, j] >= 0;
subject to positive_fn {i in N, j in N, (o, d) in OD}: FN[o, d, i, j] >= 0;

end;
