CLASSICAL PORTFOLIO RESULTS (QOBLIB 06, notebook 01_portfolio_optimisation.ipynb)
Reading guide for an AI assistant. Snapshot: 2026-11-22, about 01:20 CET.
All paths are relative to the repository root.

======================================================================
1. WHAT THIS FOLDER EXPLAINS
======================================================================

On 2026-11-21/22 we applied the classical recipe that worked on network24
(parallel tempering + iterated local search) to the portfolio problem, with
two problem-specific moves added: exact asset-trajectory DP and a day-level
tabu search. One campaign covered 125 (instance, budget, lambda) configurations.
No quantum program was used (0 qubits). Divi was not used.

Every .sol file in deliverables/portfolio/ passes the notebook's official
scorer, qoblib_tools.PortfolioModel.score (logs/verify_official_scorer.txt,
125 x OK). That scorer is the notebook's port of QOBLIB's checker. It
reproduces the published objectives of QOBLIB's reference solutions. We did
not run QOBLIB's own checker from the QOBLIB repository.

  group                         configs  below BKV  equal  above
  po_a010_* (8 inst x 7 lambda)  56       0          56     0
  po_a050_* (8 inst x 7 lambda)  56       6          34     16
  po_a200/a400 *_orig            13       no published BKV

  below the best-known value (BKV); lower is better:
  config                          ours        BKV        gap
  po_a050_t15_orig b020 l1e-2     -50,971     -31,504    -61.79%
  po_a050_t10_s00  b020 l1e-2     -19,785     -12,340    -60.33%
  po_a050_t10_orig b020 l1e-2     -44,208     -37,107    -19.14%  (*)
  po_a050_t10_s02  b020 l1e-2     -44,625     -43,565    -2.43%
  po_a050_t10_s00  b020 l5e-4     -234,696    -234,259   -0.19%
  po_a050_t15_s02  b020 l5e-4     -392,723    -392,668   -0.01%

  (*) PROVENANCE: this file comes from a run at 00:16 that was started from
  QOBLIB's published reference solution, with
  --init qoblib_data/06-portfolio/solutions/po_a050_t10_orig/po_a050_t10_orig_b020_l1e-2.bst.sol
  (see logs/log.csv, row 2026-11-22T00:16:10). It is a valid improvement of
  the published solution, but not an independent result. The run did not come
  from this session's job list: it wrote into the same solutions folder while
  this session was running. Independent runs from an empty portfolio reached
  -19,592 (hybrid without
  tabu, 2 min), -29,766 (tabu, 2 min) and -34,853 (hybrid, 3 min, seed 11,
  logs/development/a050_t10_orig_1e-2_independent_from_zero.log and .sol.txt),
  which is +6.07% above the BKV.
  The other five files below the BKV come from chains that started from
  the empty portfolio.

  above the BKV (weak spots):
  lambda 1e-2: a050_t10_s01 +55.5% (stuck at the empty portfolio, -1000),
               a050_t15_s01 +42.3%, a050_t15_s00 +18.4%, a050_t15_s02 +1.5%
  lambda 1e-3: all eight a050 instances, +0.28% to +2.76%
  lambda 5e-4: four a050 instances, +0.01% to +0.24%

HONEST SUMMARY (read before writing any claim):
- Short runs: 0.75 min (a010), 2 min (a050) and 3 min (a200/a400) per
  configuration with one seed. Longer runs would probably improve the "above"
  rows.
- QOBLIB's "best known" values for lambda = 1e-2 are weak (on a010 they are
  -1000 or -1500, the empty portfolio). The large negative gaps there say more
  about those references than about a breakthrough.
