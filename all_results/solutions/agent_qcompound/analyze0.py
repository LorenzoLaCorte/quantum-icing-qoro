import time, numpy as np, qoblib_tools as qt, itertools
from collections import deque
n=24; D=qt.load_network_demand(n)
z, arcs, _ = qt.read_network_solution('deliverables/network24/network24.sol')
print('z',z,'narcs',len(arcs), qt.is_valid_topology(n,arcs))
t=time.time(); r=qt.route_min_congestion(D,arcs); print('LP',r.objective,r.z_lp,'time',time.time()-t)
t=time.time()
for _ in range(3): qt.route_min_congestion(D,arcs)
print('LP avg', (time.time()-t)/3)
def hop(arcs):
    adj=[[] for _ in range(n)]
    for i,j in arcs: adj[i].append(j)
    H=np.zeros((n,n),int)
    for s in range(n):
        d=[-1]*n; d[s]=0; q=deque([s])
        while q:
            u=q.popleft()
            for v in adj[u]:
                if d[v]<0: d[v]=d[u]+1; q.append(v)
        H[s]=d
    return H
H=hop(arcs)
tot=(D*H).sum(); print('sum d*hop',tot,'hop bound',tot*1000/48,'diam',H.max(),'avg hop',H[D>0].mean())
print('total demand',D.sum(),'nonzero',(D>0).sum(), 'max',D.max())
# Moore bound per source (out) and per dest (in)
slots=[1]*2+[2]*4+[3]*8+[4]*16
lb_out=sum(sum(a*b for a,b in zip(sorted(D[s][np.arange(n)!=s],reverse=True),slots)) for s in range(n))
lb_in=sum(sum(a*b for a,b in zip(sorted(D[:,s][np.arange(n)!=s],reverse=True),slots)) for s in range(n))
print('Moore LB out',lb_out*1000/48,'in',lb_in*1000/48)
