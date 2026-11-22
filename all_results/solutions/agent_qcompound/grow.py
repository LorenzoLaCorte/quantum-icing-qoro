"""Grow: insert node n-1 into a good (n-1)-node topology at every arc pair, LP all, descend the best few.
usage: grow.py small.sol n n_desc minutes"""
import sys, time, itertools, numpy as np
sys.path.insert(0, '.'); sys.path.insert(0, 'solutions/agent_qcompound')
import memguard; memguard.start(min_mb=900)
import qoblib_tools as qt
from network_ils import WarmLP, move_2ex
import bank
src, n, n_desc, minutes = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
T_END = time.time() + minutes * 60
D = qt.load_network_demand(n); k = n - 1
_, small, _ = qt.read_network_solution(src); small = [tuple(a) for a in small]
rng = np.random.default_rng(1)
def descent(W, arcs, z, tlim):
    arcs = list(arcs); W.solve(arcs); basis = W.h.getBasis(); m = len(arcs)
    improved = True
    while improved and time.time() < tlim:
        improved = False
        pairs = list(itertools.combinations(range(m), 2)); rng.shuffle(pairs)
        for p, q in pairs:
            if time.time() > tlim: break
            new = move_2ex(arcs, p, q)
            if new is None or len(set(new)) < m: continue
            z2, _ = W.solve(new, cutoff=z - 1e-3, basis=basis)
            if z2 is not None and z2 < z - 1e-3:
                arcs, z = new, z2; W.solve(arcs); basis = W.h.getBasis(); improved = True; break
    return arcs, z
W = None; res = []
for p, q in itertools.combinations(range(len(small)), 2):
    (a, b), (c, d) = small[p], small[q]
    if a == c or b == d: continue
    new = list(small); new[p] = (a, k); new[q] = (c, k); new += [(k, b), (k, d)]
    if len(set(new)) < 2 * n or any(u == v for u, v in new): continue
    if W is None: W = WarmLP(D, new)
    res.append((W.solve(new)[0], new))
res.sort(key=lambda r: r[0])
print('insertions', len(res), 'best', [round(r[0]) for r in res[:8]], flush=True)
best = None
for z, new in res[:n_desc]:
    if time.time() > T_END: break
    arcs, z2 = descent(W, new, z, T_END)
    print(f'desc {z:.0f} -> {z2:.0f}', flush=True)
    if best is None or z2 < best[0]: best = (z2, arcs)
print('GROW BEST', best[0], flush=True)
bank.bank(n, best[1], f'grow from {src} + 2ex descent', 'solutions/agent_qcompound/grow')
