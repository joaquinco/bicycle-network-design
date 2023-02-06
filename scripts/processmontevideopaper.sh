#!/bin/bash

path=$1

if [ -z $path ]; then
    echo "path is required as first argument"
    exit 1
fi

python scripts/processsensitivity.py \
    --demand-by-budget-breakpoint-count 10 \
    --draw-width 0.5 \
    --draw-skip-flows \
    --draw-skip-odpairs \
    --draw-skip-arrows \
    --draw-fig-width 8 \
    --draw-fig-height 6 \
    --draw-node-size 0.1 \
    --draw-skip-labels $@
