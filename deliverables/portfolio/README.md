# Portfolio optimisation (QOBLIB 06-portfolio) hand-in

These are our best portfolio results so far. Each instance folder holds one `.sol` file in QOBLIB's canonical format. Every file passes QOBLIB's official Rust checker (`06-portfolio/check`) and the Python referee (`qoblib_tools.PortfolioModel.score`). For both, a lower score is better. Gap = (our score − QOBLIB reference) / |reference|, so a negative gap beats QOBLIB. The full write-up is the [portfolio report](../../portfolio_QIcing/report/portfolio_qicing.pdf).

The selection has three groups:

* **Beats QOBLIB:** 5 best-known values improved on 50-asset instances. All five came from classical search.
* **First value:** `a200` and `a400`, where QOBLIB lists no solution.
* **Quantum:** the best result of the quantum pipeline (PCE quantum large-neighbourhood search), where it comes within 20% of the reference.

The other 64 `a010` instances match QOBLIB exactly. Our exact dynamic program proves them optimal, so they are not repeated here.

"Binary variables" is the size of QOBLIB's reference QUBO model (`bqp_u3_c10`, 3 unit copies per asset and direction, 4+7 slack bits per day). Our quantum runs use a compact equivalent QUBO: 630 variables for `a010_t10` and 3,090 for `a050_t10`.

| Instance | B | λ | Solution | Binary variables | Qubits used | Checked objective | QOBLIB reference | Gap |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| **Beats QOBLIB** | | | | | | | | |
| `po_a050_t10_s00` | 20 | 1e-2 | [.sol](po_a050_t10_s00_b020_l1e-2/po_a050_t10_s00_b020_l1e-2.sol) | 3,110 | 0 | −17,675 | −12,340 (best known) | −43.23% |
| `po_a050_t15_orig` | 20 | 1e-2 | [.sol](po_a050_t15_orig_b020_l1e-2/po_a050_t15_orig_b020_l1e-2.sol) | 4,665 | 0 | −45,031 | −31,504 (best known) | −42.94% |
| `po_a050_t10_s02` | 20 | 1e-2 | [.sol](po_a050_t10_s02_b020_l1e-2/po_a050_t10_s02_b020_l1e-2.sol) | 3,110 | 0 | −45,069 | −43,565 (best known) | −3.45% |
| `po_a050_t15_s02` | 20 | 1e-2 | [.sol](po_a050_t15_s02_b020_l1e-2/po_a050_t15_s02_b020_l1e-2.sol) | 4,665 | 0 | −41,517 | −40,622 (best known) | −2.20% |
| `po_a050_t10_s00` | 20 | 5e-4 | [.sol](po_a050_t10_s00_b020_l5e-4/po_a050_t10_s00_b020_l5e-4.sol) | 3,110 | 0 | −234,587 | −234,259 (best known) | −0.14% |
| **First value** | | | | | | | | |
| `po_a200_t10_orig` | 50 | 1e-3 | [.sol](po_a200_t10_orig_b050_l1e-3/po_a200_t10_orig_b050_l1e-3.sol) | 12,110 | 0 | −818,362 | none | first value |
| `po_a400_t10_orig` | 100 | 1e-3 | [.sol](po_a400_t10_orig_b100_l1e-3/po_a400_t10_orig_b100_l1e-3.sol) | 24,110 | 0 | −1,896,257 | none | first value |
| **Quantum** | | | | | | | | |
| `po_a010_t10_orig` | 4 | 1e-4 | [.sol](po_a010_t10_orig_b004_l1e-4/po_a010_t10_orig_b004_l1e-4.sol) | 710 | 9 | −69,482 | −69,482 (proven optimal by our DP) | 0.000% |
| `po_a010_t10_orig` | 4 | 5e-4 | [.sol](po_a010_t10_orig_b004_l5e-4/po_a010_t10_orig_b004_l5e-4.sol) | 710 | 9 | −27,044 | −27,044 (proven optimal by our DP) | 0.000% |
| `po_a010_t10_orig` | 4 | 1e-3 | [.sol](po_a010_t10_orig_b004_l1e-3/po_a010_t10_orig_b004_l1e-3.sol) | 710 | 9 | −8,397 | −8,397 (proven optimal by our DP) | 0.000% |
| `po_a010_t10_s02` | 4 | 1e-4 | [.sol](po_a010_t10_s02_b004_l1e-4/po_a010_t10_s02_b004_l1e-4.sol) | 710 | 9 | −53,220 | −53,255 (proven optimal by our DP) | +0.066% |
| `po_a050_t10_s00` | 20 | 1e-4 | [.sol](po_a050_t10_s00_b020_l1e-4/po_a050_t10_s00_b020_l1e-4.sol) | 3,110 | 9 | −340,222 | −355,530 (best known) | +4.31% |
| `po_a050_t10_s00` | 20 | 1e-3 | [.sol](po_a050_t10_s00_b020_l1e-3/po_a050_t10_s00_b020_l1e-3.sol) | 3,110 | 9 | −157,229 | −191,879 (best known) | +18.06% |

