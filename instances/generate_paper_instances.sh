#!/bin/bash

output_dir=$1
max_distance=3000
odpair_count=600
budget_factor=0.068

if [ -z $output_dir ]; then
    echo "output dir is required"
    exit 1
fi

mkdir -p $output_dir

: '
Presupuesto y función de transferencia fija.
Dos cantidades de puntos de quiebre, 10 y 20.
DOs cantidades de pares od, top 600 y top 3000.
'
generate_instances() {
    python scripts/runmontevideo.py \
        --function $1 \
        --name-suffix 10_breakpoints_${odpair_count}_od \
        --breakpoint-count 10 \
        --max-distance $max_distance $output_dir \
        --odpair-count $odpair_count \
        --budget-factor $budget_factor
}

# Equivalencia con el presupuesto asignado en Montevideo.
# (0.40 + 2 * 0.63 + 4 * 0.24) / 100 = 0.026
# Dicho valor multiplicado por dos porque ahi se construye ida y vuelta.

generate_instances inv_logit
