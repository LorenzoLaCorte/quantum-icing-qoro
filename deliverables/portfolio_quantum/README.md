# Portfolio optimisation (QOBLIB 06): quantum hand-in

Each `.sol` here was produced by the quantum large-neighbourhood search in
[`portfolio_quantum/`](../../portfolio_quantum/README.md). Every accepted improvement is a bitstring
sampled by a Divi QAOA program: p = 5, Dicke initial state, XY mixer that conserves the day budget, and
transferred angles. The programs ran on the Maestro simulator, with up to 18 qubits locally and 26 on
Qoro's cloud. The referee re-scored each file. The `.log.json` next to it lists every accepted window
and the run settings.

| Instance | B | λ | Binary variables | Largest QAOA (qubits) | Start | Quantum LNS | QOBLIB best known | Gap | Earlier classical (repo) | vs classical |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| `po_a050_t10_s00` | 20 | 0.001 | 3,110 | 18 | best | -191,256 | -191,879 | +0.32% | -190,685 | -571 |
| `po_a050_t10_s01` | 20 | 0.001 | 3,110 | 18 | best | -140,407 | -141,376 | +0.69% | -139,048 | -1,359 |
| `po_a050_t15_s00` | 20 | 0.001 | 4,665 | 18 | best | -312,668 | -314,736 | +0.66% | -312,312 | -356 |
| `po_a050_t15_s01` | 20 | 0.0005 | 4,665 | 18 | qbest | -304,271 | -304,289 | +0.01% | -303,567 | -704 |
| `po_a400_t15_orig` | 100 | 0.001 | 36,165 | 26 | best | -3,015,526 | — | — | -2,986,716 | -28,810 |

Verify from the repo root. `python portfolio_quantum/report.py` re-scores the source files in
`portfolio_quantum/solutions/`. You can also check each file here directly with the referee:

```python
import qoblib_tools as qt
h, pos = qt.read_portfolio_solution("deliverables/portfolio_quantum/po_a400_t15_orig_b100_l1e-3.sol")
m = qt.PortfolioModel(qt.load_portfolio_instance(h["instance"]), budget=int(h["budget"]), lam=h["lambda"])
print(m.score(pos))
```
