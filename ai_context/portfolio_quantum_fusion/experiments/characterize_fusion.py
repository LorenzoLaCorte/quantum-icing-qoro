"""Send one real balanced-fusion window (a400_t15 l1e-3) to Divi's Characterization Service."""
import sys, json, time, warnings, logging
import numpy as np, dimod
warnings.filterwarnings("ignore"); logging.disable(logging.WARNING)
sys.path.insert(0, "portfolio_quantum")
import qlns_core as qc, fusion_qaoa as fq
from paired_trajectory_qaoa import all_energies
from divi.backends import QoroService
from divi.backends.characterization import characterize_and_validate
from divi.qprog.problems import BinaryOptimizationProblem

p = qc.ps.Problem("po_a400_t15_orig", "1e-3")
d = np.load("ai_context/portfolio_quantum/experiments/a400_balanced_fusion_replay.npz")
state = qc.State(p, d["start"].astype(np.int64))
rng = np.random.default_rng(5)
best = None
for k in range(len(d["parents"])):
    par = d["parents"][k].astype(np.int64)
    days = [t for t in range(p.T - 1) if not np.array_equal(par[t], state.v[t])]
    for t in days:
        alts = {t: par[t]} if t + 1 not in days else {t: par[t], t + 1: par[t + 1]}
        a, b, comps = fq.fusion_window(state, alts, rng)
        if len(comps) < 8:
            continue
        E = all_energies(a, b)
        if E.min() < 0 and (best is None or len(comps) > best[3]):
            best = (a, b, int(E.argmin()), len(comps), int(E.min()), t, k)
a, b, kmin, M, emin, t, k = best
print(f"window: parent {k}, day {t}, {M} qubits, optimum dE={emin}", flush=True)
Q = {(i, i): float(a[i]) for i in range(M)}
Q.update({(i, j): float(b[i, j]) for i in range(M) for j in range(i + 1, M) if b[i, j]})
bqm = dimod.BinaryQuadraticModel.from_qubo(Q)
ref = "".join(str((kmin >> i) & 1) for i in range(M))
t0 = time.time()
rep = characterize_and_validate(BinaryOptimizationProblem(bqm), reference_states=[ref], service=QoroService())
print(f"done in {time.time() - t0:.0f}s, job {rep.job_id}", flush=True)
print(rep)
for name in ("summary", "recommendations", "recommended_layers", "gap_closed", "structure", "classical", "qaoa", "references"):
    if hasattr(rep, name):
        print(f"--- {name}:", getattr(rep, name))
