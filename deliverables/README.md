# Qoro hackathon hand-in

Notebook 00 asks for each checked `.sol` file, the instance and binary variable count, the largest quantum program in qubits, the official objective alongside QOBLIB's best-known value, and the method and settings needed to reproduce the result. **Source code is optional under the notebook instructions.** Follow any additional directions Qoro announces at the event. [Handing in](../00_main_qubo_101.ipynb)

| Instance | Solution | Binary variables | Qubits used to produce solution | Checked objective | QOBLIB reference | Gap |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `network05` | [network05.sol](network05/network05.sol) | 20 | 0 | 65,500 | 65,500 (proven optimum) | 0.00% |
| `network18` | [network18.sol](network18/network18.sol) | 306 | 18 | 473,000 | 473,375 (best known) | −0.08% |
| `network19` | [network19.sol](network19/network19.sol) | 342 | 18 | 488,895 | 492,924 (best known) | −0.82% |
| `network20` | [network20.sol](network20/network20.sol) | 380 | 18 | 519,343 | 528,528 (best known) | −1.74% |
| `network21` | [network21.sol](network21/network21.sol) | 420 | 18 | 562,362 | 569,273 (best known) | −1.21% |
| `network22` | [network22.sol](network22/network22.sol) | 462 | 18 | 606,424 | 618,135 (best known) | −1.90% |
| `network23` | [network23.sol](network23/network23.sol) | 506 | 18 | 639,739 | 659,369 (best known) | −2.98% |
| `network24` | [network24.sol](network24/network24.sol) | 552 | 0 | 657,121 | 663,688 (best known) | −0.99% |

The `network05` and `network24` solutions were found by classical searches. `network18`–`network23` come from a hybrid chain, network23 → network18. Each instance starts from the polished topology of the next larger one with its last node deleted. Exact-LP 2-exchange descent refines it, and a QAOA step (Divi, local Maestro simulator, 18 qubits, p=2) samples combinations of 2-exchange moves to escape local optima. QAOA samples gave direct improvements on network22 and network19 and kicks before later descents on network20, while most of the gain came from the classical descent and the exact pair scan. The search code is [solutions/agent_qcompound/small/qls.py](../solutions/agent_qcompound/small/qls.py). The logs, transcripts and a reading guide are in [ai_context/quantum_networks/](../ai_context/quantum_networks/READ_ME_FIRST.txt). The [network24 report](reports/network24_report_eng.tex) describes how parallel tempering and iterated local search were combined to produce the checked result.

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
