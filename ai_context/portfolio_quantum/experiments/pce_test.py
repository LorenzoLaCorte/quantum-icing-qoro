"""PCE (Divi) on whole-day rounding windows of a400_t15 vs exact optimum and relaxation seed.

Run from the repo root: .venv/bin/python ai_context/portfolio_quantum/experiments/pce_test.py [K] [days]
"""
import sys, time, warnings, logging
import numpy as np, dimod
warnings.filterwarnings("ignore"); logging.disable(logging.WARNING)
sys.path.insert(0, "portfolio_quantum")
import qlns_core as qc, qlns, qaoa_solver as qs, portfolio_search as ps
from pathlib import Path
from divi.backends import MaestroSimulator
from divi.qprog.algorithms import PCE, PolyEncoding, SoftObjective
from divi.qprog.optimizers import ScipyOptimizer, ScipyMethod
from divi.qprog.problems import BinaryOptimizationProblem

K = int(sys.argv[1]) if len(sys.argv) > 1 else 28
NDAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 4
p = ps.Problem("po_a400_t15_orig", "1e-3")
start = min(list(Path("portfolio_quantum/solutions/po_a400_t15_orig_b100_l1e-3").glob("*.sol")), key=ps.read_objective)
s = qc.State(p, qc.load_v(p, start))
print("start", s.obj, start.name, flush=True)
rng = np.random.default_rng(11)
days = rng.choice(p.T - 1, size=NDAYS, replace=False)

def feasible_and_E(tmp, moves, X, a, b):
    best = (None, None)
    for x in X:
        if qc.feasible_x(tmp, moves, x):
            e = qc.energy(a, b, x)
            if best[0] is None or e < best[0]:
                best = (e, x)
    return best

def topk(scores, moves, hw, tmp):
    """Exactly hw selected moves; '+'/'-' counts inside the capital range (like round_seed)."""
    seed, _ = qlns.round_seed(tmp, moves, hw, (scores - scores.min()) / (np.ptp(scores) + 1e-12))
    return seed

tot = {"oracle": 0, "seed": 0, "pce_samples": 0, "pce_topk": 0}
for t in days:
    t = int(t)
    tmp, moves, hw = qlns.round_window(s, t, rng, K)
    prior = qlns.round_window.prior
    M = len(moves)
    a, b, _ = qc.build_qubo(tmp, moves)
    thr = s.obj - p.objective(tmp.v)          # window energy at which the day equals the incumbent
    t0 = time.time(); eo, xo = qc.oracle(tmp, moves, any_sign=True); t_or = time.time() - t0
    seed, groups = qlns.round_seed(tmp, moves, hw, prior) if hw is not None else (None, None)
    es = qc.energy(a, b, seed) if seed is not None else None
    # PCE on the exact rounding QUBO + cardinality penalty (normalised by the energy std)
    scale = qs.energy_std(a, b, M, hw, rng)
    Q = {(m, m): a[m] / scale for m in range(M)}
    for m in range(M):
        for k in range(m + 1, M):
            if b[m, k]: Q[(m, k)] = b[m, k] / scale
    bqm = dimod.BinaryQuadraticModel.from_qubo(Q)
    if hw is not None:
        pen = dimod.BinaryQuadraticModel("BINARY")
        pen.add_linear_equality_constraint([(m, 1.0) for m in range(M)], 1.0, -float(hw))
        pen.scale(1.0); bqm.update(pen)
    t0 = time.time()
    pce = PCE(BinaryOptimizationProblem(bqm), encoding=PolyEncoding(), objective=SoftObjective(alpha=2.0),
              n_layers=4, optimizer=ScipyOptimizer(method=ScipyMethod.COBYLA), max_iterations=250,
              backend=MaestroSimulator(shots=4000), seed=int(t))
    pce.run()
    sols = pce.get_top_solutions(n=2000, min_prob=0.0, sort_by="energy")
    X = [np.array([int(c) for c in so.bitstring[:M]]) for so in sols]
    ep, _ = feasible_and_E(tmp, moves, X, a, b)
    z = pce._variable_expectations(np.atleast_2d(pce.best_params))[0][:M]
    xk = topk(z, moves, hw, tmp) if hw is not None else (z > 0).astype(int)
    ek = qc.energy(a, b, xk) if xk is not None and qc.feasible_x(tmp, moves, xk) else None
    t_pce = time.time() - t0
    print(f"day {t}: M={M} hw={hw} qubits={pce.n_qubits} | oracle {eo} ({t_or:.0f}s) | seed {es} | "
          f"PCE samples {ep} | PCE top-k {ek} | incumbent level {thr} | PCE {t_pce:.0f}s, {pce.total_circuit_count} circ", flush=True)
    for name, e in (("oracle", eo), ("seed", es), ("pce_samples", ep), ("pce_topk", ek)):
        if e is not None:
            tot[name] += min(0, e - thr)
print("sum of day improvements vs incumbent:", tot, flush=True)
