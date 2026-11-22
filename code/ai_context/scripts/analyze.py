import json, sys, numpy as np, collections
recs=[json.loads(l) for l in open(sys.argv[1])]
print(len(recs),"steps; qubits",set(r["qubits"] for r in recs),"circuits/step",set(r["circuits"] for r in recs))
S=["divi","sa","exact","random"]
for s in S:
    dz=np.array([r["samplers"][s]["best_dz"] for r in recs]); ranks=[r["samplers"][s].get("rank") for r in recs if r["samplers"][s].get("rank")]
    print(f"{s:7s} median best Δ {np.median(dz):8.0f}  mean {np.mean(dz[np.isfinite(dz)]):8.0f}  rank1 {np.mean([x==1 for x in ranks]):.0%}  top5 {np.mean([x<=5 for x in ranks]):.0%} median rank {np.median(ranks)}  improving {np.sum(dz<0)}")
# pairwise wins divi vs sa
d=np.array([r["samplers"]["divi"]["best_dz"] for r in recs]); a=np.array([r["samplers"]["sa"]["best_dz"] for r in recs]); e=np.array([r["samplers"]["exact"]["best_dz"] for r in recs])
print("divi<sa",np.sum(d<a-1e-6),"tie",np.sum(abs(d-a)<1e-6),"divi>sa",np.sum(d>a+1e-6))
print("divi<exact",np.sum(d<e-1e-6),"tie",np.sum(abs(d-e)<1e-6),"divi>exact",np.sum(d>e+1e-6))
print("oracle n",np.median([r["oracle"]["n"] for r in recs if r["oracle"]]), "divi p_ground mean",np.mean([r["divi_p_ground"] for r in recs]))
print("accepted sources",collections.Counter(r["source"] for r in recs if r["accepted"]))
print("t_divi",np.mean([r["t_divi"] for r in recs]),"t_sa",np.mean([r["t_sa"] for r in recs]),"t_build",np.mean([r["t_build"] for r in recs]))
print("best_z",min(r["best_z"] for r in recs),"final banked",recs[-1]["banked"],"n_lp",recs[-1]["n_lp"])
