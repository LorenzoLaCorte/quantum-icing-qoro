# Quantum network-design track: handoff

This is the working state of the quantum track for QOBLIB 08 (network design), written so a new
session can continue without the original chat. **Results and the explanations behind them are in
the [status report](../docs/hopqubo/hopqubo.pdf).** This file covers the code, the commands, the
open work and the pitfalls.

## Where things stand (21 Nov 2026)

| instance | best result | gap vs QOBLIB best known | quantum? |
|---|---|---:|---|
| network05 | warm-started QAOA (notebook 00) + 2-exchange polish | 0.00% (3/3 seeds) | yes, 20 qubits |
| network12 | SA on QUBO + 2-exchange polish | +2.3% | no |
| network12 | exchange-mixer quantum local search, 15 steps | +17.5% | yes, ≤16 qubits |
| network24 | team submission (PT + ILS, see [README](README.md)) | −0.99% | no |

Best known values are in `network_pipeline.BKV`: network12 = 276,474, network24 = 663,688.
network05–10 are proven optimal.

## Pipeline

Every method follows the same steps, so results are comparable:

1. **Propose** topologies. This is the quantum step: QAOA, PCE, partitioned QAOA, or SA as the classical reference.
2. **Repair** each sample to a valid topology (2 in / 2 out per node) with `qt.repair_topology`.
3. **Rank** the topologies by the cheap surrogate `H2` (traffic × hops, capped at 3).
4. **Score** the top 10 with the exact routing LP (`qt.route_min_congestion`), which is the referee.
5. **Polish** with a 2-exchange local search, `(a→b),(c→d) ⇒ (a→d),(c→b)`, scored by the LP.
6. **Report** the gap vs best known. Compare with a *polish-only* baseline that gets the same LP budget.

## Code map

| file | what it does | main commands |
|---|---|---|
| `network_sweep.py` | **Configuration sweep** over QAOA X mixer (layers, penalty λ, warm start), exchange mixer, PCE, and partitioned QAOA/PCE. Writes `runs/sweep.csv`. | `characterize --n 5`, `screen --preset n05 --seeds 0 1 2`, `rank` |
| `network_mixer.py` | **Exchange mixer**: a QAOA mixer whose every state is a valid topology. Also the exact `H2` HUBO, a reliability test, and the quantum local search. | `verify`, `full5`, `reliable --n 5`, `qlns --n 12 --r 4 --final-polish 150` |
| `network_moves.py` | 2-exchange `polish`, move-space SA, and surrogates including node-load L2 (route via quiet nodes). | `polish`, `busy`, `busyopt` |
| `network_hopqubo.py` | Path-variable QUBOs (2-hop/3-hop, strict/soft): fidelity and solvability tests. | `fidelity`, `surropt`, `qubo`, `lns` |
| `network_hopqubo_divi.py` | Path-variable QUBOs through Divi (partitioned QAOA, PCE). Parked. | `--qubo … --method … --cloud qoro_cpu` |
| `network_flipstart.py` | QAOA from basis-state starts. The lesson: with the X mixer, only the start and its global flip are reachable. | n/a |
| `network_design/sa_search.py` | Our parallel SA over topologies (`RUN_DIR`, `lp_eval`), used by lns, qlns and mixer. | `python -m network_design.sa_search --n 24` |
| `network_lns.py`, `network_qlns.py` | Earlier classical / quantum LNS on freed arcs. | see file docstrings |

Common flags: `--cloud qoro_cpu|qoro_gpu` (default is the local simulator), `--mps-bond N` for
tensor-network simulation, `--seed(s)`, `--pop/--iters` for Divi's Monte Carlo optimiser.

## Working rules (agreed with the user)

- **Backend.** Jobs under 25 qubits run on CPU: the local simulator if a job takes under about 4
  minutes, otherwise `qoro_cpu`. Use `qoro_gpu` only for 25 qubits or more, and only after a
  single-batch cost probe.
- **Warm-start QAOA**, always, from `characterize_and_validate` angles (notebook 00). Reports can be
  re-fetched for free with `get_characterization_result(job_id)`. For network11 and up, the reference
  state must be our own topology, not QOBLIB's published solution, because QOBLIB forbids published
  solutions as starts.
- **Always report the gap vs QOBLIB best known**, not only against baselines.
- **Clear names**: `n_layers` (QAOA depth) and `penalty_weight` / λ. Never p/P.
- **Credit cap** for the current sweep's cloud stages: 300 credits. The balance was about 3,243 on 21 Nov.

## Open work

1. **network05 sweep** (`runs/sweep_n05.txt`, `runs/sweep.csv`). 22 of 45 runs were done at
   writing. Remaining: exchange mixer at 4 layers, PCE (4 configs), partitioned QAOA/PCE (3 configs).
   Then `python network_sweep.py rank` and fill the "pending" row in the report.
2. **Stage 3.** Confirm the top network05 configurations with 5 seeds on `qoro_cpu`.
3. **Warm-start the exchange mixer.** It is still blind and weak: 0/3 optima sampled.
4. **network12 quantum local search to convergence**, with warm start and node-load L2 cost. The 40-step
   run (`runs/mixer_qlns12_long_s0.txt`) was cancelled by the Qoro scheduler before the quantum
   proposer finished.
5. **Parked:** PCE and partitioned QAOA, which break the degree rules (0–15% valid samples).
   Revisit with constraint-aware partitions or valid-repair decoding.

## Pitfalls

- **Cost.** Billing counts compute-seconds summed over a batch (0.065 credits/s on `qoro_gpu`). One
  30-qubit full-problem QAOA batch cost **515 credits with no result**. 42 qubits failed on
  `qoro_gpu`, both as a full statevector and as MPS with bond dimension 128.
- **Qoro reliability.** On 21 Nov evening the scheduler cancelled 4 jobs and the API was very slow.
  Check that it responds (e.g. a credit-balance call) before long cloud runs.
- **Brute-force trap.** On tiny instances, repairing *all* samples enumerates the whole space (216
  topologies for network05). The sweep therefore uses only each run's first 20 samples (`--max-samples`).
- **Penalty weight λ.** For the strict path QUBO it must exceed 3, or leaving constraints violated pays off.
  The characterization recommends λ ≈ 0.5 for the notebook-02 QUBO on network05.
- **Slow Python startup on `/mnt/d` (WSL).** Importing Divi modules takes about 20–40 s per
  process. Avoid loops that start a new interpreter per check.
- **Killing jobs.** `pkill -f <pattern>` also matches the shell that runs it. Kill by PID instead.
- **Logs are not in git.** `runs/` is gitignored, so experiment logs exist only on the machine that
  ran them. The PDF has the numbers that matter.
- **Divi custom mixer.** Divi exponentiates the mixer one Pauli string at a time. The exchange mixer
  is valid only because each 2-exchange's 8 commuting strings stay together; do not `simplify()` the operator.
