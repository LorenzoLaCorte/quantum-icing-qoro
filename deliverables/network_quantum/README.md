# Network design with simulated Grover search

The campaign improved five of the seven starting topologies from commit `4bdab9b`. Four results also improve on the hand-in at `253fcbf`, the repository revision used to archive this campaign. The best result is `network23` at **632,319**, down 7,420 from the hand-in and 4.10% below the QOBLIB reference. The upstream Rust checker validated all five exported solutions. [Checker output](logs/checker.log) · [QOBLIB reference scores](https://github.com/ZIB-AOPT/QOBLIB/blob/main/08-network/solutions/README.md)

| Instance | Campaign start | Campaign best | Hand-in at `253fcbf` | Campaign vs hand-in |
| --- | ---: | ---: | ---: | ---: |
| [network18](network18.sol) | 472,112 | 471,395 | **469,000** | +2,395 |
| [network19](network19.sol) | 488,895 | **486,579** | 488,895 | −2,316 |
| [network20](network20.sol) | 519,343 | **516,397** | 518,305 | −1,908 |
| network21 | 562,362 | 562,362 | 562,362 | 0 |
| [network22](network22.sol) | 604,540 | **604,229** | 604,540 | −311 |
| [network23](network23.sol) | 639,739 | **632,319** | 639,739 | −7,420 |
| network24 | 657,121 | 657,121 | 657,121 | 0 |

## How the search works

1. **Generate valid rewires.** Pick two to six arcs and shuffle their destinations. This keeps every node's in-degree and out-degree at two. Discard loops, repeated arcs, and disconnected candidates. Later rounds sample some arc sets preferentially based on the best LP-scored candidates from the previous round.
2. **Estimate congestion.** Shortlist candidates using demand-weighted path lengths and excess link loads. Refine the ranking with five weighted shortest-path routings. Start from tolls informed by the current topology's routing LP duals and raise tolls on links with higher average load.
3. **Simulate Grover sampling.** Prepare a uniform superposition over the shortlist indices. A phase oracle marks roughly the best 12% under the congestion estimate. Grover reflections amplify those indices. Each round uses up to 11 index qubits and draws 2,048 shots.
4. **Score and check.** An exact multicommodity routing LP scores up to 120 distinct measured topologies. The walk can accept bounded uphill steps and restart from its best topology. When the LP bound allows a new record, the solver constructs integer flows and checks the exported solution.

The selector runs as an ideal statevector simulation with an oracle built from the classically evaluated shortlist. A separate Qiskit circuit reproduced the first improving `network23` round's probabilities within `1.3e-13`. That circuit used 17,164 CNOT gates after transpilation to `rz`, `sx`, `x` and `cx` before hardware mapping. [Search code](../../network_design/quantum_congestion.py) · [Circuit verification log](logs/network23-circuit.log)

## Comparison at equal routing budget

Greedy and uniform selection each received 120 distinct candidates per round from the same shortlist. Only the Grover-selected candidates directed the walk. Wins, ties and losses compare the best LP result per round. When both methods hit the LP cutoff, the result counts as a tie.

| Control | Grover wins | Ties | Grover losses |
| --- | ---: | ---: | ---: |
| Greedy by congestion estimate | 4 | 309 | 51 |
| Uniform sampling | 294 | 56 | 14 |

Greedy matched the routing LP score in each round that set a new record. The comparison favors greedy on the shared candidate pools and evaluates solution quality in simulation. The campaign ran one seed per instance. [Benchmark table](benchmark.csv) · [Per-round logs and run settings](logs/)

## Reproduce the campaign

Run from the repository root with the project virtual environment. Restore the historical starting files because `network18` and `network20` have since been updated.

```bash
baseline=4bdab9b7ec6180e3e3ed9ca9e19640cbffc4695e
replay_dir=runs/network-grover/reproduction
mkdir -p "$replay_dir/starts"

for n in 18 19 20 21 22 23 24; do
  git show "$baseline:deliverables/network$n/network$n.sol" \
    > "$replay_dir/starts/network$n.sol" || exit 1
  OPENBLAS_NUM_THREADS=1 .venv/bin/python -m network_design.quantum_congestion \
    --nodes "$n" --start "$replay_dir/starts/network$n.sol" \
    --seed 73 --rounds 52 --radii 2 3 4 5 6 --subsets 950 --shortlist 3250 \
    --passes 5 --budget 120 --shots 2048 --mark-fraction .12 \
    --workers 2 --restart 19 --slack 18000 --uphill .35 \
    --output-dir "$replay_dir/network$n" || exit 1
done
```

Each run writes a JSONL trace, a summary with all settings, and a solution file whenever it improves on the starting score. Use a fresh output directory for each campaign so that the JSONL files contain one run each. To verify the archived solutions with the repository checker, run the following command.

```bash
NETWORK_SOL_DIR=deliverables/network_quantum .venv/bin/python network_pipeline.py status
```
