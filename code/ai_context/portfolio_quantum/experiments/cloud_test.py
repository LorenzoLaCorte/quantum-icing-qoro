import sys, time, numpy as np
sys.path.insert(0, "portfolio_quantum")
import qlns_core as qc, qlns, qaoa_solver as qs, portfolio_search as ps
from divi.backends import QoroService
svc = QoroService(); b0 = float(svc.get_credit_balance()["balance"]); print("balance", b0, flush=True)
p = ps.Problem("po_a050_t10_s01", "1e-3")
s = qc.State(p, qc.load_v(p, qc.best_known_file(p.stem)))
rng = np.random.default_rng(2)
M = int(sys.argv[1])
sol = qs.QAOASolver(layers=5, shots=4000, cloud=True, seed=1, angles_file="portfolio_quantum/angles/a050_l1e-3.json")
tmp, moves, hw = qlns.round_window(s, 3, rng, M)
a, b, _ = qc.build_qubo(tmp, moves)
t0 = time.time(); xs = sol.solve(tmp, moves, True, hw=hw); dt = time.time() - t0
c = qlns._distinct_feasible(tmp, moves, xs, a, b)
xo = qc.oracle(tmp, moves, any_sign=True)[1]
print(f"M={len(moves)} hw={hw} cloud best={c[0][0]} oracle={qc.energy(a, b, xo)} distinct={len(xs)} {dt:.1f}s circuits={sol.circuits}", flush=True)
time.sleep(5)
b1 = float(svc.get_credit_balance()["balance"]); print("balance", b1, "used", b0 - b1)
