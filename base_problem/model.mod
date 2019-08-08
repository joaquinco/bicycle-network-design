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

/* Amount of origin destination pairs */
param K > 0 integer;

set KINDEX := 1..K;

param ORIG{KINDEX};
param DEST{KINDEX};
param DEMAND{KINDEX};

### Variables ###

/* Binary variable which is 1 if there is flow of bikes over each arch */
var X{N, N} binary;

/* Binary variable which is 1 if cycling infrastructure is built on each arch */
var Y{N, N} binary;

/* Variable which models the flow of users per OD pair on each arch where cycling
  infrastructure is built
 */
var FI{KINDEX, N, N};

/* Variable which models the flow of users per OD pair on each arch where cycling
  infrastructure is not built
*/
var FN{KINDEX, N, N};

### Objective ###

minimize user_cost:
  sum{k in KINDEX} (
    sum{i in N, j in N} G[i, j] * (CI[i, j] * FI[k, i, j] + CN[i, j] * FN[k, i, j])
  );

### Constraint ###

subject to build_or_not_build {i in N, j in N}: X[i, j] + Y[i, j] <= 1;
subject to fi_where_needed {i in N, j in N}:
  sum{k in KINDEX} FI[k, i, j] <= Y[i, j] * sum{k in KINDEX} DEMAND[k];
subject to fn_where_needed {i in N, j in N}:
  sum{k in KINDEX} FN[k, i, j] <= X[i, j] * sum{k in KINDEX} DEMAND[k];
subject to satisfy_demand {i in N, k in KINDEX}:
  sum{j in N} (FI[k, i, j] + FN[k, i, j]) - sum{l in N} (FI[k, l, i] + FN[k, l, i]) =
    if i = ORIG[k] then DEMAND[k]
    else if i = DEST[k] then -DEMAND[k]
    else 0;

subject to respect_lmax: sum{i in N, j in N} L[i, j] <= LMAX;
subject to positive_fi {i in N, j in N, k in KINDEX}: FI[k, i, j] >= 0;
subject to positive_fn {i in N, j in N, k in KINDEX}: FN[k, i, j] >= 0;
