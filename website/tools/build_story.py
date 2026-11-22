"""Rebuild the network23 story for the website, from the checked files and a seeded replay.

    .venv/bin/python website/tools/build_story.py

Acts, all on real data:
  1. network24 hand-in (657,121), the topology the chain starts from.
  2. Deleting node 24 and splicing its arcs gives the derived network23 (642,084).
  3. Two exact-LP 2-exchanges give the network23 hand-in (639,739).
  4. A replay of the Grover walk (network_design/quantum_congestion.py, seed 73,
     52 rounds, the settings of runs/network-grover/walk23) logs every round's pool,
     Grover marking, measured shots, LP scores and the move the walk takes.
     It reaches the checked 632,319 of deliverables/network_quantum/network23.sol.

Writes website/data/network23_story.json. Loads come from a two-stage routing LP:
minimum congestion first, then the least total flow at that congestion.
"""
from __future__ import annotations

import json
import math
import multiprocessing
import sys
from concurrent.futures import ProcessPoolExecutor
from itertools import permutations
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "solutions" / "agent_qcompound")]

import qoblib_tools as qt  # noqa: E402
import shrink  # noqa: E402
from network_design import quantum_congestion as qc  # noqa: E402
from network_design.iterated_local_search import WarmLP, move_2ex  # noqa: E402
from network_design.pipeline import BKV  # noqa: E402
from network_design.solutions import checked_score, save_checked_solution  # noqa: E402

OUT = ROOT / "website" / "data" / "network23_story.json"
SCRATCH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "runs" / "website-replay"


def arcs_of(path):
    return [tuple(map(int, a)) for a in qt.read_network_solution(path)[1]]


def flows_two_stage(demand, arcs):
    """Min congestion, then min total flow at that congestion. Returns (z_lp, loads, per-source)."""
    arcs = sorted(set(arcs))
    var, c, A_ub, A_eq, b_eq = qt._routing_lp(demand, arcs)
    first = linprog(c, A_ub=A_ub, b_ub=np.zeros(A_ub.shape[0]), A_eq=A_eq, b_eq=b_eq,
                    bounds=(0, None), method="highs")
    z = first.fun
    bounds = [(0, None)] * (len(c) - 1) + [(0, z * (1 + 1e-9) + 1e-6)]
    cost = np.ones(len(c))
    cost[-1] = 0.
    second = linprog(cost, A_ub=A_ub, b_ub=np.zeros(A_ub.shape[0]), A_eq=A_eq, b_eq=b_eq,
                     bounds=bounds, method="highs")
    x = second.x
    loads = np.zeros(len(arcs))
    per = [[] for _ in arcs]
    for (k, a), idx in var.items():
        if x[idx] > 0.5:
            loads[a] += x[idx]
            per[a].append([k, int(round(x[idx]))])
    return float(z), arcs, loads, per


def state(label, demand, arcs, score, note=""):
    z, arcs, loads, per = flows_two_stage(demand.astype(float), arcs)
    return {
        "label": label, "score": int(score), "z_lp": round(z, 3), "note": note,
        "arcs": [list(a) for a in arcs], "loads": [int(round(v)) for v in loads],
        "per_source": per,
    }


def diff(old, new):
    old, new = set(map(tuple, old)), set(map(tuple, new))
    return sorted(map(list, old - new)), sorted(map(list, new - old))


def heads_to_arcs(heads):
    return [list(a) for a in qc.topology(heads)]


