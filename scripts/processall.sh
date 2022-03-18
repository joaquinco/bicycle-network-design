#!/bin/bash

set -e
set -x

: "
Perform processing over all instances generated in throuthough the
development of the project
"

export PYTHONPATH=$PWD

# Model choice, first run
runs_first_round=${RUNS_FIRST_ROUND:-data/comparison}

python scripts/processruns.py $runs_first_round

# Model choice, second run
runs_second_round=${RUNS_SECOND_ROUND:-data/comparison_2021_12_01}

python scripts/processruns.py $runs_second_round

# Sensibility
sensibility_data=${SENSIBILITY_DATA:-data/sensitivity_10_cplex/}

python scripts/processsensitivity.py $sensibility_data

# Montevideo runs
# Warning: runtimes and gap are hardcoded

montevideo_data=${MONTEVIDEO_DATA:-data/montevideo_v2}

./scripts/processcplexsol.sh $montevideo_data
python scripts/postprocesscplex.py $montevideo_data
python scripts/processsensitivity.py $montevideo_data --skip-instance-drawing \
    --demand-by-budget-breakpoint-count 10

# Regenerate doc resources
python scripts/docresources.py
