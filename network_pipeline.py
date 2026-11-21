"""Network design (QOBLIB 08): end-to-end pipeline, classical baseline.

Pipeline for every instance:
    topology (2 in / 2 out per node) -> exact routing LP (score) -> integer flows
    -> write .sol -> read it back through the official checker.

Steps:
    python network_pipeline.py check-ref 24      # sanity: published solution passes our checker
    python network_pipeline.py step1             # network05: brute force vs proven optimum
    python network_pipeline.py step2 --evals 400 # network24: greedy + local search, bank .sol

No quantum here on purpose: this is the plumbing + the classical bar that a
quantum proposer must beat later.
"""
from __future__ import annotations

import argparse
import itertools
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=SyntaxWarning)
import qoblib_tools as qt  # noqa: E402

SOL_DIR = Path(__file__).resolve().parent / "solutions"

# Best-known values (QOBLIB 08 solutions/README.md); <= network10 proven optimal.
BEST_KNOWN = {5: 65500, 12: 276474, 24: 663688}


def gap(score: float, n: int) -> str:
    bk = BEST_KNOWN.get(n)
    return "n/a" if bk is None else f"{(score - bk) / abs(bk):+.2%}"


def score(demand, arcs) -> float:
    """Referee score of a topology (LP optimum rounded up, 1/1000 units)."""
    return qt.route_min_congestion(demand, arcs).objective


def write_and_check(n: int, demand, arcs, path: Path, only_if_better: bool = False) -> int:
    """Integer flows -> temp .sol -> official checker -> move into place.

    The target file is only replaced once the new one passes the checker (and,
    with ``only_if_better``, has a strictly lower checked max_flow than the old one).
    """
    routing = qt.route_integral(demand, arcs)
    path.parent.mkdir(exist_ok=True)
    tmp = path.with_suffix(".sol.tmp")
    qt.write_network_solution(tmp, n, routing)
    valid, max_flow, msg = qt.check_network_solution(tmp, n, demand)
    if not valid:
        tmp.unlink()
        raise RuntimeError(f"{path.name}: checker rejected it: {msg}")
    if only_if_better and path.exists():
        ok, old, _ = qt.check_network_solution(path, n, demand)
        if ok and old <= max_flow:
            tmp.unlink()
            print(f"  kept existing {path.name} ({old}): new one ({max_flow}) is not better")
            return old
    tmp.replace(path)
    print(f"  wrote {path.relative_to(path.parent.parent)}  checker: {msg}, max_flow={max_flow}")
    return max_flow


def bank(n: int, demand, arcs) -> None:
    """Keep the file only if its *checked* score beats the already-checked one on disk."""
    path = SOL_DIR / f"network{n:02d}.sol"
    if path.exists():
        ok, old, _ = qt.check_network_solution(path, n, demand)
        if ok and old <= score(demand, arcs):  # cheap pre-filter: LP score is a lower bound
            print(f"  kept existing {path.name} ({old}): new one is not better")
            return
    write_and_check(n, demand, arcs, path, only_if_better=True)


# ── sanity check ─────────────────────────────────────────────────────────
def check_ref(n: int) -> None:
    kind = "opt" if n <= 10 else "bst"
    ref = qt.fetch_qoblib_file(f"08-network/solutions/network{n:02d}.{kind}.sol")
    demand = qt.load_network_demand(n)
    print(f"network{n:02d} published solution:", qt.check_network_solution(ref, n, demand))
    _, arcs, _ = qt.read_network_solution(ref)
    print("  our LP re-scores its topology as:", score(demand, arcs))


# ── step 1: network05, exhaustive ────────────────────────────────────────
def all_valid_topologies(n: int):
    # each node picks 2 out-neighbours; keep combos where every in-degree is 2 too
    rows = [list(itertools.combinations([j for j in range(n) if j != i], 2)) for i in range(n)]
    for choice in itertools.product(*rows):
        arcs = [(i, j) for i, pair in enumerate(choice) for j in pair]
        if qt.is_valid_topology(n, arcs):
            yield arcs


def step1() -> None:
    n = 5
    demand = qt.load_network_demand(n)
    tops = list(all_valid_topologies(n))
    scores = [score(demand, a) for a in tops]
    best = int(np.argmin(scores))
    print(f"network05: {len(tops)} valid topologies, best {scores[best]:.0f} "
          f"(proven optimum {BEST_KNOWN[n]}, gap {gap(scores[best], n)})")
    assert scores[best] == BEST_KNOWN[n], "pipeline does not reproduce the proven optimum"
    write_and_check(n, demand, tops[best], SOL_DIR / "network05.sol")


# ── step 2: network24, greedy + local search ─────────────────────────────
def swap_heads(arcs, a: int, b: int):
    """(i,j),(k,l) -> (i,l),(k,j): keeps every in/out degree. None if invalid."""
    (i, j), (k, l) = arcs[a], arcs[b]
    if i == l or k == j or j == l:
        return None
    new = list(arcs)
    new[a], new[b] = (i, l), (k, j)
    return new if len(set(new)) == len(new) else None


def local_search(demand, arcs, evals: int, seed: int = 0):
    """Random head-swaps, keep if not worse (sideways moves escape plateaus,
    since only the bottleneck link sets the score)."""
    rng = np.random.default_rng(seed)
    cur, cur_s = list(arcs), score(demand, arcs)
    best, best_s = cur, cur_s
    t0 = time.time()
    for e in range(1, evals + 1):
        a, b = rng.choice(len(cur), 2, replace=False)
        cand = swap_heads(cur, a, b)
        if cand is None:
            continue
        s = score(demand, cand)
        if s <= cur_s:
            cur, cur_s = cand, s
            if s < best_s:
                best, best_s = cand, s
                print(f"  eval {e:4d}  {best_s:.0f}  gap {gap(best_s, len(demand))}  ({time.time() - t0:.0f}s)")
    return best, best_s


def step2(evals: int, seed: int) -> None:
    n = 24
    demand = qt.load_network_demand(n)
    # greedy start: the valid topology keeping the highest direct-demand links
    start = qt.repair_topology(n, [], demand)
    assert qt.is_valid_topology(n, start)
    s0 = score(demand, start)
    print(f"network24 greedy start: {s0:.0f}  gap {gap(s0, n)}")
    bank(n, demand, start)  # secure a checked submission before searching

    best, best_s = local_search(demand, start, evals, seed)
    print(f"network24 after {evals} evals: {best_s:.0f}  gap {gap(best_s, n)}")
    bank(n, demand, best)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check-ref").add_argument("n", type=int)
    sub.add_parser("step1")
    s2 = sub.add_parser("step2")
    s2.add_argument("--evals", type=int, default=400)
    s2.add_argument("--seed", type=int, default=0)
    args = p.parse_args()
    if args.cmd == "check-ref":
        check_ref(args.n)
    elif args.cmd == "step1":
        step1()
    else:
        step2(args.evals, args.seed)
