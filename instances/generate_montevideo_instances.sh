#!/bin/bash

output_dir=$1
breakpoint_count=10
max_distance=5000

if [ -z $output_dir ]; then
    echo "output dir is required"
    exit 1
fi

mkdir -p $output_dir

generate_instances() {
    python scripts/runmontevideo.py \
        --function $1 \
        --name-suffix $1 \
        --breakpoint-count $breakpoint_count \
        --max-distance $max_distance $output_dir
    python scripts/runmontevideo.py \
        --function $1 \
        --name-suffix $1_0.4_budget_factor \
        --breakpoint-count $breakpoint_count \
        --max-distance $max_distance $output_dir \
        --budget-factor 0.4
    python scripts/runmontevideo.py \
        --function $1 \
        --name-suffix $1_1.6_budget_factor \
        --breakpoint-count $breakpoint_count \
        --max-distance $max_distance $output_dir \
        --budget-factor 1.6
    python scripts/runmontevideo.py \
        --function $1 \
        --name-suffix $1_0.1_budget_factor \
        --breakpoint-count $breakpoint_count \
        --max-distance $max_distance $output_dir \
        --budget-factor 0.1
}

# Equivalencia con el presupuesto asignado en Montevideo.
# (0.40 + 2 * 0.63 + 4 * 0.24) / 100 = 0.026
# Dicho valor multiplicado por dos porque ahi se construye ida y vuelta.

generate_instances linear
generate_instances inv_logit

for dat_file in $(ls $output_dir/*.dat); do
glpsol -m exact/single_level.mod -d $dat_file --wlp ${dat_file%.*}.lp --check
done
