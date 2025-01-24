#!/bin/bash
#BSUB -J vasp
#BSUB -n 4
#BSUB -q 6230r
#BSUB -e err

export I_MPI_ADJUST_REDUCE=3

mpiexec.hydra vasp_std
