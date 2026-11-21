"""Network design (QOBLIB 08): secure a checked submission, then bank every improvement.

    python network_pipeline.py verify                    # network05 against the proven optimum
    python network_pipeline.py search 24 --minutes 10    # improve network24, banking as it goes
    python network_pipeline.py status                    # re-check every banked .sol file

Every candidate topology is scored by the exact routing LP. A topology is banked only after
integer flows are written to a .sol file and that file passes ``qt.check_network_solution``
with a strictly better score than the file already banked. ``qoblib_tools.py`` stays untouched.

The search is a degree-preserving 2-exchange local search, (a→b),(c→d) ⇒ (a→d),(c→b), with
moves biased towards congested links via the LP's dual values. The proposer is a plain function
(``propose_moves``) so a Divi-based proposer can replace it later.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

import qoblib_tools as qt

SOL_DIR = Path(os.environ.get("NETWORK_SOL_DIR", Path(__file__).resolve().parents[1] / "solutions"))
LOG_PATH = SOL_DIR / "log.csv"

# Best-known values from QOBLIB's 08-network/solutions/README.md (lower is better).
BKV = {
    5: 65500, 6: 101000, 7: 142400, 8: 170231, 9: 196750, 10: 210800,
    11: 238334, 12: 276474, 13: 300620, 14: 343091, 15: 370870, 16: 397908,
    17: 437000, 18: 473375, 19: 492924, 20: 528528, 21: 569273, 22: 618135,
    23: 659369, 24: 663688,
}
PROVEN_OPTIMAL = set(range(5, 11))

Arc = tuple[int, int]


def gap(n: int, score: float) -> float:
    return (score - BKV[n]) / abs(BKV[n])


# ── Scoring ────────────────────────────────────────────────────────────────────────────

_DEMAND: np.ndarray | None = None


def _init_worker(demand: np.ndarray) -> None:
    global _DEMAND
    _DEMAND = demand


def score_topology(arcs: list[Arc], demand: np.ndarray | None = None) -> tuple[float, np.ndarray | None]:
    """Exact LP congestion (fractional, 1/1000 units) and per-arc duals, arcs in sorted order.

    Same LP as ``qt.route_min_congestion``; the referee's score is ``ceil`` of the first value.
    The duals say how much each link's capacity row binds: large dual = congested link.
    """
    demand = _DEMAND if demand is None else demand
    arcs = sorted(arcs)
    _, c, A_ub, A_eq, b_eq = qt._routing_lp(demand, arcs)
    res = linprog(c, A_ub=A_ub, b_ub=np.zeros(A_ub.shape[0]), A_eq=A_eq, b_eq=b_eq,
                  bounds=(0, None), method="highs")
    if res.status != 0:
        return math.inf, None
    return float(res.fun), -np.asarray(res.ineqlin.marginals)


# ── Banking ────────────────────────────────────────────────────────────────────────────

def banked_path(n: int) -> Path:
    return SOL_DIR / f"network{n:02d}.sol"


def banked_score(n: int, demand: np.ndarray) -> int | None:
    """Score of the banked file according to the checker (None if absent or invalid)."""
    path = banked_path(n)
    if not path.exists():
        return None
    valid, score, _ = qt.check_network_solution(path, n, demand)
    return score if valid else None


def bank(n: int, demand: np.ndarray, arcs: list[Arc], method: str) -> tuple[bool, int, str]:
    """Write integer flows for ``arcs``, check the file, keep it only if it beats the bank.

    Returns ``(banked, checked_score, message)``.
    """
    SOL_DIR.mkdir(exist_ok=True)
    routing = qt.route_integral(demand, arcs)
    if routing.flows is None:
        return False, -1, "unroutable topology"
    tmp = SOL_DIR / f".network{n:02d}.candidate.sol"
    qt.write_network_solution(tmp, n, routing)
    valid, score, msg = qt.check_network_solution(tmp, n, demand)
    if not valid:
        tmp.unlink()
        return False, -1, f"checker rejected the file: {msg}"
    prev = banked_score(n, demand)
    if prev is not None and score >= prev:
        tmp.unlink()
        return False, score, f"checked {score}, not better than banked {prev}"
    tmp.replace(banked_path(n))
    new_log = not LOG_PATH.exists()
    with LOG_PATH.open("a", newline="") as f:
        w = csv.writer(f)
        if new_log:
            w.writerow(["timestamp", "instance", "variables", "score", "best_known", "gap", "method"])
        w.writerow([datetime.now().isoformat(timespec="seconds"), f"network{n:02d}", n * (n - 1),
                    score, BKV[n], f"{gap(n, score):.4%}", method])
    return True, score, f"banked {score} (gap {gap(n, score):+.3%}, was {prev})"


# ── Proposals ──────────────────────────────────────────────────────────────────────────

def swap(arcs: list[Arc], p: int, q: int) -> list[Arc] | None:
    """2-exchange of arcs p=(a,b) and q=(c,d) → (a,d),(c,b); None if it breaks the rules."""
    (a, b), (c, d) = arcs[p], arcs[q]
    if a == c or b == d or a == d or c == b:
        return None
    present = set(arcs)
    if (a, d) in present or (c, b) in present:
        return None
    new = list(arcs)
    new[p], new[q] = (a, d), (c, b)
    return sorted(new)


def propose_moves(arcs: list[Arc], duals: np.ndarray, k: int, rng: np.random.Generator,
                  bias: float = 0.7) -> list[list[Arc]]:
    """Up to ``k`` distinct neighbours. With probability ``bias`` the first arc is drawn in
    proportion to its LP dual (congested links first), otherwise uniformly."""
    m = len(arcs)
    w = np.clip(duals, 0, None) + 1e-12
    w = w / w.sum()
    seen, out = set(), []
    for _ in range(20 * k):
        if len(out) >= k:
            break
        p = rng.choice(m, p=w) if rng.random() < bias else rng.integers(m)
        q = rng.integers(m)
        new = swap(arcs, int(p), int(q))
        if new is not None and (key := tuple(new)) not in seen:
            seen.add(key)
            out.append(new)
    return out


# ── Search ─────────────────────────────────────────────────────────────────────────────

def search(n: int, minutes: float, seed: int, batch: int, workers: int,
           start: str = "greedy", t0: float = 3000.0, t1: float = 30.0, patience: int = 400,
           verbose: bool = True) -> tuple[float, list[Arc]]:
    demand = qt.load_network_demand(n)
    rng = np.random.default_rng(seed)
    if start == "banked" and banked_path(n).exists():
        _, cur, _ = qt.read_network_solution(banked_path(n))
    elif start == "random":
        cur = qt.random_topology(n, rng)
    else:  # links with the most direct demand
        cur = qt.repair_topology(n, [], demand)
    cur = sorted(cur)
    cur_z, cur_d = score_topology(cur, demand)
    best_z, best = cur_z, cur
    ok, score, msg = bank(n, demand, best, f"search start={start} seed={seed}")
    banked = banked_score(n, demand)
    if verbose:
        print(f"network{n:02d}: start ({start}) LP {cur_z:.0f} → {msg}")

    deadline = time.time() + 60 * minutes
    t_start, step, since_best = time.time(), 0, 0
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker, initargs=(demand,)) as pool:
        while time.time() < deadline:
            frac = (time.time() - t_start) / (deadline - t_start)
            temp = t0 * (t1 / t0) ** frac
            cands = propose_moves(cur, cur_d, batch, rng)
            if not cands:
                break
            results = list(pool.map(score_topology, cands, chunksize=max(1, len(cands) // workers)))
            i = int(np.argmin([z for z, _ in results]))
            z, d = results[i]
            if z <= cur_z or rng.random() < math.exp(-(z - cur_z) / temp):
                cur, cur_z, cur_d = cands[i], z, d
            step += 1
            since_best += 1
            if cur_z < best_z - 1e-6:
                best_z, best, since_best = cur_z, cur, 0
                if banked is None or math.ceil(best_z - 1e-6) < banked:
                    ok, score, msg = bank(n, demand, best, f"search start={start} seed={seed} step={step}")
                    if ok:
                        banked = score
                    if verbose:
                        print(f"  step {step:>5}  T={temp:7.1f}  LP {best_z:.0f}  {msg}")
            if since_best >= patience:  # restart from the best topology found so far
                cur, cur_z = best, best_z
                cur_d = score_topology(cur, demand)[1]
                since_best = 0
    if verbose:
        el = time.time() - t_start
        print(f"network{n:02d}: {step} steps in {el:.0f}s, best LP {best_z:.0f}, "
              f"banked {banked} (gap {gap(n, banked):+.3%} vs {BKV[n]})")
    return best_z, best


# ── Commands ───────────────────────────────────────────────────────────────────────────

def cmd_verify(args) -> None:
    """network05: referee on the published optimum, then the full pipeline from a random start."""
    n = 5
    demand = qt.load_network_demand(n)
    ref = qt.fetch_qoblib_file(f"08-network/solutions/network{n:02d}.opt.sol")
    print("checker on the published optimum:", qt.check_network_solution(ref, n, demand))
    best_z, best = search(n, minutes=args.minutes, seed=args.seed, batch=8, workers=2,
                          start="random", verbose=False)
    score = banked_score(n, demand)
    status = "OK" if score == BKV[n] else "MISMATCH"
    print(f"pipeline on network05: LP {best_z:.0f}, banked file checks at {score}, "
          f"proven optimum {BKV[n]} → {status}")


def cmd_search(args) -> None:
    search(args.n, args.minutes, args.seed, args.batch, args.workers, start=args.start,
           t0=args.t0, t1=args.t1, patience=args.patience)


def cmd_status(args) -> None:
    files = sorted(SOL_DIR.glob("network[0-9][0-9].sol"))
    if not files:
        print("nothing banked yet")
    for path in files:
        n = int(path.stem[-2:])
        valid, score, msg = qt.check_network_solution(path, n, qt.load_network_demand(n))
        tag = "proven optimum" if n in PROVEN_OPTIMAL else "best known"
        line = f"{path.name}: {msg}, score {score}" if valid else f"{path.name}: INVALID ({msg})"
        if valid:
            line += f", {tag} {BKV[n]}, gap {gap(n, score):+.3%}"
        print(line)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify", help="network05 against the proven optimum")
    v.add_argument("--minutes", type=float, default=0.2)
    v.add_argument("--seed", type=int, default=0)
    v.set_defaults(func=cmd_verify)
    s = sub.add_parser("search", help="local search on one instance, banking every checked improvement")
    s.add_argument("n", type=int, choices=sorted(BKV))
    s.add_argument("--minutes", type=float, default=10)
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--batch", type=int, default=32, help="candidate moves scored in parallel per step")
    s.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    s.add_argument("--start", choices=["greedy", "random", "banked"], default="greedy")
    s.add_argument("--t0", type=float, default=3000.0, help="initial temperature (1/1000 flow units)")
    s.add_argument("--t1", type=float, default=30.0, help="final temperature")
    s.add_argument("--patience", type=int, default=400, help="steps without improvement before a restart")
    s.set_defaults(func=cmd_search)
    st = sub.add_parser("status", help="re-check every banked .sol file")
    st.set_defaults(func=cmd_status)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
