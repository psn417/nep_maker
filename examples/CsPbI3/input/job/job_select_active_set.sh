#/bin/bash
#BSUB -q 75434090ib!
#BSUB -gpu "num=1"
#BSUB -n 1
#BSUB -J select
#BSUB -e err.txt
#BSUB -o out.txt

module purge
module load gcc/12.1.0 cuda/12.0.0

export OMP_NUM_THREAD=8

source /fs08/home/js_pansn/apps/anaconda3/bin/activate ase
python /fs08/home/js_pansn/python_packages/nep_maker/nep_active/select_active.py