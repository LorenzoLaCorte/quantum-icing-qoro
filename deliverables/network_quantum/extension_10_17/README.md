# Grover search on network10–network17

The campaign improved seven of the eight starting solutions in commit `402e57e`. The largest gain was on `network15`, from 376,305 to **369,637**, which is 0.33% below the QOBLIB reference of 370,870. The upstream Rust checker validated the final score for each instance. [Checker output](logs/checker.log) · [QOBLIB references](https://github.com/ZIB-AOPT/QOBLIB/blob/main/08-network/solutions/README.md)

| Instance | Starting score | Final checked score | Reduction | QOBLIB reference | Gap vs QOBLIB |
| --- | ---: | ---: | ---: | ---: | ---: |
| [network10](network10.sol) | 215,077 | **213,000** | 2,077 | 210,800 | +1.04% |
| [network11](network11.sol) | 240,889 | **240,334** | 555 | 238,334 | +0.84% |
| network12 | 276,474 | 276,474 | 0 | 276,474 | 0.00% |
| [network13](network13.sol) | 304,273 | **302,500** | 1,773 | 300,620 | +0.63% |
| [network14](network14.sol) | 344,910 | **343,800** | 1,110 | 343,091 | +0.21% |
| [network15](network15.sol) | 376,305 | **369,637** | 6,668 | 370,870 | −0.33% |
| [network16](network16.sol) | 403,637 | **399,875** | 3,762 | 397,908 | +0.49% |
| [network17](network17.sol) | 442,158 | **439,134** | 3,024 | 437,000 | +0.49% |

`network10` came within 2,200 of its proven optimum. `network12` started at the published best-known value and finished at the same score.

## Method and comparison

This extension used the same degree-preserving rewires, congestion estimate, ideal Grover simulation, and routing LP as the first campaign. It ran 52 rounds per instance with seed 73, 2,048 shots per round, and up to 11 index qubits. The eight runs ran in parallel. The longest took 174 seconds. [Method](../README.md#how-the-search-works)

Each selector received up to 120 distinct routing evaluations per round from the same candidate pool. On three rounds of `network11`, Grover measured fewer distinct candidates, so all selectors used the same reduced budgets of 115, 118 and 118. Only Grover's candidates directed the search. The comparison uses the best LP score per selector and counts two cutoff results as a tie.

| Control | Grover wins | Ties | Grover losses |
| --- | ---: | ---: | ---: |
| Greedy by congestion estimate | 17 | 359 | 40 |
| Uniform sampling | 317 | 58 | 41 |

Greedy matched 15 of the 16 record-setting rounds. In round 3 of `network11`, Grover found a checked improvement to 240,429 and both controls missed it at the same routing budget. Across all rounds the comparison still favored greedy on the shared pools. [Round trace](logs/network11.jsonl) · [Full benchmark](benchmark.csv)

## Reproduce the campaign

Run from the repository root with the project virtual environment. The starting files come from the commit that supplied the original inputs. Choose a fresh output directory for each replay.

```bash
baseline=402e57ef72f4d16cabe1231a13a8727727f73fcf
replay_dir=runs/network-grover/reproduce-10-17
mkdir -p "$replay_dir/starts"

for n in 10 11 12 13 14 15 16 17; do
  git show "$baseline:deliverables/network$n/network$n.sol" \
    > "$replay_dir/starts/network$n.sol" || exit 1
  OPENBLAS_NUM_THREADS=1 .venv/bin/python -m network_design.quantum_congestion \
    --nodes "$n" --start "$replay_dir/starts/network$n.sol" \
    --seed 73 --rounds 52 --budget 120 --workers 2 \
    --output-dir "$replay_dir/network$n" || exit 1
done
```

The archived per-round traces and parameter summaries are in [logs/](logs/). Run the repository checker on the seven archived solutions with the command below.

```bash
NETWORK_SOL_DIR=deliverables/network_quantum/extension_10_17 \
  .venv/bin/python network_pipeline.py status
```
