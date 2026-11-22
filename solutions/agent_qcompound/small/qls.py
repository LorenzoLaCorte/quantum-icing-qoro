"""Quantum-compound local search on QOBLIB network instances, chained by node deletion.

python qls.py --start SOL --start-n N --chain 22,21,20 --minutes 5,5,5 --seed 1 --tag p1 --end 23:01:00
Per instance: 2-exchange first-improvement descent (exact warm LP, cutoff) -> local optimum;
then a QAOA compound step (QUBO over the N lowest-delta 2-exchanges with exact pair interactions),
LP-evaluate the best conflict-free samples; accept improvements, else ILS kick; restart from best.
"""
import sys, os, time, argparse, itertools, datetime, warnings
sys.path[:0] = [os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if os.path.basename(os.path.dirname(os.path.abspath(__file__))) in ('small', 'net24') else os.path.dirname(os.path.abspath(__file__)), '.']
import memguard; memguard.start(min_mb=900)
warnings.filterwarnings("ignore")
import numpy as np, dimod
import qoblib_tools as qt
from network_ils import WarmLP, move_2ex
import shrink, bank

OUT = 'solutions/agent_qcompound/small'
OPTIMAL = {5, 6, 7, 8, 9, 10}  # QOBLIB status 'optimal': stop once matched
ap = argparse.ArgumentParser()
ap.add_argument('--start'); ap.add_argument('--start-n', type=int)
ap.add_argument('--chain'); ap.add_argument('--minutes')
ap.add_argument('--seed', type=int, default=1); ap.add_argument('--tag', default='p')
ap.add_argument('--end', default='23:01:00'); ap.add_argument('--nq', type=int, default=16)
ap.add_argument('--qiters', type=int, default=4)
args = ap.parse_args()
today = datetime.date.today().isoformat()
END = datetime.datetime.fromisoformat(f'{today}T{args.end}').timestamp()
rng = np.random.default_rng(args.seed)
LOG = open(os.path.join(OUT, f'run_{args.tag}.log'), 'a')
def log(*a):
    s = f'[{time.strftime("%H:%M:%S")}] ' + ' '.join(map(str, a)); print(s, flush=True); LOG.write(s + '\n'); LOG.flush()
def ok(new): return new is not None and len(set(new)) == len(new) and all(i != j for i, j in new)


def apply_moves(arcs, mv):
    cur = arcs
    for p, q in mv:
        cur = move_2ex(cur, p, q)
        if cur is None: return None
    return cur if ok(cur) else None


