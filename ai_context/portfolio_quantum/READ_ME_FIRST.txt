QUANTUM PORTFOLIO RESULTS (QOBLIB 06, notebook 01_portfolio_optimisation.ipynb)
Reading guide. Snapshot: 2026-11-22, about 03:40 CET. Paths are relative to the repo root.

1. WHAT THIS IS
Quantum large-neighbourhood search (QLNS). Every accepted improvement is a bitstring sampled by a
Divi QAOA program on an exact sub-QUBO of the official model. Classical parts: a one-day continuous
relaxation that picks the window, exact scoring of the samples, accept-if-better. There is no
classical local search, repair or annealing.
Code: portfolio_quantum/ (README.md explains the method). Hand-in: deliverables/portfolio_quantum/.

2. RESULTS (official referee, see verify_official_scorer.txt)
  config                  vars    max qubits  quantum      QOBLIB BKV   gap     earlier classical
  a050_t10_s00 b020 1e-3  3110    18          -191,256     -191,879     +0.32%  -190,685
  a050_t10_s01 b020 1e-3  3110    18          -140,407     -141,376     +0.69%  -139,048
  a050_t15_s00 b020 1e-3  4665    18          -312,668     -314,736     +0.66%  -312,312
  a050_t15_s01 b020 5e-4  4665    18          -304,271     -304,289     +0.01%  -303,567
  a400_t15_orig b100 1e-3 36165   26 (cloud)  -3,015,526   none         --      -2,986,716
Independent run from the empty portfolio: a050_t10_s01 1e-3 -> -139,634 (12 min, local), already
better than the earlier classical -139,048. Exact window solver, same settings: -140,770 (ceiling).
QAOA found the exact window optimum in 120/244 checked windows (49%).

3. PROVENANCE (read before claiming)
- Four results are warm-started from the repo's EARLIER CLASSICAL solutions (portfolio_QIcing/ lns
  files and deliverables/portfolio, never QOBLIB's published solutions); the gains on top are
  QAOA samples. The exact start file of each run is listed in verify_official_scorer.txt.
- One result (a050_t10_s01 -139,634, kept in portfolio_quantum/solutions/) starts from empty.
- Local programs: Maestro simulator, <= 18 qubits. Cloud: Qoro qoro_maestro, 26-qubit programs,
  8 rounds x 7 programs, 112 circuits, 84.7 credits (logs/cloud_a400_t15_l1e-3.log).
- Not below any BKV yet. No change on a050_t10_orig / t15_orig at 5e-4. lambda=1e-2 does not work
  with this method (rounding breaks the hedges). The random-sampling ablation was queued but not run.

4. FILES
  logs/phaseA, logs/phaseB   one log per run (qlns.py); *_campaign*.out = runner logs.
                             phaseA/..._best_11782.log was stopped by the RAM guard (incomplete).
  logs/cloud_a400_t15_l1e-3.log   cloud batch on the largest instance
  logs/dev/                  QAOA vs exact-oracle comparison runs; the oracle .sol is .sol.txt
                             (classical exact sub-solver, NOT a hand-in)
  scripts/                   job lists given to portfolio_quantum/campaign.py
  experiments/               development scripts + NOTES.md with their results
  transcripts/               session transcript (email redacted)
  verify_official_scorer.txt referee check of every .sol + start file of each run

5. REPRODUCE
  .venv/bin/python portfolio_quantum/qlns.py --inst po_a050_t10_s01 --lam 1e-3 --solver qaoa \
    --start empty --minutes 12 --seed 3 --kround 16 --kmove 7 --p-round 0.7 --p-block 0 \
    --angles portfolio_quantum/angles/a050_l1e-3.json
  cd portfolio_quantum && ../.venv/bin/python cloud_batch.py --inst po_a400_t15_orig --lam 1e-3 \
    --start best --kround 26 --rounds 8 --seed 5
  .venv/bin/python portfolio_quantum/report.py      # re-score and print the table
Max 2 QAOA processes in parallel (about 700 MB each; machine has 7.4 GB).

6. UPDATE 2026-11-22 06:20: PAIRED-TRANSFER QAOA (portfolio_quantum/paired_transfer_run.py)
One qubit = one transfer of <= 3 units between two same-side assets of one day (keeps budget and
net exactly). QAOA p=3, <=16 qubits, 448 shots, local numba statevector (not Divi). 35-minute runs
from the best repo file, 6 in parallel. Logs: logs/paired/.
  a050_t15_s01 5e-4  -304,307 -> -304,333  (QOBLIB BKV -304,289: BELOW BKV by 44)
  a050_t15_orig 5e-4 -397,236 -> -397,384  (BKV -397,497, +0.03%)
  a050_t15_orig 1e-3 -321,070 -> -321,183  (BKV -321,907, +0.22%)
  a050_t10_orig 1e-3 -205,672 -> -205,699  (BKV -206,239, +0.26%)
  a050_t10_orig 5e-4 -254,857 unchanged
  a400_t15_orig 1e-3 -3,163,545 -> -3,164,781 (start = the other session's paired-trajectory file)
Earlier cloud runs on a400: logs/cloud_a400_t15_l1e-3_k28.log (28 qubits, stopped; the gain of its first
round was not saved) and logs/cloud_a400_t15_l1e-3_grouped.log (grouped Dicke + uncertain slots +
3 variants per day + capital rule in the relaxation: -3,015,526 -> -3,061,607 in round 0, saved).
PCE on whole-day a400 windows did not work (logs/dev/pce_test_a400.log).
