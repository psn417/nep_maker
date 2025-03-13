# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 10:18:20 2021

@author: PSN
"""

from ase.io import read
from nep_maker.active_learning import ActiveLearning


def get_gpumd_input(steps):
    input = f"""
replicate   2 2 2
potential   ../nep.txt
velocity    20
time_step   5

compute_extrapolation asi_file ../active_set.asi check_interval 10 gamma_low 5 gamma_high 10
dump_thermo 200
ensemble npt_mttk tri 0 0 temp 20 620
run         {steps}

compute_extrapolation asi_file ../active_set.asi check_interval 10 gamma_low 5 gamma_high 10
dump_thermo 200
ensemble npt_mttk tri 0 0 temp 620 20
run         {steps}

"""
    return input


atoms = read("gamma.vasp")

a = ActiveLearning()
a.max_structures_per_iteration = 20
a.input_gpumd = [get_gpumd_input(100000)]*4
a.atoms_gpumd = [atoms]*len(a.input_gpumd )
a.run()
