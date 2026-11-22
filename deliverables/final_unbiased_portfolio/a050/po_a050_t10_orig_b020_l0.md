# po_a050_t10_orig_b020_l0

- **Instance:** `po_a050_t10_orig` (50 assets × 10 days), budget B = 20, λ = 0
- **Official objective (referee re-score):** **-501737**, feasible: True
- **Breakdown:** risk=0, return=-530389, transaction=29309, cash_interest=-860, short_cost=203, liquidation=0
- **QOBLIB best known:** -501737 (optimal); gap +0.000%
- **Size:** 3110 binary variables in the official QUBO formulation; largest quantum program used for this file: **0 qubits** (classical)

## Method

**Previous team pipeline** (old repository, `portfolio_QIcing/` and `portfolio_search.py`): exact DP over periods (a010), pool-DP + exact-DP LNS, day-by-day tabu search, ILS, parallel tempering, and PCE-based quantum LNS for some a010 files. See the comment lines of the .sol and the old repository's notes for the exact run.

Reduced model used by the solver (equivalent to QOBLIB `bqp_u3_c10.zpl`): v = L − S per day and asset (long and short in one asset is dominated), interest = −10·(C − net) is linear, the capital rule is −5 ≤ Σv ≤ 10 and the budget rule Σ|v| ≤ B. The objective is checked to equal the official referee on every file.

Comment lines in the .sol: `QIcing portfolio attack | method: pool-DP + LNS-exactDP (classical)`; `settings: QP-relax+round+pair-descent+ILS pool (916), chain DP, LNS k<=4 150s seed 0`; `quantum: False | qubo vars:  | max qubits:`

Source file: `/mnt/d/Repos/Quantum_Munich_Challenges_TUM_Hackathon_PushQuantum_2026/quantum-icing-qoro/portfolio_QIcing/solutions/po_a050_t10_orig_b020_l0/po_a050_t10_orig_b020_l0__lns__20261121-221901.sol`

## Reproduce

```bash
cd opus_lab
# produced by the previous pipeline, see the source path above
~/.venvs/opus_pf/bin/python status.py   # re-score with the official referee
```

_Generated 2026-11-22 09:04 by make_submission.py._
