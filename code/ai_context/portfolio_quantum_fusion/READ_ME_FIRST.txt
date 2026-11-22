BALANCED-FUSION QAOA / GROVER ON po_a400_t15_orig b100 l1e-3 (QOBLIB 06)
Reading guide. Snapshot: 2026-11-22, about 07:45 CET. Paths are relative to the repo root.

1. RESULT
  deliverables/portfolio_quantum/po_a400_t15_orig_b100_l1e-3__balanced-fusion-grover.sol
  objective -3,167,105, feasible (verify_official_scorer.txt). No QOBLIB best-known value for a400.
  Start: -3,163,545 (..._paired-trajectory-qaoa.sol, same folder). Leaderboard reference at the time:
  -3,162,386 (Jules02, classical "block decomposition + local search").

2. METHOD (portfolio_quantum/fusion_qaoa.py, block_trajectory_qaoa.py, exchange_xy_qaoa.py)
  - A perturbed classical day tabu search (portfolio_search.day_tabu) proposes alternative daily
    portfolios. These are the "parents".
  - Fusion QUBO: the differences between the incumbent and a parent are split into asset groups
    that are balanced in long and short volume. Copying any subset of groups keeps the budget and
    the net position. One qubit per group (and per day, also on two consecutive days). The energy
    is exact, including the rebalancing cost between consecutive days. <= 17 qubits.
  - Sampler: QAOA (p = 3) or Grover minimum finding (Durr-Hoyer), local ideal statevector
    simulation (numba, not Divi). The best sample is kept if it lowers the official objective.
  Scores tried (logs/balanced_fusion_grover_run.log.json): categorical QAOA -3,163,943; XY
  fixed weight -3,163,665; one-day fusion QAOA -3,165,216; one-day fusion Grover -3,165,616;
  mixed-day fusion QAOA -3,166,315; mixed-day fusion Grover -3,167,105 (best).
  On 350 improvable windows with 480 reads each, the exact window optimum was found by Grover
  350 times, by QAOA 321 times and by uniform sampling 12 times. Grover uses several oracle
  queries per read, and in simulation the oracle is the precomputed list of all 2^n energies.

3. DIVI CHARACTERIZATION SERVICE (logs/characterize_fusion.log, experiments/characterize_fusion.py)
  One real fusion window (day 2, 15 qubits, optimum dE = -165) was sent to the Qoro cloud.
  Job 191c7490-79b4-4c27-bceb-ab171141ef3b, 11 s.
  Summary: "The exact optimum is already known classically; use QAOA here to tune or benchmark
  it before scaling up." The problem splits into 2 independent parts (largest 9 variables).
  QAOA (X mixer):  p=1  gap closed 45%, P(optimum) 0.3%, 1608 shots for 99% confidence
                   p=3  77%, 6.9%, 65 shots          p=6  91%, 17.9%, 24 shots
  Recommended layers: 6 (still improving). The service does not evaluate Grover.

4. HONEST READING
  The solution is valid and is the best a400 l1e-3 file in the repo. The windows are small enough
  to be solved exactly by enumeration (Divi says so). The quantum step is a validated sampler,
  not an advantage over classical search, and the classical tabu search generates the parents.

5. REPRODUCE
  Replay data: ai_context/portfolio_quantum/experiments/a400_balanced_fusion_replay.npz
  .venv/bin/python portfolio_quantum/fusion_qaoa.py --start <replay.npz> --population-only \
      --sampler grover --output runs/fusion_replay.sol        (see --help for the options)
  .venv/bin/python ai_context/portfolio_quantum_fusion/experiments/characterize_fusion.py
