import time, numpy as np, qoblib_tools as qt, itertools, sys
sys.path.insert(0,'.')
from network_ils import WarmLP, move_2ex
n=24; D=qt.load_network_demand(n)
_, arcs, _ = qt.read_network_solution('deliverables/network24/network24.sol')
arcs=[tuple(a) for a in arcs]
W=WarmLP(D,arcs)
t=time.time(); z0,du=W.solve(arcs); print('z0',z0,time.time()-t)
basis=W.h.getBasis()
print('dual support (price>1e-6):',int((du>1e-6).sum()),'sum',du.sum())
# loads
sol=W.h.getSolution(); x=np.asarray(sol.col_value)[:-1].reshape(n,len(arcs))
load=x.sum(0); print('loads sorted',np.sort(load)[::-1][:12].round(0))
print('arcs at max (>z-1):',int((load>z0-1).sum()))
res=[]
t=time.time()
for p,q in itertools.combinations(range(48),2):
    new=move_2ex(arcs,p,q)
    if new is None or len(set(new))<48: continue
    z,_=W.solve(new,basis=basis)
    res.append((z,p,q))
W.solve(arcs,basis=basis)
dt=time.time()-t
res.sort()
print('n moves',len(res),'time',dt,'per',dt/len(res))
zs=np.array([r[0] for r in res])
print('best deltas',(zs[:30]-z0).round(1))
print('count delta<=0',(zs<=z0+1e-6).sum(),'<=+1000',(zs<=z0+1000).sum(),'<=+3000',(zs<=z0+3000).sum())
np.save('solutions/agent_qcompound/probe1_moves.npy',np.array(res))
