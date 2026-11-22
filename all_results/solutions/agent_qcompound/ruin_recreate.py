"""Node-level ruin & recreate for network24: delete node k, polish the 23-node remainder
(2-exchange descent on the demand without k), re-insert k in the best of all arc-pair slots,
then 2-exchange descent on the full instance. Classical LP-only (no Divi), one process."""
import sys, time, itertools, numpy as np
sys.path.insert(0, '.'); sys.path.insert(0, 'solutions/agent_qcompound')
import memguard; memguard.start(min_mb=900)
import qoblib_tools as qt
from network_ils import WarmLP, move_2ex
import bank

N = 24; D = qt.load_network_demand(N)
OUT = 'solutions/agent_qcompound/rr'
T_END = time.time() + float(sys.argv[1]) * 60
rng = np.random.default_rng(int(sys.argv[2]) if len(sys.argv) > 2 else 0)
_, best, _ = qt.read_network_solution('deliverables/network24/network24.sol')
best = [tuple(a) for a in best]
W24 = WarmLP(D, best); best_z, _ = W24.solve(best)
print('start', best_z, flush=True)

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
                arcs, z = new, z2; W.solve(arcs); basis = W.h.getBasis(); improved = True
                break
    return arcs, z

order = list(rng.permutation(N))
for k in order:
    if time.time() > T_END - 60: break
    t0 = time.time()
    others = [v for v in range(N) if v != k]; idx = {v: i for i, v in enumerate(others)}
    Dk = D[np.ix_(others, others)]
    keep = [a for a in best if k not in a]
    ins = [i for i, j in best if j == k]; outs = [j for i, j in best if i == k]
    cands = []
    for perm in itertools.permutations(outs):
        new = keep + list(zip(ins, perm))
        if all(u != v for u, v in new) and len(set(new)) == len(new): cands.append(new)
    if not cands: continue
    sub = [[(idx[u], idx[v]) for u, v in c] for c in cands]
    W23 = WarmLP(Dk, sub[0])
    zs = [W23.solve(s)[0] for s in sub]; s = sub[int(np.argmin(zs))]; z23 = min(zs)
    s, z23p = descent(W23, s, z23, time.time() + 90)
    small = [(others[u], others[v]) for u, v in s]
    # re-insert k: remove (a,b),(c,d), add (a,k),(k,b),(c,k),(k,d)
    W24.solve(best); res = []
    for p, q in itertools.combinations(range(len(small)), 2):
        (a, b), (c, d) = small[p], small[q]
        if a == c or b == d: continue
        new = list(small); new[p] = (a, k); new[q] = (c, k); new += [(k, b), (k, d)]
        if len(set(new)) < 48 or any(u == v for u, v in new): continue
        z, _ = W24.solve(new)
        res.append((z, new))
    res.sort(key=lambda r: r[0])
    line = f'k={k} sub23 {z23:.0f}->{z23p:.0f} insert best {res[0][0]:.0f}'
    for z, new in res[:2]:
        arcs, z2 = descent(W24, new, z, min(T_END, time.time() + 150))
        line += f' | desc {z:.0f}->{z2:.0f}'
        if z2 < best_z - 1e-3:
            best, best_z = arcs, z2
            print('NEW BEST', best_z, flush=True)
            bank.bank(24, best, f'node ruin&recreate k={k} + 2ex descent', OUT)
    print(line, f'({time.time()-t0:.0f}s) best {best_z:.0f}', flush=True)
print('done best', best_z)
