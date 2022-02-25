#!/bin/bash

output_dir=montevideo/
breakpoint_count=10
max_distance=5000

mkdir -p $output_dir

generate_instances() {
    python scripts/runmontevideo.py \
        --function $1 \
        --name-suffix $1 \
        --breakpoint-count $breakpoint_count \
        --max-distance $max_distance $output_dir
}

generate_instances linear
generate_instances inv_logit

for dat_file in $(ls $output_dir/*.dat); do
    glpsol -m exact/single_level.mod -d $dat_file --wlp ${dat_file%.*}.lp --check
done
