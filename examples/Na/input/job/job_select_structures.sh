#/bin/bash
#BSUB -q 75434090ib!
#BSUB -gpu "num=1"
#BSUB -n 1
#BSUB -J select
#BSUB -e err.txt
#BSUB -o out.txt

module purge
module load gcc/12.1.0 cuda/12.0.0
module load anaconda/3
. /fs00/software/anaconda/3/etc/profile.d/conda.sh
conda activate ase

export OMP_NUM_THREAD=8

python /fsb/home/jiansun/js_pansn/common/python_packages/nep_maker/nep_extrapolation/select_extend.py