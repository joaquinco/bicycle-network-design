/**
 * Model file for the single level problem.
 *
 * Problem: Demand transfer optimization to bicycle from other means of transportation
 * by constructing infrastructures that reduce user cost of arc traversal.
 */


/*** Set definition ***/
/* Set of Arcs */
set A;

/* Set of Nodes */
set N;

/* Set of Infrastructures for each arc */
set I;

/* Set of origin-destination pairs */
set OD within N cross N;

/* Index set J */
set J;

/*** Parameter definition ***/
/* Construction Budget */
param B >= 0;

/* Construction cost of infrastructure i on arc a */
param M{A,I} >= 0;

/* User cost of traversing arc a over infrastructure i */
param C{A,I} >= 0;

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
var z{OD,J} >= 0 <= 1;

/*** Objective ***/
/* Maximize demand transfer to bicycle */
maximize demand_transfer: sum{k in OD, j in J} P[k,j] * z[k,j];


/*** Constraints ***/
/* Activation of z */
s.t. activate_z {k in OD, j in J}: Q[k,j] * z[k,j] <= w[k];

/* Activate at most one z per OD */
s.t. at_most_one_z {k in OD}: sum{j in J} z[k,j] = 1;

/* Respect Budget */
s.t. respect_budget: sum{a in A, i in I} M[a,i] * y[a,i] <= B;

/* Activate always one y per arc */
s.t. one_y_active {a in A}: sum{i in I} y[a,i] = 1;

/* Flow balance */


/* x assignment from h */
s.t. x_assigned_from_h {a in A, k in OD}: x[a,k] = sum{i in I} h[a,k,i];

/* Restrict h to active infrastructures */
s.t. restrict_h_to_active_infras {a in A, k in OD, i in I}: h[a,k,i] <= y[a,i];
