#!/bin/bash
#BSUB -J vasp
#BSUB -n 4
#BSUB -q 9242opa!
#BSUB -e err.txt
#BSUB -o out.txt

export I_MPI_ADJUST_REDUCE=3

mpiexec.hydra vasp_std