## Method and settings

Each `.sol` header records the method, the full settings, and whether a quantum circuit produced it. The copies here are byte-identical to the originals in [portfolio_QIcing/solutions/](../../portfolio_QIcing/solutions/), which keeps every run.

- **Quantum (PCE-QLNS).** [run_qlns.py](../../portfolio_QIcing/run_qlns.py) starts from an empty portfolio and repeatedly picks a window of 5–6 assets over one or two days. It builds the exact conditional sub-QUBO of the compact model and solves it with Divi PCE (`n_layers=3`, at most 9 qubits, 4,000 shots, local Maestro simulator). It accepts the best feasible spliced sample. The `a010` results chain 2–3 runs from empty: 0.22 M circuits for λ=1e-4, 0.29 M for 5e-4, 0.91 M for 1e-3 and 0.73 M for `s02`. The `a050` results are single 30-minute runs from empty: seeds 22 and 21, 0.90 M and 0.94 M circuits.
- **Classical (pool-DP + LNS).** [lns.py](../../portfolio_QIcing/lns.py) / [run_lns.py](../../portfolio_QIcing/run_lns.py) work in three steps. First they build a per-day candidate pool (convex relaxation rounded at many scales, pair-move descent, ILS, SA). Then an exact DP picks one pool vector per day with the true transaction costs. Finally an LNS re-optimises k ≤ 4 assets exactly over all days, for 150–232 s with seed 0. The `a050_t10_s02` result comes from a 120 s `run_lns.solve` run with seed 1, the equal-wall-time baseline for the parallel-tempering experiments.

| Deliverable | Original file |
| --- | --- |
| `po_a010_t10_orig_b004_l1e-3` | `po_a010_t10_orig_b004_l1e-3__qlns-pce__20261121-223909.sol` |
| `po_a010_t10_orig_b004_l1e-4` | `po_a010_t10_orig_b004_l1e-4__qlns-pce__20261121-221811.sol` |
| `po_a010_t10_orig_b004_l5e-4` | `po_a010_t10_orig_b004_l5e-4__qlns-pce__20261121-222829.sol` |
| `po_a010_t10_s02_b004_l1e-4` | `po_a010_t10_s02_b004_l1e-4__qlns-pce__20261121-223909.sol` |
| `po_a050_t10_s00_b020_l1e-2` | `po_a050_t10_s00_b020_l1e-2__lns__20261121-221132.sol` |
| `po_a050_t10_s00_b020_l1e-3` | `po_a050_t10_s00_b020_l1e-3__qlns-pce__20261121-235627.sol` |
| `po_a050_t10_s00_b020_l1e-4` | `po_a050_t10_s00_b020_l1e-4__qlns-pce__20261121-235627.sol` |
| `po_a050_t10_s00_b020_l5e-4` | `po_a050_t10_s00_b020_l5e-4__lns__20261121-221402.sol` |
| `po_a050_t10_s02_b020_l1e-2` | `po_a050_t10_s02_b020_l1e-2__pooldp__20261122-002024.sol` |
| `po_a050_t15_orig_b020_l1e-2` | `po_a050_t15_orig_b020_l1e-2__lns__20261121-222308.sol` |
| `po_a050_t15_s02_b020_l1e-2` | `po_a050_t15_s02_b020_l1e-2__lns__20261121-222307.sol` |
| `po_a200_t10_orig_b050_l1e-3` | `po_a200_t10_orig_b050_l1e-3__lns__20261121-222313.sol` |
| `po_a400_t10_orig_b100_l1e-3` | `po_a400_t10_orig_b100_l1e-3__lns__20261121-222416.sol` |

## Verify

Build QOBLIB's checker once (it needs a Rust toolchain), then run it on every file from the repo root.

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/ZIB-AOPT/QOBLIB.git /tmp/qoblib
git -C /tmp/qoblib sparse-checkout set 06-portfolio/check
(cd /tmp/qoblib/06-portfolio/check && cargo build --release)

for f in deliverables/portfolio/*/*.sol; do
  /tmp/qoblib/06-portfolio/check/target/release/check_portfolio \
    qoblib_data/06-portfolio/instances "$f" | tail -1
done
```

Each line should read `Solution successfully verified`. The checker reads the instance, budget and λ from the file header.
