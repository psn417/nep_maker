# Introduction

This Python package facilitates the construction of NEP using active learning techniques. It employs the same strategies as **MTP** [J. Chem. Phys. 159, 084112 (2023)] and **ACE** [Phys. Rev. Materials 7, 043801 (2023)].

The package automates active learning by submitting and monitoring jobs. The workflow is as follows:

### 1. Calculating Energy, Force, and Virial via *Ab Initio* Calculations

If this is the first iteration and no structures are available, you can generate simple structures. For instance, you can perturb a crystal structure to create an initial training set.

If a `train.xyz` file (containing energy and force data) already exists before the first iteration, this step will be skipped.

**Note:** The initial training set should not be too small for active set selection. For a NEP with a 30×30 neural network, approximately 1000 local environments (e.g., 10 structures with 100 atoms each) are required. If your NEP includes *N* elements, you will need *N* × 1000 local environments for each element type.

### 2. Selecting an Active Set

The `MaxVol` algorithm is used to select an active set, which consists of reference environments for calculating the extrapolation level.

### 3. Training the NEP

Train the NEP using the structures from Step 1. If a `nep.txt` file is provided, this step will be skipped in the first iteration.

### 4. Performing Molecular Dynamics (MD) to Generate New Structures

Run GPUMD to actively select new structures based on an extrapolation level cutoff. If no structures are generated, the loop terminates. You can run multiple MD simulations under different conditions to accelerate exploration.

### 5. Selecting Structures to Add to the Training Set

While the structures from Step 4 have high extrapolation levels, they may lack diversity. Therefore, another `MaxVol` selection is performed to identify the most representative structures.

---

# Installation

### Dependencies

First, install the required dependencies, including `PyNEP` and `CuPy`. Refer to [this page](https://github.com/psn417/nep_extrapolation) for detailed instructions.

### Installing the Package

1. Clone the code by running:
   ```bash
   git clone --recursive https://github.com/psn417/nep_maker.git
   ```

1. For Bash users:
   - Open `~/.bashrc` in a text editor.
   - Add the following line at the end of the file:
     ```bash
     export PYTHONPATH=$PYTHONPATH:/path/to/my_packages
     ```
   - Save the file and reload the shell configuration:
     ```bash
     source ~/.bashrc
     ```

2. Place the `nep_maker` package into the `my_packages` directory to make it accessible to Python.

2. Verify the installation by opening Python and typing `import nep_maker`. If the import is successful, the package is installed correctly.

---

# Input Files

Prepare the following input files:

1. **`init_structures.xyz`**: Structures used to train the NEP in the first iteration.
2. **(Optional) `train.xyz` and `nep.txt`**: If you already have an NEP, you can perform active learning based on it.
3. **`run.in`**: Specifies how to train the NEP.
4. **Job Scripts**: Define how to run NEP, GPUMD, and other tasks. Examples are provided for `LSF`; modify them according to your job system.
5. **`vasp.yaml`**: Specifies VASP parameters and pseudopotentials. Include the location of pseudopotentials. Refer to the [ASE documentation](https://wiki.fysik.dtu.dk/ase/ase/calculators/vasp.html#module-ase.calculators.vasp) for more details.
6. **`run_active.py`**: The main script for the active learning process. Only one CPU core is needed for it.
7. **`submit_command.sh`**: Specifies how to submit your jobs. For `LSF`, it is `bsub < job.sh`. For `slurm`, it is `sbatch job.sh`.

An example folder, `example_Na`, is provided with all necessary files.