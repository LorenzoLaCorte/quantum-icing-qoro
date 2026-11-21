# Divi documentation snippets (from Context7)

Copied on 2026-11-21 from https://context7.com/qoroquantum/divi (suggested by the course instructor).
Each snippet points to its source file in https://github.com/qoroquantum/divi. These snippets track
Divi's `main` branch, while this repo pins `qoro-divi==0.16.2`: check an API against the installed
version before relying on it.

---

### Install qoro-divi from source

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/installation.rst

Clone the repository and sync dependencies with uv. Provides the core installation from a source checkout.

```bash
git clone https://github.com/QoroQuantum/divi.git
cd divi
uv sync
```

--------------------------------

### Install and run the Birkhoff decomposition example

Source: https://github.com/qoroquantum/divi/blob/main/demos/minimum_birkhoff_decomposition/README.md

Install dependencies and run the main script. The example connects circuit-sampling results to a classical CPLEX integer program.

```bash
pip install -r requirements.txt
python main.py
```

--------------------------------

### Run a tutorial example from repo root

Source: https://github.com/qoroquantum/divi/blob/main/tutorials/README.md

Run any self-contained example by pointing Python at the file from the repo root. Example shown for the QAOA graph problems tutorial.

```bash
python tutorials/optimization/qaoa_graph_problems.py
```

--------------------------------

### Install qoro-divi with uv

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/installation.rst

Core installation using uv. Covers local simulation, cloud execution, VQE, QAOA, program ensembles, circuit pipelines, and all optimizers except PymooOptimizer.

```bash
uv add qoro-divi
```

--------------------------------

### Install Divi with chem extra

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/quickstart.rst

Install the qoro-divi package with the chem extra to access molecule inputs for quantum chemistry problems.

```bash
pip install "qoro-divi[chem]"
```

--------------------------------

### Install optional extras with uv

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/installation.rst

Install multiple optional extras (aer, chem, pennylane) using uv in a single command.

```bash
uv add "qoro-divi[aer,chem,pennylane]"
```

--------------------------------

### Install and run divi-ai

Source: https://github.com/qoroquantum/divi/blob/main/README.md

Install the AI assistant with pip and run it in the terminal. No API keys or internet required after setup; it uses a local LLM.

```bash
pip install qoro-divi[ai]
divi-ai
```

--------------------------------

### Install specific nightly build by date

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/installation.rst

Pin a specific nightly build by its version date. Nightly builds may contain unstable or experimental features.

```bash
pip install qoro-divi==0.8.0.dev20260305
```

--------------------------------

### Shared setup for partitioned QAOA/PCE examples

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/algorithms/combinatorial_optimization_qaoa_pce.rst

Common imports and helper function used by all partitioning examples. Defines a large random BQM, a D-Wave EnergyImpactDecomposer, a COBYLA optimizer, and a MaestroSimulator backend.

```python
import dimod
import hybrid
from qiskit.circuit.library import RYGate, RZGate
from divi.qprog.algorithms import DenseEncoding, InterpolationStrategy, SoftObjective
from divi.qprog.problems import BinaryOptimizationProblem
from divi.qprog.ensembles import PartitioningProgramEnsemble
from divi.qprog.algorithms import GenericLayerAnsatz
from divi.qprog.optimizers import ScipyMethod, ScipyOptimizer
from divi.backends import MaestroSimulator

def run_partitioned(ensemble):
    ensemble.run()
    return ensemble.aggregate_results()

large_bqm = dimod.generators.gnp_random_bqm(25, 0.5, vartype="BINARY")
decomposer = hybrid.EnergyImpactDecomposer(size=5)
optimizer = ScipyOptimizer(method=ScipyMethod.COBYLA)
backend = MaestroSimulator()
```

--------------------------------

### Install optional extras with pip

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/installation.rst

Install one or more optional extras (aer, pennylane, chem) using pip. Multiple extras can be combined in a single command.

```bash
pip install "qoro-divi[aer]"
pip install "qoro-divi[pennylane]"
pip install "qoro-divi[aer,chem,pennylane]"
```

--------------------------------

### IterativeQAOA Example

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/algorithms/combinatorial_optimization_qaoa_pce.rst

Shows how to use IterativeQAOA with a MaxCutProblem, specifying interpolation strategy and other parameters. The example is incomplete in the source; only the imports and problem setup are shown.

```python
   import networkx as nx
   from divi.qprog.algorithms import InterpolationStrategy, IterativeQAOA
   from divi.qprog.problems import MaxCutProblem
   from divi.qprog.optimizers import ScipyMethod, ScipyOptimizer
   from divi.backends import MaestroSimulator
```

--------------------------------

### Install all extras except ai with pip

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/installation.rst

Install every optional extra except 'ai'. The 'ai' extra depends on llama-cpp-python, which may require a C++ toolchain on platforms without prebuilt wheels.

```bash
pip install "qoro-divi[all]"
```

--------------------------------

### Install Divi with jupyter and qubo-decompose extras

Source: https://github.com/qoroquantum/divi/blob/main/demos/README.md

Install the Divi framework with the jupyter and qubo-decompose extras. Examples that need further packages list them in a requirements.txt in their own directory.

```bash
pip install "qoro-divi[jupyter,qubo-decompose]"
```

--------------------------------

### Clone and set up the repository with uv and pre-commit

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/development/contributing.rst

Commands to clone the repository, install dependencies with uv (including dev, testing, and docs groups), and install pre-commit hooks. Run the test suite with 'uv run pytest -n auto'.

