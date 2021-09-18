/**
 * Model file for the single level problem.
 *
 * Problem: Demand transfer optimization to bicycle from other means of transportation
 * by constructing infrastructures that reduce user cost of arc traversal.
 *
 * V6, changes over v5:
 * - Changes f_k implementation, uses v3.
 */

/*** Set definition ***/
/* Set of Arcs */
set A;

/* Set of Nodes */
set N;

/* Arcs starting from each node */
set A_OUT{N};

/* Arcs arriving to each node */
set A_IN{N};

/* Set of Infrastructures for each arc */
set I;

/* Set of origin-destination pairs */
set OD;

/* Index set J */
set J;

/*** Parameter definition ***/
/* Construction cost of infrastructure i on arc a */
param M{A,I} >= 0;

/* User cost of traversing arc a over infrastructure i */
param C{A,I} >= 0;

/* Origin and destinations nodes */
param ORIGIN{OD} in N;
param DESTINATION{OD} in N;

/* Construction Budget */
param B >= 0;

/* Demand transfer (P) and breakpoint (Q) parameters */
param P{OD,J} >= 0;
param Q{OD,J} >= 0;

/*** Variable definition ***/
/* Shortest path user cost for an OD pair */
var w{OD} >= 0;

/* If infrastructure i is active on arc a */
var y{A,I} binary;

/* Unitary flow over arc a for an OD pair */
var x{A,OD} >= 0;

/* Unitary flow over arc a, infrastructure i for an OD pair */ 
var h{A,OD,I} >= 0;

/* Decision variable that activates a value on P[OD,] and Q[OD,] */
var z{OD,J} binary;

/* the INFINITE value per od pair */
param INF{OD};

/* Actual demand transfered */
var demand_transfered;

/* Shortest path cost per j value, either w[k] or 0 */
var waux{OD,J} >= 0;
var wsink{OD, J} >= 0;

/*** Objective ***/
/* Maximize demand transfer to bicycle */
maximize demand_transfer_with_penalty: sum{k in OD} (-w[k] + sum{j in J} P[k,j] * z[k,j]);

/*** Constraints ***/
/* Cost of interest */
s.t. demand_transferer: demand_transfered = sum{k in OD, j in J} P[k,j] * z[k,j];

/* Activation of z */
s.t. activate_breakpoint {k in OD, j in J}: Q[k,j] * z[k,j]  >= waux[k,j];
s.t. toggle_waux {k in OD, j in J}: waux[k,j] <= z[k,j] * INF[k];
s.t. toggle_wsink {k in OD, j in J}: wsink[k, j] <= (1 - z[k, j]) * INF[k]; 
s.t. activate_waux{k in OD, j in J}: waux[k, j] + wsink[k, j] = w[k];

/* Activate at most one z per OD */
s.t. only_one_z {k in OD}: sum{j in J} z[k,j] = 1;

/* Assign shortest path cost per OD */
s.t. assign_wk{k in OD}: sum{a in A, i in I} C[a, i] * h[a, k, i] = w[k];

/* Respect Budget */
s.t. respect_budget: sum{a in A, i in I} M[a,i] * y[a,i] <= B;

/* Activate always one y per arc */
s.t. one_y_active {a in A}: sum{i in I} y[a,i] = 1;

/* Flow balance */
s.t. flow_balance {n in N, k in OD}: sum{a in A_OUT[n]} x[a, k] - sum{a in A_IN[n]} x[a, k] = if n = ORIGIN[k] then 1
            else if n = DESTINATION[k] then -1
            else 0;

/* x assignment from h */
s.t. x_assigned_from_h {a in A, k in OD}: x[a,k] = sum{i in I} h[a,k,i];

/* Restrict h to active infrastructures */
s.t. restrict_h_to_active_infras {a in A, k in OD, i in I}: h[a,k,i] <= y[a,i];

solve;

/*** OUTPUT ***/

printf: "\n";
printf: "---shortest_paths\n";
/* Shortest path cost */
printf: "origin,destination,shortest_path_cost\n";
for {k in OD} {
  printf: "%s,%s,%s\n", ORIGIN[k], DESTINATION[k], w[k];
}
printf: "---flows\n";
printf: "origin,destination,arc,infrastructure,flow\n";
for {k in OD} {
  for {a in A} {
    for {i in I: h[a,k,i] > 0} {
      printf: "%s,%s,%s,%s,%s\n", ORIGIN[k], DESTINATION[k], a,i, h[a,k,i];
    }
  }
}
printf: "---infrastructures\n";
printf: "arc,infrastructure,construction_cost\n";
for {a in A} {
  for {i in I: y[a,i] > 0 and M[a,i] > 0} {
    printf: "%s,%s,%s\n", a, i, M[a,i];
  }
}
printf: "---demand_transfered\n";
printf: "origin,destination,demand_transfered,z,j_value\n";
for {k in OD} {
  for {j in J: z[k,j] > 0} {
    printf: "%s,%s,%s,%s,%s\n", ORIGIN[k], DESTINATION[k], (sum {j2 in J} P[k,j2] * z[k,j2]), z[k,j], j;
  }
}
printf: "---total_demand_transfered\n";
printf: "total_demand_transfered\n";
printf: "%s\n", demand_transfered;
printf: "---budget_used\n";
printf: "budget_used\n";
printf: "%s\n", sum {a in A, i in I} M[a,i]*y[a,i];
printf: "---\n";

end;
