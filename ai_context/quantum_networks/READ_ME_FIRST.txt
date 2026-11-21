QUANTUM-ASSISTED NETWORK DESIGN RESULTS (QOBLIB 08, network18-network24)
Reading guide for an AI assistant. Snapshot: 2026-11-21, about 23:15 CET.
All paths are relative to the repository root.

======================================================================
1. WHAT THIS FOLDER EXPLAINS
======================================================================

On 2026-11-21 we pushed six QOBLIB network-design instances below their
published best-known values (BKV), using a hybrid search with a QAOA step
(Divi, local Maestro simulator). We also tried hard to improve network24 with
quantum methods and failed. Both outcomes are documented here.

Every .sol file below passes the official checker (qoblib_tools.check_network_solution).

  instance   variables  QAOA qubits  our score  QOBLIB BKV  gap      file
  network18  306        18           473,000    473,375     -0.08%   deliverables/network18/network18.sol
  network19  342        18           488,895    492,924     -0.82%   deliverables/network19/network19.sol
  network20  380        18           519,343    528,528     -1.74%   deliverables/network20/network20.sol
  network21  420        18           562,362    569,273     -1.21%   deliverables/network21/network21.sol
  network22  462        18           606,424    618,135     -1.90%   deliverables/network22/network22.sol
  network23  506        18           639,739    659,369     -2.98%   deliverables/network23/network23.sol
  network24  552        0            657,121    663,688     -0.99%   deliverables/network24/network24.sol (unchanged; classical, found earlier)
  network17  272        16           445,682    437,000     +1.99%   not handed in (above BKV)

The QOBLIB BKVs for network11-23 come from one parallel-tempering submission
(20260818_ParallelTempering_Gupta). Our network24 (657,121) was already lower
than that submission's network23 BKV (659,369), even though network23 is a
sub-instance with one node fewer. That observation started this work.

HONEST SUMMARY OF THE QUANTUM ROLE (read this before writing any claim):
- Most of the gain is classical: the node-deletion warm start, exact-LP
  2-exchange descent, and the exact pair scan used to build the QUBO.
- QAOA is the escape/proposal step. In the chain that produced the handed-in
  files, its one improvement the classical pair scan could not find is
  network19: a 4-move compound at 496,000 when the best exact pair gave
  497,143. On network22 its improvement was a 2-move compound identical to the
  best exact pair. On network20 the final result came from descent after a
  QAOA-proposed kick.
- In the second, non-winning process, QAOA also found 3-move compounds better
  than the best pair on network21 and network18 (intermediate states only).
- On network24 the same quantum step found nothing. On the same QUBOs,
  simulated annealing matched or beat QAOA's energy in all 21 rounds
  (8 equal, 13 better), in about 0.1 s against 45-110 s for QAOA.
- Everything ran on a local noiseless statevector simulator (MaestroSimulator),
  not on quantum hardware and not on the Qoro cloud.

======================================================================
2. THE PROBLEM IN ONE PARAGRAPH
======================================================================

networkNN: build a directed graph on NN nodes where every node has out-degree
2 and in-degree 2, with no self-loops (2*NN arcs out of NN*(NN-1) binary
variables). Route the demand matrix (top-left NN x NN block of QOBLIB's
demand.txt) as a splittable multicommodity flow. Score = minimum possible
max arc load x 1000, rounded up. Lower is better. For a fixed topology, an
exact LP gives the score (qoblib_tools.route_min_congestion, which reproduces
every QOBLIB value). We use a warm-started HiGHS version (network_ils.WarmLP),
about 15-22 ms per neighbouring topology. A move that keeps degrees valid is
the 2-exchange (a->b),(c->d) => (a->d),(c->b).

======================================================================
3. THE METHOD
======================================================================

Step A - node-deletion warm start (solutions/agent_qcompound/shrink.py)
  Delete the last node of a good (NN+1)-node topology. Splice its two
  in-neighbours to its two out-neighbours (best of the two pairings, by LP).
  Since networkNN's demand is the top-left block of network(NN+1)'s, this is
  a strong start. From network24 = 657,121 it gave network23 = 642,084
  (-2.62% vs BKV) with no search at all. Chaining deletions without search
  degrades fast (+0.8% at network22, +3.8% at network20), so each instance is
  polished before the next smaller one is derived from it:
  23 -> 22 -> 21 -> 20 -> 19 -> 18.

