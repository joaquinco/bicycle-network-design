#!/bin/bash

instances_dir=/clusteruy/home/joaquin.correa/jobs/bcnetwork/montevideo_v2
run_dir=/scratch/joaquin.correa/montevideo_v2

THREAD_COUNT=16
MAX_MEM=18000
TIMEOUT_DAYS=5
TIMEOUT_SECONDS=$(echo "$TIMEOUT_DAYS * 24 * 60 * 60" | bc)
TIMEOUT_FORMATTED=$(echo "$TIMEOUT_DAYS * 24" | bc):00:00

cd $instances_dir

for lp_file in $(ls *.lp); do
    prefix=${lp_file%.*}
    job_file=$prefix.sh
    cplex_file=$prefix.cplex
    log_file=$prefix.log
    solution_file=$prefix.sol

    if [ -f $solution_file ]; then
        echo "Skipping $prefix, solution already present"
        continue
    fi

    cat > $job_file << EOL
#!/bin/bash

#SBATCH --job-name=$(echo "$lp_file" | tr "/" "-")
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=$THREAD_COUNT
#SBATCH --mem=$MAX_MEM
#SBATCH --time=$TIMEOUT_FORMATTED
#SBATCH --mail-type=ALL
#SBATCH --mail-user=joaquin.correa@fing.edu.uy

mkdir -p $run_dir
cp $cplex_file $lp_file $run_dir
cd $run_dir
cplex -f $cplex_file
cp $log_file $solution_file $instances_dir
EOL

    cat > $cplex_file << EOL
set threads $THREAD_COUNT
set logfile $log_file
set mip display 2
set workmem $MAX_MEM
set timelimit $TIMEOUT_SECONDS
set benders strategy 3

read $lp_file
opt
write $solution_file
quit
EOL
    sbatch $job_file
done

cd -
