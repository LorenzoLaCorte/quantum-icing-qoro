import sys, time, itertools, numpy as np, dimod, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.WARNING)
sys.path.insert(0, "portfolio_quantum")
import qlns_core as qc, qlns, portfolio_search as ps
from divi.backends import MaestroSimulator
from divi.hamiltonians import xy_mixer
from divi.qprog.algorithms import QAOA
from divi.qprog.initial_states import DickeState
from divi.qprog.optimizers import MonteCarloOptimizer, ScipyOptimizer, ScipyMethod
from divi.qprog.problems import BinaryOptimizationProblem
p = ps.Problem("po_a050_t10_s01", "1e-3")
s = qc.State(p, qc.load_v(p, qc.best_known_file(p.stem)))
rng = np.random.default_rng(5)
tmp, moves, hw = qlns.round_window(s, 1, rng, 16)
M = len(moves); a, b, _ = qc.build_qubo(tmp, moves)
# energies of whole subspace
combos = [c for c in itertools.combinations(range(M), hw)]
E = []
for c in combos:
    x = np.zeros(M, dtype=np.int64); x[list(c)] = 1; E.append(qc.energy(a, b, x))
E = np.array(E); order = np.argsort(E); Emin = E[order[0]]
print("M", M, "hw", hw, "subspace", len(E), "Emin", Emin, "E2", E[order[1]], "median", np.median(E), "std", E.std())
xopt = np.zeros(M, dtype=np.int64); xopt[list(combos[order[0]])] = 1; key = "".join(map(str, xopt))
def run(scale_mode, layers, mixer, pop, iters, init):
    scale = float(max(np.abs(a).max(), np.abs(b).max())) if scale_mode == "max" else float(E.std())
    quad = {(m, m): a[m] / scale for m in range(M)}
    for m in range(M):
        for k in range(m + 1, M):
            if b[m, k]: quad[(m, k)] = b[m, k] / scale
    bqm = dimod.BinaryQuadraticModel.from_qubo(quad)
    prog = QAOA(BinaryOptimizationProblem(bqm), initial_state=DickeState(hw), n_layers=layers,
                optimizer=MonteCarloOptimizer(population_size=pop), max_iterations=iters,
                backend=MaestroSimulator(shots=4000), seed=7)
    edges = [(k, (k + 1) % M) for k in range(M)] if mixer == "ring" else list(itertools.combinations(range(M), 2))
    prog.mixer_hamiltonian = xy_mixer(edges, n_qubits=M)
    t0 = time.time()
    prog.run(initial_params=init(layers, pop))
    sols = prog.get_top_solutions(n=4000)
    probs = {s_.bitstring[:M]: s_.prob for s_ in sols}
    es = sorted(qc.energy(a, b, np.array([int(c) for c in bs])) for bs in probs)
    rank = next((i for i, s_ in enumerate(sols) if s_.bitstring[:M] == key), None)
    print(f"{scale_mode:4s} p={layers} {mixer:4s} pop={pop} it={iters}: p(opt)={probs.get(key,0):.4f} rank={rank} best={es[0]} "
          f"loss={prog.best_loss:.3f} circ={prog.total_circuit_count} {time.time()-t0:.1f}s params={np.round(prog.best_params,2)}", flush=True)
def ramp(g, bb):
    def f(L, pop):
        base = np.array([x for k in range(L) for x in (g*(k+.5)/L, bb*(1-(k+.5)/L))])
        r = np.random.default_rng(0)
        return np.array([base] + [base + 0.1*r.normal(size=base.size) for _ in range(pop-1)])
    return f
for sm in ("std", "max"):
    for g in (0.3, 1.0, 3.0):
        run(sm, 2, "ring", 8, 4, ramp(g, 0.6))
run("std", 3, "ring", 8, 6, ramp(1.0, 0.6))
run("std", 3, "full", 8, 6, ramp(1.0, 0.6))
run("std", 4, "ring", 10, 10, ramp(1.0, 0.6))