```bash
git clone https://github.com/QoroQuantum/divi.git
cd divi
uv sync                # installs dev, testing, and docs groups
pre-commit install
```

--------------------------------

### Install nightly development build

Source: https://github.com/qoroquantum/divi/blob/main/README.md

Installs the latest development build published daily from the `main` branch. Use the `--pre` flag to include pre-release versions.

```bash
pip install qoro-divi --pre
```

--------------------------------

### Install documentation dependencies

Source: https://github.com/qoroquantum/divi/blob/main/CONTRIBUTING.md

Install the docs group with uv sync --group docs.

```bash
uv sync --group docs
```

--------------------------------

### Example docstring for optimize_circuit

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/development/building_docs.rst

Example of a Google-style docstring for a public method. Includes type hints, Args, Returns, and Raises sections. This block is skipped by Sybil (.. skip: next) because it is pseudocode.

```python
def optimize_circuit(self, circuit: Circuit, method: str = "default") -> Circuit:
    """Optimize a quantum circuit using the specified method.

    Args:
        circuit: The quantum circuit to optimize
        method: Optimization method to use

    Returns:
        The optimized circuit

    Raises:
        ValueError: If the method is not supported
    """
    pass
```

--------------------------------

### Sync extras from source checkout with uv

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/installation.rst

Sync specific extras, all extras, or all extras except 'ai' from a source checkout. Note that --no-extra only works alongside --all-extras.

```bash
uv sync --extra aer --extra chem --extra pennylane
uv sync --all-extras
uv sync --all-extras --no-extra ai
```

--------------------------------

### Install qoro-divi with pip

Source: https://github.com/qoroquantum/divi/blob/main/README.md

Installs the qoro-divi package. Optional extras are available for additional features; use `pip install "qoro-divi[all]"` for all extras except `ai`.

```bash
pip install qoro-divi
```

--------------------------------

### Complete QAOA example with checkpointing

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/execution_workflows/resuming_long_runs.rst

Complete example showing checkpointing with QAOA. Imports required modules including networkx, QAOA, MaxCliqueProblem, CheckpointConfig, PymooOptimizer, PymooMethod, and MaestroSimulator.

```python
import networkx as nx
from pathlib import Path
from divi.qprog.algorithms import QAOA
from divi.qprog.problems import MaxCliqueProblem
from divi.qprog.checkpointing import CheckpointConfig
from divi.qprog.optimizers import PymooOptimizer, PymooMethod
from divi.backends import MaestroSimulator
```

--------------------------------

### TimeEvolution with SparsePauliOp Hamiltonian

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/quickstart.rst

Simulates real-time quantum dynamics under a Hamiltonian using TimeEvolution with Trotter-Suzuki or QDrift. Prints basis-state probabilities after running.

```python
import math
from qiskit.quantum_info import SparsePauliOp
from divi.qprog.algorithms import TimeEvolution
from divi.backends import MaestroSimulator

te = TimeEvolution(
    hamiltonian=SparsePauliOp.from_sparse_list(
        [("X", [0], 1.0), ("X", [1], 1.0)], num_qubits=2
    ),
    time=math.pi / 2,
    backend=MaestroSimulator(shots=5000),
)
te.run()
print(te.results)  # basis-state probabilities
```

--------------------------------

### Install uv

Source: https://github.com/qoroquantum/divi/blob/main/CONTRIBUTING.md

Install the uv dependency manager using the official installer script.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

--------------------------------

### Install dependencies with uv sync --all-extras

Source: https://github.com/qoroquantum/divi/blob/main/AGENTS.md

Use this command to install all dependencies, including the 'ai' extras, in the project's virtual environment. Always sync with extras to include AI-related dependencies.

```bash
uv sync --all-extras
```

--------------------------------

### Example test with fixtures: VQE initialization and cloud backend integration

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/development/testing.rst

Shows how to write tests using the dummy_simulator fixture (fake backend) and the api_key fixture for cloud backend tests. The cloud test is marked with @pytest.mark.requires_api_key and only runs with --run-api-tests. The VQE test asserts that n_params_per_layer and n_layers are not None.

```python
import pytest
from pyscf import gto
from divi.qprog.algorithms import VQE
from divi.qprog.algorithms import HartreeFockAnsatz
from divi.qprog.problems import MolecularProblem

def test_vqe_initialization(dummy_simulator):
    """Test that VQE initializes correctly with mock backend."""
    # Minimal H2 molecule for testing (or use a fixture from conftest)
    mol = gto.M(
        atom="H 0 0 -0.6614; H 0 0 0.6614", basis="sto-3g", unit="Bohr"
    )
    vqe = VQE(
        MolecularProblem.from_molecule(mol),
        ansatz=HartreeFockAnsatz(),
        backend=dummy_simulator,
    )
    assert vqe.n_params_per_layer is not None
    assert vqe.n_layers is not None

@pytest.mark.requires_api_key
def test_cloud_backend_integration(api_key):
    """Test integration with cloud backend."""
    # This test only runs with --run-api-tests
    pass
```

--------------------------------

### Find max-clique of a graph with QAOA

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/algorithms/combinatorial_optimization_qaoa_pce.rst

Imports networkx, QAOA, MaxCliqueProblem, ScipyMethod, ScipyOptimizer, and MaestroSimulator. The example is incomplete in the source; the full setup and run call are not shown.

