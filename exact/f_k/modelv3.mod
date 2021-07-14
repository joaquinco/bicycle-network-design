

set J;
param P{J} >= 0;
param Q{J} >= 0;

param W >= 0;

param M := 1000;

var y{J} binary;
var waux{J} >= 0;
var wsink{J} >= 0;

maximize demand_transfered: sum {j in J} P[j] * y[j];

s.t. respect_breakpoint {j in J}: Q[j] >= waux[j];
s.t. assign_waux {j in J}: waux[j] + wsink[j] = W;
s.t. activate_waux {j in J}: waux[j] <= M * y[j];
s.t. activate_wsink {j in J}: wsink[j] <= M * (1 - y[j]);
s.t. single_y: sum {j in J} y[j] = 1;
