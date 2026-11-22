# TheGOAT_Testing

Work from one Claude Code session, kept in its own folder so it can be reviewed separately from
the rest of the repo.

| File | What it is |
|---|---|
| `diagnostics.py` | Does a surrogate rank solutions like the referee? Oriented Spearman, ties at the model's optimum, and a verdict: `weak` (rewrite the surrogate), `underdetermined` (add a tie-breaker), `strong` (invest in the sampler). Also `baseline_table` for keeping the classical bar next to every result. |
| `block_fidelity.py` | For a block of r freed arcs of the incumbent (tails kept, heads permuted, so degrees always hold), enumerates every valid rewiring, scores each with the exact LP and measures how well each surrogate ranks them: the existing `network_qlns` sub-QUBO, the LP weak-duality bound, plain hop count, and linear / quadratic models fitted on half the block. Output: `runs/goat/fidelity/`, one JSON per block. |
| `goat_lns.py` | Quantum-proposer LNS. Per step: free r arcs, learn a block QUBO from the cheap exact bound, sample it with Divi (PCE poly encoding; QAOA with W-state + XY; or QAOA warm-started at the incumbent with a 2-exchange mixer that never leaves the permutation space), decode by Hungarian, LP-check the top K. SA on the same QUBO and random rewirings get the same LP budget on the same block. Resumable; banks improvements through the official checker. Output: `runs/goat/lns/<tag>/`. |
| `goat_swaps.py` | Same LNS with swap variables: y_e = 1 if two freed arcs swap heads (a 2-exchange). Any set of disjoint swaps keeps every degree, and the QUBO is the exact second-order expansion of the hop count around the current topology, with a trust region (cost per swap) that keeps the optimum where that expansion holds. PCE poly encoding: r(r-1)/2 swaps on about r qubits. Controls: SA, greedy on single swaps, sampled, random. Output: `runs/goat/swaps/<tag>/`. |
| `optimizer_bench.py` | Same blocks, same learned QUBO, one PCE run per classical optimizer (Monte Carlo, COBYLA, L-BFGS-B, quantum natural gradient, QN-SPSA, QN-SPSA with angles inherited from the previous block): distance to SA's optimum of the QUBO and LP value of the candidates. Output: `runs/goat/optbench/`. |
| `node_insertion.py` | Regrows network(n) from a network(n−1) topology: every degree-preserving insertion of the missing node, scored with the exact LP and the hop count. Output: `runs/goat/insertion/`. |
| `summarize.py` | Markdown tables from `runs/goat/`: block fidelity, LNS runs, head-to-head per block. |
| `REPORT.md` | **Start here.** What the measurements say, verdict first. |
| `tests/` | Unit tests on synthetic data. |

## Environment

From the repo root, with Python 3.11 or newer:

```bash
uv venv --python 3.12 venv            # or: python3.12 -m venv venv
uv pip install --python venv/bin/python -r requirements.txt pytest
venv/bin/python -m pytest -p no:cacheprovider TheGOAT_Testing/tests
```
