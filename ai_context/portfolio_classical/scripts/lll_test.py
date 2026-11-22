import numpy as np, numba as nb, time, sys
sys.path.insert(0, ".")  # run from the repo root: python ai_context/portfolio_classical/scripts/lll_test.py
from portfolio_search import *

@nb.njit(cache=True)
def lll(b, delta):
    n, m = b.shape
    U = np.eye(n, dtype=np.int64)
    bs = np.zeros((n, m)); mu = np.zeros((n, n)); Bn = np.zeros(n)
    def_gs_from = 0
    k = 1
    # initial GS
    for i in range(n):
        bs[i] = b[i]
        for j in range(i):
            mu[i, j] = np.dot(b[i], bs[j]) / Bn[j]
            bs[i] -= mu[i, j] * bs[j]
        Bn[i] = np.dot(bs[i], bs[i])
    while k < n:
        for j in range(k - 1, -1, -1):
            q = np.round(mu[k, j])
            if q != 0:
                b[k] -= q * b[j]
                U[k] -= np.int64(q) * U[j]
                for l in range(j):
                    mu[k, l] -= q * mu[j, l]
                mu[k, j] -= q
        if Bn[k] >= (delta - mu[k, k - 1] ** 2) * Bn[k - 1]:
            k += 1
        else:
            tb = b[k].copy(); b[k] = b[k - 1]; b[k - 1] = tb
            tu = U[k].copy(); U[k] = U[k - 1]; U[k - 1] = tu
            for i in range(k - 1, n):
                bs[i] = b[i]
                for j in range(i):
                    mu[i, j] = np.dot(b[i], bs[j]) / Bn[j]
                    bs[i] -= mu[i, j] * bs[j]
                Bn[i] = np.dot(bs[i], bs[i])
            k = max(k - 1, 1)
    return U

p = Problem("po_a050_t10_orig", "1e-2")
t = 8
R = p.R[t].astype(float)
ev = np.linalg.eigvalsh(R); print("eigs <50:", (ev < 50).sum(), " <500:", (ev < 500).sum(), " of", len(ev))
Q = (R + R.T) / 2 + 5 * np.eye(p.n)
L = np.linalg.cholesky(Q)
t0 = time.time(); U = lll(L.copy(), 0.99); print("LLL", time.time() - t0, "s")
ret = -p.lin[t]
rows = []
for u in U:
    if ret @ u < 0: u = -u
    rows.append((int(u @ p.R[t] @ u), int(ret @ u), int(np.abs(u).sum()), int(np.abs(u).max())))
rows.sort()
for r in rows[:25]: print("risk %7d ret %7d L1 %3d max %d" % r)
