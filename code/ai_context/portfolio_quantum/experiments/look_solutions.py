import sys, numpy as np
sys.path.insert(0, "portfolio_quantum")
import qlns_core as qc, portfolio_search as ps
for inst, lam in [("po_a050_t10_s01","1e-3"),("po_a050_t10_s00","1e-2"),("po_a050_t10_orig","1e-3")]:
    p = ps.Problem(inst, lam); f = qc.best_known_file(p.stem); v = qc.load_v(p, f)
    print("==", inst, lam, ps.read_objective(f), f.name)
    for t in range(p.T):
        nz = np.flatnonzero(v[t]); 
        print(t, "budget", np.abs(v[t]).sum(), "net", v[t].sum(), "nassets", len(nz), "vals", sorted(v[t][nz].tolist()))
    # day-to-day persistence
    print("changes per day", [int(np.abs(v[t]-v[t-1]).sum()) for t in range(1,p.T)])
    ev = np.linalg.eigvalsh(p.R[0].astype(float)); print("eig R0 min/max", ev[:3], ev[-1], "R_ii median", np.median(np.diag(p.R[0])), "|ret| median", np.median(np.abs(p.lin[0])))