def replay_walk(n=23):
    """quantum_congestion.run with the walk23 settings, instrumented. Same rng call order."""
    args = SimpleNamespace(nodes=n, start=None, output_dir=SCRATCH, seed=73, rounds=52,
                           radii=[2, 3, 4, 5, 6], subsets=950, shortlist=3250, passes=5,
                           budget=120, shots=2048, mark_fraction=.12, workers=2, restart=19,
                           slack=18000., uphill=.35, methods=list(qc.METHODS))
    name = f"network{n:02d}"
    start = ROOT / "deliverables" / name / f"{name}.sol"
    demand = qt.load_network_demand(n)
    scaled = demand.astype(float) * qt.INTSCALE
    record = checked_score(start, demand)
    initial = qc.ordered_heads(qt.read_network_solution(start)[1])
    best, current = initial, initial
    rng = np.random.default_rng(args.seed)
    priority = np.ones(len(initial))
    dest = args.output_dir / f"{name}.sol"
    orders = {
        r: np.asarray([p for p in permutations(range(r)) if all(p[i] != i for i in range(r))])
        for r in args.radii
    }
    stall = 0
    current_score = float(record)
    seen = set()
    rounds = []
    with ProcessPoolExecutor(max_workers=args.workers, initializer=qc.init_routing_worker,
                             initargs=(demand, initial),
                             mp_context=multiprocessing.get_context("fork")) as executor:
        context = WarmLP(demand, qc.topology(initial))
        context.h.resetGlobalScheduler(True)
        for step in range(args.rounds):
            restarted = False
            if args.restart and stall >= args.restart:
                current, current_score = best, float(record)
                priority.fill(1.)
                stall = 0
                restarted = True
            before = current.copy()
            _, dual = context.solve(qc.topology(current))
            duals = np.ones(len(current)) if dual is None else np.maximum(dual, 0.) * len(current)
            pool = qc.propose_pool(current, scaled, record, orders, args.subsets, args.shortlist,
                                   rng, priority)
            keys = [key for key in pool if key not in seen]
            if not keys:
                continue
            heads, coarse = map(np.asarray, zip(*(pool[key] for key in keys)))
            energy = qc.congestion_energy(heads, coarse, scaled, duals, record, args.passes)
            # selections(), unrolled to keep the measured shots
            count = min(args.budget, len(energy))
            probability, layers, marked = qc.grover_probabilities(energy, args.mark_fraction)
            drawn = rng.choice(len(energy), args.shots, replace=True, p=probability)
            distinct = list(dict.fromkeys(drawn))
            count = min(count, len(distinct))
            selected = {"quantum": [int(i) for i in distinct[:count]]}
            selected["greedy"] = np.argsort(energy, kind="stable")[:count].tolist()
            selected["uniform"] = rng.choice(len(energy), count, replace=False).tolist()
            ids = sorted({i for choices in selected.values() for i in choices})
            cutoff = max(record, current_score) + args.slack
            scores = list(executor.map(qc.score_candidate, ((heads[i], cutoff) for i in ids),
                                       chunksize=4))
            lp = dict(zip(ids, scores))
            best_ids = {m: min(c, key=lp.__getitem__) for m, c in selected.items()}
            index = best_ids["quantum"]
            score = lp[index]
            pre_record = record
            record_index = None
            if score <= record - 1 + 1e-6:
                for candidate in sorted(selected["quantum"], key=lp.__getitem__):
                    if lp[candidate] > record - 1 + 1e-6:
                        break
                    try:
                        routing = qt.route_integral(demand, qc.topology(heads[candidate]))
                    except RuntimeError:
                        continue
                    if routing.objective < record:
                        record = int(routing.objective)
                        best = heads[candidate]
                        save_checked_solution(dest, demand, routing, expected_score=record)
                        current, current_score = best, lp[candidate]
                        record_index = candidate
                        print(f"  record {record:,} at round {step + 1}", flush=True)
                        break
            moved = "record" if record_index is not None else "stay"
            if record < pre_record:
                stall = 0
            else:
                stall += 1
                if score < record + args.slack and (score < current_score or rng.random() < args.uphill):
                    moved = "downhill" if score < current_score else "uphill"
                    current, current_score = heads[index], score
            weights = np.ones(len(initial))
            for i in sorted(selected["quantum"], key=lp.__getitem__)[:8]:
                if math.isfinite(lp[i]):
                    weights[heads[i] != current] += 1.
            priority = .5 * priority + .5 * weights
            seen.update(keys[i] for i in selected["quantum"])

            threshold = float(np.partition(energy, marked - 1)[marked - 1])
            counts = np.bincount(drawn, minlength=len(energy))
            fin = lambda v: None if not math.isfinite(v) else round(float(v), 1)  # noqa: E731
            taken = record_index if record_index is not None else index
            removed, added = diff(qc.topology(before), qc.topology(heads[taken]))
            moved_removed, moved_added = diff(qc.topology(before), qc.topology(current))
            rounds.append({
                "round": step + 1, "restart": restarted, "pool": len(energy), "marked": marked,
                "layers": layers, "index_qubits": (len(energy) - 1).bit_length(),
                "threshold": round(threshold, 1),
                "energy": [round(float(e)) for e in energy],
                "shots": {str(i): int(c) for i, c in enumerate(counts) if c},
                "quantum_ids": selected["quantum"],
                "lp": {str(i): fin(lp[i]) for i in selected["quantum"]},
                "best": {m: fin(lp[i]) for m, i in best_ids.items()},
                "best_index": int(taken),
                "best_lp": fin(lp[taken]),
                "move": {"removed": removed, "added": added},
                "moved": moved,
                "step": {"removed": moved_removed, "added": moved_added},
                "checked_best": record, "current_lp": round(float(current_score), 1),
                "current_arcs": heads_to_arcs(current),
            })
            print(f"{step + 1:3d} pool={len(energy)} q={fin(score)} checked={record:,} {moved}",
                  flush=True)
    return rounds, best


