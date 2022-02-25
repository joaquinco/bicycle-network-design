#!/bin/bash

instances_dir=montevideo
THREAD_COUNT=39
MAX_MEM=120000
# 5 days
TIMEOUT_DAYS=5
TIMEOUT_SECONDS=$(echo "$TIMEOUT_DAYS * 24 * 60 * 60" | bc)
TIMEOUT_FORMATTED=$(echo "$TIMEOUT_DAYS * 24" | bc):00:00

for lp_file in $(ls $instances_dir/*.lp); do
    prefix=${lp_file%.*}
    job_file=$prefix.sh
    cplex_file=$prefix.cplex
    log_file=$prefix.log
    solution_file=$prefix.sol

    cat > $job_file << EOL
#!/bin/bash

#SBATCH --job-name=$(echo "$lp_file" | tr "/" "-")
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=$THREAD_COUNT
#SBATCH --mem=$MAX_MEM
#SBATCH --time=$TIMEOUT_FORMATTED
#SBATCH --mail-type=ALL
#SBATCH --mail-user=joaquin.correa@fing.edu.uy

cplex -f $cplex_file
EOL

    cat > $cplex_file << EOL
set threads '$THREAD_COUNT'
set logfile '$log_file'
set mip display 2
set workmem $MAX_MEM
set timelimit $TIMEOUT_SECONDS

read '$lp_file'
opt
write '$solution_file'
quit
EOL
    sbatch $job_file
done