```python
import networkx as nx
from divi.qprog.algorithms import QAOA
from divi.qprog.problems import MaxCliqueProblem
from divi.qprog.optimizers import ScipyMethod, ScipyOptimizer
from divi.backends import MaestroSimulator
```

--------------------------------

### Useful commands for the Birkhoff decomposition example

Source: https://github.com/qoroquantum/divi/blob/main/demos/minimum_birkhoff_decomposition/README.md

Run with custom parameters or show help. `-n 4 -k 2 -inst 5 -it 20` sets the problem size, instance, and iterations.

```bash
python main.py -n 4 -k 2 -inst 5 -it 20
python main.py --help
```

--------------------------------

### Run all documentation snippet tests with make test-snippets

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/development/building_docs.rst

Run all snippet examples locally. By default runs all snippets with no early exit.

```bash
cd docs
make test-snippets
```

--------------------------------

### Additional Makefile commands for documentation

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/development/building_docs.rst

Shows all available Makefile commands for documentation: help, clean, test, spelling, linkcheck, coverage, open, and install.

```bash
cd docs
make help          # Show all available commands
make clean         # Remove all build files
make test          # Run all quality checks (spelling, linkcheck, coverage)
make spelling      # Check for spelling errors
make linkcheck     # Check for broken links
make coverage      # Run a documentation coverage check
make open          # Open the built documentation in your browser
make install       # Install documentation dependencies
```

--------------------------------

### CustomVQA constructor options example

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/execution_workflows/pipeline_authoring.rst

Shows how to pass MeasurementStage options like shot_distribution and grouping_strategy to the VQE constructor. Use when configuring a VQE instance with custom measurement settings.

```python
vqe = VQE(problem, ..., shot_distribution="weighted", grouping_strategy="qwc")
```

--------------------------------

### Import benchmark functions from main

Source: https://github.com/qoroquantum/divi/blob/main/demos/quantum_guided_cluster/quantum_guided_cluster.ipynb

Imports the benchmark runner functions used by all examples on this page.

```python
import time

from main import run_benchmark, run_multiseed_benchmark
```

--------------------------------

### Set up pre-commit hooks

Source: https://github.com/qoroquantum/divi/blob/main/CONTRIBUTING.md

Install pre-commit hooks to enforce formatting and license headers. Run all hooks manually with pre-commit run -a.

```bash
pre-commit install
```

```bash
pre-commit run -a
```

--------------------------------

### Install AI dependencies with uv sync

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/tools/divi_ai.rst

Install only the AI stack with `uv sync --extra ai`, or the full development environment with `uv sync --all-extras` for docs, tests, and other areas.

```bash
uv sync --extra ai
```

```bash
uv sync --all-extras
```

--------------------------------

### Install dependencies with uv sync

Source: https://github.com/qoroquantum/divi/blob/main/CONTRIBUTING.md

Install the dev, testing, and docs groups by default. Add the --extra ai flag for AI-related dependencies.

```bash
uv sync
```

```bash
uv sync --extra ai            # divi-ai dependencies
```

--------------------------------

### Install qoro-divi with qrmi extra

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/execution_workflows/backends.rst

Installs the qrmi extra on Linux, which includes QRMI 0.27+ and IBM resource support. Required for QRMIBackend.

```console
$ pip install "qoro-divi[qrmi]"
```

--------------------------------

### Live reload for documentation development

Source: https://github.com/qoroquantum/divi/blob/main/CONTRIBUTING.md

Start a live-reload development server for the documentation by running make dev in the docs directory.

```bash
cd docs
make dev
```

--------------------------------

### Install Divi with uv or pip

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/index.rst

Install the qoro-divi package using uv or pip. This covers local and cloud execution, VQE, QAOA, and program ensembles; heavier features require optional extras.

```bash
uv add qoro-divi     # or: pip install qoro-divi
```

--------------------------------

### QuantumProgram.assemble_pipeline

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/execution_workflows/pipeline_authoring.rst

Assembles the pipeline stages. Direct subclasses with parameterized circuits must add ParameterBindingStage themselves.

```APIDOC
## QuantumProgram.assemble_pipeline

### Description
Assembles the pipeline stages. Direct subclasses with parameterized circuits must add ParameterBindingStage themselves.

### Method
assemble_pipeline

### Parameters
- **spec_stage** (Stage) - Required - The specification stage.
- **terminal_stage** (Stage) - Required - The terminal stage.
- **result_format** (ResultFormat) - Required - The result format.
- **extra_stages** (tuple) - Optional - Additional stages to include.

### Response
- **pipeline** (CircuitPipeline) - The assembled pipeline.

### Request Example
```python
# Example usage (from source)
class SingleQubitRotation(QuantumProgram):
    def assemble_pipeline(self, spec_stage, terminal_stage, *, result_format, extra_stages=()):
        return CircuitPipeline(stages=[
            spec_stage,
            *extra_stages,
            *self._build_mitigation_stages(result_format),
            terminal_stage,
            ParameterBindingStage(),   # last keeps binding on its fast path
        ])
```
```

--------------------------------

### Missing extra error message

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/installation.rst

Example error shown when a feature behind an optional extra is used without the extra installed. The error names the feature and the install command.

```text
ImportError: QiskitSimulator requires the 'aer' extra; install it with
`pip install qoro-divi[aer]`. Divi's default simulator, MaestroSimulator,
is included in the core install.
```

--------------------------------

### qaoa.get_top_solutions

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/algorithms/combinatorial_optimization_qaoa_pce.rst

