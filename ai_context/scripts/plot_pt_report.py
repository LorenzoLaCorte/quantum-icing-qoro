"""Generate the network design report figures from logs and checked solutions."""

import ast
import math
import re
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, NullLocator, PercentFormatter


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "ai_context/logs/parallel_tempering"
FIGURES = ROOT / "deliverables/reports/figures"
REFERENCE = 663_688

BANK = re.compile(r"^\s*\[\s*(\d+)s\] round (\d+) slot \d+: LP [^\n]+? -> banked (\d+)", re.M)
END = re.compile(r"^done \d+ rounds in (\d+)s: [^\n]+banked (\d+)", re.M)
SAMPLE = re.compile(r"^\[\s*(\d+)s\] rnd [^\n]+? \| z (\[[^\]]+\])", re.M)
RATES = re.compile(r"^temps (\[[^\]]+\]) swap rates (\[[^\]]+\]) acc (\[[^\]]+\])", re.M)
ILS_BANK = re.compile(
    r"^(\d{2}:\d{2}:\d{2}) \[seed \d+\] bank: banked (\d+) \([^\n]* was (\d+)\)", re.M
)
CHAIN_START = re.compile(r"^\[([\d:]+)\] network(\d+) start (\d+) BKV (\d+)")
CHAIN_BEST = re.compile(r"^\[([\d:]+)\]\s+NEW BEST network(\d+) (\d+) via (.+?)\s+\(BKV ")


def checked_trace(log):
    opening = re.search(r"^network24 PT: .* banked=(\d+)$", log, re.M)
    finish = END.search(log)
    if opening is None or finish is None:
        raise ValueError("Expected a completed PT run with a checked starting score")
    banks = [(int(seconds), int(round_no), int(score)) for seconds, round_no, score in BANK.findall(log)]
    end_sec, end_score = map(int, finish.groups())
    trace = [(0, int(opening[1])), *((sec, score) for sec, _, score in banks)]
    if trace[-1][1] != end_score:
        raise ValueError("Checked improvements do not match the final checked score")
    trace.append((end_sec, end_score))
    return trace, banks


def ils_trace(log):
    opening = re.search(r"^(\d{2}:\d{2}:\d{2}) \[seed \d+\] start=banked ", log, re.M)
    banks = ILS_BANK.findall(log)
    if opening is None or not banks:
        raise ValueError("Expected a banked ILS start and at least one checked improvement")
    start = datetime.strptime(opening[1], "%H:%M:%S")
    trace = [(0, int(banks[0][2]))]
    for clock, score, previous in banks:
        elapsed = (datetime.strptime(clock, "%H:%M:%S") - start).total_seconds()
        if trace[-1][1] != int(previous):
            raise ValueError("ILS log has a gap in its checked incumbent history")
        trace.append((elapsed, int(score)))
    return trace


def format_axis(axis, title, xlabel, ylabel):
    axis.set_title(title, loc="left", pad=4)
    axis.set(xlabel=xlabel, ylabel=ylabel)
    axis.spines[["top", "right"]].set_visible(False)


def plot_progress(first_pt, ils, final_pt):
    first_trace, _ = checked_trace(first_pt)
    middle_trace = ils_trace(ils)
    final_trace, _ = checked_trace(final_pt)
    handoff = next((i for i, (_, score) in enumerate(first_trace) if score == middle_trace[0][1]), None)
    if handoff is None or middle_trace[-1][1] != final_trace[0][1]:
        raise ValueError("The archived scores disagree at a PT/ILS handoff")

    figure, axes = plt.subplots(1, 3, sharey=True, figsize=(6.65, 2.25), layout="constrained")
    panels = [
        ("a", "PT r6", first_trace[:handoff + 1], [0, 600, 1200]),
        ("b", "ILS run8", middle_trace, [0, 50, 100]),
        ("c", "PT r7", final_trace[:-1], [0, 30, 60]),
    ]
    for axis, (panel, run, trace, ticks) in zip(axes, panels):
        seconds, scores = zip(*trace)
        thousands = [score / 1000 for score in scores]
        axis.step(seconds, thousands, where="post", color="black", marker="o")
        axis.axhline(REFERENCE / 1000, ls=":", color="0.3")
        format_axis(axis, f"({panel}) {run}", "Elapsed time (s)", "")
        axis.set_xlim(-0.04 * seconds[-1], 1.08 * seconds[-1])
        axis.set_xticks(ticks)
    axes[0].set(ylabel=r"Checked objective ($10^3$)", ylim=(655, 675))
    axes[0].yaxis.set_major_locator(MultipleLocator(5))
    figure.savefig(FIGURES / "pt-progress.pdf", metadata={"CreationDate": None})
    plt.close(figure)


