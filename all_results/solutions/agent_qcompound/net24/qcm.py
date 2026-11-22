"""Quantum Compound Moves (QCM) for QOBLIB network24.
usage: python qcm.py MODE SEED N DURATION_S   (MODE = A: QAOA, B: PCE + ridge refit)
"""
import sys, os, time, math, itertools, warnings, json, gc, ctypes
sys.path[:0] = [os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if os.path.basename(os.path.dirname(os.path.abspath(__file__))) in ('small', 'net24') else os.path.dirname(os.path.abspath(__file__)), '.']
import memguard; memguard.start(min_mb=900)
warnings.filterwarnings("ignore")
import numpy as np, dimod
import qoblib_tools as qt
from network_ils import WarmLP, move_2ex
import bank
from dwave.samplers import SimulatedAnnealingSampler
from divi.backends import MaestroSimulator
from divi.qprog.algorithms import QAOA, PCE, PolyEncoding, SoftObjective
from divi.qprog.optimizers import MonteCarloOptimizer
from divi.qprog.problems import BinaryOptimizationProblem

MODE, SEED, DUR = sys.argv[1], int(sys.argv[2]), float(sys.argv[4])
NS = [int(x) for x in sys.argv[3].split(',')]
SMOKE = len(sys.argv) > 5 and sys.argv[5] == 'smoke'
REPAIR = 'repair' in sys.argv[5:]
T_END = time.time() + DUR
OUT = 'solutions/agent_qcompound/net24'
LOG = open(f'{OUT}/log_{MODE}{SEED}.txt', 'a')
def log(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); LOG.write(s + '\n'); LOG.flush()

rng = np.random.default_rng(SEED)
n = 24; D = qt.load_network_demand(n)
_, arcs0, _ = qt.read_network_solution('deliverables/network24/network24.sol')
arcs0 = [tuple(map(int, a)) for a in arcs0]
W = WarmLP(D, arcs0)
NLP = 0
def lp(arcs, cutoff=None, basis=None):
    global NLP; NLP += 1
    return W.solve(arcs, cutoff=cutoff, basis=basis)
def score(z): return math.ceil(z - 1e-6)

cur = list(arcs0); zc, du = lp(cur)
best, zbest = list(cur), zc
best_score = score(zc)
log(f'start mode={MODE} seed={SEED} N={NS} z0={zc:.2f} score={best_score}')

def try_best(arcs, z, how):
    global best, zbest, best_score
    if z is None or not np.isfinite(z): return False
    if score(z) < best_score:
        best, zbest, best_score = list(arcs), z, score(z)
        log(f'*** NEW BEST {best_score} (z={z:.2f}) via {how}')
        try:
            r = bank.bank(24, best, f'QCM seed{SEED}: {how}', OUT); log('bank ->', r)
        except Exception as e: log('bank error', e)
        return True
    return False

def apply_moves(arcs, moves):
    """moves = list of (p,q) with disjoint slots; returns new list or None."""
    new = list(arcs)
    for p, q in moves:
        (a, b), (c, d) = arcs[p], arcs[q]
        if a == d or c == b or a == c or b == d: return None
        new[p], new[q] = (a, d), (c, b)
    if len(set(new)) < 48: return None
    return new

def sample_quantum(bqm, nvar, seed, mode):
    t = time.time()
    if mode == 'A':
        prog = QAOA(BinaryOptimizationProblem(bqm), n_layers=2, optimizer=MonteCarloOptimizer(population_size=20),
                    max_iterations=5, backend=MaestroSimulator(shots=10000), seed=seed)
        prog.run(); sols = prog.get_top_solutions(n=3000)
    else:
        prog = PCE(BinaryOptimizationProblem(bqm), encoding=PolyEncoding(), objective=SoftObjective(alpha=2.0), n_layers=2,
                   optimizer=MonteCarloOptimizer(population_size=40), max_iterations=80,
                   backend=MaestroSimulator(shots=10000), seed=seed)
        prog.run(); sols = prog.get_top_solutions(n=3000, min_prob=0.0, sort_by="energy")
    Y = np.array([[int(ch) for ch in s.bitstring] for s in sols], dtype=np.int8)
    assert Y.shape[1] == nvar, (Y.shape, nvar)
    nc = getattr(prog, 'total_circuit_count', -1)
    del prog, sols; gc.collect()
    try: ctypes.CDLL('libc.so.6').malloc_trim(0)
    except Exception: pass
    return Y, time.time() - t, nc

def bqm_energies(Y, lin, Q):
    Yf = Y.astype(float)
    return Yf @ lin + np.einsum('ki,ij,kj->k', Yf, Q, Yf)

def make_bqm(lin, Q):
    return dimod.BinaryQuadraticModel({i: float(lin[i]) for i in range(len(lin))},
                                      {(i, j): float(Q[i, j]) for i in range(len(lin)) for j in range(i + 1, len(lin)) if Q[i, j] != 0},
                                      0.0, dimod.BINARY)

