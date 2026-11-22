import sys, numpy as np
sys.path.insert(0, "portfolio_quantum")
import qlns_core as qc, portfolio_search as ps
p = ps.Problem("po_a050_t10_s01", "1e-3")
f = qc.best_known_file(p.stem); print(f, ps.read_objective(f))
s = qc.State(p, qc.load_v(p, f)); print("obj", s.obj)
rng = np.random.default_rng(0)
bad = 0
for trial in range(300):
    T = p.T
    days = sorted(rng.choice(T - 1, size=rng.integers(1, 4), replace=False))
    moves, used = [], set()
    for t in days:
        for i in rng.choice(p.n, size=5, replace=False):
            for d in [[1], [-1], [1, -1]][rng.integers(3)]:
                x0 = s.v[t, i]
                if abs(x0 + d) <= 3 and (t, i, d) not in used:
                    moves.append((int(t), int(i), int(d))); used.add((t, i, d))
    # forbid 3-way: drop double-move slots whose asset appears on adjacent days
    a, b, bud = qc.build_qubo(s, moves)
    for _ in range(20):
        x = rng.integers(0, 2, len(moves))
        v2 = s.v.copy()
        for (t, i, d), on in zip(moves, x):
            if on: v2[t, i] += d
        slots = {}
        for (t, i, d) in moves: slots.setdefault((t, i), []).append(d)
        threeway = any(len(slots[(t, i)]) == 2 and ((t - 1, i) in slots or (t + 1, i) in slots) for (t, i) in slots)
        if threeway or not p.feasible(v2): continue
        de = p.objective(v2) - s.obj
        if de != qc.energy(a, b, x): bad += 1
print("mismatches", bad)
