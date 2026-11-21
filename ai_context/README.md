# AI context: how the network24 solution was found

Material that is **not** elsewhere in the repo, collected so that someone (or their AI assistant) can
follow how `solutions_best/network24.sol` (score 657,121, 0.99% below QOBLIB's best known 663,688)
was found. Start with `../network24_report_eng.pdf`, then use this folder for detail.

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
| `make_report.py`, `make_report_eng.py` | Build the Italian and English PDF reports from `solutions/**/log.csv` (needs `reportlab`, `matplotlib`). Usage: `python make_report_eng.py <repo_dir> <out.pdf>`. |
| `analyze.py` | Summarises the Divi experiment log `solutions/agent_divi/divi_run_divi_s1.jsonl` (sampler comparison table). |

## Verifying the solution yourself

From the repo root:

```bash
python -c "import qoblib_tools as qt; print(qt.check_network_solution('solutions_best/network24.sol', 24, qt.load_network_demand(24)))"
```

Expected output: `(True, 657121, 'valid')`. It was also checked with QOBLIB's official Rust
checker (`08-network/check` in the QOBLIB repo), which returned `VALID`.
