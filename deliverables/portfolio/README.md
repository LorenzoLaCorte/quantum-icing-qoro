# Portfolio optimisation (QOBLIB 06): classical hand-in

This folder holds 221 checked `.sol` files for QOBLIB 06, multi-period portfolio optimisation (notebook 01). They cover 221 (instance, budget, λ) configurations, from `po_a010_t10` (710 binary variables) to `po_a400_t15` (36,165 binary variables). All of them come from a **classical** search: no quantum program was used, so the qubit count is 0. The search code is [portfolio_search.py](../../portfolio_search.py). The logs, the run history and a reading guide are in [ai_context/portfolio_classical/](../../ai_context/portfolio_classical/READ_ME_FIRST.txt).

| Group | Configurations | Below the QOBLIB best-known value | Equal | Above |
| --- | ---: | ---: | ---: | ---: |
| `po_a010_*` (8 instances × 7 λ) | 56 | 0 | 56 | 0 |
| `po_a050_*` (8 instances × 7 λ) | 56 | **6** | 34 | 16 |
| `po_a200_*_orig`, `po_a400_*_orig` | 13 | no value published | | |
| `po_a200_*_s0x`, `po_a400_*_s0x` (12 instances × 8 λ) | 96 | no value published | | |

The budget B is 4, 20, 50 and 100 open units for 10, 50, 200 and 400 assets. λ = 0 was run only for the 12 `po_a200`/`po_a400` seed instances (`s00`–`s02`), and the tiny `a003`–`a005` instances were not run. "Binary variables" is the size of the notebook's official QUBO (`qoblib_tools.PortfolioQUBO`): 6 position bits per asset and day plus 11 slack bits per day.

## Verify

Every file is re-scored with `qoblib_tools.PortfolioModel.score`, the notebook's port of QOBLIB's checker. It reproduces the published objective of QOBLIB's reference solutions exactly. From the repo root:

```bash
source .venv/bin/activate
PORTFOLIO_SOL_DIR=deliverables/portfolio python portfolio_search.py verify   # about 15 min, 1.2 GB peak (a400)
PORTFOLIO_SOL_DIR=deliverables/portfolio python portfolio_search.py status   # objective vs best-known value
```

The run of 2026-11-22 printed `OK` for the first 125 files ([verify_official_scorer.txt](../../ai_context/portfolio_classical/logs/verify_official_scorer.txt)) and for the 96 seed-instance files ([verify log of the seed campaign](../../ai_context/portfolio_classical/logs/campaign_seeds/verify_official_scorer.txt)).

## Method and settings

The model is rewritten on one integer per asset and day, v = long − short in −3..3. Holding long and short units of the same asset at once never helps. The cost then equals the official score, which `python portfolio_search.py selftest` checks on random states against `PortfolioModel.score_arrays`. Four moves are combined:

1. **Exact asset DP.** The whole 10- or 15-day trajectory of one asset (7 states per day) or of a pair of assets (49 states per day) is re-optimised by dynamic programming, with every other position fixed. Days are coupled only through rebalancing costs, so this step is exact.
2. **Day tabu search.** Tabu search runs on one day's vector, with single and pair ±1 moves evaluated in O(1). It runs for 50 + 10·B iterations with tenure 7 + n/20, and sometimes starts from an emptied day. The covariance matrices are nearly singular (21 of 50 eigenvalues ≈ 0 on `a050_t10_orig`). Once λ ≥ 5e-4 makes risk dominant, good portfolios are hedges of about 20 assets held for a single day, and no single-asset or pair move from an empty day is profitable. This move builds those hedges.
3. **ILS.** It applies 1 to max(3, n/8) random block kicks (shift, set, zero or hedge an asset over a day interval), then runs the DP descent. A kick is kept if the result is no worse, and the search restarts from the best solution every 200 kicks.
4. **Parallel tempering.** 12 replicas run Metropolis block moves at geometric temperatures, which are calibrated automatically from the median |Δ| of random moves. Every 10 s the best state is polished with the DP descent and injected into the coldest replica.

`--method hybrid` (the default) repeats ILS → day tabu → PT phases. The campaign used seed 11 and 0.75, 2 and 3 minutes per configuration for a010, a050 and a200/a400, with 6 processes in parallel ([campaign.sh](../../ai_context/portfolio_classical/scripts/campaign.sh), [job list](../../ai_context/portfolio_classical/scripts/campaign_jobs.txt)). A run warm-starts from the best `.sol` already present and overwrites it only on improvement, so some files are the end of a short chain of runs. [log.csv](../../ai_context/portfolio_classical/logs/log.csv) records every run in order, with its objective, gap and method string.

The 96 seed-instance files (`po_a200`/`po_a400`, `t10`/`t15`, `s00`–`s02`, all 8 λ) come from a second campaign, one run per configuration from the empty portfolio with `--method tabu` (day tabu + DP polish + ILS kicks) and seed 11. Times: 12 min (a400) and 10 min (a200) for λ = 1e-2 and 1e-3; 12 min (a400) and 3 min (a200) for 5e-4; 12 min (a400) and 2 min (a200) for 1e-4; 1 min (a400) and 0.5 min (a200) for λ ≤ 5e-5. The planned warm-started second pass was dropped to finish sooner; on λ = 1e-2 the search was still improving (1–5.6% in the last 6 of 12 minutes on a400), so those files are the least converged. Scripts and logs: [campaign_seeds_resume.sh](../../ai_context/portfolio_classical/scripts/campaign_seeds_resume.sh), [logs/campaign_seeds/](../../ai_context/portfolio_classical/logs/campaign_seeds/log.csv).

To continue from this hand-in set (improvements overwrite the files here):

```bash
PORTFOLIO_SOL_DIR=deliverables/portfolio python portfolio_search.py run \
  --inst po_a050_t15_s01 --lam 1e-2 --minutes 10 --seed 12
```

¹ **Provenance note for `po_a050_t10_orig`, λ = 1e-2.** The file comes from a run started from QOBLIB's published reference solution (`--init …/po_a050_t10_orig_b020_l1e-2.bst.sol`, objective −37,107). That run improved it to −44,208. It is a valid improvement of the published solution, but not an independent result. An independent 3-minute run from the empty portfolio, with the campaign settings (hybrid, seed 11), reached −34,853, which is 6.07% above the best-known value ([log](../../ai_context/portfolio_classical/logs/development/a050_t10_orig_1e-2_independent_from_zero.log)).

## All configurations

Objectives are minimised, so a negative gap means below the QOBLIB best-known value. Those gaps are in bold.