Retrieves the top solutions from the QAOA optimization. The example shows obtaining the best solution with decoding and repair feasibility.

```APIDOC
## qaoa.get_top_solutions

### Description
Retrieves the top solutions from the QAOA optimization. The example shows obtaining the best solution with decoding and repair feasibility.

### Method
Function call

### Parameters
- `n` (int) - Required - Number of top solutions to retrieve.
- `include_decoded` (bool) - Required - Whether to include decoded solution.
- `feasibility` (string) - Required - Feasibility handling strategy (e.g., "repair").

### Response
Returns a list of solution objects. Each solution has `decoded` (holdings) and `energy` (objective value).

### Request Example
```python
best = qaoa.get_top_solutions(n=1, include_decoded=True, feasibility="repair")[0]
print(f"Holdings: {best.decoded}, objective: {best.energy:.5f}")
print(problem.metrics(best.bitstring))
```
```

--------------------------------

### Import libraries and set constants for TSP

Source: https://github.com/qoroquantum/divi/blob/main/demos/travelling_salesman/travelling_salesman.ipynb

Imports required modules and sets SHOTS and SEED for the TSP examples.

```python
import time

from travelling_salesman import (
    compute_distance_matrix,
    extract_best_tour,
    generate_cities,
    plot_cities,
    plot_comparison,
    print_comparison,
    solve_brute_force,
    solve_partitioned_tsp,
    solve_with_pce,
    solve_with_qaoa,
)

from divi.backends import MaestroSimulator

SHOTS = 20_000
SEED = 42
```

--------------------------------

### Backend CLI flags for get_backend() tutorials

Source: https://github.com/qoroquantum/divi/blob/main/tutorials/README.md

Tutorials using get_backend() from _backend.py accept these flags: --local-maestro (default, MaestroSimulator), --local-qiskit (QiskitSimulator, needs aer extra), --cloud-maestro (QoroService), and --force-sampling (disables exact expectation values, uses shot-based sampling).

```bash
python tutorials/optimization/qaoa_graph_problems.py --local-maestro
```

```bash
python tutorials/optimization/qaoa_graph_problems.py --cloud-maestro
```

```bash
python tutorials/optimization/qaoa_graph_problems.py --local-qiskit --force-sampling
```

--------------------------------

### Run main.py locally

Source: https://github.com/qoroquantum/divi/blob/main/demos/quantum_guided_cluster/README.md

Executes simulated annealing, a cluster algorithm with coupling-constant correlations, and cluster algorithms with QAOA correlations. Requires the project files and dependencies; alternatively open the quantum_guided_cluster.ipynb notebook.

```bash
python main.py
```

--------------------------------

### Create ensemble with separate sampling backend and run

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/execution_workflows/program_ensembles.rst

Constructs a PartitioningProgramEnsemble with distinct optimisation and sampling backends, then runs it. The sampling backend is used only for final solution measurements; if omitted, both phases use the normal backend.

```python
ensemble = PartitioningProgramEnsemble(
    ...,
    backend=optimisation_backend,
    sampling_backend=sampling_backend,
)
ensemble.run()
```

--------------------------------

### Run the portfolio optimization notebook

Source: https://github.com/qoroquantum/divi/blob/main/demos/portfolio_optimization/README.md

Launch the Jupyter notebook that builds a Markowitz QUBO, partitions it into communities, and solves with QAOA. The default path uses MaestroSimulator locally.

```bash
jupyter notebook portfolio_optimization.ipynb
```

--------------------------------

### PCE for QUBO with GenericLayerAnsatz

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/quickstart.rst

Runs PCE on a QUBO matrix using a GenericLayerAnsatz with RY and RZ gates and CX entangler. Uses MonteCarloOptimizer and MaestroSimulator.

```python
import numpy as np
from qiskit.circuit.library import CXGate, RYGate, RZGate
from divi.qprog.algorithms import PCE, GenericLayerAnsatz
from divi.qprog.problems import BinaryOptimizationProblem
from divi.backends import MaestroSimulator

from divi.qprog.optimizers import MonteCarloOptimizer

qubo_matrix = np.array([[-1.0, 2.0], [0.0, 1.0]])
pce = PCE(
    problem=BinaryOptimizationProblem(qubo_matrix),
    ansatz=GenericLayerAnsatz(
        gate_sequence=[RYGate, RZGate],
        entangler=CXGate,
        entangling_layout="all-to-all",
    ),
    optimizer=MonteCarloOptimizer(),
    backend=MaestroSimulator(),
)
pce.run()
```

--------------------------------

### Inspect dry_run report for cost pipeline

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/execution_workflows/pipelines.rst

Use dry_run() to get a report keyed by pipeline name. The example prints stage factors, total circuits, and cadence for the cost pipeline.

```python
reports = vqe.dry_run()   # `vqe` from the example above
cost = reports["cost"]

# What is in this pipeline, and what does each stage do to the batch?
# `factor` is the ratio of circuits out to circuits in, so a reduction reads as
# a fraction: the tree's ÷14 is factor == 1 / 14 here.
print([(s.name, s.factor) for s in cost.stages])
print(cost.total_circuits)        # 500 — one evaluation (this optimizer: one θ)
print(cost.cadence)               # PipelineCadence.PER_EVALUATION
```

--------------------------------

### CircuitPipeline.run

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/execution_workflows/pipeline_authoring.rst