def main():
    n = 23
    d24 = qt.load_network_demand(24)
    d23 = qt.load_network_demand(n)
    a24 = arcs_of(ROOT / "deliverables/network24/network24.sol")
    s24 = state("network24 hand-in", d24, a24, checked_score(ROOT / "deliverables/network24/network24.sol", d24),
                "PT → ILS → PT")
    z_derived, derived = shrink.shrink(a24, 24, d23)
    derived = [tuple(map(int, a)) for a in derived]
    node = 23
    deletion = {
        "node": node,
        "in": [list(a) for a in a24 if a[1] == node],
        "out": [list(a) for a in a24 if a[0] == node],
        "spliced": sorted(map(list, set(derived) - set(a24))),
    }
    s_derived = state("derived by node deletion", d23, derived, z_derived, "delete node 24, splice")

    # Two 2-exchanges take the derived topology to the hand-in; take the better first.
    hand = arcs_of(ROOT / "deliverables/network23/network23.sol")
    gone, new = diff(derived, hand)
    steps = []
    cur = list(derived)
    pending = [tuple(map(tuple, (a, b))) for a in map(tuple, gone) for b in map(tuple, gone) if a < b]
    while set(cur) != set(hand):
        options = []
        for p, q in pending:
            ip, iq = cur.index(p), cur.index(q)
            moved = move_2ex(cur, ip, iq)
            if moved is None or not (set(moved) - set(cur)) <= set(map(tuple, new)):
                continue
            z = qt.route_min_congestion(d23, moved).objective
            options.append((z, moved, p, q))
        z, cur, p, q = min(options)
        r, a = diff(steps[-1]["arcs"] if steps else derived, cur)
        _, routed, loads, _ = flows_two_stage(d23.astype(float), cur)
        steps.append({"removed": r, "added": a, "score": int(z), "arcs": [list(x) for x in routed],
                      "loads": [int(round(v)) for v in loads]})
        pending = [(x, y) for x, y in pending if x in cur and y in cur]
    s_hand = state("network23 hand-in", d23, hand, checked_score(ROOT / "deliverables/network23/network23.sol", d23),
                   "exact-LP 2-exchange descent")

    rounds, best = replay_walk(n)
    final_path = ROOT / "deliverables/network_quantum/network23.sol"
    final = arcs_of(final_path)
    assert set(map(tuple, qc.topology(best))) == set(final), "replay did not reach the checked file"

    records = []
    for r in rounds:
        if r["moved"] == "record":
            records.append(state(f"round {r['round']}", d23, [tuple(a) for a in r["current_arcs"]],
                                 r["checked_best"], "Grover"))
    # Loads for the walk's current topology after every round (for the live heat map).
    cache = {}
    for r in rounds:
        key = tuple(sorted(map(tuple, r["current_arcs"])))
        if key not in cache:
            z, arcs, loads, _ = flows_two_stage(d23.astype(float), list(key))
            cache[key] = [int(round(v)) for v in loads]
        r["current_loads"] = cache[key]
        r["current_arcs"] = [list(a) for a in key]

    import networkx as nx
    from TheGOAT_Testing.instance_bound import bounds
    G = nx.Graph()
    G.add_nodes_from(range(24))
    for arcs in [a24, derived, hand, final]:
        G.add_edges_from(map(tuple, arcs))
    pos = nx.spring_layout(G, dim=3, seed=11, iterations=400)
    P = np.array([pos[i] for i in range(24)])
    P -= P[:23].mean(axis=0)
    P /= np.linalg.norm(P[:23], axis=1).max()

    story = {
        "instance": "network23", "nodes": n, "binary_variables": n * (n - 1),
        "bkv": BKV[n], "bkv24": BKV[24], "lower_bound": math.ceil(bounds(d23)["best"]),
        "intscale": qt.INTSCALE,
        "demand": d23.tolist(), "demand24": d24.tolist(),
        "layout": np.round(P, 4).tolist(),
        "network24": s24, "deletion": deletion, "derived": s_derived,
        "descent": steps, "hand_in": s_hand,
        "records": records, "final_checked": checked_score(final_path, d23),
        "walk": {"settings": {"seed": 73, "rounds": 52, "radii": [2, 3, 4, 5, 6], "budget": 120,
                              "shots": 2048, "mark_fraction": .12, "uphill": .35, "restart": 19},
                 "rounds": rounds},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(story, separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
