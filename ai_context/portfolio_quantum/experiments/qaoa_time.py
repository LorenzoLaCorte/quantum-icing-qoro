import sys, time, numpy as np, dimod, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.WARNING)
from divi.backends import MaestroSimulator
from divi.hamiltonians import xy_mixer
from divi.qprog.algorithms import QAOA
from divi.qprog.initial_states import DickeState
from divi.qprog.optimizers import MonteCarloOptimizer
from divi.qprog.problems import BinaryOptimizationProblem
rng = np.random.default_rng(0)
prm = np.array([0.1, 2.81, 0.3, 1.69, 0.06, 1.58, 0.73, -0.49, 1.26, -0.28])
for M in (14, 16, 18):
    Q = rng.normal(size=(M, M)); Q = np.triu(Q + Q.T)
    bqm = dimod.BinaryQuadraticModel.from_qubo({(i, j): Q[i, j] for i in range(M) for j in range(i, M)})
    for iters in (0, 1):
        try:
            t0 = time.time()
            prog = QAOA(BinaryOptimizationProblem(bqm), initial_state=DickeState(M // 2), n_layers=5,
                        optimizer=MonteCarloOptimizer(population_size=1, n_best_sets=1), max_iterations=iters,
                        backend=MaestroSimulator(shots=4000), seed=1)
            prog.mixer_hamiltonian = xy_mixer([(k, (k + 1) % M) for k in range(M)], n_qubits=M)
            prog.run(initial_params=prm[None, :])
            n = len(prog.get_top_solutions(n=4000))
            print(M, "iters", iters, f"{time.time()-t0:.2f}s circuits={prog.total_circuit_count} distinct={n}", flush=True)
        except Exception as e:
            print(M, "iters", iters, "ERR", type(e).__name__, str(e)[:120])
