#!/bin/bash

: '
Scritp that generates scripts slurm jobs scripts for
every model file (*.pkl) under a directory specified
as a parameter.
'

if [ -z $1 ]; then
    echo "Instances path is required"
    exit 1
fi

instances_dir=$PWD/$1

THREAD_COUNT=${THREAD_COUNT:-16}
MAX_MEM=${MAX_MEM:-180000}
TIMEOUT_DAYS=${TIMEOUT_DAYS:-2}

TIMEOUT_SECONDS=$(echo "($TIMEOUT_DAYS * 24 - 1) * 60 * 60" | bc)
TIMEOUT_FORMATTED=$(echo "$TIMEOUT_DAYS * 24" | bc):00:00

cd $instances_dir

for pkl_file in $(ls *.pkl); do
    prefix=${pkl_file%.*}
    job_file=$prefix.sh
    solution_file=$prefix.sol.pkl


    cat > $job_file << EOL
#!/bin/bash

#SBATCH --job-name=$(echo "$pkl_file" | tr "/" "-")
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=$THREAD_COUNT
#SBATCH --mem=$MAX_MEM
#SBATCH --time=$TIMEOUT_FORMATTED
#SBATCH --mail-type=ALL
#SBATCH --mail-user=joaquin.correa@fing.edu.uy
#SBATCH --qos bigmem

timeout_seconds=$TIMEOUT_SECONDS
max_mem=$MAX_MEM
thread_count=$THREAD_COUNT
instances_dir=$instances_dir
model_file=$instances_dir/$pkl_file

EOL

	cat >> $job_file << 'EOL'
export BCNETWORK_CPLEX_OPTS=`cat <<EOC
set mip strategy file 3
set mip tolerances mipgap 0.01
set workmem $max_mem
EOC`

set -e

project_root=~/projects/bicycle-network-design/
run_dir=/scratch/joaquin.correa/run_$(date +"%Y%m%d%k%M%S")

export PYTHONPATH=${project_root}
source ~/.bashrc
pyenv-init
pyenv activate bcnetwork

mkdir -p $run_dir

cd $project_root
python -m bcnetwork solve \
      --parallelism $thread_count \
      --timeout $timeout_seconds \
      --output-dir $run_dir \
      --model $model_file \
      --solver cplex
cp $run_dir/* $instances_dir

EOL

    # Queues the job if not already
    if myqueue | grep "$prefix" ; then
    echo "Skipping batching $prefix since it's running already"
    else
        echo "Enqueuing job $job_file"
    sbatch $job_file
    fi
done

cd -
