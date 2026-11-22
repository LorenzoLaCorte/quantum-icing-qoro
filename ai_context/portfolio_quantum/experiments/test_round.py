import sys, time, numpy as np
sys.path.insert(0, "portfolio_quantum")
import qlns_core as qc, dayrelax as dr, portfolio_search as ps
inst, lam = sys.argv[1], sys.argv[2]
K = int(sys.argv[3]) if len(sys.argv) > 3 else 20
p = ps.Problem(inst, lam)
f = qc.best_known_file(p.stem); v0 = qc.load_v(p, f); obj0 = p.objective(v0)
print("incumbent", obj0)
tot = 0
for t in range(p.T - 1):
    t0 = time.time()
    vs, mu = dr.solve_day(p, v0, t)
    # continuous day cost vs incumbent: evaluate relaxation objective is not integer; compare by rounding
    order = np.argsort(-np.abs(vs))
    win = [i for i in order[:K] if abs(vs[i]) > 1e-6]
    base = np.trunc(vs).astype(np.int64)
    base[[i for i in range(p.n) if i not in win]] = 0
    vb = v0.copy(); vb[t] = base
    s = qc.State(p, vb)
    moves = [(t, int(i), int(np.sign(vs[i]))) for i in win if abs(vs[i] - np.trunc(vs[i])) > 1e-6]
    de, x = qc.oracle(s, moves, any_sign=True)
    if de is None:
        print(t, "no feasible rounding"); continue
    s.apply(moves, x)
    d = s.obj - obj0
    tot += min(d, 0)
    print(t, f"mu={mu:.0f} |v*|1={np.abs(vs).sum():.1f} supp={int((np.abs(vs)>1e-6).sum())} moves={len(moves)} "
          f"rounded day: dE vs incumbent = {d:+d}  ({time.time()-t0:.2f}s)", flush=True)
print("sum of per-day improvements", tot)
