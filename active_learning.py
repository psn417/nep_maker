import os
import time
import random
import ase.io
import yaml
from .print_block import print_block
from .task_pool import Pool
from .task import vasp_task, gpumd_task, nep_task, Task
from pynep.io import load_nep, dump_nep


class active_learning:
    def __init__(self):
        self.path = os.getcwd()
        self.input_gpumd = []
        self.max_structures_per_iteration = 9999

    def load_inputs(self):
        os.chdir(self.path)
        if os.path.exists("input/gpumd"):
            os.chdir("input/gpumd")
            if len(os.listdir()) != 0:
                self.input_gpumd = []
            for ii in os.listdir():
                with open(ii) as f:
                    self.input_gpumd.append(f.read())
        os.chdir(self.path)

        with open("input/vasp.yaml") as f:
            self.input_vasp = yaml.safe_load(f)
        with open("input/run.in") as f:
            self.input_gpumd = f.read()
        with open("input/nep.in") as f:
            self.input_nep = f.read()

        with open("job/job_vasp.sh") as f:
            self.job_vasp = f.read()
        with open("job/job_gpumd.sh") as f:
            self.job_gpumd = f.read()
        with open("job/job_nep.sh") as f:
            self.job_nep = f.read()
        with open("job/job_maxvol.sh") as f:
            self.job_maxvol = f.read()

    def run(self):
        iter_num = 0
        while True:
            t1 = time.time()
            print_block(f"Iter-{iter_num} begins.")

            i = self.iter(iter_num)
            if i == 0:
                break

            t2 = time.time()
            print_block(f"Iter-{iter_num} done! Takes {int((t2 - t1) / 60)} minutes.")
            iter_num += 1

    def iter(self, iter_num):
        os.chdir(self.path)
        self.load_inputs()
        dir_name = "iter_" + str(iter_num)
        os.mkdir(dir_name)
        os.chdir(dir_name)

        scf_traj = []

        if iter_num == 0:
            if os.path.exists("../train.xyz"):
                pass
            elif os.path.exists("../init_structures.xyz"):
                scf_traj = ase.io.read("../init_structures.xyz", index=":")
                scf_traj = self.run_vasp(scf_traj)
                dump_nep(scf_traj, "../train.xyz")
            else:
                raise Exception("You need to provide initial structures!")
        else:
            scf_traj = load_nep("../to_add.xyz")
            scf_traj = self.run_vasp(scf_traj)
            dump_nep(scf_traj, "scf.xyz")
            os.system("cat scf.xyz >> ../train.xyz")

        self.run_nep()
        self.select_active_set()
        large_gamma_structures = self.run_gpumd()
        if len(large_gamma_structures) == 0:
            return 0
        if len(large_gamma_structures) > self.max_structures_per_iteration:
            random.shuffle(large_gamma_structures)
            large_gamma_structures = large_gamma_structures[
                : self.max_structures_per_iteration
            ]

        self.select_structures()

        return 1

    def select_active_set(self):
        os.mkdir("select_active_set")
        os.chdir("select_active_set")
        os.system("cp ../../nep.txt .")
        os.system("cp ../../train.xyz .")
        tasks = [Task(job_script=self.job_select_active_set)]
        pool = Pool(tasks)
        pool.run()
        os.system("cp active_set.asi ..")
        os.chdir("..")

    def select_structures(self):
        os.mkdir("select_selectures")
        os.chdir("select_selectures")
        os.system("cp ../../nep.txt .")
        os.system("cp ../../train.xyz .")
        os.system("cp ../large_gamma.xyz .")
        tasks = [Task(job_script=self.job_select_structures)]
        pool = Pool(tasks)
        pool.run()
        os.system("cp to_add.xyz ../..")
        os.chdir("..")

    def run_nep(self):
        os.mkdir("train")
        os.chdir("train")
        print_block("Training now.")
        os.system("cp ../../train.xyz .")
        tasks = [nep_task(input=self.input_nep, job_script=self.job_nep)]
        pool = Pool(tasks)
        pool.run()
        os.system("cp nep.txt ../nep.txt")
        os.chdir("..")

    def run_gpumd(self):
        os.mkdir("gpumd")
        os.chdir("gpumd")
        print_block("Running GPUMD now.")
        tasks = [gpumd_task(ii, self.job_gpumd) for ii in self.input_gpumd]
        pool = Pool(tasks)
        pool.run()
        os.system("cat */extrapolation_dump.xyz >> ../large_gamma.xyz")
        os.chdir("..")
        return ase.io.read("large_gamma.xyz", index=":")

    def run_vasp(self, traj):
        print_block(f"Doing SCF now, {len(traj)} SCF to do.")
        os.mkdir("dft")
        os.chdir("dft")
        tasks = [
            vasp_task(atoms=atoms, input=self.input_vasp, job_script=self.job_vasp)
            for atoms in traj
        ]
        pool = Pool(tasks)
        pool.run()

        scf_traj = []
        for ii in os.listdir():
            try:
                atoms = ase.io.read(ii + "/OUTCAR")
                scf_traj.append(atoms)
            except:
                print(f"Vasp fail in {ii}")
                pass
        os.chdir("..")
        return scf_traj