tabu = {}  # arc -> iteration until which it may not be re-added
it = 0; fails = 0; total_compounds = 0
SA = SimulatedAnnealingSampler()
while time.time() < T_END - 30:
    it += 1; t_it = time.time()
    mode = MODE[(it - 1) % len(MODE)]; N = NS[(it - 1) % len(NS)]
    zc, du = lp(cur); basis = W.h.getBasis()
    # 1. all 2-exchanges
    cut = zc * 1.06; singles = []
    for p, q in itertools.combinations(range(48), 2):
        new = move_2ex(cur, p, q)
        if new is None or len(set(new)) < 48: continue
        z, _ = lp(new, cutoff=cut, basis=basis)
        if z is None or not np.isfinite(z): continue
        added = (new[p], new[q])
        if any(tabu.get(a, 0) >= it for a in added) and score(z) >= best_score: continue
        singles.append((z, p, q))
        try_best(new, z, 'single 2-exchange')
    lp(cur, basis=basis); basis = W.h.getBasis()
    singles.sort()
    if not singles: log('no singles'); cur = list(best); continue
    if singles[0][0] < zc - 1e-6:  # descent step
        z, p, q = singles[0]; cur = move_2ex(cur, p, q)
        log(f'it{it} descent z {zc:.0f}->{z:.0f} best {best_score} nLP {NLP} t {time.time()-t_it:.1f}s'); continue
    # 2. candidates
    if mode == 'B':
        key = [(z - zc - 0.05 * zc * (du[p] + du[q])) * (1 + 0.3 * rng.random()) for z, p, q in singles]
    else:
        key = [(z - zc) * (1 + 0.3 * rng.random()) for z, p, q in singles]
    order = np.argsort(key); use = np.zeros(48, int); cand = []
    for k in order:
        z, p, q = singles[k]
        if use[p] >= 2 or use[q] >= 2: continue
        use[p] += 1; use[q] += 1; cand.append((z - zc, p, q))
        if len(cand) == N: break
    Nc = len(cand)
    dl = np.array([c[0] for c in cand]); mv = [(c[1], c[2]) for c in cand]
    dcap = 2 * dl.max()
    # 3. exact pairs
    J = np.zeros((Nc, Nc)); conflict = np.zeros((Nc, Nc), bool); pairs_eval = []
    for i, j in itertools.combinations(range(Nc), 2):
        if len({*mv[i], *mv[j]}) < 4: conflict[i, j] = True; continue
        new = apply_moves(cur, [mv[i], mv[j]])
        if new is None: conflict[i, j] = True; continue
        z, _ = lp(new, cutoff=zc + dcap, basis=basis)
        dz = dcap if (z is None or not np.isfinite(z)) else z - zc
        J[i, j] = dz - dl[i] - dl[j]
        pairs_eval.append((zc + dz, (i, j)))
        if z is not None: try_best(new, z, f'exact pair step it{it}')
    lp(cur, basis=basis)
    # 4. QUBO (normalised); cardinality penalty steers to K moves
    K = int(rng.integers(3, 6))
    s = max(np.abs(dl).max(), np.abs(J).max()); P = 2.0
    lin = dl / s; Q = J / s
    Q[conflict] = P
    gam = 0.3 * dl.mean() / s
    lin = lin + gam * (1 - 2 * K); Q = Q + 2 * gam * np.triu(np.ones((Nc, Nc)), 1)
    bqm = make_bqm(lin, Q)
    feats_i, feats_j = np.triu_indices(Nc, 1)
    data_Y, data_t = [], []
    def evaluate(Y, tag, kmax):
        """LP-evaluate the best (by model energy) distinct conflict-free samples with >=3 moves."""
        global total_compounds
        E = bqm_energies(Y, lin, Q); seen = set(); res = []; Erep = []
        for k in np.argsort(E):
            idx = list(np.flatnonzero(Y[k]))
            if REPAIR:  # greedy decode: drop the move with most conflicts until conflict-free
                while len(idx) > 1:
                    C = (conflict | conflict.T)[np.ix_(idx, idx)].sum(1)
                    if C.max() == 0: break
                    idx.pop(int(np.argmax(C + 1e-3 * dl[idx])))
            y = np.zeros(Nc, np.int8); y[idx] = 1; key_ = y.tobytes()
            if key_ in seen or y.sum() < 3: continue
            if conflict[np.ix_(idx, idx)].any(): continue
            seen.add(key_); Erep.append(float(y @ lin + y @ Q @ y))
            if key_ in evaluated: continue
            new = apply_moves(cur, [mv[i] for i in idx])
            if new is None: continue
            z, _ = lp(new, cutoff=zc + 3 * dcap, basis=basis)
            if z is None or not np.isfinite(z): z = zc + 3 * dcap
            evaluated[key_] = z; total_compounds += 1
            data_Y.append(y.copy()); data_t.append(min(z - zc, 3 * dcap) / s)
            res.append((z, len(idx), new, tag))
            try_best(new, z, f'{tag} compound of {len(idx)} moves it{it}')
            if len(res) >= kmax: break
        lp(cur, basis=basis)
        ebest[tag] = min(Erep, default=float('nan'))
        return res
    evaluated = {}; ebest = {}
    # 5. quantum sample
    Yq, tq, ncirc = sample_quantum(bqm, Nc, SEED * 1000 + it, mode)
    Eq = bqm_energies(Yq, lin, Q); Eq_best = Eq.min()
    yb = Yq[np.argmin(Eq)]; e_chk = bqm.energy({i: int(yb[i]) for i in range(Nc)})
    resq = evaluate(Yq, 'quantum', 40)
    # classical reference: SA on the same BQM
    ts = time.time(); ss = SA.sample(bqm, num_reads=200, seed=SEED + it)
    Ysa = np.array([[int(r[i]) for i in range(Nc)] for r in ss.record.sample], dtype=np.int8)
    Esa_best = float(ss.first.energy); tsa = time.time() - ts
    ressa = evaluate(Ysa, 'SA', 10)
    resr = []
    if mode == 'B' and data_Y:  # ridge refit (BOCS/FMQA-style) on singles+pairs features, then resample
        def phi(y): yf = y.astype(float); return np.concatenate([yf, yf[feats_i] * yf[feats_j]])
        w0 = np.concatenate([dl / s, (J / s)[feats_i, feats_j]])
        X = np.array([phi(y) for y in data_Y]); r = np.array(data_t) - X @ w0
        # pin singles and pairs exactly (residual 0) by including them as data
        Xs = []
        for i in range(Nc): y = np.zeros(Nc, np.int8); y[i] = 1; Xs.append(phi(y))
        for (zz, (i, j)) in pairs_eval: y = np.zeros(Nc, np.int8); y[i] = y[j] = 1; Xs.append(phi(y))
        X = np.vstack([X, np.array(Xs)]); r = np.concatenate([r, np.zeros(len(Xs))])
        w = w0 + X.T @ np.linalg.solve(X @ X.T + 0.1 * np.eye(len(X)), r)
        lin2 = w[:Nc].copy(); Q2 = np.zeros((Nc, Nc)); Q2[feats_i, feats_j] = w[Nc:]
        Q2[conflict] = P
        lin = lin2 + gam * (1 - 2 * K); Q = Q2 + 2 * gam * np.triu(np.ones((Nc, Nc)), 1)
        bqm = make_bqm(lin, Q)
        Yq2, tq2, _ = sample_quantum(bqm, Nc, SEED * 1000 + it + 500, mode)
        resr = evaluate(Yq2, 'quantum-refit', 30)
    allres = resq + ressa + resr
    bq = min([r[0] for r in resq], default=float('nan')); bs = min([r[0] for r in ressa], default=float('nan'))
    br = min([r[0] for r in resr], default=float('nan'))
    bpair = min([p[0] for p in pairs_eval], default=float('nan'))
    log(f'it{it} [{mode}] z_cur {zc:.0f} best {best_score} nLP {NLP} Nc {Nc} K {K} | E_q {Eq_best:.3f} (chk {e_chk:.3f}, {ncirc} circ, {tq:.1f}s) '
        f'E_sa {Esa_best:.3f} ({tsa:.1f}s) feasE q {ebest.get("quantum")} sa {ebest.get("SA")} | LPbest pair {bpair:.0f} q {bq:.0f} ({len(resq)}) sa {bs:.0f} ({len(ressa)}) refit {br:.0f} ({len(resr)}) '
        f'| compounds {total_compounds} t {time.time()-t_it:.1f}s')
    if SMOKE: break
    # 6. ILS kick
    if score(zc) > best_score or True:
        fails += 1
    if fails % 4 == 0:
        cur = list(best); log(f'it{it} restart from best'); continue
    cands = [(r[0], r[2]) for r in allres] + [(p[0], apply_moves(cur, [mv[p[1][0]], mv[p[1][1]]])) for p in pairs_eval]
    cands = [c for c in cands if c[1] is not None and c[0] <= zc * 1.015]
    if cands:
        cands.sort(key=lambda c: c[0]); zk, newk = cands[min(int(rng.integers(0, 3)), len(cands) - 1)]
    else:
        zk, p, q = singles[int(rng.integers(0, min(5, len(singles))))]; newk = move_2ex(cur, p, q)
    removed = set(cur) - set(newk)
    for a in removed: tabu[a] = it + 3
    log(f'it{it} kick -> z {zk:.0f} ({len(removed)} arcs changed)')
    cur = newk
log(f'END best {best_score} z {zbest:.2f} nLP {NLP} compounds {total_compounds}')
