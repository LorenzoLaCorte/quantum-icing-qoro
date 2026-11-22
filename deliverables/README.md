# Qoro hackathon hand-in

Notebook 00 asks for each checked `.sol` file, the instance and binary variable count, the largest quantum program in qubits, the official objective alongside QOBLIB's best-known value, and the method and settings needed to reproduce the result. **Source code is optional under the notebook instructions.** Follow any additional directions Qoro announces at the event. [Handing in](../00_main_qubo_101.ipynb)

| Instance | Solution | Binary variables | Qubits used to produce solution | Checked objective | QOBLIB reference | Gap | Certified |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `network05` | [network05.sol](network05/network05.sol) | 20 | 0 | 65,500 | 65,500 (proven optimum) | 0.00% | optimal (all 216 topologies) |
| `network18` | [network18.sol](network18/network18.sol) | 306 | 18 | 472,112 | 473,375 (best known) | −0.27% | radius 3 |
| `network19` | [network19.sol](network19/network19.sol) | 342 | 18 | 488,895 | 492,924 (best known) | −0.82% | radius 3 |
| `network20` | [network20.sol](network20/network20.sol) | 380 | 18 | 519,343 | 528,528 (best known) | −1.74% | radius 3 |
| `network21` | [network21.sol](network21/network21.sol) | 420 | 18 | 562,362 | 569,273 (best known) | −1.21% | radius 3 |
| `network22` | [network22.sol](network22/network22.sol) | 462 | 18 | 604,540 | 618,135 (best known) | −2.20% | radius 3 |
| `network23` | [network23.sol](network23/network23.sol) | 506 | 18 | 639,739 | 659,369 (best known) | −2.98% | radius 3 |
| `network24` | [network24.sol](network24/network24.sol) | 552 | 0 | 657,121 | 663,688 (best known) | −0.99% | radius 3 |

**Portfolio optimisation:** 13 checked solutions are in [portfolio/](portfolio/README.md). They are 5 improved best-known values on 50-asset instances (classical, up to −43%), first values for `a200` and `a400`, and the best quantum results. PCE quantum LNS reaches the proven optimum on 3 `a010` instances and +4.3% on `a050_t10_s00` at λ=1e-4, starting from an empty portfolio with at most 9 qubits.

The `network05` and `network24` solutions were found by classical searches. `network18`–`network23` come from a hybrid chain, network23 → network18. Each instance starts from the polished topology of the next larger one with its last node deleted. Exact-LP 2-exchange descent refines it, and a QAOA step (Divi, local Maestro simulator, 18 qubits, p=2) samples combinations of 2-exchange moves to escape local optima. QAOA samples gave direct improvements on network22 and network19 and kicks before later descents on network20, while most of the gain came from the classical descent and the exact pair scan. The search code is [solutions/agent_qcompound/small/qls.py](../solutions/agent_qcompound/small/qls.py). The logs, transcripts and a reading guide are in [ai_context/quantum_networks/](../ai_context/quantum_networks/READ_ME_FIRST.txt). The [network24 report](reports/network24_report_eng.tex) describes how parallel tempering and iterated local search were combined to produce the checked result.

**Every hand-in above is a certified radius-3 local optimum.** The `Certified` column is a proof, not a search result: for each instance, *every* topology differing from the one handed in by two or three arcs has been enumerated and refuted. Degrees force any move between two valid topologies differing in k arcs to be a derangement of the heads of those k arcs, so each radius is finite — 630 moves at radius 2 and 14,280 at radius 3 on 18 nodes, 1,128 and 34,592 on 24 — and [TheGOAT_Testing/certify_descent.py](../TheGOAT_Testing/certify_descent.py) enumerates them all against a warm dual simplex bounded at the incumbent, taking the single best improving move and repeating until a pass comes back empty. `network05` is stronger still: all 216 valid topologies were scored, so its optimum is proven outright.

That sweep improved two hand-ins over the hybrid chain's results: **`network18` 473,000 → 472,112** (−0.08% → −0.27%) and **`network22` 606,424 → 604,540** (−1.90% → −2.20%), both re-validated by the checker. Each improving move is a 3-rotation — a move type the chain's ILS already samples — which is the point: sampling a neighbourhood is not exhausting it, and two minutes of enumeration found what hours of heuristic search had missed. Both start from the chain's own topologies, so the 18-qubit QAOA step stays in their ancestry and only the last refinement is classical and exhaustive.

