import os
import time
import random
import logging
from pathlib import Path
import ase.io
import yaml
from .task_pool import Pool
from .task import vasp_task, gpumd_task, nep_task, Task
from pynep.io import load_nep, dump_nep


class ActiveLearning:
    def __init__(self):
        self.path = Path(os.getcwd())
        self.input_gpumd = []
        self.atoms_gpumd = []
        self.max_structures_per_iteration = 9999
        self.setup_logging()

    def setup_logging(self):
        """Set up logging for the application."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            filename="active_learning.log",
        )
        self.logger = logging.getLogger(__name__)

    def load_inputs(self):
        """Load input files for the simulation."""
        input_path = self.path / "input"
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory {input_path} not found.")

        # Load GPUMD input files
        """
        gpumd_path = input_path / "gpumd"
        if gpumd_path.exists() and any(gpumd_path.iterdir()):
            self.input_gpumd = [
                f.read_text() for f in gpumd_path.iterdir() if f.is_file()
            ]
        """

        # Load VASP input files
        vasp_config_path = input_path / "vasp.yaml"
        if vasp_config_path.exists():
            with open(vasp_config_path, "r") as f:
                self.input_vasp = yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"Vasp config file {vasp_config_path} not found.")

        self.input_nep = (input_path / "nep.in").read_text()

        # Load job scripts
        job_path = input_path / "job"
        if not job_path.exists():
            raise FileNotFoundError(f"Job directory {job_path} not found.")
        self.job_vasp = (job_path / "job_vasp.sh").read_text()
        self.job_gpumd = (job_path / "job_gpumd.sh").read_text()
        self.job_nep = (job_path / "job_nep.sh").read_text()
        self.job_select_active_set = (job_path / "job_select_active_set.sh").read_text()
        self.job_select_structures = (job_path / "job_select_structures.sh").read_text()
        self.submit_command = (input_path / "submit_command.sh").read_text()

    def run(self, max_iterations=100):
        """Run the active learning process."""
        iter_num = 0
        while iter_num < max_iterations:
            t1 = time.time()
            self.logger.info(f"Iter-{iter_num} begins.")

            if self.iter(iter_num) == 0:
                self.logger.info(f"Active learning completed!")
                break

            t2 = time.time()
            self.logger.info(
                f"Iter-{iter_num} done! Takes {int((t2 - t1) / 60)} minutes.\n"
            )
            iter_num += 1

    def iter(self, iter_num):
        """Perform a single iteration of the active learning process."""
        iter_dir = self.path / f"iter_{iter_num}"
        iter_dir.mkdir(exist_ok=False)
        os.chdir(iter_dir)

        self.load_inputs()
        self.run_scf(iter_num)
        self.run_nep(iter_num)
        self.select_active_set()
        self.run_gpumd()
        if os.path.getsize("large_gamma.xyz") == 0:
            return 0

        to_add = self.select_structures()
        if len(to_add) > self.max_structures_per_iteration:
            random.seed(42)  # Set random seed for reproducibility
            random.shuffle(to_add)
            to_add = to_add[: self.max_structures_per_iteration]
        ase.io.write(f"{self.path / 'to_add.xyz'}", to_add)

        return 1

    def run_scf(self, iter_num):
        if iter_num == 0:
            if (self.path / "train.xyz").exists():
                self.logger.info("'train.xyz' exists, skip SCF in iter-0.")
            elif (self.path / "init_structures.xyz").exists():
                scf_traj = ase.io.read(self.path / "init_structures.xyz", index=":")
                self.logger.info(f"Loading 'init_structures.xyz'.")
                self.logger.info(f"Doing SCF now, {len(scf_traj)} SCF to do.")
                scf_traj = self.run_vasp(scf_traj)
                dump_nep(self.path / "train.xyz", scf_traj)
                dump_nep("scf.xyz", scf_traj)
            else:
                raise FileNotFoundError("You need to provide initial structures!")
        else:
            scf_traj = ase.io.read(self.path / "to_add.xyz", index=":")
            self.logger.info(f"Doing SCF now, {len(scf_traj)} SCF to do.")
            scf_traj = self.run_vasp(scf_traj)
            dump_nep("scf.xyz", scf_traj)
            with open(self.path / "train.xyz", "a") as f:
                f.write(open("scf.xyz").read())

    def run_vasp(self, traj):
        """Run VASP tasks for the given trajectory."""
        os.mkdir("1-scf")
        os.chdir("1-scf")
        tasks = [
            vasp_task(
                atoms=atoms,
                input=self.input_vasp,
                job_script=self.job_vasp,
                submit_command=self.submit_command,
            )
            for atoms in traj
        ]
        pool = Pool(tasks)
        pool.run()

        scf_traj = []
        for task_dir in os.listdir():
            try:
                atoms = ase.io.read(Path(task_dir) / "OUTCAR")
                scf_traj.append(atoms)
            except:
                self.logger.error(f"VASP failed in {task_dir}.")
        os.chdir("..")
        return scf_traj

    def run_nep(self, iter_num):
        if iter_num == 0 and (self.path / "nep.txt").exists():
            self.logger.info("'nep.txt' exists, skip training in iter-0.")
            return
        """Run NEP training."""
        os.mkdir("2-train")
        os.chdir("2-train")
        self.logger.info("Training now.")
        os.system(f"cp {self.path / 'train.xyz'} .")
        tasks = [
            nep_task(
                input=self.input_nep,
                job_script=self.job_nep,
                submit_command=self.submit_command,
            )
        ]
        pool = Pool(tasks)
        pool.run()
        os.system(f"cp nep.txt {self.path}")
        os.chdir("..")

    def select_active_set(self):
        """Select the active set for training."""
        self.logger.info("Selecting active set.")
        os.mkdir("3-select_active_set")
        os.chdir("3-select_active_set")
        os.system(f"cp {self.path / 'nep.txt'} .")
        os.system(f"cp {self.path / 'train.xyz'} .")
        tasks = [
            Task(
                job_script=self.job_select_active_set,
                submit_command=self.submit_command,
            )
        ]
        pool = Pool(tasks)
        pool.run()
        os.system(f"cp active_set.asi {self.path}")
        os.chdir("..")

    def run_gpumd(self):
        """Run GPUMD tasks."""
        os.mkdir("4-gpumd")
        os.chdir("4-gpumd")
        os.system(f"cp {self.path / 'nep.txt'} .")
        os.system(f"cp {self.path / 'active_set.asi'} .")
        self.logger.info("Running GPUMD now.")
        tasks = [
            gpumd_task(
                input=ii,
                atoms=jj,
                job_script=self.job_gpumd,
                submit_command=self.submit_command,
            )
            for ii, jj in zip(self.input_gpumd, self.atoms_gpumd)
        ]
        pool = Pool(tasks)
        pool.run()
        os.system("cat */extrapolation_dump.xyz >> ../large_gamma.xyz")
        os.chdir("..")

    def select_structures(self):
        """Select structures for the next iteration."""
        os.mkdir("5-select_structures")
        os.chdir("5-select_structures")
        self.logger.info("Selecting structures.")
        os.system(f"cp {self.path / 'nep.txt'} .")
        os.system(f"cp {self.path / 'train.xyz'} .")
        os.system("cp ../large_gamma.xyz .")
        tasks = [
            Task(
                job_script=self.job_select_structures,
                submit_command=self.submit_command,
            )
        ]
        pool = Pool(tasks)
        pool.run()
        ret = ase.io.read("to_add.xyz", index=":")
        os.chdir("..")
        return ret
