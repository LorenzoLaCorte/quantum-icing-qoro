import time, warnings, numpy as np, dimod
warnings.filterwarnings("ignore")
from divi.backends import MaestroSimulator
from divi.qprog.algorithms import QAOA
from divi.qprog.optimizers import MonteCarloOptimizer
from divi.qprog.problems import BinaryOptimizationProblem
import logging; logging.disable(logging.WARNING)
rng = np.random.default_rng(0)
for n in (16, 20, 22, 24):
    Q = rng.normal(size=(n, n)); Q = np.triu(Q + Q.T); 
    Q /= np.abs(Q).max()
    bqm = dimod.BinaryQuadraticModel.from_qubo({(i, j): Q[i, j] for i in range(n) for j in range(i, n)})
    prob = BinaryOptimizationProblem(bqm)
    t0 = time.time()
    q = QAOA(prob, n_layers=2, optimizer=MonteCarloOptimizer(population_size=8), max_iterations=2,
             backend=MaestroSimulator(shots=4000, force_sampling=True), seed=1)
    q.run()
    top = q.get_top_solutions(n=200)
    dt = time.time() - t0
    # brute check that bitstring index k <-> variable k
    best = min(top, key=lambda s: bqm.energy({k: int(b) for k, b in enumerate(s.bitstring)}))
    e = bqm.energy({k: int(b) for k, b in enumerate(best.bitstring)})
    print(n, f"{dt:.1f}s circuits={q.total_circuit_count} ntop={len(top)} best_e={e:.3f}", flush=True)
