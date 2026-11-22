import sys, time, numpy as np
sys.path.insert(0, "portfolio_quantum")
import qlns_core as qc, qlns, qaoa_solver as qs, portfolio_search as ps
inst, lam, M = sys.argv[1], sys.argv[2], int(sys.argv[3])
p = ps.Problem(inst, lam)
s = qc.State(p, qc.load_v(p, qc.best_known_file(p.stem)))
rng = np.random.default_rng(7)
sol = qs.QAOASolver(layers=5, shots=4000, seed=1, retrain_every=10**9, train_iters=120, log=lambda *a: print(*a, flush=True))
import json; lib = json.load(open("portfolio_quantum/angles/a050_l1e-3.json")); sol.library["xy"] = np.array(lib["xy_p5"])
days = list(range(p.T - 1)); rng.shuffle(days)
tot = {"dicke": 0, "warm": 0, "oracle": 0}
for t in days[:6]:
    tmp, moves, hw = qlns.round_window(s, t, rng, M)
    prior = qlns.round_window.prior
    if hw is None: print("free window, skip"); continue
    seed, groups = qlns.round_seed(tmp, moves, hw, prior)
    if seed is None: print("no feasible count split"); continue
    a, b, _ = qc.build_qubo(tmp, moves)
    eo = qc.energy(a, b, qc.oracle(tmp, moves, any_sign=True)[1])
    inc = s.obj - p.objective(tmp.v)  # energy (vs base) that the incumbent day corresponds to: improve iff E < -(base - incumbent)
    thr = s.obj - p.objective(tmp.v)
    out = [f"t={t} M={len(moves)} hw={hw} oracle={eo} seed={qc.energy(a, b, seed)} incumbent_level={thr}"]
    out.append(f"groups={'yes' if groups else 'no'}")
    for name, sd in (("dicke", None), ("warm", seed)):
        t0 = time.time()
        xs = sol.solve(tmp, moves, True, hw=hw, seed=sd, groups=groups if sd is not None else None)
        c = qlns._distinct_feasible(tmp, moves, xs, a, b)
        e = c[0][0] if c else 10**9
        out.append(f"{name}={e} ({len(xs)} distinct, {time.time()-t0:.1f}s)")
        tot[name] += min(0, e - thr)
    tot["oracle"] += min(0, eo - thr)
    print("  ".join(out), flush=True)
print("total improvement vs incumbent days:", tot)