Runs a pipeline of stages on an initial spec and environment, returning the final result. The example shows a minimal pipeline with BellSpecStage and MeasurementStage, and how to access the result value.

```APIDOC
## CircuitPipeline.run

### Description
Runs a pipeline of stages on an initial spec and environment, returning the final result. The example shows a minimal pipeline with BellSpecStage and MeasurementStage, and how to access the result value.

### Method
`run`

### Parameters
- **initial_spec** - Required - Initial specification (can be `None`)
- **env** (PipelineEnv) - Required - Pipeline environment with backend

### Returns
- **result** - The pipeline result; use `result.value` for the natural dict shape when the spec axis has been stripped

### Example
```python
# Build a minimal pipeline
pipeline = CircuitPipeline(stages=[
    BellSpecStage(),
    MeasurementStage(),   # Declares probability-mode results
])

# Run the pipeline
env = PipelineEnv(backend=MaestroSimulator())
result = pipeline.run(initial_spec=None, env=env)

# BellSpecStage.reduce strips the "bell" axis, so the result collapses
# to key () — use result.value for the natural dict shape.
probs = result.value   # ≈ {"00": ~0.5, "11": ~0.5}
assert isinstance(probs, dict)
assert set(probs.keys()) == {"00", "11"} or len(probs) >= 1
# result[()] is equivalent when the spec axis has been stripped.
assert result[()] == probs
```
```

--------------------------------

### QAOA for Max-Cut with networkx graph

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/quickstart.rst

Creates a random graph with networkx and runs QAOA to solve a Max-Cut problem. Prints the best loss and the solution after running.

```python
import networkx as nx
from divi.qprog.algorithms import QAOA
from divi.qprog.problems import MaxCutProblem
from divi.qprog.optimizers import MonteCarloOptimizer

# Create your problem graph
graph = nx.erdos_renyi_graph(10, 0.5, seed=42)

qaoa = QAOA(
    MaxCutProblem(graph),
    n_layers=2,
    max_iterations=10,
    optimizer=MonteCarloOptimizer(),
    backend=MaestroSimulator()
)
qaoa.run()
print(f"Best loss: {qaoa.best_loss:.4f}")
print(f"Solution: {qaoa.solution}")
```

--------------------------------

### VQE with UCCSDAnsatz and MonteCarloOptimizer

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/quickstart.rst

Configures a VQE for molecular ground state calculations using a UCCSDAnsatz and MonteCarloOptimizer with a MaestroSimulator backend. Suitable for electronic structure problems.

```python
from divi.qprog.algorithms import VQE, UCCSDAnsatz
from divi.qprog.optimizers import MonteCarloOptimizer

vqe = VQE(
    h2_problem,
    ansatz=UCCSDAnsatz(),
    n_layers=2,
    optimizer=MonteCarloOptimizer(),
    backend=MaestroSimulator()
)
```

--------------------------------

### Serve built documentation

Source: https://github.com/qoroquantum/divi/blob/main/CONTRIBUTING.md

Serve the built documentation locally by running make serve in the docs directory.

```bash
cd docs
make serve
```

--------------------------------

### Run QNN with MaestroSimulator

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/quickstart.rst

Constructs and runs a QNN with a feature map, ansatz, and optimizer. Uses squared error loss and COBYLA. The backend is MaestroSimulator. The run is performed with perform_final_computation=False.

```python
import numpy as np
from qiskit.circuit.library import CXGate, RYGate, RZGate
from divi.qprog.algorithms import QNN, AngleEmbedding, GenericLayerAnsatz
from divi.qprog.optimizers import ScipyMethod, ScipyOptimizer
from divi.backends import MaestroSimulator

qnn = QNN(
    n_qubits=2,
    feature_map=AngleEmbedding(rotation="Y"),
    ansatz=GenericLayerAnsatz(
        gate_sequence=[RYGate, RZGate],
        entangler=CXGate,
        entangling_layout="linear",
    ),
    feature_batch=np.array([[0.1, 0.2], [2.0, 2.1]]),
    labels=np.array([-1.0, 1.0]),
    loss_fn="squared_error",
    max_iterations=5,
    optimizer=ScipyOptimizer(method=ScipyMethod.COBYLA),
    backend=MaestroSimulator(),
)
qnn.run(perform_final_computation=False)
```

--------------------------------

### Configure QoroService backend for remote execution

Source: https://github.com/qoroquantum/divi/blob/main/demos/minimum_birkhoff_decomposition/birkhoff_decomposition.ipynb

Shows how to set up a QoroService backend with a JobConfig specifying 10,000 shots, as an alternative to the local MaestroSimulator for running the experiment on QoroService.

```python
from divi.backends import JobConfig, QoroService
qpu_backend = QoroService(job_config=JobConfig(shots=10_000))
```

--------------------------------

### Run VQE on H2 molecule with ScipyOptimizer

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/quickstart.rst

Defines an H2 molecule, wraps it in a MolecularProblem, and runs a VQE with a HartreeFockAnsatz, ScipyOptimizer (COBYLA), and MaestroSimulator. Prints ground state energy and circuit count after running.

