#!/bin/bash

# Given a CPLEX solution and output file, creates
# a concatenation of the output and the bcnetwork readable
# format of the solution file.

set -e

if [ -z $1 ]; then
    echo "Usage $0 <cplex_runs_dir>"
    exit 1
fi

dir=$1

export PYTHONPATH=$PWD

for sol_file in $(ls $dir/*.sol); do
    base_path=${sol_file%.*}
    new_output=$base_path.sol.out
    model=$base_path.pkl
    sol=`dirname $base_path`/solution_`basename $base_path`.pkl

    if [ ! -f $new_output ]; then
        echo "processing $base_path"
        ( cat $base_path.log ; python scripts/processcplexsol.py --model $model $base_path.sol ) > $new_output
        python -c "import bcnetwork as bc; bc.solution.Solution(stdout_file=\"${new_output}\").save(\"$sol\")"
    else
        echo "skipping $base_path"
    fi
done