class Search:
    def __init__(self, n, arcs):
        self.n = n; self.D = qt.load_network_demand(n); self.m = len(arcs)
        self.W = WarmLP(self.D, arcs); self.W.h.resetGlobalScheduler(True)
        self.pairs = list(itertools.combinations(range(self.m), 2))
        self.set_cur(arcs)
        self.best = (self.z, list(arcs), 'start'); self.zstart = self.z
        self.banked = None; self.stats = {}

    def set_cur(self, arcs):
        z, _ = self.W.solve(arcs)
        if not np.isfinite(z): self.W.h.resetGlobalScheduler(True); self.W.h.clearSolver(); z, _ = self.W.solve(arcs)
        self.cur, self.z, self.basis = list(arcs), z, self.W.h.getBasis()

    def lp(self, new, cutoff=None):
        return self.W.solve(new, cutoff=cutoff, basis=self.basis)[0]

    def descent(self, deadline):
        """First improvement over all 2-exchanges; records deltas (within margin) of the final pass."""
        nimp = 0
        while time.time() < deadline:
            margin = 0.02 * self.z; deltas = []; improved = False
            order = rng.permutation(len(self.pairs))
            for t in order:
                if time.time() > deadline: return nimp, None
                p, q = self.pairs[t]
                new = move_2ex(self.cur, p, q)
                if not ok(new): continue
                zn = self.lp(new, cutoff=self.z + margin)
                if zn is None: continue
                if zn < self.z - 0.5:
                    self.set_cur(new); nimp += 1; improved = True; break
                deltas.append((zn - self.z, p, q))
            if not improved:
                deltas.sort(); return nimp, deltas
        return nimp, None

    def compound(self, deltas, label):
        """QAOA compound step. Returns (z_best_compound, arcs, info)."""
        N = min(args.nq, len(deltas))
        if N < 3: return (np.inf, None, None), (np.inf, None)
        cand = [(p, q) for _, p, q in deltas[:N]]; d = np.array([x[0] for x in deltas[:N]])
        J = {}; conflict = set()
        for i, j in itertools.combinations(range(N), 2):
            if set(cand[i]) & set(cand[j]): conflict.add((i, j)); continue
            new = apply_moves(self.cur, [cand[i], cand[j]])
            if new is None: conflict.add((i, j)); continue
            zij = self.lp(new)
            J[(i, j)] = zij - self.z - d[i] - d[j]
        s = max(1.0, float(np.median(np.abs(d))) if N else 1.0)
        mu = float(d[min(3, N - 1)])  # bias: favour compounds of several cheap moves
        Jv = np.array(list(J.values())) if J else np.zeros(1)
        P = 2.0 * (np.abs(d - mu).max() + np.abs(Jv).max()) / s + 1.0
        lin = {i: (d[i] - mu) / s for i in range(N)}
        quad = {k: v / s for k, v in J.items()}
        for k in conflict: quad[k] = P
        bqm = dimod.BinaryQuadraticModel(lin, quad, 0.0, dimod.BINARY)
        from divi.backends import MaestroSimulator  # lazy: keep LP-only phases light
        from divi.qprog.algorithms import QAOA
        from divi.qprog.optimizers import MonteCarloOptimizer
        from divi.qprog.problems import BinaryOptimizationProblem
        t = time.time()
        qa = QAOA(BinaryOptimizationProblem(bqm), n_layers=2, optimizer=MonteCarloOptimizer(population_size=16),
                  max_iterations=args.qiters, backend=MaestroSimulator(shots=4000), seed=int(rng.integers(1 << 30)))
        qa.run()
        sols = qa.get_top_solutions(n=0, include_decoded=True)
        tq = time.time() - t
        seen = set(); cands = []
        for so in sols:
            y = np.asarray(so.decoded)[:N]
            idx = tuple(int(i) for i in np.flatnonzero(y))
            if len(idx) < 2 or idx in seen: continue
            seen.add(idx)
            if any((a, b) in conflict for a, b in itertools.combinations(idx, 2)): continue
            e = sum(lin[i] for i in idx) + sum(quad.get((a, b), 0) for a, b in itertools.combinations(idx, 2))
            cands.append((e, idx))
        cands.sort()
        bestc = (np.inf, None, None)
        for e, idx in cands[:30]:
            new = apply_moves(self.cur, [cand[i] for i in idx])
            if new is None: continue
            zc = self.lp(new)
            if zc < bestc[0]: bestc = (zc, new, idx)
        # classical reference: best exactly-evaluated pair
        bp = min(J.items(), key=lambda kv: kv[1] + d[kv[0][0]] + d[kv[0][1]]) if J else None
        zpair = self.z + bp[1] + d[bp[0][0]] + d[bp[0][1]] if bp else np.inf
        log(f'  {label} QAOA N={N} conf={len(conflict)} negJ={sum(v < 0 for v in J.values())} q={tq:.1f}s '
            f'samples={len(cands)} bestcomp={bestc[0]:.0f} ({"%+.3f" % (100 * (bestc[0] - self.z) / self.z)}%, k={len(bestc[2]) if bestc[2] else 0}) bestpair={zpair:.0f} cur={self.z:.0f}')
        return bestc, (zpair, [cand[bp[0][0]], cand[bp[0][1]]] if bp else None)

    def maybe_bank(self, how, force=False):
        z, arcs, _ = self.best
        if z >= bank.BKV[self.n] and not force: return
        if self.banked is not None and z >= self.banked - 0.5: return
        if not force and self.banked is not None: return  # bank first sub-BKV now, the rest at the end
        t = time.time(); sc = bank.bank(self.n, arcs, f'qcompound-{args.tag}:{how}', OUT)
        self.W.h.resetGlobalScheduler(True)
        log(f'  bank network{self.n:02d} lp={z:.0f} -> {sc} ({time.time() - t:.1f}s)')
        self.banked = z

    def upd(self, how):
        if self.z < self.best[0] - 0.5:
            self.best = (self.z, list(self.cur), how)
            self.stats[how] = self.stats.get(how, 0) + 1
            log(f'  NEW BEST network{self.n:02d} {self.z:.0f} via {how}  (BKV {bank.BKV[self.n]}, {100 * (self.z - bank.BKV[self.n]) / bank.BKV[self.n]:+.3f}%)')
            self.maybe_bank(how)

    def run(self, deadline):
        log(f'network{self.n:02d} start {self.z:.0f} BKV {bank.BKV[self.n]} gap {100 * (self.z - bank.BKV[self.n]) / bank.BKV[self.n]:+.3f}%')
        self.maybe_bank('derived')
        origin = 'descent'; stall = 0; cyc = 0
        while time.time() < deadline:
            cyc += 1
            nimp, deltas = self.descent(deadline)
            self.upd(origin if origin != 'descent' else 'descent')
            if deltas is None or time.time() > deadline - 15: break
            if self.n in OPTIMAL and np.ceil(self.best[0] - 1e-6) <= bank.BKV[self.n]: log(f'  network{self.n:02d} at the proven optimum'); break
            log(f' cyc{cyc} local opt {self.z:.0f} ({nimp} imps, origin {origin}); best {self.best[0]:.0f}')
            (zc, newc, idx), (zp, mvp) = self.compound(deltas, f'cyc{cyc}')
            if mvp is not None and zp < self.z - 0.5 and (newc is None or zp < zc - 0.5):
                self.set_cur(apply_moves(self.cur, mvp)); self.upd('pair-scan(classical part of QUBO build)'); origin = 'descent-after-pair-improve'
            elif newc is not None and zc < self.z - 0.5:
                self.set_cur(newc); self.upd('qaoa-compound'); origin = 'descent-after-qaoa-improve'
            elif newc is not None and zc <= self.z * 1.015:
                self.set_cur(newc); origin = 'descent-after-qaoa-kick'
            else:
                k = int(rng.integers(2, 4)); mv = []
                new = None
                for _ in range(50):
                    mv = [self.pairs[t] for t in rng.choice(len(self.pairs), k, replace=False)]
                    new = apply_moves(self.cur, mv)
                    if new is not None: break
                if new is not None: self.set_cur(new)
                origin = 'descent-after-random-kick'
            if self.best[0] < self.z - 0.5 and self.z > self.best[0] * 1.02: stall += 1
            if cyc % 4 == 0:
                self.set_cur(self.best[1]); log('  restart from best')
        self.maybe_bank(self.best[2], force=True)
        log(f'network{self.n:02d} done: start {self.zstart:.0f} best {self.best[0]:.0f} via {self.best[2]} counts {self.stats}')
        return self.best


if args.start == 'random':  # random valid topology on --start-n nodes
    arcs = qt.random_topology(args.start_n, rng)
else:
    _, arcs, _ = qt.read_network_solution(args.start)
arcs = [tuple(map(int, a)) for a in arcs]; n = args.start_n
chain = [int(x) for x in args.chain.split(',')]; mins = [float(x) for x in args.minutes.split(',')]
for k, NN in enumerate(chain):
    while n > NN:
        z, arcs = shrink.shrink(arcs, n, qt.load_network_demand(n - 1)); n -= 1
        log(f'derived network{n:02d} by deletion: {z:.0f}')
    if time.time() > END - 30: break
    dl = min(END, time.time() + 60 * mins[min(k, len(mins) - 1)])
    S = Search(NN, arcs)
    z, arcs, how = S.run(dl)
log('all done')