The portfolio hand-in (QOBLIB 06, 221 configurations, 6 below the best-known value) is summarised in [Portfolio optimisation](#portfolio-optimisation-qoblib-06) at the end of this file.

## Method and settings

- `network05` used seed `0`, a random starting topology, degree-preserving link swaps, and exact LP routing. The verification command uses a batch of 8 moves, 2 LP workers, and a 0.2-minute budget. The banked sequence was 83,000 → 81,500 → 74,000 → 71,500 → 65,500. [Banking log](../solutions/log.csv) · [Methodology and reproduction](../ai_context/README.md#network05-from-83000-to-the-proven-optimum)
- `network24` followed a PT → ILS → PT sequence. PT run `r6` supplied the 670,621 topology. ILS run `run8` reduced it to 661,760, then PT run `r7` reached 657,121 after 62 seconds from that warm start. The report gives the settings for all three runs. [Initial PT log](../ai_context/logs/parallel_tempering/pt_r6.log) · [ILS log](../ai_context/logs/ils_stdout/ils_run8.out) · [Final PT log](../ai_context/logs/parallel_tempering/pt_r7.log)

## Verify and build

From the repo root, run the referee on each submitted file.

```bash
source venv/bin/activate
NETWORK_SOL_DIR=deliverables/network05 python network_pipeline.py status
NETWORK_SOL_DIR=deliverables/network24 python network_pipeline.py status
```

### Replay the network24 stages

The two warm-start files at 670,621 and 661,760 are absent from the archive. To replay from those starts, put each recovered `network24.sol` in its own scratch directory, then run the corresponding command from the repo root with the virtual environment active.

```bash
NETWORK_SOL_DIR="$ILS_DIR" python network_ils.py run --n 24 --minutes 20 \
  --chains 5 --seed 700 --starts banked --deep 12 --deep_tol 0.015 \
  --kmax 8 --sync --log "$ILS_DIR/run8.log"

NETWORK_SOL_DIR="$PT_DIR" python -m network_design.parallel_tempering 24 \
  --minutes 20 --replicas 10 --workers 10 --tmin 450 --tmax 2500 \
  --banked 2 --K 60 --p-double 0.5 --p-tri 0.03 --steps 15 --seed 8 --tag r7
```

For the initial PT run, use the same PT settings with `--minutes 30 --seed 7 --tag r6` and the 673,253 starting topology in [the archived snapshot](../solutions/agent_pt/r5_best24.json). The historical handoff to ILS used the checked 670,621 solution from round 595. Preserve that file if a rerun reaches it, since subsequent improvements replace it.

### Build the report

Open the repo folder in VS Code with the LaTeX Workshop extension installed. With [the report](reports/network24_report_eng.tex) active, run **LaTeX Workshop: Build LaTeX project** from the Command Palette, then **LaTeX Workshop: View LaTeX PDF file**. The [workspace recipe](../.vscode/settings.json) uses XeLaTeX and writes to `deliverables/reports/build/`. If VS Code cannot find `latexmk`, make sure the TeX installation is on its PATH. On macOS with MacTeX, launch VS Code from a terminal that has `/Library/TeX/texbin` on its PATH. [LaTeX Workshop build documentation](https://github.com/James-Yu/LaTeX-Workshop/wiki/Compile)

The equivalent terminal build from the repo root is

```bash
latexmk -cd -xelatex -synctex=1 -interaction=nonstopmode -file-line-error \
  -halt-on-error -outdir=build deliverables/reports/network24_report_eng.tex
```

For optional code sharing, the solver implementations live in [network_design/](../network_design/), the referee is [qoblib_tools.py](../qoblib_tools.py), and the Python dependencies are in [requirements.txt](../requirements.txt). Submitting a benchmark to QOBLIB is a separate process with its own checker and submission metadata. [QOBLIB contribution guide](https://github.com/ZIB-AOPT/QOBLIB/blob/main/CONTRIBUTING.md)

## Portfolio optimisation (QOBLIB 06)

[portfolio/](portfolio/README.md) holds 221 checked `.sol` files, one per (instance, budget, λ). A **classical** search produced all of them (0 qubits): exact asset-trajectory DP, a day-level tabu search, ILS and parallel tempering, implemented in [portfolio_search.py](../portfolio_search.py). All 56 `po_a010` configurations and 34 of the 56 `po_a050` ones match QOBLIB's best-known value. Six `po_a050` configurations go below it, and 16 stay above it, mostly with λ = 1e-3 (gaps of 0.3–2.8%) and three with λ = 1e-2. The 109 `po_a200`/`po_a400` files (13 on the `_orig` instances, 96 on the 12 seed instances `s00`–`s02` with all 8 λ) have no published value to compare against.

| Instance | B | λ | Solution | Binary variables | Qubits | Checked objective | QOBLIB reference | Gap |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `po_a050_t15_orig` | 20 | 1e-2 | [po_a050_t15_orig_b020_l1e-2.sol](portfolio/po_a050_t15_orig_b020_l1e-2.sol) | 4,665 | 0 | −50,971 | −31,504 (best known) | **−61.79%** |
| `po_a050_t10_s00` | 20 | 1e-2 | [po_a050_t10_s00_b020_l1e-2.sol](portfolio/po_a050_t10_s00_b020_l1e-2.sol) | 3,110 | 0 | −19,785 | −12,340 (best known) | **−60.33%** |
| `po_a050_t10_orig` | 20 | 1e-2 | [po_a050_t10_orig_b020_l1e-2.sol](portfolio/po_a050_t10_orig_b020_l1e-2.sol) | 3,110 | 0 | −44,208 | −37,107 (best known) | **−19.14%** ¹ |
| `po_a050_t10_s02` | 20 | 1e-2 | [po_a050_t10_s02_b020_l1e-2.sol](portfolio/po_a050_t10_s02_b020_l1e-2.sol) | 3,110 | 0 | −44,625 | −43,565 (best known) | **−2.43%** |
| `po_a050_t10_s00` | 20 | 5e-4 | [po_a050_t10_s00_b020_l5e-4.sol](portfolio/po_a050_t10_s00_b020_l5e-4.sol) | 3,110 | 0 | −234,696 | −234,259 (best known) | **−0.19%** |
| `po_a050_t15_s02` | 20 | 5e-4 | [po_a050_t15_s02_b020_l5e-4.sol](portfolio/po_a050_t15_s02_b020_l5e-4.sol) | 4,665 | 0 | −392,723 | −392,668 (best known) | **−0.01%** |
| `po_a400_t15_orig` | 100 | 1e-3 | [po_a400_t15_orig_b100_l1e-3.sol](portfolio/po_a400_t15_orig_b100_l1e-3.sol) | 36,165 | 0 | −2,986,716 | none published | — |

¹ This run started from QOBLIB's published reference solution and improved it, so it is not an independent result. See the [provenance note](portfolio/README.md#method-and-settings).

Verify all 221 files from the repo root with `PORTFOLIO_SOL_DIR=deliverables/portfolio python portfolio_search.py verify`. The method, the settings and the full table are in [portfolio/README.md](portfolio/README.md). The run logs and the reading guide are in [ai_context/portfolio_classical/](../ai_context/portfolio_classical/READ_ME_FIRST.txt).

## Portfolio optimisation, quantum pipeline (QOBLIB 06)

[portfolio_quantum/](portfolio_quantum/README.md) holds 5 checked `.sol` files from a **quantum** large-neighbourhood
search: Divi QAOA, p = 5, Dicke state + XY mixer that conserves the budget, transferred angles. The programs have up to
18 qubits on the local Maestro simulator and 26 qubits on Qoro's cloud. Every file improves on the earlier classical
file for the same configuration, up to `po_a400_t15_orig` (36,165 binary variables): −3,015,526 against −2,986,716.
Method: [portfolio_quantum/README.md](../portfolio_quantum/README.md). Logs: [ai_context/portfolio_quantum/](../ai_context/portfolio_quantum/READ_ME_FIRST.txt).
