#!/bin/bash


path=$1

if [ -z $path ]; then
    echo "path is required as first argument"
    exit 1
fi

python scripts/processsensitivity.py \
    --draw-fig-width 10 \
    --draw-fig-height 5 \
    --draw-skip-legend $@

rm $path/sioux_falls*0.4*linear*50*.png

# Draw legend only in instance 13
python scripts/processsensitivity.py \
    --draw-fig-width 10 \
    --draw-fig-height 5 \
    $@
