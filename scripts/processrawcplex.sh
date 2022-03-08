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
    basename=${sol_file%.*}
    new_output=$basename.sol.out
    model=$basename.pkl
    sol=$basename.sol.pkl
    if [ ! -f $new_output ]; then
        ( cat $basename.log ; python scripts/processcplexsol.py --model $basename.pkl $basename.sol ) > $new_output
        python -c "import bcnetwork as bc; bc.solution.Solution(stdout_file=\"${new_output}\").save(\"$sol\")"
    fi
done