def plot_diagnostics(log):
    temperatures, swaps, acceptance = (ast.literal_eval(value) for value in RATES.search(log).groups())
    samples = [(int(time), ast.literal_eval(values)) for time, values in SAMPLE.findall(log) if int(time) <= 240]
    seconds, scores = zip(*samples)
    _, banks = checked_trace(log)
    best_time, _, _ = min(banks, key=lambda event: event[2])

    figure, (trace, rates) = plt.subplots(2, 1, figsize=(6.65, 3.55), layout="constrained")

    for slot in range(2, len(temperatures) - 1):
        trace.plot(seconds, [sample[slot] for sample in scores], color="0.65", lw=0.65)
    for slot, linestyle, marker in [(0, "-", "o"), (1, "--", "s"), (len(temperatures) - 1, "-.", "^")]:
        trace.plot(seconds, [sample[slot] for sample in scores], linestyle=linestyle, marker=marker,
                   color="black", label=fr"$T={temperatures[slot]}$")
    trace.axvline(best_time, color="0.4", ls=":", lw=0.8)
    format_axis(trace, "(a)", "Elapsed time (s)", r"LP objective ($10^3$)")
    trace.set(xlim=(0, 240), ylim=(654, 732))
    trace.xaxis.set_major_locator(MultipleLocator(60))
    trace.yaxis.set_major_locator(MultipleLocator(20))
    trace.legend(loc="upper right", ncols=3)

    midpoints = [math.sqrt(low * high) for low, high in zip(temperatures, temperatures[1:])]
    rates.plot(temperatures, acceptance, "-o", color="black", label="Local move")
    rates.plot(midpoints, swaps, "--s", color="black", markerfacecolor="white", label="Replica exchange")
    format_axis(rates, "(b)", "Temperature", "Acceptance")
    rates.set(xscale="log", ylim=(0, 1))
    rates.set_xticks(temperatures, [str(value) for value in temperatures])
    rates.xaxis.set_minor_locator(NullLocator())
    rates.yaxis.set_major_locator(MultipleLocator(0.25))
    rates.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    rates.legend(loc="upper right", ncols=2)
    figure.savefig(FIGURES / "pt-diagnostics.pdf", metadata={"CreationDate": None})
    plt.close(figure)


def plot_benchmark_comparison():
    import qoblib_tools as qt
    from network_design.pipeline import BKV

    nodes = list(range(18, 25))
    reductions, saturated = [], []
    for n in nodes:
        instance = f"network{n:02d}"
        path = ROOT / "deliverables" / instance / f"{instance}.sol"
        valid, score, message = qt.check_network_solution(path, n, qt.load_network_demand(n))
        if not valid:
            raise ValueError(f"{path.name}: {message}")
        _, arcs, flows = qt.read_network_solution(path)
        loads = dict.fromkeys(arcs, 0)
        for (_, u, v), flow in flows.items():
            loads[u, v] += flow
        reductions.append((BKV[n] - score) / BKV[n])
        saturated.append(sum(load == score for load in loads.values()) / len(arcs))

    figure, (gap, bottlenecks) = plt.subplots(1, 2, figsize=(6.65, 2.25), layout="constrained")
    gap.bar(nodes, reductions, color="0.35", width=0.6)
    gap.set(ylim=(0, 0.032), xticks=nodes)
    gap.yaxis.set_major_locator(MultipleLocator(0.01))
    gap.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    format_axis(gap, "(a)", "Number of vertices", "Reduction from QOBLIB")

    bottlenecks.plot(nodes, saturated, linestyle="none", marker="o", markersize=4, color="black")
    bottlenecks.set(ylim=(0, 0.6), xticks=nodes)
    bottlenecks.yaxis.set_major_locator(MultipleLocator(0.2))
    bottlenecks.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    format_axis(bottlenecks, "(b)", "Number of vertices", "Arcs at maximum load")
    figure.savefig(FIGURES / "benchmark-comparison.pdf", metadata={"CreationDate": None})
    plt.close(figure)


