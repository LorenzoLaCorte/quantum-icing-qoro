# Methodology and run evidence

The [network design report](../deliverables/reports/network24_report.tex) explains the search
that reached 657,121 on `network24`. The [original English overview](reports/network24_report_eng.tex)
covers the broader experiment history and the Divi comparison. The [hand-in folder](../deliverables/)
contains the final checked solutions.

**Portfolio, QOBLIB 06 (classical, 221 configurations, 6 below BKV):** start from
[portfolio_classical/READ_ME_FIRST.txt](portfolio_classical/READ_ME_FIRST.txt). It covers the method
(asset DP, day tabu, ILS, PT), every run log, the campaign script, a provenance note on
`po_a050_t10_orig` λ=1e-2, and the redacted session transcript. The checked files are in
[../deliverables/portfolio/](../deliverables/portfolio/README.md).

**network18–network23 (below BKV, hybrid with QAOA):** start from
[quantum_networks/READ_ME_FIRST.txt](quantum_networks/READ_ME_FIRST.txt). It lists every file to read,
the method, the logs, the transcripts, and what the quantum step did and did not contribute.

## Network05 from 83000 to the proven optimum

1. Read the top-left 5 × 5 block of the demand matrix. A candidate topology chooses 10 of the 20 possible directed links and gives every node exactly two incoming and two outgoing links. `random_topology` draws two link permutations with no self-loops or duplicate links. [Demand loader and topology generator](../qoblib_tools.py)
2. Swap the destinations of two links, for example `a → b, c → d` becomes `a → d, c → b`. The move preserves both degrees. It is discarded if it introduces a self-loop or a duplicate. The search uses the routing LP's capacity duals to bias proposals toward links where extra capacity would most improve the score. [Swap and proposal code](../network_design/pipeline.py)
3. For each topology, solve a continuous routing LP. A flow variable tracks how much traffic from one source travels on a selected link. At every other node, incoming flow minus outgoing flow must equal that source's demand for the node. The LP minimizes `z`, an upper bound on the sum of flows using each link. The search scores a batch of up to eight candidates with two workers and applies a simulated annealing acceptance rule to its best candidate. [Routing model](../qoblib_tools.py) · [Search loop](../network_design/pipeline.py)
4. When a topology improves the incumbent, reroute it with integer flows, write the `.sol`, and re-read it with the referee before keeping it. The log records **83,000 → 81,500 → 74,000 → 71,500 → 65,500** in four improving steps from the seed-0 random start. The final **65,500** matches the proven optimum. [Run log](../solutions/log.csv#L2) · [Checked solution](../deliverables/network05/network05.sol)

Re-run the original verification in a fresh scratch directory. `verify` checks the published optimum as a control, then starts the search from a random topology generated with seed `0`.

```bash
source venv/bin/activate
trial=$(mktemp -d /tmp/qoblib-network05.XXXXXX)
NETWORK_SOL_DIR="$trial" python network_pipeline.py verify --minutes 0.2 --seed 0
cat "$trial/log.csv"
```

## Network24 provenance

Read the [pipeline](../network_design/pipeline.py) for the shared LP and banking logic, then the
[parallel tempering implementation](../network_design/parallel_tempering.py) for cheap candidate screening,
cold and hot replicas, and replica exchanges. The [ILS implementation](../network_design/iterated_local_search.py)
shows the incremental HiGHS model and the deep step that reached 661,760. The
[Divi proposer](../network_design/divi_proposer.py) and its [raw samples](../solutions/agent_divi/divi_run_divi_s1.jsonl)
document the quantum comparison. The [PT banking log](../solutions/agent_pt/log.csv) identifies the exact run
that reached 657,121. Its historical warm start was the intermediate 661,760 file. The log records that score,
and the final topology is archived, but the intermediate `.sol` is absent from this checkout.

## transcripts/

Full Claude Code transcripts (JSONL, one event per line: user messages, assistant messages,
tool calls and their outputs). Snapshot taken on 2026-11-21 at about 17:10. The user's email address
has been replaced with `<email-redacted>`.

| File | What it is |
|---|---|
| `main_session.jsonl` | The main session: plan, `network_pipeline.py`, network05 check, first network24 submission, launching the subagents, follow-up runs, Rust checker verification, the PDF reports. Mostly in Italian. |
| `subagents/agent-ac080c5cb56fef21b.jsonl` | Subagent **parallel tempering**: wrote `network_pt.py`, 684,455 → 673,253. |
| `subagents/agent-a5097a40907d9b1e4.jsonl` | Subagent **ILS** (iterated local search): wrote `network_ils.py` (incremental HiGHS LP, deep step), 684,455 → 673,219. |
| `subagents/agent-a3ba794d3cd6c2cf1.jsonl` | Subagent **Divi**: wrote `network_divi.py` (QAOA on 16 qubits as a proposer); no improvement, a measured negative result. |
| `subagents/*.meta.json` | Metadata for each subagent (task description). |

Tip: these files are large. Search them for keywords (`banked`, `score`, `step`, `deep`), or
extract only the `"type":"assistant"` text messages, rather than reading them whole.

## logs/

| Folder | Content |
|---|---|
| `parallel_tempering/` | stdout of `network_pt.py` runs. `r1`, `r2`: plain PT (no gains). `r3`, `r5`: guided proposals (684,455 → 673,253). `rA`, `rB`: A/B test of the smoothing term. `pt_r6.log`: 30-min continuation (→ 666,300). `pt_r7.log`: 20 min from 661,760 (→ **657,121**, the final solution). Each line: replica scores, Metropolis acceptance and swap rates per temperature. |
| `ils_stdout/` | stdout of `network_ils.py` runs. `run1`–`run5` were affected by an LP-update bug (fixed before run6). `run6.out`: escape from 683,887 to 673,219. `ils_run8.out`: 670,621 → 661,760 (first result below the record). `ils_run9.out`: independently found the same 657,121 topology. The matching structured logs are in `../solutions/agent_ils/run*.log`. |

## scripts/

| File | What it is |
|---|---|
| `make_report_eng.py` | Original ReportLab generator for the [archived English overview](reports/network24_report_eng.tex). |
| `plot_pt_report.py` | Rebuilds the report figures from the archived PT, ILS, and compound-move logs and the checked network solutions. Run `python -m ai_context.scripts.plot_pt_report` from the repo root with Matplotlib installed. |
| `plot_portfolio_report.py` | Rebuilds the portfolio report figures from the saved PCE JSON traces, classical logs, and solution audit. Run `python -m ai_context.scripts.plot_portfolio_report` from the repo root. |
| `analyze.py` | Summarises the Divi experiment log `solutions/agent_divi/divi_run_divi_s1.jsonl` (sampler comparison table). |

## divi_docs_context7.md

Divi documentation snippets (install, QAOA, PCE, partitioning ensembles, pipelines, backends) copied
on 2026-11-21 from https://context7.com/qoroquantum/divi. They track Divi's `main` branch, while the
repo pins `qoro-divi==0.16.2`: check an API against the installed version before using it.

## Verifying the solution yourself

From the repo root:

```bash
NETWORK_SOL_DIR=deliverables/network24 python network_pipeline.py status
```

Expected score is `657121` with status `valid`. The report also records `VALID` from QOBLIB's
official Rust checker (`08-network/check` in the QOBLIB repo).
