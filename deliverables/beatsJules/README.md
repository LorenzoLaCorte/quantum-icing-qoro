# Portfolio results that beat the leaderboard leader (Jules02)

These two solutions beat Jules02, who held first place on the leaderboard for these instances with "Block decomposition + local search". They also beat QOBLIB's best-known values by wide margins. Both files pass QOBLIB's official Rust checker (`06-portfolio/check`) and the Python referee (`qoblib_tools.PortfolioModel.score`). Lower is better.

| Instance | B | λ | Solution | Our objective | Jules02 (#1 before) | vs Jules02 | Our previous best | QOBLIB best known | Gap vs QOBLIB |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `po_a050_t15_orig` | 20 | 1e-2 | [.sol](po_a050_t15_orig_b020_l1e-2/po_a050_t15_orig_b020_l1e-2.sol) | **−78,299** | −77,193 | −1,106 (−1.4%) | −50,971 | −31,504 | −148.5% |
| `po_a050_t10_s00` | 20 | 1e-2 | [.sol](po_a050_t10_s00_b020_l1e-2/po_a050_t10_s00_b020_l1e-2.sol) | **−39,665** | −24,353 | −15,312 (−62.9%) | −19,785 | −12,340 | −221.4% |

Both solutions are classical (0 qubits). Each file is byte-identical to its original in `portfolio_QIcing/solutions/<instance>/…__strongpool__<timestamp>.sol`.

## Why this works

At λ = 1e-2, our earlier best solutions left 5 of 14 trading days (t15_orig) and 6 of 9 (t10_s00) **empty**. Our per-day candidate generator could not find good integer portfolios for those days. It rounded the convex relaxation at a few fixed scales and then ran descent.

Here, a full 20-unit, factor-neutral basket is worth −2k to −16k on *every* trading day. Rotating 20 units in or out costs only about 2k each way. So the fix is a better per-day candidate pool. The chain DP over days was already exact.

## Method (`portfolio_QIcing/reset-3AM/strongpool.py`)

1. For each trading day t, and for entry-cost emulation e ∈ {0, 1} (an extra e·tc·|v| term), solve the day's continuous convex relaxation (`lns.period_relaxation`).
2. Draw 150 **randomised roundings** of the relaxation, x = floor(x* + U[0,1)). Repair each to feasibility, then run exact single and pair unit-move descent (`lns.period_descent`).
3. Run iterated local search from these starts: 600 kicks, each perturbing 2–6 assets, then descent (`lns.period_ils`).
4. Keep the 40 best distinct vectors per (t, e). Add our previous best solution's day vectors and the empty portfolio. That gives a pool of 1,136 vectors for t15_orig and 731 for t10_s00.
5. **Chain DP** (`lns.chain_dp`): pick exactly one pool vector per day, with exact transaction costs.
6. Polish with the exact-DP LNS (`lns.lns`, k ≤ 4 assets, 120 s). It found no further gain.

Wall time was 6 min (t15_orig) and 4 min (t10_s00) on a laptop, with 2 numba threads and seed fixed per day.

Reproduce from `portfolio_QIcing/`:

```bash
NUMBA_NUM_THREADS=2 ../.venv/bin/python reset-3AM/strongpool.py po_a050_t15_orig 1e-2 out_t15orig.npy
NUMBA_NUM_THREADS=2 ../.venv/bin/python reset-3AM/strongpool.py po_a050_t10_s00 1e-2 out_t10s00.npy
```

The full diagnosis is in [GatherMethods.md §6](../../portfolio_QIcing/reset-3AM/GatherMethods.md): the per-day relaxation bounds and the per-day comparison of the old and new candidate generators.

## Verify

```bash
for f in deliverables/beatsJules/*/*.sol; do
  /path/to/qoblib/06-portfolio/check/target/release/check_portfolio \
    qoblib_data/06-portfolio/instances "$f" | tail -1
done
```

Each line should read `Solution successfully verified`. See [portfolio/README.md](../portfolio/README.md#verify) for how to build the checker.