- For lambda <= 1e-4 every config matches the BKV. Many of those are proven
  optimal ("optimal" in QOBLIB's table), so they cannot be beaten.
- a200/a400: only the *_orig instances, with lambda in {1e-2, 1e-3, 1e-5},
  plus a400_t15 with 1e-4. They have no reference values, so these are just
  the first checked numbers at that scale (up to 36,165 QUBO variables).

======================================================================
2. THE PROBLEM IN ONE PARAGRAPH
======================================================================

T days (10 or 15), n assets (10/50/200/400). Each day, hold 0..3 units long
and 0..3 short of each asset. Minimise lambda*risk - returns + transaction
costs - cash interest + short fees + liquidation, subject to: net position
(long - short) in [C-15, C] with C = 10, and at most B open units per day
(B = 4/20/50/100). All coefficients are pre-rounded integers exactly as in
QOBLIB's Zimpl model (qoblib_tools.PortfolioModel). The notebook's QUBO has
T*(6n + 11) binary variables (710 for a010_t10, 36,165 for a400_t15).

Rewrite used here: v[t,i] = long - short in -3..3. Holding both sides never
helps, because every cost is at least as large. Per day:
  v'R_t v + lin.v + short_fee.neg(v) + tc.|v| (first/last day)
  + cash_table[C - net] + w_t.|v_t - v_{t-1}| (rebalancing, days 1..T-2)
The transition into the last day is free, and the last day pays liquidation.
`python portfolio_search.py selftest` checks this against the official
scorer on random states and on the published references.

KEY STRUCTURAL FACT: the covariance matrices are nearly singular (on
a050_t10_orig day 8, 21 of 50 eigenvalues are ~0). Once lambda >= 5e-4 makes
risk dominant (lambda 1e-2: risk of one unit ~15,000, while a good 20-unit
hedge has risk ~12,000), good solutions are
sparse hedges of about 20 assets held for 1-2 days, with the whole budget
used. Starting from an empty day, no single- or pair-asset move is
profitable. Plain PT stayed at the empty portfolio (-1000) for 120 s, and so
did DP descent. LLL reduction of the risk form finds low-risk integer vectors,
but they are dense (L1 norm 60-100, against B = 20), so they cannot be used
directly (scripts/lll_test.py).

======================================================================
3. THE METHOD (portfolio_search.py)
======================================================================

Integer tables are built once per instance with exact Fraction arithmetic
and cached in qoblib_data/06-portfolio/cache/<inst>.npz, which holds all
lambdas (a400_t15 takes ~130 s to build). The numba kernels then run:

  dp_single / dp_pair   exact DP over the T days for the whole trajectory of
                        one asset (7 states/day) or a pair (49 states/day;
                        separable transitions, O(K^3) per day), others fixed.
  descent               single-asset DP sweeps to convergence, then pair-DP
                        sweeps (all pairs for n <= 60), repeated.
  day_tabu              tabu search on one day's vector. It evaluates every
                        single +-1 and pair (+-1, +-1) move in O(1), using
                        G = (R + R')v, and applies the best admissible one
                        even if it worsens. Tenure 7 + n/20 (+random); a
                        reversed move is tabu unless it reaches a new best;
                        if every move is tabu, it takes the best one anyway.
                        Iterations 50 + 10*B. The day is sometimes emptied first.
  ILS                   1..max(3, n/8) random block kicks (shift / set / zero /
                        hedge an asset or pair over a day interval), then
                        descent; keep if not worse; restart from the best every
                        200 iterations.
  PT                    12 replicas, geometric temperatures from 0.5*median|delta|
                        down to /300, Metropolis on block moves, neighbour swaps.
                        Every 10 s the best state is DP-polished and injected
                        into the coldest replica.
  hybrid (default)      repeat: ILS (phase/3) -> day tabu (phase/2) -> PT (phase/2),
                        phase = max(10 s, run/6).

Which phase produced improvements (counts of "new best" lines in the 124
campaign logs): ILS 630, day tabu 720, PT 16. PT almost never improved on its
own; the day tabu is what unlocked lambda = 1e-2 and 1e-3. Before the day
tabu existed, a050_t10_orig lambda 1e-2 reached -19,592 (hybrid without tabu,
2 min from empty); the tabu alone reached -29,766 in 2 min from empty. On
lambda 1e-3 the hybrid without tabu reached -201,009, and 2 more minutes of
tabu from there gave -203,878.

======================================================================
4. FILES
======================================================================

deliverables/portfolio/*.sol         the 125 checked solutions (canonical QOBLIB format)
deliverables/portfolio/README.md     hand-in table and method
portfolio_search.py                  all code (build / selftest / run / verify / status)
ai_context/portfolio_classical/
  logs/log.csv                       every run in time order: timestamp, instance, budget,
                                     lambda, binary_vars (notebook QUBO size), objective,
                                     BKV, gap, method string (method, seed, minutes, init)
  logs/campaign/c_<inst>_<lam>.log   stdout of the 124 campaign runs (seed 11). Each "new best"
                                     line names the phase (ils / tabu / pt) and the time.
                                     Six a010 logs are from a re-run: the first attempt crashed
                                     on a cache-building race between parallel jobs (fixed in
                                     build_tables: temporary file names now include the PID).
  logs/development/                  first tests: a010 sanity runs, first a050_t10_orig batch
                                     (6 lambdas, before the day tabu), the tabu test, the a200
                                     scale test, the cache build log, and the independent
                                     from-zero rerun of a050_t10_orig lambda 1e-2.
  logs/verify_official_scorer.txt    125 x OK from `portfolio_search.py verify`
  scripts/campaign.sh                the campaign driver (6 parallel, xargs)
  scripts/campaign_jobs.txt          the 124 jobs: "<instance> <lambda> <minutes>"
  scripts/lll_test.py                the LLL experiment on the day-8 risk form (negative result)
  transcripts/portfolio_main_session.jsonl
                                     full Claude Code transcript of this session (JSONL, one
                                     event per line; mostly in Italian). The user's email
                                     addresses are replaced with <email-redacted>. Search it
                                     for "FINAL", "tabu", "eigs", "LLL" rather than reading it all.

======================================================================
5. REPRODUCE / CONTINUE
======================================================================

source .venv/bin/activate
python portfolio_search.py selftest --inst po_a010_t10_orig       # scorer equivalence
PORTFOLIO_SOL_DIR=deliverables/portfolio python portfolio_search.py verify
PORTFOLIO_SOL_DIR=deliverables/portfolio python portfolio_search.py status

# one configuration from scratch, in a scratch folder:
PORTFOLIO_SOL_DIR=/tmp/pf python portfolio_search.py run --inst po_a050_t15_orig \
    --lam 1e-2 --minutes 2 --seed 11 --init zero

# the whole campaign (about 35 min with 6 processes, <= 400 MB each):
sh ai_context/portfolio_classical/scripts/campaign.sh

Runs are not bit-for-bit reproducible because each phase is time-boxed, but
they reach the same quality. RAM: this machine has 7.4 GB, so keep to 6
processes or fewer. `verify` peaks at 1.2 GB on a400, because the official
scorer parses the covariances with Fractions.

======================================================================
6. NEXT STEPS THAT WOULD MOST LIKELY HELP
======================================================================

- A stronger per-day solver for the sparse integer QP (lambda >= 5e-4): longer
  tabu with restarts, multi-day blocks, or a MIQP sub-solver as an LNS move.
- Longer runs and more seeds on the 16 "above" rows (all a050, lambda 1e-3 / 1e-2).
- A natural place for Divi: the day subproblem restricted to a window of assets
  is a small QUBO (a hybrid LNS move, as was done for network18-23).
