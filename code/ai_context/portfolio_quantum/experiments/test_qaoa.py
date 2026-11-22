import sys, time, numpy as np
sys.path.insert(0, "portfolio_quantum")
import qlns_core as qc, qlns, qaoa_solver as qs, portfolio_search as ps
p = ps.Problem("po_a050_t10_s01", "1e-3")
s = qc.State(p, qc.load_v(p, qc.best_known_file(p.stem)))
rng = np.random.default_rng(5)
layers = int(sys.argv[1]) if len(sys.argv) > 1 else 2
sol = qs.QAOASolver(layers=layers, shots=int(sys.argv[2]) if len(sys.argv) > 2 else 2000, mc_pop=6, mc_iter=2, seed=1)
ora = qlns.OracleSolver()
for k in range(8):
    t = k % (p.T - 1)
    w = qlns.round_window(s, t, rng, 16, noise=0.1 if k > 3 else 0.0)
    tmp, moves, hw = w
    a, b, _ = qc.build_qubo(tmp, moves)
    t0 = time.time(); xs = sol.solve(tmp, moves, True, hw=hw); dt = time.time() - t0
    feas = qlns._distinct_feasible(tmp, moves, xs, a, b)
    rev = qlns._distinct_feasible(tmp, moves, [x[::-1].copy() for x in xs], a, b)
    xo = ora.solve(tmp, moves, True)[0]; eo = qc.energy(a, b, xo)
    # rank of the oracle optimum among sampled bitstrings (by probability order)
    pos = next((r for r, x in enumerate(xs) if np.array_equal(x, xo)), None)
    hwset = {int(x.sum()) for x in xs}
    print(f"t={t} M={len(moves)} hw={hw} qaoa_best={feas[0][0] if feas else None} rev_best={rev[0][0] if rev else None} oracle={eo} "
          f"opt_rank={pos} nsamp={len(xs)} weights={sorted(hwset)[:4]} {dt:.1f}s circuits={sol.circuits}", flush=True)
print("library", sol.library)
