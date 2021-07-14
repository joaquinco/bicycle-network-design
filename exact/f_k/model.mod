

set J;
param P{J} >= 0;
param Q{J} >= 0;

param W >= 0;

var y{J} binary;

maximize demand_transfered: sum {j in J} P[j] * y[j];

s.t. respect_breakpoint {j in J}: Q[j] >= W * y[j];
s.t. single_y: sum {j in J} y[j] = 1;
