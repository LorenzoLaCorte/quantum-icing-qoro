import sys, time, argparse, numpy as np
sys.path.insert(0, "portfolio_quantum")
import qlns_core as qc, windows as W, portfolio_search as ps

ap = argparse.ArgumentParser()
ap.add_argument("--inst", default="po_a050_t10_s01")
ap.add_argument("--lam", default="1e-3")
ap.add_argument("--K", type=int, default=9)
ap.add_argument("--iters", type=int, default=3000)
ap.add_argument("--start", default="best")
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--block", type=float, default=0.2)
a = ap.parse_args()
p = ps.Problem(a.inst, a.lam)
if a.start == "best":
    f = qc.best_known_file(p.stem); v = qc.load_v(p, f)
else:
    v = np.zeros((p.T, p.n), dtype=np.int64)
s = qc.State(p, v)
corr = W.corr_matrix(p)
rng = np.random.default_rng(a.seed)
print("start", s.obj, flush=True)
t0 = time.time(); stats = {}
for it in range(a.iters):
    if rng.random() < a.block:
        moves, kind = W.block_window(s, rng, K=max(3, a.K // 2), D=int(rng.integers(2, 4)), corr=corr)
    else:
        moves, kind = W.day_window(s, rng, a.K, corr=corr)
    if len(moves) > 22: moves = moves[:22]
    if not moves: continue
    de, x = qc.oracle(s, moves)
    if de < 0:
        s.apply(moves, x)
        stats[kind] = stats.get(kind, 0) + 1
    if it % 250 == 0:
        print(it, s.obj, f"{time.time()-t0:.0f}s", stats, flush=True)
print("final", s.obj, p.feasible(s.v), stats)
