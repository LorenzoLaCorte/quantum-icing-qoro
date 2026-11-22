import os, qoblib_tools as qt, bank
for n in range(23, 16, -1):
    p = f'solutions/agent_qcompound/small/network{n:02d}.sol'
    if not os.path.exists(p): continue
    ok, sc, msg = qt.check_network_solution(p, n, qt.load_network_demand(n))
    print(f'network{n:02d} ok={ok} score={sc} BKV={bank.BKV[n]} gap={100*(sc-bank.BKV[n])/bank.BKV[n]:+.3f}% {msg if not ok else ""}')
