# Development experiments (2026-11-22, 01:45–03:30 CET)

Run each script from the repo root with `.venv/bin/python ai_context/portfolio_quantum/experiments/<script>`.
The numbers below are the outputs printed during the session; the transcript has them in full.

| Script | Question | Result |
|---|---|---|
| `bench_qaoa.py` | Divi QAOA cost on dense random QUBOs (p=2, 17 circuits, Maestro) | 12 q 0.1 s, 16 q 1.3 s, 20 q 6.6 s, 22 q 28 s, 24 q 129 s. `force_sampling` does not help. Local windows therefore stay at ≤ 18 qubits. |
| `selftest.py` | Is the move-selection QUBO exact? | 0 mismatches against `Problem.objective` on 300 random windows × 20 assignments. |
| `oracle_lns.py` | Do ±1 windows of 9 assets on one day (exact solve) improve the classical best of a050_t10_s01 λ=1e-3? | No: 0 improvements in 2 000 windows from −139 048. From empty, −120 691. |
| `look_solutions.py` | Structure of the classical bests | λ=1e-3: budget 20 saturated every day, 14–17 assets, 30–38 unit changes per day. λ=1e-2: hedges of about 15 assets on a few days. |
| `test_round.py` | Relaxation-guided rounding, exact solve, one window per day | Day 4 is −1 055 better than the classical best. Days 2 and 6 reproduce the classical day exactly. This is the window type that works. |
| (`qlns.py --solver oracle`) | Full LNS with rounding and swap windows, exact sub-solver, 5–12 min | a050_t10_s01 λ=1e-3: −140 919 from the classical best and −140 770 from empty. Ceiling for the QAOA. |
| `test_qaoa.py` | QAOA, Dicke + ring XY, p=2, Monte Carlo 6×2 | Correct Hamming weight on every sample, but the window optimum was among the top 512 samples only 1/8 times. |
| `qaoa_tune.py` | Scaling, depth, ring/complete mixer, budget (16 qubits, C(16,8) = 12 870) | All variants close to random sampling (loss 0.2 → −0.1, against about −1 at the optimum). |
| `qaoa_transfer.py` | Angles trained with COBYLA on one window, then **fixed** on others (14 qubits) | p=5: window optimum found in 4/5 unseen windows, about 8× the uniform probability. Linear ramp: 0/5. p=3: 2/5. This is the configuration used. |
| `qaoa_time.py` | Fixed angles, p=5, 2 circuits per window | 14 q 0.20 s, 16 q 0.25 s, 18 q 0.61 s. `max_iterations=0` is not accepted. |
| `cloud_test.py` | One 16-qubit window on Qoro's cloud | Found the exact optimum. 0.02 credits, 168 s latency. (26-qubit programs cost about 0.75 credits per circuit, see `logs/cloud_a400_t15_l1e-3.log`.) |
| `test_hedge.py` | Rounding windows on empty days at λ=1e-2 | Fails: every rounded day is +10 000 to +17 000 worse than empty (the hedge breaks). The exact LNS (`logs/dev/o_l2.log`) finds nothing in 4 min either. |
| `warm_vs_dicke.py` | Warm seed vs Dicke on a400 | Interrupted for lack of CPU and RAM. A smoke test showed that the trained warm angles have β ≈ 0.03 (they barely mix), so the warm family was not used for the results. |
| `prof.py` | Profiling of one window | 16-qubit rounding window about 0.8 s. A swap window with Divi `LinearConstraint` slack had 19 qubits and took 5.7 s, which led to the flip trick (fixed weight, no slack). |
