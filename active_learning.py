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
        gpumd_path = input_path / "gpumd"
        if gpumd_path.exists() and any(gpumd_path.iterdir()):
            self.input_gpumd = [
                f.read_text() for f in gpumd_path.iterdir() if f.is_file()
            ]

        # Load VASP input files
        vasp_config_path = input_path / "vasp.yaml"
        if vasp_config_path.exists():
            with open(vasp_config_path, "r") as f:
                self.input_vasp = yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"Vasp config file {vasp_config_path} not found.")

        # Load job scripts
        job_path = self.path / "job"
        if not job_path.exists():
            raise FileNotFoundError(f"Job directory {job_path} not found.")
        self.job_vasp = (job_path / "job_vasp.sh").read_text()
        self.job_gpumd = (job_path / "job_gpumd.sh").read_text()
        self.job_nep = (job_path / "job_nep.sh").read_text()
        self.job_select_active_set = (job_path / "job_select_active_set.sh").read_text()
        self.job_select_structures = (job_path / "job_select_structures.sh").read_text()

    def run(self, max_iterations=100):
        """Run the active learning process."""
        iter_num = 0
        while iter_num < max_iterations:
            t1 = time.time()
            self.logger.info(f"Iter-{iter_num} begins.")

            if self.iter(iter_num) == 0:
                break

            t2 = time.time()
            self.logger.info(
                f"Iter-{iter_num} done! Takes {int((t2 - t1) / 60)} minutes."
            )
            iter_num += 1

    def iter(self, iter_num):
        """Perform a single iteration of the active learning process."""
        iter_dir = self.path / f"iter_{iter_num}"
        iter_dir.mkdir(exist_ok=False)
        os.chdir(iter_dir)

        self.load_inputs()
        self.prepare_initial_structures(iter_num)
        self.run_nep()
        self.select_active_set()
        large_gamma_structures = self.run_gpumd()

        if not large_gamma_structures:
            return 0
        if len(large_gamma_structures) > self.max_structures_per_iteration:
            random.seed(42)  # Set random seed for reproducibility
            random.shuffle(large_gamma_structures)
            large_gamma_structures = large_gamma_structures[
                : self.max_structures_per_iteration
            ]

        self.select_structures()
        return 1

    def prepare_initial_structures(self, iter_num):
        """Prepare initial structures for the simulation."""
        if iter_num == 0:
            if (self.path / "train.xyz").exists():
                pass
            elif (self.path / "init_structures.xyz").exists():
                scf_traj = ase.io.read(self.path / "init_structures.xyz", index=":")
                scf_traj = self.run_vasp(scf_traj)
                dump_nep(scf_traj, self.path / "train.xyz")
            else:
                raise FileNotFoundError("You need to provide initial structures!")
        else:
            scf_traj = load_nep(self.path / "to_add.xyz")
            scf_traj = self.run_vasp(scf_traj)
            dump_nep(scf_traj, "scf.xyz")
            with open(self.path / "train.xyz", "a") as f:
                f.write(open("scf.xyz").read())

    def run_vasp(self, traj):
        """Run VASP tasks for the given trajectory."""
        self.logger.info(f"Doing SCF now, {len(traj)} SCF to do.")
        os.mkdir("dft")
        os.chdir("dft")
        tasks = [
            vasp_task(atoms=atoms, input=self.input_vasp, job_script=self.job_vasp)
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

    def run_nep(self):
        """Run NEP training."""
        os.mkdir("train")
        os.chdir("train")
        self.logger.info("Training now.")
        os.system(f"cp {self.path / 'train.xyz'} .")
        tasks = [nep_task(input=self.input_nep, job_script=self.job_nep)]
        pool = Pool(tasks)
        pool.run()
        os.system(f"cp nep.txt {self.path}")
        os.chdir("..")

    def run_gpumd(self):
        """Run GPUMD tasks."""
        os.mkdir("gpumd")
        os.chdir("gpumd")
        os.system(f"cp {self.path / 'nep.txt'} .")
        os.system(f"cp {self.path / 'active_set.asi'} .")
        self.logger.info("Running GPUMD now.")
        tasks = [gpumd_task(ii, self.job_gpumd) for ii in self.input_gpumd]
        pool = Pool(tasks)
        pool.run()
        os.system("cat */extrapolation_dump.xyz >> ../large_gamma.xyz")
        os.chdir("..")
        return ase.io.read("large_gamma.xyz", index=":")

    def select_active_set(self):
        """Select the active set for training."""
        os.mkdir("select_active_set")
        os.chdir("select_active_set")
        os.system(f"cp {self.path / 'nep.txt'} .")
        os.system(f"cp {self.path / 'train.xyz'} .")
        tasks = [Task(job_script=self.job_select_active_set)]
        pool = Pool(tasks)
        pool.run()
        os.system(f"cp active_set.asi {self.path}")
        os.chdir("..")

    def select_structures(self):
        """Select structures for the next iteration."""
        os.mkdir("select_structures")
        os.chdir("select_structures")
        os.system(f"cp {self.path / 'nep.txt'} .")
        os.system(f"cp {self.path / 'train.xyz'} .")
        os.system("cp ../large_gamma.xyz .")
        tasks = [Task(job_script=self.job_select_structures)]
        pool = Pool(tasks)
        pool.run()
        os.system(f"cp to_add.xyz {self.path}")
        os.chdir("..")