Step B - exact 2-exchange descent
  First improvement over all 2-exchanges, scored by the exact LP with a
  cutoff, until a local optimum.

Step C - Quantum Compound Move step (QAOA), in small/qls.py, method compound()
  1. Take the N = 18 (process p1) or N = 16 (process p2) least-bad 2-exchanges
     at the local optimum. Their exact deltas d_i come from the descent's
     last pass.
  2. LP every compatible pair to get exact interactions
     J_ij = z_ij - z - d_i - d_j. Pairs that share an arc or give an invalid
     graph are conflicts.
  3. QUBO over y in {0,1}^N:
       E(y) = sum_i (d_i - mu) y_i + sum_ij J_ij y_i y_j + P * conflicts,
     normalised. mu (the 4th smallest delta) is a bias towards compounds of
     several cheap moves. This is the second-order expansion of the true
     objective in move space. The max-load objective is a min-max, so moves
     that each relieve a different saturated arc only help together (J < 0).
  4. Sample with Divi QAOA: p = 2, MonteCarloOptimizer(population_size=16),
     8 iterations (p1) or 6 (p2), MaestroSimulator(shots=4000). Bit i of the
     bitstring = variable i (checked in small/maptest.py).
  5. LP-evaluate the 30 lowest-energy conflict-free samples with at least
     2 moves. The exact best pair is the classical reference.
  6. Accept, in this order of priority:
     - the pair, if strictly better;
     - else the QAOA compound, if it improves;
     - else the QAOA compound as an ILS kick, if within +1.5%;
     - else a random kick.
     Restart from the best every 4 cycles.
  Every improvement is labelled in the logs with its origin: descent,
  pair-scan, qaoa-compound, descent-after-qaoa-kick, and so on.

Step D - banking (solutions/agent_qcompound/bank.py)
  Integer routing (qoblib_tools.route_integral) -> .sol -> official checker
  -> log.csv.

RAM guard (solutions/agent_qcompound/memguard.py): the machine has 7.4 GB.
Every run exits if MemAvailable falls below 900 MB. At most 2 heavy processes
ran at once (about 500 MB each with Divi loaded).

======================================================================
4. FILES TO READ, IN ORDER (feed these to the AI)
======================================================================

Essential:
  1. ai_context/quantum_networks/READ_ME_FIRST.txt   (this file)
  2. deliverables/README.md                          (hand-in table and method summary)
  3. 02_network_design.ipynb                         (the hackathon task: problem, scoring, Divi usage, ideas list)
  4. solutions/agent_qcompound/small/qls.py          (the search that produced network18-23: descent + QAOA compound step + chain)
  5. solutions/agent_qcompound/shrink.py             (node-deletion warm start)
  6. solutions/agent_qcompound/bank.py               (integral routing, checker, log)
  7. ai_context/quantum_networks/logs/chain_network18-23/run_p1.log
     (winning chain 23->18: every QAOA round with N, #conflicts, #negative J,
      QAOA time, best compound vs best exact pair, and the origin of each new best)
  8. ai_context/quantum_networks/logs/chain_network18-23/log.csv  (every banked solution with score, gap and origin)

Supporting:
  9.  ai_context/quantum_networks/logs/chain_network18-23/run_p2.log
      (second process, chain 22(smoke)->21->20->19->18->17; produced only network17)
  10. ai_context/quantum_networks/logs/chain_network18-23/p1.out, p2.out, run_smoke.log  (raw stdout)
  11. solutions/agent_qcompound/small/verify.py, small/maptest.py  (checker loop; Divi bit-order test)
  12. qoblib_tools.py   (referee: route_min_congestion, route_integral, check_network_solution)
  13. network_ils.py    (WarmLP: warm-started HiGHS LP; move_2ex)
  14. solutions/agent_qcompound/analyze0.py, probe1.py, qaoa_probe.py
      (first measurements at network24 = 657,121:
       - LP takes 0.11 s cold, about 22 ms warm;
       - all 936 2-exchanges are worse, the best by +3,110;
       - 25 of 48 arcs sit at max load and 23 carry positive dual prices;
       - the hop-count lower bound is 615,604;
       - a 20-qubit QAOA run (101 circuits) takes 10.5 s and about 500 MB)

