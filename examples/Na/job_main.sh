#/bin/bash
#BSUB -q 6230r
#BSUB -n 1
#BSUB -J active_learning
#BSUB -e err.txt

module load anaconda/3
. /fs00/software/anaconda/3/etc/profile.d/conda.sh
conda activate ase

python run_active.py