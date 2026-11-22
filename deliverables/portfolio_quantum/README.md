# Portfolio optimisation (QOBLIB 06): quantum hand-in

Each `<instance>_b<budget>_l<lambda>.sol` here is the best file of the quantum pipeline in
[`portfolio_quantum/`](../../portfolio_quantum/README.md) for its configuration. The referee re-scored
every one of them. The `.log.json` next to each file lists the accepted windows and the settings. Every
accepted improvement is a QAOA sample:

- *Quantum LNS* (`qlns-qaoa`): Divi QAOA, p = 5, Dicke state + XY mixer that conserves the budget.
  Up to 18 qubits on the Maestro simulator and up to 28 on Qoro's cloud.
- *Paired-transfer QAOA* (`paired-transfer-qaoa`): one qubit per transfer that keeps budget and net
  position, p = 3, ≤ 16 qubits, local statevector.

`po_a400_t15_orig_b100_l1e-3__paired-trajectory-qaoa.sol` (−3,163,545) is the start of the a400 run.

| Instance | B | λ | Binary variables | Largest QAOA (qubits) | Start | Quantum LNS | QOBLIB best known | Gap | Earlier classical (repo) | vs classical |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| `po_a050_t10_orig` | 20 | 0.001 | 3,110 | 16 | best | -205,699 | -206,239 | +0.26% | -205,672 | -27 |
| `po_a050_t10_s00` | 20 | 0.001 | 3,110 | 18 | best | -191,256 | -191,879 | +0.32% | -190,685 | -571 |
| `po_a050_t10_s01` | 20 | 0.001 | 3,110 | 18 | best | -140,407 | -141,376 | +0.69% | -139,048 | -1,359 |
| `po_a050_t15_orig` | 20 | 0.001 | 4,665 | 16 | best | -321,183 | -321,907 | +0.22% | -321,070 | -113 |
| `po_a050_t15_orig` | 20 | 0.0005 | 4,665 | 16 | best | -397,384 | -397,497 | +0.03% | -397,236 | -148 |
| `po_a050_t15_s00` | 20 | 0.001 | 4,665 | 18 | best | -312,668 | -314,736 | +0.66% | -312,312 | -356 |
| `po_a050_t15_s01` | 20 | 0.0005 | 4,665 | 16 | best | -304,333 | -304,289 | -0.01% | -303,567 | -766 |
| `po_a400_t15_orig` | 100 | 0.001 | 36,165 | 16 | best | -3,164,781 | — | — | -2,986,716 | -178,065 |

Verify any file from the repo root:

```python
import qoblib_tools as qt
h, pos = qt.read_portfolio_solution("deliverables/portfolio_quantum/po_a400_t15_orig_b100_l1e-3.sol")
m = qt.PortfolioModel(qt.load_portfolio_instance(h["instance"]), budget=int(h["budget"]), lam=h["lambda"])
print(m.score(pos))
```