| Instance | B | λ | Solution | Binary variables | Qubits | Checked objective | QOBLIB reference | Gap |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `po_a010_t10_orig` | 4 | 1e-2 | [po_a010_t10_orig_b004_l1e-2.sol](po_a010_t10_orig_b004_l1e-2.sol) | 710 | 0 | -1,000 | -1,000 (best known) | 0.00% |
| `po_a010_t10_orig` | 4 | 1e-3 | [po_a010_t10_orig_b004_l1e-3.sol](po_a010_t10_orig_b004_l1e-3.sol) | 710 | 0 | -8,397 | -8,397 (best known) | 0.00% |
| `po_a010_t10_orig` | 4 | 1e-4 | [po_a010_t10_orig_b004_l1e-4.sol](po_a010_t10_orig_b004_l1e-4.sol) | 710 | 0 | -69,482 | -69,482 (best known) | 0.00% |
| `po_a010_t10_orig` | 4 | 1e-5 | [po_a010_t10_orig_b004_l1e-5.sol](po_a010_t10_orig_b004_l1e-5.sol) | 710 | 0 | -103,821 | -103,821 (optimal) | 0.00% |
| `po_a010_t10_orig` | 4 | 1e-6 | [po_a010_t10_orig_b004_l1e-6.sol](po_a010_t10_orig_b004_l1e-6.sol) | 710 | 0 | -109,847 | -109,847 (optimal) | 0.00% |
| `po_a010_t10_orig` | 4 | 5e-4 | [po_a010_t10_orig_b004_l5e-4.sol](po_a010_t10_orig_b004_l5e-4.sol) | 710 | 0 | -27,044 | -27,044 (best known) | 0.00% |
| `po_a010_t10_orig` | 4 | 5e-5 | [po_a010_t10_orig_b004_l5e-5.sol](po_a010_t10_orig_b004_l5e-5.sol) | 710 | 0 | -84,980 | -84,980 (best known) | 0.00% |
| `po_a010_t10_s00` | 4 | 1e-2 | [po_a010_t10_s00_b004_l1e-2.sol](po_a010_t10_s00_b004_l1e-2.sol) | 710 | 0 | -1,000 | -1,000 (best known) | 0.00% |
| `po_a010_t10_s00` | 4 | 1e-3 | [po_a010_t10_s00_b004_l1e-3.sol](po_a010_t10_s00_b004_l1e-3.sol) | 710 | 0 | -30,171 | -30,171 (best known) | 0.00% |
| `po_a010_t10_s00` | 4 | 1e-4 | [po_a010_t10_s00_b004_l1e-4.sol](po_a010_t10_s00_b004_l1e-4.sol) | 710 | 0 | -142,819 | -142,819 (best known) | 0.00% |
| `po_a010_t10_s00` | 4 | 1e-5 | [po_a010_t10_s00_b004_l1e-5.sol](po_a010_t10_s00_b004_l1e-5.sol) | 710 | 0 | -204,770 | -204,770 (optimal) | 0.00% |
| `po_a010_t10_s00` | 4 | 1e-6 | [po_a010_t10_s00_b004_l1e-6.sol](po_a010_t10_s00_b004_l1e-6.sol) | 710 | 0 | -227,446 | -227,446 (best known) | 0.00% |
| `po_a010_t10_s00` | 4 | 5e-4 | [po_a010_t10_s00_b004_l5e-4.sol](po_a010_t10_s00_b004_l5e-4.sol) | 710 | 0 | -59,949 | -59,949 (best known) | 0.00% |
| `po_a010_t10_s00` | 4 | 5e-5 | [po_a010_t10_s00_b004_l5e-5.sol](po_a010_t10_s00_b004_l5e-5.sol) | 710 | 0 | -169,115 | -169,115 (best known) | 0.00% |
| `po_a010_t10_s01` | 4 | 1e-2 | [po_a010_t10_s01_b004_l1e-2.sol](po_a010_t10_s01_b004_l1e-2.sol) | 710 | 0 | -1,000 | -1,000 (best known) | 0.00% |
| `po_a010_t10_s01` | 4 | 1e-3 | [po_a010_t10_s01_b004_l1e-3.sol](po_a010_t10_s01_b004_l1e-3.sol) | 710 | 0 | -22,808 | -22,808 (best known) | 0.00% |
| `po_a010_t10_s01` | 4 | 1e-4 | [po_a010_t10_s01_b004_l1e-4.sol](po_a010_t10_s01_b004_l1e-4.sol) | 710 | 0 | -86,861 | -86,861 (best known) | 0.00% |
| `po_a010_t10_s01` | 4 | 1e-5 | [po_a010_t10_s01_b004_l1e-5.sol](po_a010_t10_s01_b004_l1e-5.sol) | 710 | 0 | -133,752 | -133,752 (best known) | 0.00% |
| `po_a010_t10_s01` | 4 | 1e-6 | [po_a010_t10_s01_b004_l1e-6.sol](po_a010_t10_s01_b004_l1e-6.sol) | 710 | 0 | -145,362 | -145,362 (best known) | 0.00% |
| `po_a010_t10_s01` | 4 | 5e-4 | [po_a010_t10_s01_b004_l5e-4.sol](po_a010_t10_s01_b004_l5e-4.sol) | 710 | 0 | -39,933 | -39,933 (best known) | 0.00% |
| `po_a010_t10_s01` | 4 | 5e-5 | [po_a010_t10_s01_b004_l5e-5.sol](po_a010_t10_s01_b004_l5e-5.sol) | 710 | 0 | -103,323 | -103,323 (best known) | 0.00% |
| `po_a010_t10_s02` | 4 | 1e-2 | [po_a010_t10_s02_b004_l1e-2.sol](po_a010_t10_s02_b004_l1e-2.sol) | 710 | 0 | -1,000 | -1,000 (best known) | 0.00% |
| `po_a010_t10_s02` | 4 | 1e-3 | [po_a010_t10_s02_b004_l1e-3.sol](po_a010_t10_s02_b004_l1e-3.sol) | 710 | 0 | -6,053 | -6,053 (best known) | 0.00% |
| `po_a010_t10_s02` | 4 | 1e-4 | [po_a010_t10_s02_b004_l1e-4.sol](po_a010_t10_s02_b004_l1e-4.sol) | 710 | 0 | -53,255 | -53,255 (best known) | 0.00% |
| `po_a010_t10_s02` | 4 | 1e-5 | [po_a010_t10_s02_b004_l1e-5.sol](po_a010_t10_s02_b004_l1e-5.sol) | 710 | 0 | -102,157 | -102,157 (optimal) | 0.00% |
| `po_a010_t10_s02` | 4 | 1e-6 | [po_a010_t10_s02_b004_l1e-6.sol](po_a010_t10_s02_b004_l1e-6.sol) | 710 | 0 | -120,706 | -120,706 (best known) | 0.00% |
| `po_a010_t10_s02` | 4 | 5e-4 | [po_a010_t10_s02_b004_l5e-4.sol](po_a010_t10_s02_b004_l5e-4.sol) | 710 | 0 | -19,633 | -19,633 (best known) | 0.00% |
| `po_a010_t10_s02` | 4 | 5e-5 | [po_a010_t10_s02_b004_l5e-5.sol](po_a010_t10_s02_b004_l5e-5.sol) | 710 | 0 | -67,517 | -67,517 (best known) | 0.00% |
| `po_a010_t15_orig` | 4 | 1e-2 | [po_a010_t15_orig_b004_l1e-2.sol](po_a010_t15_orig_b004_l1e-2.sol) | 1,065 | 0 | -1,500 | -1,500 (best known) | 0.00% |
| `po_a010_t15_orig` | 4 | 1e-3 | [po_a010_t15_orig_b004_l1e-3.sol](po_a010_t15_orig_b004_l1e-3.sol) | 1,065 | 0 | -10,304 | -10,304 (best known) | 0.00% |
| `po_a010_t15_orig` | 4 | 1e-4 | [po_a010_t15_orig_b004_l1e-4.sol](po_a010_t15_orig_b004_l1e-4.sol) | 1,065 | 0 | -102,371 | -102,371 (best known) | 0.00% |
| `po_a010_t15_orig` | 4 | 1e-5 | [po_a010_t15_orig_b004_l1e-5.sol](po_a010_t15_orig_b004_l1e-5.sol) | 1,065 | 0 | -162,439 | -162,439 (best known) | 0.00% |
| `po_a010_t15_orig` | 4 | 1e-6 | [po_a010_t15_orig_b004_l1e-6.sol](po_a010_t15_orig_b004_l1e-6.sol) | 1,065 | 0 | -172,660 | -172,660 (optimal) | 0.00% |
| `po_a010_t15_orig` | 4 | 5e-4 | [po_a010_t15_orig_b004_l5e-4.sol](po_a010_t15_orig_b004_l5e-4.sol) | 1,065 | 0 | -34,903 | -34,903 (best known) | 0.00% |
| `po_a010_t15_orig` | 4 | 5e-5 | [po_a010_t15_orig_b004_l5e-5.sol](po_a010_t15_orig_b004_l5e-5.sol) | 1,065 | 0 | -128,828 | -128,828 (best known) | 0.00% |
| `po_a010_t15_s00` | 4 | 1e-2 | [po_a010_t15_s00_b004_l1e-2.sol](po_a010_t15_s00_b004_l1e-2.sol) | 1,065 | 0 | -1,500 | -1,500 (best known) | 0.00% |
| `po_a010_t15_s00` | 4 | 1e-3 | [po_a010_t15_s00_b004_l1e-3.sol](po_a010_t15_s00_b004_l1e-3.sol) | 1,065 | 0 | -34,944 | -34,944 (best known) | 0.00% |
| `po_a010_t15_s00` | 4 | 1e-4 | [po_a010_t15_s00_b004_l1e-4.sol](po_a010_t15_s00_b004_l1e-4.sol) | 1,065 | 0 | -174,429 | -174,429 (best known) | 0.00% |
| `po_a010_t15_s00` | 4 | 1e-5 | [po_a010_t15_s00_b004_l1e-5.sol](po_a010_t15_s00_b004_l1e-5.sol) | 1,065 | 0 | -260,398 | -260,398 (best known) | 0.00% |
| `po_a010_t15_s00` | 4 | 1e-6 | [po_a010_t15_s00_b004_l1e-6.sol](po_a010_t15_s00_b004_l1e-6.sol) | 1,065 | 0 | -297,922 | -297,922 (best known) | 0.00% |
| `po_a010_t15_s00` | 4 | 5e-4 | [po_a010_t15_s00_b004_l5e-4.sol](po_a010_t15_s00_b004_l5e-4.sol) | 1,065 | 0 | -71,733 | -71,733 (best known) | 0.00% |
| `po_a010_t15_s00` | 4 | 5e-5 | [po_a010_t15_s00_b004_l5e-5.sol](po_a010_t15_s00_b004_l5e-5.sol) | 1,065 | 0 | -209,366 | -209,366 (best known) | 0.00% |
| `po_a010_t15_s01` | 4 | 1e-2 | [po_a010_t15_s01_b004_l1e-2.sol](po_a010_t15_s01_b004_l1e-2.sol) | 1,065 | 0 | -1,500 | -1,500 (best known) | 0.00% |
| `po_a010_t15_s01` | 4 | 1e-3 | [po_a010_t15_s01_b004_l1e-3.sol](po_a010_t15_s01_b004_l1e-3.sol) | 1,065 | 0 | -31,250 | -31,250 (best known) | 0.00% |
| `po_a010_t15_s01` | 4 | 1e-4 | [po_a010_t15_s01_b004_l1e-4.sol](po_a010_t15_s01_b004_l1e-4.sol) | 1,065 | 0 | -141,340 | -141,340 (best known) | 0.00% |
| `po_a010_t15_s01` | 4 | 1e-5 | [po_a010_t15_s01_b004_l1e-5.sol](po_a010_t15_s01_b004_l1e-5.sol) | 1,065 | 0 | -228,862 | -228,862 (best known) | 0.00% |
| `po_a010_t15_s01` | 4 | 1e-6 | [po_a010_t15_s01_b004_l1e-6.sol](po_a010_t15_s01_b004_l1e-6.sol) | 1,065 | 0 | -245,915 | -245,915 (best known) | 0.00% |
| `po_a010_t15_s01` | 4 | 5e-4 | [po_a010_t15_s01_b004_l5e-4.sol](po_a010_t15_s01_b004_l5e-4.sol) | 1,065 | 0 | -57,907 | -57,907 (best known) | 0.00% |
| `po_a010_t15_s01` | 4 | 5e-5 | [po_a010_t15_s01_b004_l5e-5.sol](po_a010_t15_s01_b004_l5e-5.sol) | 1,065 | 0 | -176,875 | -176,875 (best known) | 0.00% |
| `po_a010_t15_s02` | 4 | 1e-2 | [po_a010_t15_s02_b004_l1e-2.sol](po_a010_t15_s02_b004_l1e-2.sol) | 1,065 | 0 | -1,500 | -1,500 (best known) | 0.00% |
| `po_a010_t15_s02` | 4 | 1e-3 | [po_a010_t15_s02_b004_l1e-3.sol](po_a010_t15_s02_b004_l1e-3.sol) | 1,065 | 0 | -16,363 | -16,363 (best known) | 0.00% |
| `po_a010_t15_s02` | 4 | 1e-4 | [po_a010_t15_s02_b004_l1e-4.sol](po_a010_t15_s02_b004_l1e-4.sol) | 1,065 | 0 | -100,135 | -100,135 (best known) | 0.00% |
| `po_a010_t15_s02` | 4 | 1e-5 | [po_a010_t15_s02_b004_l1e-5.sol](po_a010_t15_s02_b004_l1e-5.sol) | 1,065 | 0 | -166,630 | -166,630 (best known) | 0.00% |
| `po_a010_t15_s02` | 4 | 1e-6 | [po_a010_t15_s02_b004_l1e-6.sol](po_a010_t15_s02_b004_l1e-6.sol) | 1,065 | 0 | -189,531 | -189,531 (optimal) | 0.00% |
| `po_a010_t15_s02` | 4 | 5e-4 | [po_a010_t15_s02_b004_l5e-4.sol](po_a010_t15_s02_b004_l5e-4.sol) | 1,065 | 0 | -37,224 | -37,224 (best known) | 0.00% |
| `po_a010_t15_s02` | 4 | 5e-5 | [po_a010_t15_s02_b004_l5e-5.sol](po_a010_t15_s02_b004_l5e-5.sol) | 1,065 | 0 | -121,102 | -121,102 (best known) | 0.00% |
| `po_a050_t10_orig` | 20 | 1e-2 | [po_a050_t10_orig_b020_l1e-2.sol](po_a050_t10_orig_b020_l1e-2.sol) | 3,110 | 0 | -44,208 | -37,107 (best known) | **−19.14%** ¹ |
| `po_a050_t10_orig` | 20 | 1e-3 | [po_a050_t10_orig_b020_l1e-3.sol](po_a050_t10_orig_b020_l1e-3.sol) | 3,110 | 0 | -205,672 | -206,239 (best known) | +0.27% |
| `po_a050_t10_orig` | 20 | 1e-4 | [po_a050_t10_orig_b020_l1e-4.sol](po_a050_t10_orig_b020_l1e-4.sol) | 3,110 | 0 | -370,869 | -370,869 (best known) | 0.00% |
| `po_a050_t10_orig` | 20 | 1e-5 | [po_a050_t10_orig_b020_l1e-5.sol](po_a050_t10_orig_b020_l1e-5.sol) | 3,110 | 0 | -478,956 | -478,956 (best known) | 0.00% |
| `po_a050_t10_orig` | 20 | 1e-6 | [po_a050_t10_orig_b020_l1e-6.sol](po_a050_t10_orig_b020_l1e-6.sol) | 3,110 | 0 | -499,339 | -499,339 (best known) | 0.00% |
| `po_a050_t10_orig` | 20 | 5e-4 | [po_a050_t10_orig_b020_l5e-4.sol](po_a050_t10_orig_b020_l5e-4.sol) | 3,110 | 0 | -254,857 | -254,972 (best known) | +0.05% |
| `po_a050_t10_orig` | 20 | 5e-5 | [po_a050_t10_orig_b020_l5e-5.sol](po_a050_t10_orig_b020_l5e-5.sol) | 3,110 | 0 | -417,218 | -417,218 (best known) | 0.00% |
| `po_a050_t10_s00` | 20 | 1e-2 | [po_a050_t10_s00_b020_l1e-2.sol](po_a050_t10_s00_b020_l1e-2.sol) | 3,110 | 0 | -19,785 | -12,340 (best known) | **−60.33%** |
| `po_a050_t10_s00` | 20 | 1e-3 | [po_a050_t10_s00_b020_l1e-3.sol](po_a050_t10_s00_b020_l1e-3.sol) | 3,110 | 0 | -187,582 | -191,879 (best known) | +2.24% |
| `po_a050_t10_s00` | 20 | 1e-4 | [po_a050_t10_s00_b020_l1e-4.sol](po_a050_t10_s00_b020_l1e-4.sol) | 3,110 | 0 | -355,530 | -355,530 (best known) | 0.00% |
| `po_a050_t10_s00` | 20 | 1e-5 | [po_a050_t10_s00_b020_l1e-5.sol](po_a050_t10_s00_b020_l1e-5.sol) | 3,110 | 0 | -484,396 | -484,396 (best known) | 0.00% |
| `po_a050_t10_s00` | 20 | 1e-6 | [po_a050_t10_s00_b020_l1e-6.sol](po_a050_t10_s00_b020_l1e-6.sol) | 3,110 | 0 | -513,409 | -513,409 (best known) | 0.00% |
| `po_a050_t10_s00` | 20 | 5e-4 | [po_a050_t10_s00_b020_l5e-4.sol](po_a050_t10_s00_b020_l5e-4.sol) | 3,110 | 0 | -234,696 | -234,259 (best known) | **−0.19%** |
| `po_a050_t10_s00` | 20 | 5e-5 | [po_a050_t10_s00_b020_l5e-5.sol](po_a050_t10_s00_b020_l5e-5.sol) | 3,110 | 0 | -408,937 | -408,937 (best known) | 0.00% |
| `po_a050_t10_s01` | 20 | 1e-2 | [po_a050_t10_s01_b020_l1e-2.sol](po_a050_t10_s01_b020_l1e-2.sol) | 3,110 | 0 | -1,000 | -2,248 (best known) | +55.52% |
| `po_a050_t10_s01` | 20 | 1e-3 | [po_a050_t10_s01_b020_l1e-3.sol](po_a050_t10_s01_b020_l1e-3.sol) | 3,110 | 0 | -137,469 | -141,376 (best known) | +2.76% |
| `po_a050_t10_s01` | 20 | 1e-4 | [po_a050_t10_s01_b020_l1e-4.sol](po_a050_t10_s01_b020_l1e-4.sol) | 3,110 | 0 | -301,400 | -301,400 (best known) | 0.00% |
| `po_a050_t10_s01` | 20 | 1e-5 | [po_a050_t10_s01_b020_l1e-5.sol](po_a050_t10_s01_b020_l1e-5.sol) | 3,110 | 0 | -402,742 | -402,742 (best known) | 0.00% |
| `po_a050_t10_s01` | 20 | 1e-6 | [po_a050_t10_s01_b020_l1e-6.sol](po_a050_t10_s01_b020_l1e-6.sol) | 3,110 | 0 | -428,609 | -428,609 (best known) | 0.00% |
| `po_a050_t10_s01` | 20 | 5e-4 | [po_a050_t10_s01_b020_l5e-4.sol](po_a050_t10_s01_b020_l5e-4.sol) | 3,110 | 0 | -183,556 | -183,574 (best known) | +0.01% |
| `po_a050_t10_s01` | 20 | 5e-5 | [po_a050_t10_s01_b020_l5e-5.sol](po_a050_t10_s01_b020_l5e-5.sol) | 3,110 | 0 | -342,074 | -342,074 (best known) | 0.00% |
| `po_a050_t10_s02` | 20 | 1e-2 | [po_a050_t10_s02_b020_l1e-2.sol](po_a050_t10_s02_b020_l1e-2.sol) | 3,110 | 0 | -44,625 | -43,565 (best known) | **−2.43%** |
| `po_a050_t10_s02` | 20 | 1e-3 | [po_a050_t10_s02_b020_l1e-3.sol](po_a050_t10_s02_b020_l1e-3.sol) | 3,110 | 0 | -233,766 | -233,766 (best known) | 0.00% |
| `po_a050_t10_s02` | 20 | 1e-4 | [po_a050_t10_s02_b020_l1e-4.sol](po_a050_t10_s02_b020_l1e-4.sol) | 3,110 | 0 | -443,357 | -443,357 (best known) | 0.00% |
| `po_a050_t10_s02` | 20 | 1e-5 | [po_a050_t10_s02_b020_l1e-5.sol](po_a050_t10_s02_b020_l1e-5.sol) | 3,110 | 0 | -594,866 | -594,866 (best known) | 0.00% |
| `po_a050_t10_s02` | 20 | 1e-6 | [po_a050_t10_s02_b020_l1e-6.sol](po_a050_t10_s02_b020_l1e-6.sol) | 3,110 | 0 | -622,388 | -622,388 (best known) | 0.00% |
| `po_a050_t10_s02` | 20 | 5e-4 | [po_a050_t10_s02_b020_l5e-4.sol](po_a050_t10_s02_b020_l5e-4.sol) | 3,110 | 0 | -287,872 | -287,872 (best known) | 0.00% |
| `po_a050_t10_s02` | 20 | 5e-5 | [po_a050_t10_s02_b020_l5e-5.sol](po_a050_t10_s02_b020_l5e-5.sol) | 3,110 | 0 | -507,544 | -507,544 (best known) | 0.00% |
| `po_a050_t15_orig` | 20 | 1e-2 | [po_a050_t15_orig_b020_l1e-2.sol](po_a050_t15_orig_b020_l1e-2.sol) | 4,665 | 0 | -50,971 | -31,504 (best known) | **−61.79%** |
| `po_a050_t15_orig` | 20 | 1e-3 | [po_a050_t15_orig_b020_l1e-3.sol](po_a050_t15_orig_b020_l1e-3.sol) | 4,665 | 0 | -320,978 | -321,907 (best known) | +0.29% |
| `po_a050_t15_orig` | 20 | 1e-4 | [po_a050_t15_orig_b020_l1e-4.sol](po_a050_t15_orig_b020_l1e-4.sol) | 4,665 | 0 | -572,490 | -572,490 (best known) | 0.00% |
| `po_a050_t15_orig` | 20 | 1e-5 | [po_a050_t15_orig_b020_l1e-5.sol](po_a050_t15_orig_b020_l1e-5.sol) | 4,665 | 0 | -736,833 | -736,833 (best known) | 0.00% |
| `po_a050_t15_orig` | 20 | 1e-6 | [po_a050_t15_orig_b020_l1e-6.sol](po_a050_t15_orig_b020_l1e-6.sol) | 4,665 | 0 | -769,790 | -769,790 (best known) | 0.00% |
| `po_a050_t15_orig` | 20 | 5e-4 | [po_a050_t15_orig_b020_l5e-4.sol](po_a050_t15_orig_b020_l5e-4.sol) | 4,665 | 0 | -396,850 | -397,497 (best known) | +0.16% |
| `po_a050_t15_orig` | 20 | 5e-5 | [po_a050_t15_orig_b020_l5e-5.sol](po_a050_t15_orig_b020_l5e-5.sol) | 4,665 | 0 | -639,825 | -639,825 (best known) | 0.00% |
| `po_a050_t15_s00` | 20 | 1e-2 | [po_a050_t15_s00_b020_l1e-2.sol](po_a050_t15_s00_b020_l1e-2.sol) | 4,665 | 0 | -35,719 | -43,792 (best known) | +18.43% |
| `po_a050_t15_s00` | 20 | 1e-3 | [po_a050_t15_s00_b020_l1e-3.sol](po_a050_t15_s00_b020_l1e-3.sol) | 4,665 | 0 | -309,555 | -314,736 (best known) | +1.65% |
| `po_a050_t15_s00` | 20 | 1e-4 | [po_a050_t15_s00_b020_l1e-4.sol](po_a050_t15_s00_b020_l1e-4.sol) | 4,665 | 0 | -586,823 | -586,823 (best known) | 0.00% |
| `po_a050_t15_s00` | 20 | 1e-5 | [po_a050_t15_s00_b020_l1e-5.sol](po_a050_t15_s00_b020_l1e-5.sol) | 4,665 | 0 | -819,899 | -819,899 (best known) | 0.00% |
| `po_a050_t15_s00` | 20 | 1e-6 | [po_a050_t15_s00_b020_l1e-6.sol](po_a050_t15_s00_b020_l1e-6.sol) | 4,665 | 0 | -872,055 | -872,055 (best known) | 0.00% |
| `po_a050_t15_s00` | 20 | 5e-4 | [po_a050_t15_s00_b020_l5e-4.sol](po_a050_t15_s00_b020_l5e-4.sol) | 4,665 | 0 | -386,923 | -386,990 (best known) | +0.02% |
| `po_a050_t15_s00` | 20 | 5e-5 | [po_a050_t15_s00_b020_l5e-5.sol](po_a050_t15_s00_b020_l5e-5.sol) | 4,665 | 0 | -680,124 | -680,124 (best known) | 0.00% |
| `po_a050_t15_s01` | 20 | 1e-2 | [po_a050_t15_s01_b020_l1e-2.sol](po_a050_t15_s01_b020_l1e-2.sol) | 4,665 | 0 | -7,914 | -13,706 (best known) | +42.26% |
| `po_a050_t15_s01` | 20 | 1e-3 | [po_a050_t15_s01_b020_l1e-3.sol](po_a050_t15_s01_b020_l1e-3.sol) | 4,665 | 0 | -239,293 | -243,245 (best known) | +1.62% |
| `po_a050_t15_s01` | 20 | 1e-4 | [po_a050_t15_s01_b020_l1e-4.sol](po_a050_t15_s01_b020_l1e-4.sol) | 4,665 | 0 | -473,765 | -473,765 (best known) | 0.00% |
| `po_a050_t15_s01` | 20 | 1e-5 | [po_a050_t15_s01_b020_l1e-5.sol](po_a050_t15_s01_b020_l1e-5.sol) | 4,665 | 0 | -626,762 | -626,762 (best known) | 0.00% |
| `po_a050_t15_s01` | 20 | 1e-6 | [po_a050_t15_s01_b020_l1e-6.sol](po_a050_t15_s01_b020_l1e-6.sol) | 4,665 | 0 | -667,210 | -667,210 (best known) | 0.00% |
| `po_a050_t15_s01` | 20 | 5e-4 | [po_a050_t15_s01_b020_l5e-4.sol](po_a050_t15_s01_b020_l5e-4.sol) | 4,665 | 0 | -303,567 | -304,289 (best known) | +0.24% |
| `po_a050_t15_s01` | 20 | 5e-5 | [po_a050_t15_s01_b020_l5e-5.sol](po_a050_t15_s01_b020_l5e-5.sol) | 4,665 | 0 | -533,733 | -533,733 (best known) | 0.00% |
| `po_a050_t15_s02` | 20 | 1e-2 | [po_a050_t15_s02_b020_l1e-2.sol](po_a050_t15_s02_b020_l1e-2.sol) | 4,665 | 0 | -39,998 | -40,622 (best known) | +1.54% |
| `po_a050_t15_s02` | 20 | 1e-3 | [po_a050_t15_s02_b020_l1e-3.sol](po_a050_t15_s02_b020_l1e-3.sol) | 4,665 | 0 | -314,360 | -316,799 (best known) | +0.77% |
| `po_a050_t15_s02` | 20 | 1e-4 | [po_a050_t15_s02_b020_l1e-4.sol](po_a050_t15_s02_b020_l1e-4.sol) | 4,665 | 0 | -604,145 | -604,145 (best known) | 0.00% |
| `po_a050_t15_s02` | 20 | 1e-5 | [po_a050_t15_s02_b020_l1e-5.sol](po_a050_t15_s02_b020_l1e-5.sol) | 4,665 | 0 | -830,838 | -830,838 (best known) | 0.00% |
| `po_a050_t15_s02` | 20 | 1e-6 | [po_a050_t15_s02_b020_l1e-6.sol](po_a050_t15_s02_b020_l1e-6.sol) | 4,665 | 0 | -879,472 | -879,472 (best known) | 0.00% |
| `po_a050_t15_s02` | 20 | 5e-4 | [po_a050_t15_s02_b020_l5e-4.sol](po_a050_t15_s02_b020_l5e-4.sol) | 4,665 | 0 | -392,723 | -392,668 (best known) | **−0.01%** |
| `po_a050_t15_s02` | 20 | 5e-5 | [po_a050_t15_s02_b020_l5e-5.sol](po_a050_t15_s02_b020_l5e-5.sol) | 4,665 | 0 | -692,197 | -692,197 (best known) | 0.00% |
| `po_a200_t10_orig` | 50 | 1e-2 | [po_a200_t10_orig_b050_l1e-2.sol](po_a200_t10_orig_b050_l1e-2.sol) | 12,110 | 0 | -390,040 | *none published* | — |
| `po_a200_t10_orig` | 50 | 1e-3 | [po_a200_t10_orig_b050_l1e-3.sol](po_a200_t10_orig_b050_l1e-3.sol) | 12,110 | 0 | -809,239 | *none published* | — |
| `po_a200_t10_orig` | 50 | 1e-5 | [po_a200_t10_orig_b050_l1e-5.sol](po_a200_t10_orig_b050_l1e-5.sol) | 12,110 | 0 | -1,265,263 | *none published* | — |
| `po_a200_t10_s00` | 50 | 0 | [po_a200_t10_s00_b050_l0.sol](po_a200_t10_s00_b050_l0.sol) | 12,110 | 0 | -1,553,406 | *none published* | — |
| `po_a200_t10_s00` | 50 | 1e-2 | [po_a200_t10_s00_b050_l1e-2.sol](po_a200_t10_s00_b050_l1e-2.sol) | 12,110 | 0 | -327,113 | *none published* | — |
| `po_a200_t10_s00` | 50 | 1e-3 | [po_a200_t10_s00_b050_l1e-3.sol](po_a200_t10_s00_b050_l1e-3.sol) | 12,110 | 0 | -780,510 | *none published* | — |
| `po_a200_t10_s00` | 50 | 1e-4 | [po_a200_t10_s00_b050_l1e-4.sol](po_a200_t10_s00_b050_l1e-4.sol) | 12,110 | 0 | -1,079,878 | *none published* | — |
| `po_a200_t10_s00` | 50 | 1e-5 | [po_a200_t10_s00_b050_l1e-5.sol](po_a200_t10_s00_b050_l1e-5.sol) | 12,110 | 0 | -1,413,981 | *none published* | — |
| `po_a200_t10_s00` | 50 | 1e-6 | [po_a200_t10_s00_b050_l1e-6.sol](po_a200_t10_s00_b050_l1e-6.sol) | 12,110 | 0 | -1,536,118 | *none published* | — |
| `po_a200_t10_s00` | 50 | 5e-4 | [po_a200_t10_s00_b050_l5e-4.sol](po_a200_t10_s00_b050_l5e-4.sol) | 12,110 | 0 | -869,371 | *none published* | — |
| `po_a200_t10_s00` | 50 | 5e-5 | [po_a200_t10_s00_b050_l5e-5.sol](po_a200_t10_s00_b050_l5e-5.sol) | 12,110 | 0 | -1,187,046 | *none published* | — |
| `po_a200_t10_s01` | 50 | 0 | [po_a200_t10_s01_b050_l0.sol](po_a200_t10_s01_b050_l0.sol) | 12,110 | 0 | -1,485,242 | *none published* | — |
| `po_a200_t10_s01` | 50 | 1e-2 | [po_a200_t10_s01_b050_l1e-2.sol](po_a200_t10_s01_b050_l1e-2.sol) | 12,110 | 0 | -246,594 | *none published* | — |
| `po_a200_t10_s01` | 50 | 1e-3 | [po_a200_t10_s01_b050_l1e-3.sol](po_a200_t10_s01_b050_l1e-3.sol) | 12,110 | 0 | -685,206 | *none published* | — |
| `po_a200_t10_s01` | 50 | 1e-4 | [po_a200_t10_s01_b050_l1e-4.sol](po_a200_t10_s01_b050_l1e-4.sol) | 12,110 | 0 | -984,384 | *none published* | — |
| `po_a200_t10_s01` | 50 | 1e-5 | [po_a200_t10_s01_b050_l1e-5.sol](po_a200_t10_s01_b050_l1e-5.sol) | 12,110 | 0 | -1,342,586 | *none published* | — |
| `po_a200_t10_s01` | 50 | 1e-6 | [po_a200_t10_s01_b050_l1e-6.sol](po_a200_t10_s01_b050_l1e-6.sol) | 12,110 | 0 | -1,468,396 | *none published* | — |
| `po_a200_t10_s01` | 50 | 5e-4 | [po_a200_t10_s01_b050_l5e-4.sol](po_a200_t10_s01_b050_l5e-4.sol) | 12,110 | 0 | -761,096 | *none published* | — |
| `po_a200_t10_s01` | 50 | 5e-5 | [po_a200_t10_s01_b050_l5e-5.sol](po_a200_t10_s01_b050_l5e-5.sol) | 12,110 | 0 | -1,103,844 | *none published* | — |
| `po_a200_t10_s02` | 50 | 0 | [po_a200_t10_s02_b050_l0.sol](po_a200_t10_s02_b050_l0.sol) | 12,110 | 0 | -1,448,554 | *none published* | — |
| `po_a200_t10_s02` | 50 | 1e-2 | [po_a200_t10_s02_b050_l1e-2.sol](po_a200_t10_s02_b050_l1e-2.sol) | 12,110 | 0 | -250,054 | *none published* | — |
| `po_a200_t10_s02` | 50 | 1e-3 | [po_a200_t10_s02_b050_l1e-3.sol](po_a200_t10_s02_b050_l1e-3.sol) | 12,110 | 0 | -673,271 | *none published* | — |
| `po_a200_t10_s02` | 50 | 1e-4 | [po_a200_t10_s02_b050_l1e-4.sol](po_a200_t10_s02_b050_l1e-4.sol) | 12,110 | 0 | -990,299 | *none published* | — |
| `po_a200_t10_s02` | 50 | 1e-5 | [po_a200_t10_s02_b050_l1e-5.sol](po_a200_t10_s02_b050_l1e-5.sol) | 12,110 | 0 | -1,308,780 | *none published* | — |
| `po_a200_t10_s02` | 50 | 1e-6 | [po_a200_t10_s02_b050_l1e-6.sol](po_a200_t10_s02_b050_l1e-6.sol) | 12,110 | 0 | -1,430,338 | *none published* | — |
| `po_a200_t10_s02` | 50 | 5e-4 | [po_a200_t10_s02_b050_l5e-4.sol](po_a200_t10_s02_b050_l5e-4.sol) | 12,110 | 0 | -768,267 | *none published* | — |
| `po_a200_t10_s02` | 50 | 5e-5 | [po_a200_t10_s02_b050_l5e-5.sol](po_a200_t10_s02_b050_l5e-5.sol) | 12,110 | 0 | -1,095,892 | *none published* | — |
| `po_a200_t15_orig` | 50 | 1e-2 | [po_a200_t15_orig_b050_l1e-2.sol](po_a200_t15_orig_b050_l1e-2.sol) | 18,165 | 0 | -668,807 | *none published* | — |
| `po_a200_t15_orig` | 50 | 1e-3 | [po_a200_t15_orig_b050_l1e-3.sol](po_a200_t15_orig_b050_l1e-3.sol) | 18,165 | 0 | -1,293,125 | *none published* | — |
| `po_a200_t15_orig` | 50 | 1e-5 | [po_a200_t15_orig_b050_l1e-5.sol](po_a200_t15_orig_b050_l1e-5.sol) | 18,165 | 0 | -1,953,068 | *none published* | — |
| `po_a200_t15_s00` | 50 | 0 | [po_a200_t15_s00_b050_l0.sol](po_a200_t15_s00_b050_l0.sol) | 18,165 | 0 | -2,376,513 | *none published* | — |
| `po_a200_t15_s00` | 50 | 1e-2 | [po_a200_t15_s00_b050_l1e-2.sol](po_a200_t15_s00_b050_l1e-2.sol) | 18,165 | 0 | -446,636 | *none published* | — |
| `po_a200_t15_s00` | 50 | 1e-3 | [po_a200_t15_s00_b050_l1e-3.sol](po_a200_t15_s00_b050_l1e-3.sol) | 18,165 | 0 | -1,215,275 | *none published* | — |
| `po_a200_t15_s00` | 50 | 1e-4 | [po_a200_t15_s00_b050_l1e-4.sol](po_a200_t15_s00_b050_l1e-4.sol) | 18,165 | 0 | -1,686,778 | *none published* | — |
| `po_a200_t15_s00` | 50 | 1e-5 | [po_a200_t15_s00_b050_l1e-5.sol](po_a200_t15_s00_b050_l1e-5.sol) | 18,165 | 0 | -2,177,890 | *none published* | — |
| `po_a200_t15_s00` | 50 | 1e-6 | [po_a200_t15_s00_b050_l1e-6.sol](po_a200_t15_s00_b050_l1e-6.sol) | 18,165 | 0 | -2,352,147 | *none published* | — |
| `po_a200_t15_s00` | 50 | 5e-4 | [po_a200_t15_s00_b050_l5e-4.sol](po_a200_t15_s00_b050_l5e-4.sol) | 18,165 | 0 | -1,349,824 | *none published* | — |
| `po_a200_t15_s00` | 50 | 5e-5 | [po_a200_t15_s00_b050_l5e-5.sol](po_a200_t15_s00_b050_l5e-5.sol) | 18,165 | 0 | -1,847,824 | *none published* | — |
| `po_a200_t15_s01` | 50 | 0 | [po_a200_t15_s01_b050_l0.sol](po_a200_t15_s01_b050_l0.sol) | 18,165 | 0 | -2,207,397 | *none published* | — |
| `po_a200_t15_s01` | 50 | 1e-2 | [po_a200_t15_s01_b050_l1e-2.sol](po_a200_t15_s01_b050_l1e-2.sol) | 18,165 | 0 | -358,993 | *none published* | — |
| `po_a200_t15_s01` | 50 | 1e-3 | [po_a200_t15_s01_b050_l1e-3.sol](po_a200_t15_s01_b050_l1e-3.sol) | 18,165 | 0 | -1,034,466 | *none published* | — |
| `po_a200_t15_s01` | 50 | 1e-4 | [po_a200_t15_s01_b050_l1e-4.sol](po_a200_t15_s01_b050_l1e-4.sol) | 18,165 | 0 | -1,510,191 | *none published* | — |
| `po_a200_t15_s01` | 50 | 1e-5 | [po_a200_t15_s01_b050_l1e-5.sol](po_a200_t15_s01_b050_l1e-5.sol) | 18,165 | 0 | -2,011,505 | *none published* | — |
| `po_a200_t15_s01` | 50 | 1e-6 | [po_a200_t15_s01_b050_l1e-6.sol](po_a200_t15_s01_b050_l1e-6.sol) | 18,165 | 0 | -2,183,345 | *none published* | — |
| `po_a200_t15_s01` | 50 | 5e-4 | [po_a200_t15_s01_b050_l5e-4.sol](po_a200_t15_s01_b050_l5e-4.sol) | 18,165 | 0 | -1,160,913 | *none published* | — |
| `po_a200_t15_s01` | 50 | 5e-5 | [po_a200_t15_s01_b050_l5e-5.sol](po_a200_t15_s01_b050_l5e-5.sol) | 18,165 | 0 | -1,682,004 | *none published* | — |
| `po_a200_t15_s02` | 50 | 0 | [po_a200_t15_s02_b050_l0.sol](po_a200_t15_s02_b050_l0.sol) | 18,165 | 0 | -2,200,702 | *none published* | — |
| `po_a200_t15_s02` | 50 | 1e-2 | [po_a200_t15_s02_b050_l1e-2.sol](po_a200_t15_s02_b050_l1e-2.sol) | 18,165 | 0 | -392,401 | *none published* | — |
| `po_a200_t15_s02` | 50 | 1e-3 | [po_a200_t15_s02_b050_l1e-3.sol](po_a200_t15_s02_b050_l1e-3.sol) | 18,165 | 0 | -1,016,015 | *none published* | — |
| `po_a200_t15_s02` | 50 | 1e-4 | [po_a200_t15_s02_b050_l1e-4.sol](po_a200_t15_s02_b050_l1e-4.sol) | 18,165 | 0 | -1,500,032 | *none published* | — |
| `po_a200_t15_s02` | 50 | 1e-5 | [po_a200_t15_s02_b050_l1e-5.sol](po_a200_t15_s02_b050_l1e-5.sol) | 18,165 | 0 | -1,997,466 | *none published* | — |
| `po_a200_t15_s02` | 50 | 1e-6 | [po_a200_t15_s02_b050_l1e-6.sol](po_a200_t15_s02_b050_l1e-6.sol) | 18,165 | 0 | -2,174,688 | *none published* | — |
| `po_a200_t15_s02` | 50 | 5e-4 | [po_a200_t15_s02_b050_l5e-4.sol](po_a200_t15_s02_b050_l5e-4.sol) | 18,165 | 0 | -1,148,116 | *none published* | — |
| `po_a200_t15_s02` | 50 | 5e-5 | [po_a200_t15_s02_b050_l5e-5.sol](po_a200_t15_s02_b050_l5e-5.sol) | 18,165 | 0 | -1,666,607 | *none published* | — |
| `po_a400_t10_orig` | 100 | 1e-2 | [po_a400_t10_orig_b100_l1e-2.sol](po_a400_t10_orig_b100_l1e-2.sol) | 24,110 | 0 | -955,715 | *none published* | — |
| `po_a400_t10_orig` | 100 | 1e-3 | [po_a400_t10_orig_b100_l1e-3.sol](po_a400_t10_orig_b100_l1e-3.sol) | 24,110 | 0 | -1,889,243 | *none published* | — |
| `po_a400_t10_orig` | 100 | 1e-5 | [po_a400_t10_orig_b100_l1e-5.sol](po_a400_t10_orig_b100_l1e-5.sol) | 24,110 | 0 | -2,501,662 | *none published* | — |
| `po_a400_t10_s00` | 100 | 0 | [po_a400_t10_s00_b100_l0.sol](po_a400_t10_s00_b100_l0.sol) | 24,110 | 0 | -3,502,750 | *none published* | — |
| `po_a400_t10_s00` | 100 | 1e-2 | [po_a400_t10_s00_b100_l1e-2.sol](po_a400_t10_s00_b100_l1e-2.sol) | 24,110 | 0 | -853,634 | *none published* | — |
| `po_a400_t10_s00` | 100 | 1e-3 | [po_a400_t10_s00_b100_l1e-3.sol](po_a400_t10_s00_b100_l1e-3.sol) | 24,110 | 0 | -1,800,345 | *none published* | — |
| `po_a400_t10_s00` | 100 | 1e-4 | [po_a400_t10_s00_b100_l1e-4.sol](po_a400_t10_s00_b100_l1e-4.sol) | 24,110 | 0 | -2,377,742 | *none published* | — |
| `po_a400_t10_s00` | 100 | 1e-5 | [po_a400_t10_s00_b100_l1e-5.sol](po_a400_t10_s00_b100_l1e-5.sol) | 24,110 | 0 | -3,050,040 | *none published* | — |
| `po_a400_t10_s00` | 100 | 1e-6 | [po_a400_t10_s00_b100_l1e-6.sol](po_a400_t10_s00_b100_l1e-6.sol) | 24,110 | 0 | -3,436,562 | *none published* | — |
| `po_a400_t10_s00` | 100 | 5e-4 | [po_a400_t10_s00_b100_l5e-4.sol](po_a400_t10_s00_b100_l5e-4.sol) | 24,110 | 0 | -1,979,339 | *none published* | — |
| `po_a400_t10_s00` | 100 | 5e-5 | [po_a400_t10_s00_b100_l5e-5.sol](po_a400_t10_s00_b100_l5e-5.sol) | 24,110 | 0 | -2,573,021 | *none published* | — |
| `po_a400_t10_s01` | 100 | 0 | [po_a400_t10_s01_b100_l0.sol](po_a400_t10_s01_b100_l0.sol) | 24,110 | 0 | -3,248,351 | *none published* | — |
| `po_a400_t10_s01` | 100 | 1e-2 | [po_a400_t10_s01_b100_l1e-2.sol](po_a400_t10_s01_b100_l1e-2.sol) | 24,110 | 0 | -934,098 | *none published* | — |
| `po_a400_t10_s01` | 100 | 1e-3 | [po_a400_t10_s01_b100_l1e-3.sol](po_a400_t10_s01_b100_l1e-3.sol) | 24,110 | 0 | -1,852,721 | *none published* | — |
| `po_a400_t10_s01` | 100 | 1e-4 | [po_a400_t10_s01_b100_l1e-4.sol](po_a400_t10_s01_b100_l1e-4.sol) | 24,110 | 0 | -2,382,070 | *none published* | — |
| `po_a400_t10_s01` | 100 | 1e-5 | [po_a400_t10_s01_b100_l1e-5.sol](po_a400_t10_s01_b100_l1e-5.sol) | 24,110 | 0 | -2,955,294 | *none published* | — |
| `po_a400_t10_s01` | 100 | 1e-6 | [po_a400_t10_s01_b100_l1e-6.sol](po_a400_t10_s01_b100_l1e-6.sol) | 24,110 | 0 | -3,202,287 | *none published* | — |
| `po_a400_t10_s01` | 100 | 5e-4 | [po_a400_t10_s01_b100_l5e-4.sol](po_a400_t10_s01_b100_l5e-4.sol) | 24,110 | 0 | -2,019,182 | *none published* | — |
| `po_a400_t10_s01` | 100 | 5e-5 | [po_a400_t10_s01_b100_l5e-5.sol](po_a400_t10_s01_b100_l5e-5.sol) | 24,110 | 0 | -2,557,185 | *none published* | — |
| `po_a400_t10_s02` | 100 | 0 | [po_a400_t10_s02_b100_l0.sol](po_a400_t10_s02_b100_l0.sol) | 24,110 | 0 | -2,970,949 | *none published* | — |
| `po_a400_t10_s02` | 100 | 1e-2 | [po_a400_t10_s02_b100_l1e-2.sol](po_a400_t10_s02_b100_l1e-2.sol) | 24,110 | 0 | -792,884 | *none published* | — |
| `po_a400_t10_s02` | 100 | 1e-3 | [po_a400_t10_s02_b100_l1e-3.sol](po_a400_t10_s02_b100_l1e-3.sol) | 24,110 | 0 | -1,677,385 | *none published* | — |
| `po_a400_t10_s02` | 100 | 1e-4 | [po_a400_t10_s02_b100_l1e-4.sol](po_a400_t10_s02_b100_l1e-4.sol) | 24,110 | 0 | -2,087,713 | *none published* | — |
| `po_a400_t10_s02` | 100 | 1e-5 | [po_a400_t10_s02_b100_l1e-5.sol](po_a400_t10_s02_b100_l1e-5.sol) | 24,110 | 0 | -2,656,267 | *none published* | — |
| `po_a400_t10_s02` | 100 | 1e-6 | [po_a400_t10_s02_b100_l1e-6.sol](po_a400_t10_s02_b100_l1e-6.sol) | 24,110 | 0 | -2,925,462 | *none published* | — |
| `po_a400_t10_s02` | 100 | 5e-4 | [po_a400_t10_s02_b100_l5e-4.sol](po_a400_t10_s02_b100_l5e-4.sol) | 24,110 | 0 | -1,801,116 | *none published* | — |
| `po_a400_t10_s02` | 100 | 5e-5 | [po_a400_t10_s02_b100_l5e-5.sol](po_a400_t10_s02_b100_l5e-5.sol) | 24,110 | 0 | -2,242,190 | *none published* | — |
| `po_a400_t15_orig` | 100 | 1e-2 | [po_a400_t15_orig_b100_l1e-2.sol](po_a400_t15_orig_b100_l1e-2.sol) | 36,165 | 0 | -1,513,140 | *none published* | — |
| `po_a400_t15_orig` | 100 | 1e-3 | [po_a400_t15_orig_b100_l1e-3.sol](po_a400_t15_orig_b100_l1e-3.sol) | 36,165 | 0 | -2,986,716 | *none published* | — |
| `po_a400_t15_orig` | 100 | 1e-4 | [po_a400_t15_orig_b100_l1e-4.sol](po_a400_t15_orig_b100_l1e-4.sol) | 36,165 | 0 | -3,408,082 | *none published* | — |
| `po_a400_t15_orig` | 100 | 1e-5 | [po_a400_t15_orig_b100_l1e-5.sol](po_a400_t15_orig_b100_l1e-5.sol) | 36,165 | 0 | -3,898,640 | *none published* | — |
| `po_a400_t15_s00` | 100 | 0 | [po_a400_t15_s00_b100_l0.sol](po_a400_t15_s00_b100_l0.sol) | 36,165 | 0 | -4,780,649 | *none published* | — |
| `po_a400_t15_s00` | 100 | 1e-2 | [po_a400_t15_s00_b100_l1e-2.sol](po_a400_t15_s00_b100_l1e-2.sol) | 36,165 | 0 | -1,237,003 | *none published* | — |
| `po_a400_t15_s00` | 100 | 1e-3 | [po_a400_t15_s00_b100_l1e-3.sol](po_a400_t15_s00_b100_l1e-3.sol) | 36,165 | 0 | -2,596,045 | *none published* | — |
| `po_a400_t15_s00` | 100 | 1e-4 | [po_a400_t15_s00_b100_l1e-4.sol](po_a400_t15_s00_b100_l1e-4.sol) | 36,165 | 0 | -3,357,218 | *none published* | — |
| `po_a400_t15_s00` | 100 | 1e-5 | [po_a400_t15_s00_b100_l1e-5.sol](po_a400_t15_s00_b100_l1e-5.sol) | 36,165 | 0 | -4,227,688 | *none published* | — |
| `po_a400_t15_s00` | 100 | 1e-6 | [po_a400_t15_s00_b100_l1e-6.sol](po_a400_t15_s00_b100_l1e-6.sol) | 36,165 | 0 | -4,699,472 | *none published* | — |
| `po_a400_t15_s00` | 100 | 5e-4 | [po_a400_t15_s00_b100_l5e-4.sol](po_a400_t15_s00_b100_l5e-4.sol) | 36,165 | 0 | -2,858,419 | *none published* | — |
| `po_a400_t15_s00` | 100 | 5e-5 | [po_a400_t15_s00_b100_l5e-5.sol](po_a400_t15_s00_b100_l5e-5.sol) | 36,165 | 0 | -3,617,360 | *none published* | — |
| `po_a400_t15_s01` | 100 | 0 | [po_a400_t15_s01_b100_l0.sol](po_a400_t15_s01_b100_l0.sol) | 36,165 | 0 | -4,912,455 | *none published* | — |
| `po_a400_t15_s01` | 100 | 1e-2 | [po_a400_t15_s01_b100_l1e-2.sol](po_a400_t15_s01_b100_l1e-2.sol) | 36,165 | 0 | -1,364,046 | *none published* | — |
| `po_a400_t15_s01` | 100 | 1e-3 | [po_a400_t15_s01_b100_l1e-3.sol](po_a400_t15_s01_b100_l1e-3.sol) | 36,165 | 0 | -2,793,398 | *none published* | — |
| `po_a400_t15_s01` | 100 | 1e-4 | [po_a400_t15_s01_b100_l1e-4.sol](po_a400_t15_s01_b100_l1e-4.sol) | 36,165 | 0 | -3,574,738 | *none published* | — |
| `po_a400_t15_s01` | 100 | 1e-5 | [po_a400_t15_s01_b100_l1e-5.sol](po_a400_t15_s01_b100_l1e-5.sol) | 36,165 | 0 | -4,440,742 | *none published* | — |
| `po_a400_t15_s01` | 100 | 1e-6 | [po_a400_t15_s01_b100_l1e-6.sol](po_a400_t15_s01_b100_l1e-6.sol) | 36,165 | 0 | -4,840,384 | *none published* | — |
| `po_a400_t15_s01` | 100 | 5e-4 | [po_a400_t15_s01_b100_l5e-4.sol](po_a400_t15_s01_b100_l5e-4.sol) | 36,165 | 0 | -3,042,201 | *none published* | — |
| `po_a400_t15_s01` | 100 | 5e-5 | [po_a400_t15_s01_b100_l5e-5.sol](po_a400_t15_s01_b100_l5e-5.sol) | 36,165 | 0 | -3,840,929 | *none published* | — |
| `po_a400_t15_s02` | 100 | 0 | [po_a400_t15_s02_b100_l0.sol](po_a400_t15_s02_b100_l0.sol) | 36,165 | 0 | -4,506,741 | *none published* | — |
| `po_a400_t15_s02` | 100 | 1e-2 | [po_a400_t15_s02_b100_l1e-2.sol](po_a400_t15_s02_b100_l1e-2.sol) | 36,165 | 0 | -1,258,649 | *none published* | — |
| `po_a400_t15_s02` | 100 | 1e-3 | [po_a400_t15_s02_b100_l1e-3.sol](po_a400_t15_s02_b100_l1e-3.sol) | 36,165 | 0 | -2,605,774 | *none published* | — |
| `po_a400_t15_s02` | 100 | 1e-4 | [po_a400_t15_s02_b100_l1e-4.sol](po_a400_t15_s02_b100_l1e-4.sol) | 36,165 | 0 | -3,261,956 | *none published* | — |
| `po_a400_t15_s02` | 100 | 1e-5 | [po_a400_t15_s02_b100_l1e-5.sol](po_a400_t15_s02_b100_l1e-5.sol) | 36,165 | 0 | -4,078,252 | *none published* | — |
| `po_a400_t15_s02` | 100 | 1e-6 | [po_a400_t15_s02_b100_l1e-6.sol](po_a400_t15_s02_b100_l1e-6.sol) | 36,165 | 0 | -4,444,543 | *none published* | — |
| `po_a400_t15_s02` | 100 | 5e-4 | [po_a400_t15_s02_b100_l5e-4.sol](po_a400_t15_s02_b100_l5e-4.sol) | 36,165 | 0 | -2,820,435 | *none published* | — |
| `po_a400_t15_s02` | 100 | 5e-5 | [po_a400_t15_s02_b100_l5e-5.sol](po_a400_t15_s02_b100_l5e-5.sol) | 36,165 | 0 | -3,501,065 | *none published* | — |