def plot_chain_progress(log):
    started, references, traces = {}, {}, {}
    for line in log.splitlines():
        if start := CHAIN_START.match(line):
            clock, instance, score, reference = start.groups()
            started[instance] = datetime.strptime(clock, "%H:%M:%S")
            references[instance] = int(reference)
            traces[instance] = [(0, int(score), "Warm start")]
        elif best := CHAIN_BEST.match(line):
            clock, instance, score, origin = best.groups()
            seconds = (datetime.strptime(clock, "%H:%M:%S") - started[instance]).total_seconds()
            if origin.startswith("pair-scan"):
                label = "Pair scan"
            elif origin == "qaoa-compound":
                label = "QAOA compound"
            else:
                label = "Descent"
            traces[instance].append((seconds, int(score), label))

    figure, axes = plt.subplots(2, 3, sharex=True, sharey=True, figsize=(6.65, 3.35), layout="constrained")
    markers = {"Warm start": "D", "Descent": "o", "Pair scan": "s", "QAOA compound": "^"}
    for axis, (instance, trace) in zip(axes.flat, traces.items(), strict=True):
        seconds, scores, labels = zip(*trace)
        ref = references[instance]
        gaps = [(score - ref) / ref for score in scores]
        axis.axhline(0, ls=":", color="0.4", lw=0.8)
        axis.step(seconds, gaps, where="post", color="black")
        for time, gap, label in zip(seconds, gaps, labels):
            axis.plot(time, gap, marker=markers[label], color="black", linestyle="none",
                      markerfacecolor="white" if label == "Warm start" else "black")
        format_axis(axis, f"network{instance}", "", "")
    axes[0, 0].set(xlim=(-4, 96), ylim=(-0.033, 0.024), xticks=(0, 30, 60, 90))
    axes[0, 0].yaxis.set_major_locator(MultipleLocator(0.02))
    axes[0, 0].yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    figure.supxlabel("Seconds since instance start", fontsize=9)
    figure.supylabel("Gap to QOBLIB reference", fontsize=9)
    figure.savefig(FIGURES / "chain-progress.pdf", metadata={"CreationDate": None})
    plt.close(figure)


if __name__ == "__main__":
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["STIXGeneral"], "font.size": 9,
        "mathtext.fontset": "stix", "axes.formatter.use_mathtext": True,
        "axes.linewidth": 0.6, "axes.titlesize": 9,
        "lines.linewidth": 0.95, "lines.markersize": 3,
        "xtick.direction": "in", "ytick.direction": "in",
        "legend.frameon": False, "legend.fontsize": 8, "legend.columnspacing": 0.9,
        "pdf.fonttype": 42,
    })
    FIGURES.mkdir(parents=True, exist_ok=True)
    record_log = (LOGS / "pt_r7.log").read_text()
    plot_progress(
        (LOGS / "pt_r6.log").read_text(),
        (LOGS.parent / "ils_stdout/ils_run8.out").read_text(),
        record_log,
    )
    plot_diagnostics(record_log)
    plot_benchmark_comparison()
    chain_log = ROOT / "ai_context/quantum_networks/logs/chain_network18-23/run_p1.log"
    plot_chain_progress(chain_log.read_text())
