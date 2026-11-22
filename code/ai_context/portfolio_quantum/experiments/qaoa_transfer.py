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
M_CAP = int(sys.argv[1]) if len(sys.argv) > 1 else 14
wins = []
for t in range(6):
    tmp, moves, hw = qlns.round_window(s, t, rng, M_CAP)
    M = len(moves); a, b, _ = qc.build_qubo(tmp, moves)
    combos = list(itertools.combinations(range(M), hw))
    X = np.zeros((len(combos), M), dtype=np.int64)
    for r, c in enumerate(combos): X[r, list(c)] = 1
    E = (X @ a) + np.einsum("ri,ij,rj->r", X, b, X)
    wins.append((t, M, hw, a, b, X, E))
    print("window", t, "M", M, "hw", hw, "subspace", len(E), "gap1-2", np.sort(E)[1]-np.sort(E)[0], flush=True)
def program(w, layers, opt, iters, pop=1):
    t, M, hw, a, b, X, E = w
    scale = float(E.std())
    quad = {(m, m): a[m] / scale for m in range(M)}
    for m in range(M):
        for k in range(m + 1, M):
            if b[m, k]: quad[(m, k)] = b[m, k] / scale
    prog = QAOA(BinaryOptimizationProblem(dimod.BinaryQuadraticModel.from_qubo(quad)), initial_state=DickeState(hw),
                n_layers=layers, optimizer=opt, max_iterations=iters, backend=MaestroSimulator(shots=2000), seed=7)
    prog.mixer_hamiltonian = xy_mixer([(k, (k + 1) % M) for k in range(M)], n_qubits=M)
    return prog
def evaluate(w, prog):
    t, M, hw, a, b, X, E = w
    sols = prog.get_top_solutions(n=2000)
    keyopt = "".join(map(str, X[np.argmin(E)]))
    popt = sum(s_.prob for s_ in sols if s_.bitstring[:M] == keyopt)
    best = min(qc.energy(a, b, np.array([int(c) for c in s_.bitstring[:M]])) for s_ in sols)
    rank = int((E < best).sum())
    return popt * len(E), rank
for layers in (3, 5):
    base = np.array([x for k in range(layers) for x in (0.8*(k+.5)/layers, 0.8*(1-(k+.5)/layers))])
    t0 = time.time()
    prog = program(wins[0], layers, ScipyOptimizer(method=ScipyMethod.COBYLA), 120)
    prog.run(initial_params=base[None, :])
    params = np.asarray(prog.best_params).ravel()
    enr, rank = evaluate(wins[0], prog)
    print(f"p={layers} trained on w0: enrichment={enr:.1f} best_rank={rank} circ={prog.total_circuit_count} {time.time()-t0:.0f}s params={np.round(params,2)}", flush=True)
    for w in wins[1:]:
        for name, prm in (("transfer", params), ("ramp", base)):
            pr = program(w, layers, MonteCarloOptimizer(population_size=1, n_best_sets=1), 1)
            pr.run(initial_params=prm[None, :])
            enr, rank = evaluate(w, pr)
            print(f"   w{w[0]} {name:8s}: enrichment={enr:.1f} best_rank={rank}", flush=True)
