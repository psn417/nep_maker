#/bin/bash
#BSUB -q 6230r
#BSUB -n 1
#BSUB -J active_learning
#BSUB -e err.txt

source /fs08/home/js_pansn/apps/anaconda3/bin/activate ase
python run_active.py