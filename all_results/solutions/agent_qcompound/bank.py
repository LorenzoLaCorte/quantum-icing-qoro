"""bank(n, arcs, method, outdir): integral routing -> .sol -> official checker -> log. Returns score or None."""
import csv, datetime, os, qoblib_tools as qt
BKV={5:65500,6:101000,7:142400,8:170231,9:196750,10:210800,11:238334,12:276474,13:300620,14:343091,15:370870,16:397908,17:437000,18:473375,19:492924,20:528528,21:569273,22:618135,23:659369,24:663688}
def bank(n, arcs, method, outdir):
    D=qt.load_network_demand(n)
    arcs=[tuple(map(int,a)) for a in arcs]
    assert qt.is_valid_topology(n,arcs)
    r=qt.route_integral(D,arcs,time_limit=120)
    os.makedirs(outdir,exist_ok=True)
    path=os.path.join(outdir,f'network{n:02d}.sol')
    tmp=path+'.tmp'
    z=qt.write_network_solution(tmp,n,r)
    ok,score,msg=qt.check_network_solution(tmp,n,D)
    if not ok: print('CHECK FAILED',msg); return None
    if os.path.exists(path):
        old=qt.check_network_solution(path,n,D)
        if old[0] and old[1]<=score: os.remove(tmp); return old[1]
    os.replace(tmp,path)
    with open(os.path.join(outdir,'log.csv'),'a',newline='') as f:
        csv.writer(f).writerow([datetime.datetime.now().isoformat(timespec='seconds'),f'network{n:02d}',score,BKV.get(n),f'{100*(score-BKV[n])/BKV[n]:+.3f}%',method])
    print(f'BANKED network{n:02d} {score} (BKV {BKV[n]}, {100*(score-BKV[n])/BKV[n]:+.3f}%) -> {path}',flush=True)
    return score
