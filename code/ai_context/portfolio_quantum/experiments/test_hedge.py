import sys, numpy as np
sys.path.insert(0, "portfolio_quantum")
import qlns_core as qc, qlns, dayrelax as dr, portfolio_search as ps
inst = sys.argv[1]; lam = sys.argv[2]
p = ps.Problem(inst, lam)
v = np.zeros((p.T, p.n), dtype=np.int64)
s = qc.State(p, v)
rng = np.random.default_rng(0)
for t in range(p.T - 1):
    vs, mu = dr.solve_day(p, s.v, t)
    w = qlns.round_window(s, t, rng, 20)
    if w is None: print(t, "none"); continue
    tmp, moves, hw = w
    de, x = qc.oracle(tmp, moves, any_sign=True)
    v2 = tmp.v.copy()
    for (tt, i, d), on in zip(moves, x):
        if on: v2[tt, i] += d
    print(t, f"mu={mu:.0f} |v*|1={np.abs(vs).sum():.2f} max|v*|={np.abs(vs).max():.2f} supp={(np.abs(vs)>1e-6).sum()} M={len(moves)} hw={hw} "
          f"day gain vs empty={p.objective(v2) - s.obj} units={np.abs(v2[t]).sum()}", flush=True)