```python
# Step 1: Define your molecule and wrap it in a problem
h2_molecule = gto.M(
   atom="H 0 0 -0.6614; H 0 0 0.6614", basis="sto-3g", unit="Bohr"
)
h2_problem = MolecularProblem.from_molecule(h2_molecule)

# Step 2: Choose your optimizer
optimizer = ScipyOptimizer(method=ScipyMethod.COBYLA)

# Step 3: Set up your quantum program
vqe = VQE(
   h2_problem,
   ansatz=HartreeFockAnsatz(),
   n_layers=2,  # Circuit depth
   optimizer=optimizer,
   max_iterations=10,  # Optimization steps
   backend=MaestroSimulator(shots=1000),  # Local simulator
)

# Step 4: Run and get results!
vqe.run()

# Check your results
print(f"Ground state energy: {vqe.best_loss:.6f} Hartree")
print(f"Circuits executed: {vqe.total_circuit_count}")
```

--------------------------------

### Train PCE with MultiBasisEncoding and exact gradient

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/algorithms/combinatorial_optimization_qaoa_pce.rst

Uses MultiBasisEncoding with a gradient-based optimizer (ScipyOptimizer) to train on the exact gradient. The snippet is incomplete in the source; it shows imports and the start of a PCE setup but the rest is missing.

```python
import numpy as np

from divi.backends import MaestroSimulator
from divi.qprog.algorithms import PCE, MultiBasisEncoding
from divi.qprog.optimizers import ScipyMethod, ScipyOptimizer
from divi.qprog.problems import BinaryOptimizationProblem
```

--------------------------------

### Dry Run VQE with format_dry_run

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/quickstart.rst

Shows how to preview what a VQE program would submit without executing. The dry_run() output is formatted with format_dry_run. The output shows cost and sample trees with circuit and measurement stages.

```python
from divi.pipeline import format_dry_run

preview_vqe = VQE(
    h2_problem,
    ansatz=HartreeFockAnsatz(),
    n_layers=2,
    optimizer=ScipyOptimizer(method=ScipyMethod.COBYLA),
    backend=MaestroSimulator(shots=1000),
)
format_dry_run(preview_vqe.dry_run())
```

```text
cost
├── CircuitSpecStage [circuit] → 14
│   ├── n_qubits: 4
│   ├── n_gates: 82
│   └── depth: 47
├── MeasurementStage [obs_group] → ÷14
│   ├── strategy: analytic
│   └── n_pauli_terms: 14
├── Total (per evaluation): 14 ÷ 14 = 1 circuit · 1,000 shots
└── Summary: avg depth 47, width 4, 36 2q-gates total

sample
├── CircuitSpecStage [circuit] → 1
├── MeasurementStage [obs_group] → 1
├── Total (once): 1 circuit · 1,000 shots
└── Summary: avg depth 47, width 4, 36 2q-gates total
```

--------------------------------

### Submit Bell Pair Circuit to QoroService

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/quickstart.rst

Submits an OpenQASM 2.0 Bell pair circuit to the QoroService cloud simulator. Uses QORO_API_KEY from .env. The job is submitted to the 'qoro_maestro' cluster, polled until complete, and results are printed.

```python
from divi.backends import QoroService, JobConfig

# Bell pair: H + CNOT, then measure both qubits (OpenQASM 2.0)
qasm = (
    'OPENQASM 2.0;\n'
    'include "qelib1.inc";\n'
    'qreg q[2];\n'
    'creg c[2];\n'
    'h q[0];\n'
    'cx q[0],q[1];\n'
    'measure q[0] -> c[0];\n'
    'measure q[1] -> c[1];\n'
)

service = QoroService()  # Uses QORO_API_KEY from .env file
result = service.submit_circuits(
    {"my_circuit": qasm},
    job_config=JobConfig(simulator_cluster="qoro_maestro"),
)
service.poll_job_status(result, loop_until_complete=True)
completed = service.get_job_results(result)
print(completed.results)
```

--------------------------------

### PartitioningProgramEnsemble.run()

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/algorithms/combinatorial_optimization_qaoa_pce.rst

Runs the partitioned QAOA ensemble on a PortfolioSelectionProblem or MaxWeightMatchingProblem. It partitions the problem, solves each subproblem independently, and aggregates results.

```APIDOC
## PartitioningProgramEnsemble.run()

### Description
Runs the partitioned QAOA ensemble on a PortfolioSelectionProblem or MaxWeightMatchingProblem. It partitions the problem, solves each subproblem independently, and aggregates results.

### Method
run()

### Parameters
None explicitly documented.

### Response
Returns aggregated results (e.g., holdings and objective for portfolio, matching and weight for matching).

### Request Example
```python
ensemble = PartitioningProgramEnsemble(
    problem=problem,
    n_layers=1,
    optimizer=ScipyOptimizer(method=ScipyMethod.COBYLA),
    max_iterations=5,
    backend=MaestroSimulator(),
)
ensemble.run()
holdings, objective = ensemble.aggregate_results()
print(f"Holdings: {holdings}, objective: {objective:.5f}")
```

### Response Example
No response example provided in source.
```

--------------------------------

### ReplicatedCustomVQA with ReplicaBundleStage

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/execution_workflows/pipeline_authoring.rst

Subclasses CustomVQA to replicate every circuit N times by appending ReplicaBundleStage to extra_stages in assemble_pipeline. Includes a minimal two-qubit circuit, program setup with MaestroSimulator and ScipyOptimizer, and verification via dry_run() that checks for the stage class name.