network24 negative result (quantum compound moves):
  15. solutions/agent_qcompound/net24/qcm.py   (QCM for network24. Mode A: QAOA, 20 qubits, p=2.
      Mode B: PCE with 46-50 variables plus ridge refit. Includes an SA comparison on the same BQM.)
  16. ai_context/quantum_networks/logs/network24_quantum_compound_moves/
      runA1_v1.out, runA3.out, log_A1.txt, log_A3.txt  (QAOA rounds)
      runB2_v1.out, runB2.out, log_B2.txt              (PCE rounds)
      log_A98.txt, log_B97.txt, log_B99.txt            (smoke tests)
      Result: 921 compounds of 3-5 moves were LP-evaluated. The best was
      662,684 (+5,563); the best exact pair was 661,655; the best single move
      was +3,110. No improvement. Raw PCE samples were all conflicting
      (energy about +33 against SA's -1.7).
  17. ai_context/quantum_networks/logs/network24_classical_restarts/
      ruin_recreate.log  (solutions/agent_qcompound/ruin_recreate.py: delete node k, polish
                          the 23-node rest, re-insert k at the best arc pair, descend)
      grow_from_network23.log  (solutions/agent_qcompound/grow.py: insert node 24 into the
                                polished network23 = 639,739, then descend; reached 665,070)
      Descents from 665k-671k fell back to exactly 657,121, a very strong attractor.

Full process record (large; search them, don't read them whole):
  18. ai_context/quantum_networks/transcripts/quantum_networks_main_session.jsonl
      (coordinator session: reasoning, measurements, launching the subagents,
       RAM management, git rebase, hand-in)
  19. ai_context/quantum_networks/transcripts/subagents/agent-chain_network18-23.jsonl
      (wrote and ran qls.py)
  20. ai_context/quantum_networks/transcripts/subagents/agent-network24_compound_moves.jsonl
      (wrote and ran qcm.py)
  JSONL, one event per line. Extract the "type":"assistant" text, or grep for
  NEW BEST, bank, QAOA N=, bestcomp. Email addresses are replaced with
  <email-redacted>. Mostly in Italian.

Background (earlier classical work on network24, optional):
  ai_context/README.md, deliverables/reports/network24_report_eng.tex

======================================================================
5. REPRODUCE / VERIFY
======================================================================

Verify the hand-in (from the repo root, with the virtual environment active):
  python -c "import qoblib_tools as qt; [print(n, qt.check_network_solution(f'deliverables/network{n}/network{n}.sol', n, qt.load_network_demand(n))) for n in range(18, 25)]"

Re-run the winning chain (needs qoro-divi 0.16.2; about 30 minutes; one process):
  1. Rebuild the 642,084 network23 start from network24:
       PYTHONPATH=.:solutions/agent_qcompound python -c "import qoblib_tools as qt, shrink, bank; _,a,_=qt.read_network_solution('deliverables/network24/network24.sol'); z,new=shrink.shrink(a,24,qt.load_network_demand(23)); bank.bank(23,new,'node deletion','solutions/agent_qcompound')"
  2. Run the chain. --end is a wall-clock stop time today, HH:MM:SS: set it
     about 30 minutes ahead.
       PYTHONPATH=. python solutions/agent_qcompound/small/qls.py --start solutions/agent_qcompound/network23.sol --start-n 23 --chain 23,22,21,20,19,18 --minutes 2.5,4.5,4.5,4.5,4.5,6 --seed 1 --tag p1 --nq 18 --qiters 8 --end HH:MM:SS
  Results go to solutions/agent_qcompound/small/ (network*.sol, log.csv, run_p1.log).
  Divi QAOA sampling is seeded, but the search is time-limited, so exact
  numbers can differ.

======================================================================
6. OPEN POINTS / IDEAS NOT YET DONE
======================================================================
- A fair A/B test: same chain with the QAOA proposer replaced by SA, or by
  random compounds, at an equal LP budget. Without it, no claim that quantum
  beats classical.
- network17 and below: the node-deletion chain loses quality with distance
  from network24. Start them from their own good topology instead.
- network24: compounds of 2-exchanges up to 5 moves do not escape 657,121.
  A new idea is needed: different move types, or the exact MIP-based LNS
  that was not tried.
