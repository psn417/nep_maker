from ase.io import read
from nep_maker.active_learning import ActiveLearning


def get_gpumd_input(P, T):
    input = f"""
replicate   4 4 4
potential   ../nep.txt
velocity    {T}
time_step   1
compute_extrapolation asi_file ../active_set.asi check_interval 10 gamma_low 2 gamma_high 20

ensemble npt_mttk iso {P} {P} temp {T} {T}
run         50000
"""
    return input


atoms = read("Na.xyz")

a = ActiveLearning()
a.max_structures_per_iteration = 50
a.input_gpumd = [get_gpumd_input(0, T) for T in range(300, 501, 50)]
a.atoms_gpumd = [atoms] * len(a.input_gpumd)
a.run()