```python
# ReplicaBundleStage is defined in the preceding custom-stage example.

class ReplicatedCustomVQA(CustomVQA):
    """CustomVQA subclass that replicates every circuit N times."""

    def __init__(self, *args, n_replicas: int = 2, **kwargs):
        super().__init__(*args, **kwargs)
        self._n_replicas = n_replicas

    def assemble_pipeline(self, spec_stage, terminal_stage, *, result_format, extra_stages=()):
        return super().assemble_pipeline(
            spec_stage,
            terminal_stage,
            result_format=result_format,
            extra_stages=(*extra_stages, ReplicaBundleStage(n=self._n_replicas)),
        )

# A minimal two-qubit circuit; the basis measurement reads as a sum of Z.
circuit = QuantumCircuit(2, 2)
circuit.ry(Parameter("theta"), 0)
circuit.ry(Parameter("phi"), 1)
circuit.cx(0, 1)
circuit.measure([0, 1], [0, 1])

program = ReplicatedCustomVQA(
    circuit,
    param_shape=(2,),
    n_replicas=2,
    max_iterations=3,
    backend=MaestroSimulator(),
    optimizer=ScipyOptimizer(method=ScipyMethod.COBYLA),
    seed=42,
)

# Verify the custom stage is present in the cost pipeline. ``dry_run`` is the
# public way to introspect the assembled stages (no private access needed).
# ``StageInfo.name`` is the stage *class* name (``type(stage).__name__``), not
# the ``name=`` you may pass to a stage's constructor — match the class name.
stage_names = [s.name for s in program.dry_run()["cost"].stages]
assert "ReplicaBundleStage" in stage_names, f"Expected ReplicaBundleStage in {stage_names}"

program.run()
assert program.best_loss is not None
```

--------------------------------

### ProgramEnsemble.run

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/execution_workflows/program_ensembles.rst

Entry point for every ensemble. Blocks until the workflow finishes and returns the ensemble, so results are ready to aggregate as soon as it returns. Trains every sub-program before sampling any of them.

```APIDOC
## ProgramEnsemble.run

### Description
Entry point for every ensemble. Blocks until the workflow finishes and returns the ensemble, so results are ready to aggregate as soon as it returns. Trains every sub-program before sampling any of them.

### Method
run

### Parameters
None documented.

### Response
Returns the ensemble object.

### Request Example
```python
results = ensemble.run().aggregate_results()
```
```

--------------------------------

### Example test file layout for a new QAOAProblem subclass

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/development/testing.rst

Shows the layered test structure for a new problem: utility functions, problem class, QAOAProblem protocol hooks, QAOA integration, and ensemble integration. Use as a template when creating tests/qprog/problems/test_my_problem.py. Slow integration tests are marked with @pytest.mark.e2e.

```python
# tests/qprog/problems/test_my_problem.py

# --- 1. Utility functions ---
class TestBuildMyQubo:
    def test_returns_square_matrix(self): ...
    def test_rejects_invalid_input(self): ...

# --- 2. Problem class ---
class TestMyProblem:
    def test_cost_hamiltonian(self): ...
    def test_is_feasible(self): ...
    def test_compute_energy(self): ...
    def test_decode_fn(self): ...

# --- 3. QAOAProblem protocol hooks ---
class TestDecomposeMyProblem:
    def test_decompose_returns_subproblems(self): ...
    def test_extend_solution(self): ...

# --- 4. QAOA integration ---
class TestMyProblemQAOA:
    def test_runs_via_qaoa(self, default_test_simulator): ...

    @pytest.mark.e2e
    def test_e2e_solution(self, default_test_simulator): ...

# --- 5. Ensemble integration ---
class TestMyProblemEnsemble:
    def test_create_programs(self, dummy_simulator): ...

    @pytest.mark.e2e
    def test_partitioning_e2e(self, default_test_simulator): ...
```

--------------------------------

### PartitioningProgramEnsemble.run()

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/algorithms/combinatorial_optimization_qaoa_pce.rst

Executes the partitioned workflow on the ensemble. This method runs the configured quantum routine on each partition and must be called before aggregating results.

```APIDOC
## [RUN] PartitioningProgramEnsemble.run()

### Description
Executes the partitioned workflow on the ensemble. This method runs the configured quantum routine on each partition and must be called before aggregating results.

### Method
run

### Endpoint
ensemble.run()

### Parameters
None

### Response
None

### Request Example
```python
ensemble.run()
```
```

--------------------------------

### Set up partitioned portfolio problem with CommunityDecomposer and PartitioningProgramEnsemble

Source: https://github.com/qoroquantum/divi/blob/main/demos/portfolio_optimization/portfolio_optimization.ipynb

Builds a full portfolio QUBO, partitions it into communities using CommunityDecomposer with modularity method and max 20 variables per cluster, composes partitions with hybrid.SplatComposer, and creates a PartitioningProgramEnsemble with QAOA, MonteCarloOptimizer, and EarlyStopping. Prints the number of partitions created.

```python
import hybrid

from divi.qprog import EarlyStopping
from divi.qprog.ensembles import BeamSearchStrategy, PartitioningProgramEnsemble
from divi.qprog.problems import CommunityDecomposer, QUBOPartitioningConfig

MAX_PARTITION_SIZE = 20  # max assets per QAOA sub-problem

real_qubo = build_full_portfolio_qubo(
    real_returns, real_covariance, lambda_param=LAMBDA_PARAM
)

problem = BinaryOptimizationProblem(
    real_qubo,
    decomposer=CommunityDecomposer(
        QUBOPartitioningConfig(
            max_n_variables_per_cluster=MAX_PARTITION_SIZE,
            method="modularity",
            seed=42,
        )
    ),
    composer=hybrid.SplatComposer(),
)

ensemble = PartitioningProgramEnsemble(
    problem=problem,
    quantum_routine="qaoa",
    n_layers=2,
    optimizer=MonteCarloOptimizer(population_size=30, n_best_sets=5),
    max_iterations=10,
    early_stopping=EarlyStopping(patience=3),
    backend=backend,
)

print("Decomposing portfolio + creating sub-programs...")
ensemble.create_programs()
print(f"  {len(ensemble.programs)} partitions created")
```

