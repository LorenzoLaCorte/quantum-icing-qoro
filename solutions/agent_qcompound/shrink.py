"""Derive an (n-1)-node topology from an n-node one by deleting the last node and splicing its arcs."""
import sys, itertools, numpy as np, qoblib_tools as qt
BKV={11:238334,12:276474,13:300620,14:343091,15:370870,16:397908,17:437000,18:473375,19:492924,20:528528,21:569273,22:618135,23:659369,24:663688}
def shrink(arcs, n, demand_small):
    """Delete node n-1; try both splicings of in-neighbours to out-neighbours, keep the best valid."""
    x=n-1
    keep=[a for a in arcs if x not in a]
    ins=[i for i,j in arcs if j==x]; outs=[j for i,j in arcs if i==x]
    best=None
    for perm in itertools.permutations(outs):
        new=keep+[(u,v) for u,v in zip(ins,perm)]
        if qt.is_valid_topology(n-1,new) and len(set(new))==len(new):
            z=qt.route_min_congestion(demand_small,new).objective
            if best is None or z<best[0]: best=(z,new)
    if best is None:  # splice impossible (self-loop / duplicate): repair
        new=qt.repair_topology(n-1,keep+[(u,v) for u,v in zip(ins,outs) if u!=v],demand_small)
        best=(qt.route_min_congestion(demand_small,new).objective,new)
    return best
if __name__=='__main__':
    _,arcs,_=qt.read_network_solution('deliverables/network24/network24.sol')
    n=24
    while n>int(sys.argv[1] if len(sys.argv)>1 else 20):
        D=qt.load_network_demand(n-1)
        z,arcs=shrink(arcs,n,D); n-=1
        print(f'network{n:02d}: derived {z:.0f}  BKV {BKV[n]}  gap {100*(z-BKV[n])/BKV[n]:+.2f}%',flush=True)
