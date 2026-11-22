# New QOBLIB best-known values: slot formulation (2026-11-22)

This folder holds **new results only**: 4 instances where we beat QOBLIB's best-known value (BKV), found on 2026-11-22. The earlier hand-in is in [../portfolio/](../portfolio/README.md) and is unchanged. It beat the BKV on none of these 4 instances: our previous bests were −1,000, −35,445, −190,685 and −139,048, all above the BKV.

Every `.sol` is in QOBLIB's canonical format and passes both QOBLIB's official Rust checker (`06-portfolio/check`) and the Python referee (`qoblib_tools.PortfolioModel.score`). A lower score is better. Gap = (our score − BKV) / |BKV|, so a negative gap beats QOBLIB.

| Instance | B | λ | Solution | Binary variables | Qubits used | Checked objective | QOBLIB BKV | Gap | Method |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `po_a050_t10_s01` | 20 | 1e-2 | [.sol](po_a050_t10_s01_b020_l1e-2/po_a050_t10_s01_b020_l1e-2.sol) | 3,110 | 0 | −4,267 | −2,248 | **−89.81%** | classical |
| `po_a050_t10_orig` | 20 | 1e-2 | [.sol](po_a050_t10_orig_b020_l1e-2/po_a050_t10_orig_b020_l1e-2.sol) | 3,110 | 0 | −47,967 | −37,107 | **−29.27%** | classical |
| `po_a050_t10_orig` | 20 | 1e-2 | [.sol](po_a050_t10_orig_b020_l1e-2/quantum_hybrid_PCE/po_a050_t10_orig_b020_l1e-2.sol) (quantum-hybrid) | 3,110 | 9 | −44,514 | −37,107 | **−19.96%** | PCE + local search |
| `po_a050_t10_s00` | 20 | 1e-3 | [.sol](po_a050_t10_s00_b020_l1e-3/po_a050_t10_s00_b020_l1e-3.sol) | 3,110 | 0 | −191,991 | −191,879 | **−0.058%** | classical |
| `po_a050_t10_s01` | 20 | 1e-3 | [.sol](po_a050_t10_s01_b020_l1e-3/po_a050_t10_s01_b020_l1e-3.sol) | 3,110 | 0 | −141,431 | −141,376 | **−0.039%** | classical |

"Binary variables" is the size of QOBLIB's reference QUBO model (`bqp_u3_c10`), as in [../portfolio/](../portfolio/README.md). The method works per period, on 42 binary variables per move.

## Method: slot-QLNS
The method is a large-neighbourhood search built on a new **slot formulation** of one period's portfolio. The code is in [`portfolio_QIcing/formulation/`](../../portfolio_QIcing/formulation/README.md) (`slots.py`, `slot_qlns.py`).

* **Slot formulation.** One period's portfolio is a set of slots. Each slot is a 7-bit log-encoded choice of one unit: an (asset, long/short) pair, or nothing. The per-period unit budget holds for every bitstring, so there are no slack bits and no penalty. The referee's cost is exactly pairwise between slots. Asset codes are a Gray code over assets ordered by their leading correlation factor.
* **Move.** Pick a period. Remove up to k=6 held units, chosen at random or as a correlated cluster. Keep the remaining units as a fixed base. Re-choose 6 free slots jointly. The neighbourhood has roughly 101⁶ ≈ 10¹² options, which the single and pair unit moves of our earlier LNS cannot reach.
* **Sub-solver.** It proposes candidate slot bitstrings.
  * Classical files: uniform random bitstrings, 300 per move.
  * Quantum-hybrid file: **Divi PCE**, `PolyEncoding` on 9 qubits for 42 variables. The loss is a closed-form mean-field slot objective, optimised with L-BFGS-B at α=6 and 6 layers on the local Maestro simulator, using 72 k circuits over the run. Its shots and expectation roundings are the candidates.
* **Local search and acceptance.** Every candidate is polished by exact single and pair unit descent in its period. It is then scored on the exact multi-period objective, transaction costs included, and the best is accepted if it improves.
* **Runs.** Each run lasts 1,500 s. It starts from our previous best `.sol` for that instance; for `po_a050_t10_s01` λ=1e-2 that was the empty portfolio, −1,000. Settings, the start file and the seed are in each `.sol` header. Logs are in `portfolio_QIcing/formulation/logs/` (`camp_*.txt`, `slotqlns_*.txt`).

**Honest attribution.** Four of the five files used random proposals. The gains come from the slot formulation and its neighbourhood, not from the quantum sampler. In a matched head-to-head on `po_a050_t10_orig` λ=1e-2, PCE + descent and random + descent started from the same −35,445 and ran for the same 1,500 s. PCE reached −44,514 and random reached −47,800. Both beat the BKV, and random did better at equal wall time.

## Verify
From the repo root, with QOBLIB's checker built (`cargo build --release` in `06-portfolio/check`):

```bash
for f in $(find deliverables/portfolio_NEW_BKV_slot_formulation_2026-11-22 -name '*.sol'); do
  check_portfolio qoblib_data/06-portfolio/instances "$f"
done
```