--------------------------------

### Build documentation

Source: https://github.com/qoroquantum/divi/blob/main/CONTRIBUTING.md

Build the documentation by running make build in the docs directory.

```bash
cd docs
make build
```

--------------------------------

### Commit message examples

Source: https://github.com/qoroquantum/divi/blob/main/CONTRIBUTING.md

Follow Conventional Commits for commit messages. Examples include feat, fix, docs, and test prefixes.

```text
feat: add beam search aggregation strategy
fix: resolve duplicate object warnings in docs
docs: update backend execution guide with job configuration
test: add auth token resolution tests
```

--------------------------------

### ProgramEnsemble.sample_solution

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/execution_workflows/program_ensembles.rst

Samples solutions from pre-trained parameters across all sub-programs in one call. It takes trained parameters for each partition and only re-samples, without dispatching EXPECTATION jobs.

```APIDOC
## ProgramEnsemble.sample_solution

### Description
Samples solutions from pre-trained parameters across all sub-programs in one call. It takes trained parameters for each partition and only re-samples, without dispatching EXPECTATION jobs.

### Method
sample_solution

### Parameters
#### Parameters
- **params_per_program** (dict, optional) - Optional - Mapping of program_id to parameters. If None, each sub-program uses its own _best_params. Unknown program IDs raise ValueError; missing program IDs fall back to _best_params with a UserWarning.
- **blocking** (bool) - Optional - If True, blocks until sampling completes.
- **suppress_strict_warning** (bool, optional) - Optional - If True, suppresses the UserWarning about fallbacks.

### Response
#### Success Response
- **solutions** (list) - List of sampled solutions, one per sub-program.

### Request Example
```python
ensemble.sample_solution(blocking=True)
```

### Response Example
```python
# Return type is problem-dependent:
#   Graph  → list[(node_indices, energy)]
#   QUBO   → list[(solution_array, energy)]
for rank, (solution, energy) in enumerate(top_solutions, 1):
    print(f"{rank}. Energy: {energy:.6f}, Solution: {solution}")
```
```

--------------------------------

### QoroService API key .env configuration

Source: https://github.com/qoroquantum/divi/blob/main/demos/quantum_guided_cluster/quantum_guided_cluster.ipynb

Required environment file for cloud runs. Place in the repo root with your QoroService API key.

```bash
QORO_API_KEY="your_api_key_here"
```

--------------------------------

### Run PCE with DenseEncoding and SoftObjective

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/algorithms/combinatorial_optimization_qaoa_pce.rst

Sets up a PCE instance with a QUBO problem, DenseEncoding, SoftObjective, and MonteCarloOptimizer on a MaestroSimulator. After running, retrieves the top solution by energy and prints the decoded assignment and qubit count.

```python
import numpy as np

from divi.backends import MaestroSimulator
from divi.qprog.algorithms import PCE, DenseEncoding, SoftObjective
from divi.qprog.optimizers import MonteCarloOptimizer
from divi.qprog.problems import BinaryOptimizationProblem

qubo = np.array([[-1.0, 2.0], [0.0, 1.0]])
pce = PCE(
    problem=BinaryOptimizationProblem(qubo),
    encoding=DenseEncoding(),
    objective=SoftObjective(alpha=2.0),
    n_layers=2,
    optimizer=MonteCarloOptimizer(population_size=8),
    max_iterations=5,
    backend=MaestroSimulator(shots=2000),
    seed=42,
)
pce.run()

best = pce.get_top_solutions(
    n=1, include_decoded=True, sort_by="energy"
)[0]
print(f"Best solution: {best.decoded} (energy={best.energy})")
print(f"Qubits: {pce.n_qubits} for {pce.n_vars} variables")
```

--------------------------------

### MaxWeightMatchingProblem with Edge-Based Partitioning

Source: https://github.com/qoroquantum/divi/blob/main/docs/source/algorithms/combinatorial_optimization_qaoa_pce.rst

Solves the same matching problem using PartitioningProgramEnsemble with edge-based partitioning enabled via max_edges_per_partition=15 and partition_algorithm='kernighan_lin'. Prints the matching and total weight.

```python
   from divi.qprog.ensembles import PartitioningProgramEnsemble

   problem = MaxWeightMatchingProblem(
       G,
       penalty_weight=10.0,
       max_edges_per_partition=15,
       partition_algorithm="kernighan_lin",
   )

   ensemble = PartitioningProgramEnsemble(
       problem=problem,
       n_layers=2,
       optimizer=ScipyOptimizer(method=ScipyMethod.COBYLA),
       max_iterations=10,
       backend=MaestroSimulator(),
   )

   ensemble.run()
   matching, weight = ensemble.aggregate_results()
   print(f"Matching: {matching}, weight: {weight}")
```

--------------------------------

### Clone the repository

Source: https://github.com/qoroquantum/divi/blob/main/CONTRIBUTING.md

Fork the repository on GitHub and clone your fork to start contributing.

```bash
git clone https://github.com/your-username/divi.git
cd divi
```
