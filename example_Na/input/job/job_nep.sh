#/bin/bash
#BSUB -q 75434090ib!
#BSUB -gpu "num=1"
#BSUB -n 1
#BSUB -J nep

module purge
module load gcc/12.1.0 cuda/12.0.0

nep