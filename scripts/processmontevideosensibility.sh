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
    --draw-skip-legend \
    --draw-skip-arrows \
    --draw-fig-width 6 \
    --draw-fig-height 4 \
    --draw-node-size 0.1 \
    --draw-skip-labels $@

rm $path/montevideo*logit*1.6*.png

# Draw legend only in the logit 1.6
python scripts/processsensitivity.py \
    --demand-by-budget-breakpoint-count 10 \
    --draw-width 0.5 \
    --draw-skip-flows \
    --draw-skip-odpairs \
    --draw-skip-arrows \
    --draw-fig-width 6 \
    --draw-fig-height 4 \
    --draw-node-size 0.1 \
    --draw-skip-labels $@

rm $path/montevideo*0.1*.png

# Draw larger view for 0.1 budget factor
python scripts/processsensitivity.py \
    --demand-by-budget-breakpoint-count 10 \
    --draw-width 0.8 \
    --draw-skip-flows \
    --draw-skip-odpairs \
    --draw-skip-arrows \
    --draw-fig-width 8 \
    --draw-fig-height 5 \
    --draw-node-size 0.1 \
    --draw-skip-labels $@

