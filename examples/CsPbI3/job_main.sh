#/bin/bash
#BSUB -q 9242opa!
#BSUB -n 1
#BSUB -J gpumd
#BSUB -e err.txt

source /fs08/home/js_pansn/apps/anaconda3/bin/activate ase
python run_active.py