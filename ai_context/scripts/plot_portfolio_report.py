"""Build portfolio report figures from the saved PCE traces and classical logs."""

import csv
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "portfolio_QIcing"
FIGURES = ROOT / "deliverables/reports/figures"
CHAINS = [("1e-4", [3, 7]), ("5e-4", [5, 10]), ("1e-3", [6, 8, 15])]
LAM_LABELS = {"1e-4": r"10^{-4}", "5e-4": r"5\cdot10^{-4}", "1e-3": r"10^{-3}", "1e-2": r"10^{-2}"}


def quantum_progress():
    figure, axes = plt.subplots(1, 3, sharey=True, figsize=(6.65, 2.35), layout="constrained")
    for axis, (lam, seeds) in zip(axes, CHAINS, strict=True):
        scores = [-1000]
        handoffs = []
        first_optimum = None
        circuit_count = 0
        for seed in seeds:
            run = json.loads((SOURCE / "logs" / f"qlns_po_a010_t10_orig_l{lam}_pce_s{seed}.json").read_text())
            assert run["args"]["routine"] == "pce"
            reference = run["bkv"]
            for entry in run["log"]:
                assert entry["incumbent"] <= scores[-1]
                scores.append(entry["incumbent"])
                circuit_count += entry["circuits"]
                if first_optimum is None and entry["incumbent"] == reference:
                    first_optimum = (len(scores) - 1, circuit_count)
            assert scores[-1] == run["final"]
            handoffs.append(len(scores) - 1)
        gap = [(score - reference) / abs(reference) for score in scores]
        axis.step(range(len(scores)), gap, where="post", color="black")
        for boundary in handoffs[:-1]:
            axis.axvline(boundary, color="0.5", ls=":", lw=0.7)
        axis.plot(first_optimum[0], 0, "o", color="black", ms=3)
        axis.set_title(rf"$\lambda={LAM_LABELS[lam]}$", loc="left")
        axis.set(xlabel="Completed windows", xlim=(0, len(scores) - 1), yscale="symlog")
        axis.set_yscale("symlog", linthresh=0.001)
        axis.set_ylim(-0.0001, 1.1)
        axis.spines[["top", "right"]].set_visible(False)
        print(f"PCE lambda={lam}: first optimum at window {first_optimum[0]}, "
              f"{first_optimum[1]:,} circuits; total {len(scores)-1} windows, {circuit_count:,} circuits")
    axes[0].set_ylabel("Gap to exact optimum")
    axes[0].set_yticks([0, 0.001, 0.01, 0.1, 1])
    axes[0].yaxis.set_major_formatter(PercentFormatter(1, decimals=1))
    figure.savefig(FIGURES / "portfolio-pce-progress.pdf", metadata={"CreationDate": None})
    plt.close(figure)


def classical_progress():
    with (SOURCE / "results.csv").open(newline="") as handle:
        earlier = list(csv.DictReader(handle))
    campaign = ROOT / "ai_context/portfolio_classical/logs/campaign"
    update = re.compile(r"^\[\s*([\d.]+)s\]\s+(start|ils|tabu|pt)\b[^:\n]*:\s*(-?\d+)$", re.M)
    figure, axes = plt.subplots(1, 2, sharex=True, figsize=(6.65, 2.5), layout="constrained")
    names = ("po_a050_t15_orig", "po_a050_t10_s00")
    for axis, name in zip(axes, names, strict=True):
        log = (campaign / f"c_{name}_1e-2.log").read_text()
        reference = float(re.search(r"BKV=\((-?[\d.]+),", log)[1])
        previous = min(int(row["objective"]) for row in earlier
                       if row["instance"] == name and row["lambda"] == "1e-2" and row["feasible"] == "True")
        trace = [(float(t), phase, int(score) / 1000) for t, phase, score in update.findall(log)]
        assert trace[0][1] == "start" and "start=zero" in log.splitlines()[0]
        assert trace[-1][2] == int(re.search(r"^FINAL .*?: (-?\d+)", log, re.M)[1]) / 1000
        axis.step([t for t, _, _ in trace] + [120], [score for _, _, score in trace] + [trace[-1][2]],
                  where="post", color="black", label="_nolegend_")
        for phase, symbol, label in (("ils", "o", "ILS"), ("tabu", "s", "Day tabu"), ("pt", "^", "PT")):
            points = [(t, score) for t, tag, score in trace if tag == phase]
            if points:
                times, scores = zip(*points)
                axis.plot(times, scores, linestyle="none", marker=symbol, ms=3, color="black", label=label)
        axis.axhline(reference / 1000, color="0.5", ls=":", label="Published BKV")
        axis.axhline(previous / 1000, color="0.5", ls="--", label="Earlier best")
        axis.set_title(name.removeprefix("po_a050_"), loc="left")
        axis.set(xlabel="Elapsed search time (s)", xlim=(-2, 122), xticks=(0, 30, 60, 90, 120))
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel(r"Objective ($10^3$)")
    handles = {}
    for axis in axes:
        panel_handles, panel_labels = axis.get_legend_handles_labels()
        handles.update(zip(panel_labels, panel_handles))
    figure.legend(list(handles.values()), list(handles), loc="outside upper center", ncols=len(handles))
    figure.savefig(FIGURES / "portfolio-classical-progress.pdf", metadata={"CreationDate": None})
    plt.close(figure)


if __name__ == "__main__":
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["STIXGeneral"], "font.size": 9,
        "mathtext.fontset": "stix", "axes.formatter.use_mathtext": True,
        "axes.linewidth": 0.6, "axes.titlesize": 9, "lines.linewidth": 0.95,
        "lines.markersize": 4, "xtick.direction": "in", "ytick.direction": "in",
        "legend.frameon": False, "legend.fontsize": 8, "pdf.fonttype": 42,
    })
    FIGURES.mkdir(exist_ok=True, parents=True)
    quantum_progress()
    classical_progress()
