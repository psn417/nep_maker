import os
from ase.io import write
from uuid import uuid4
from ase.calculators.vasp import Vasp


class Task:
    def __init__(self, **kwargs):
        self.id = uuid4()
        self.folder_name = "task_" + str(self.id)
        self.seperate_dir = False
        self.path = None
        self.submitted = False
        self.done = False
        self.job_script = kwargs["job_script"]
        self.input = kwargs.get("input", None)

    def submit_job(self):
        job_script_text = self.job_script + "\n touch DONE"
        with open("job.sh", "w") as f:
            f.write(job_script_text)
        os.system("bsub < job.sh")
        self.submitted = True

    def prepare_job(self):
        pass

    def run(self):
        if self.seperate_dir:
            os.mkdir(self.folder_name)
            os.chdir(self.folder_name)

        self.path = os.getcwd()
        self.prepare_job()
        self.submit_job()

        if self.seperate_dir:
            os.chdir("..")

    def is_finished(self):
        if os.path.exists(os.path.join(self.path, "DONE")):
            return True
        else:
            return False


class vasp_task(Task):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.atoms = kwargs["atoms"]
        self.calc = Vasp(**self.input)
        self.seperate_dir = True

    def prepare_job(self):
        # write INCAR, POSCAR and POTCAR
        self.calc.write_input(self.atoms)


class gpumd_task(Task):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.seperate_dir = True
        self.atoms = kwargs["atoms"]

    def prepare_job(self):
        with open("run.in", "w") as f:
            f.write(self.input)
        write("model.xyz", self.atoms)


class nep_task(Task):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def prepare_job(self):
        with open("nep.in", "w") as f:
            f.write(self.input)
