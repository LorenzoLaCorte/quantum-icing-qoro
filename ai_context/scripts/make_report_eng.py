"""Build network24_report_eng.pdf (English) from the banking logs."""
import csv
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import font_manager
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

REPO = Path(sys.argv[1])
OUT = Path(sys.argv[2])
SCR = Path(__file__).resolve().parent
BKV = 663688

# ── palette (dataviz reference, light mode) ──
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"
BLUE, GRID, SURF = "#2a78d6", "#e4e3df", "#fcfcfb"
ACCENT_BG = "#eef4fc"

# ── data: best-so-far on network24 across every banking folder ──
pts = []
for folder in ["", "agent_pt", "agent_ils"]:
    p = REPO / "solutions" / folder / "log.csv"
    for row in csv.DictReader(p.open()):
        if row["instance"] == "network24":
            pts.append((datetime.fromisoformat(row["timestamp"]), int(row["score"])))
pts.sort()
best, curve = None, []
for t, s in pts:
    if best is None or s < best:
        best = s
        curve.append((t, s))

# ── chart ──
font_manager.fontManager.addfont("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
fig, ax = plt.subplots(figsize=(7.0, 2.5), dpi=220)
fig.patch.set_facecolor("white")
ts = [t for t, _ in curve] + [datetime(2026, 11, 21, 16, 0)]
ys = [s for _, s in curve] + [curve[-1][1]]
ax.step(ts, [y / 1000 for y in ys], where="post", color=BLUE, lw=2, zorder=3)
ax.scatter([t for t, _ in curve], [s / 1000 for _, s in curve], s=12, color=BLUE,
           edgecolor="white", linewidth=1.2, zorder=4)
ax.axhline(BKV / 1000, color=INK2, lw=1, ls=(0, (4, 3)), zorder=2)
ax.text(datetime(2026, 11, 21, 12, 14), BKV / 1000 + 1.6, "QOBLIB best known 663.7k",
        color=INK2, fontsize=7.5)
ann = {768375: ("first topology 768.4k", (8, -4)), 684455: ("single swaps: stuck at 684.5k", (10, 5)),
       673253: ("parallel tempering 673.3k", (-40, 22)), 661760: ("ILS, deep step: 661.8k", (-140, -14)),
       657121: ("657.1k", (46, -3))}
for t, s in curve:
    if s in ann:
        txt, off = ann[s]
        arrow = dict(arrowstyle="-", color=MUTED, lw=0.6) if s in (673253, 661760) else None
        ax.annotate(txt, (t, s / 1000), xytext=off, textcoords="offset points", fontsize=7.5,
                    color=INK, arrowprops=arrow)
ax.set_ylabel("score (thousands)")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.grid(axis="y", color=GRID, lw=0.6)
ax.set_axisbelow(True)
for side in ["top", "right"]:
    ax.spines[side].set_visible(False)
ax.set_ylim(648, 775)
ax.set_xlim(datetime(2026, 11, 21, 12, 0), datetime(2026, 11, 21, 16, 25))
ax.axvspan(datetime(2026, 11, 21, 12, 14), datetime(2026, 11, 21, 14, 20), color="#f3f2ef", lw=0, zorder=0)
ax.text(datetime(2026, 11, 21, 13, 17), 722, "pause\n(no search running)", ha="center",
        fontsize=7, color=MUTED)
fig.tight_layout()
chart = SCR / "score_chart_eng.png"
fig.savefig(chart, facecolor="white")

# ── PDF ──
pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVM", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("DV", normal="DV", bold="DVB", italic="DV", boldItalic="DVB")

base = ParagraphStyle("b", fontName="DV", fontSize=8.8, leading=11.8, textColor=INK, alignment=TA_LEFT)
small = ParagraphStyle("s", parent=base, fontSize=7.8, leading=10.2, textColor=INK2)
h1 = ParagraphStyle("h1", parent=base, fontName="DVB", fontSize=17, leading=21, spaceAfter=2)
sub = ParagraphStyle("sub", parent=base, fontSize=9, textColor=INK2, spaceAfter=8)
h2 = ParagraphStyle("h2", parent=base, fontName="DVB", fontSize=11, leading=14, spaceBefore=8,
                    spaceAfter=3, textColor=INK)
cell = ParagraphStyle("c", parent=base, fontSize=8, leading=10.4)
cellb = ParagraphStyle("cb", parent=cell, fontName="DVB")
code = ParagraphStyle("code", parent=base, fontName="DVM", fontSize=7, leading=9.2, textColor=INK,
                      backColor="#f3f2ef", borderPadding=(4, 5, 4, 5), spaceBefore=2, spaceAfter=6)
bullet = ParagraphStyle("bl", parent=base, leftIndent=10, bulletIndent=0, spaceAfter=2)


def P(t, s=base):
    return Paragraph(t, s)


def B(t):
    return Paragraph(t, bullet, bulletText="•")


def table(rows, widths, header=True, bold_rows=()):
    data = [[P(c, cellb if (header and i == 0) or i in bold_rows else cell) for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, hAlign="LEFT")
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor(INK2)),
          ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor(GRID)),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    for r in bold_rows:
        st.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor(ACCENT_BG)))
    t.setStyle(TableStyle(st))
    return t


W = A4[0] - 36 * mm
story = []
story += [P("Network design QOBLIB 08: network24 below the best known", h1),
          P("Qoro × PushQuantum Hackathon · 21 November 2026 · network design track, "
            "instance network24 (552 binary variables)", sub)]

# hero box
hero = Table([[P("<font size=22><b>657,121</b></font>", base),
               P("<font size=22><b>−0.99%</b></font>", base),
               P("<b>VALID</b> according to the official QOBLIB Rust checker and the Python referee "
                 "<font name=DVM size=7.5>qoblib_tools.py</font>", cell)],
              [P("submission score (lower is better)", small),
               P("gap to the published best known, 663,688", small),
               P("file: <font name=DVM size=7>solutions/network24.sol</font>", small)]],
             colWidths=[W * 0.27, W * 0.30, W * 0.43])
hero.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(ACCENT_BG)),
                          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                          ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                          ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
story += [hero, Spacer(1, 6)]

story += [P("The problem", h2),
          P("Build a directed network on 24 nodes in which every node has exactly 2 outgoing and "
            "2 incoming links. Route all the traffic in the demand matrix; flows may split over "
            "several paths. The <b>score</b> is the load on the busiest link, in thousandths of a "
            "demand unit: the lower it is, the less congested the network. Once the topology is "
            "fixed, optimal routing is a linear program (LP) solved exactly in about 55 ms. The "
            "hard part is choosing the topology.")]

story += [P("The approach: propose a topology, let the exact LP decide", h2),
          P("Every search follows the same loop:"),
          B("a <b>proposer</b> changes the current topology without ever breaking the 2-in, 2-out "
            "rule. The basic move swaps the heads of two links: (a→b),(c→d) ⇒ (a→d),(c→b);"),
          B("the <b>exact routing LP</b> scores every proposal. Its dual values show which links are "
            "congested, and moves on those links are tried more often;"),
          B("a better topology is <b>banked</b> only after a full check. Integer flows are computed, "
            "the <font name=DVM size=8>.sol</font> file is written and read back through the checker. "
            "The banked file is replaced only if the new one is valid and strictly better."),
          P("Before touching network24, the pipeline was verified on network05. From a random "
            "topology it reaches the proven optimum of 65,500, and the file passes the checker.")]

methods = [
    ["Method", "How it works", "How we used it"],
    ["<b>Local search</b>",
     "Start from a solution and change it a little, one move at a time, keeping only the changes "
     "that improve it. It stops at a <i>local minimum</i>: a point where no small change helps, "
     "even though better solutions exist elsewhere.",
     "Basic move: swap the heads of two links. It is the building block of every method below."],
    ["<b>Simulated annealing (SA)</b>",
     "Local search that sometimes accepts worse moves too, with a probability set by a "
     "<i>temperature</i>. Early on the temperature is high and the search explores; then it falls "
     "and the search settles on a good solution. The name comes from annealing metals.",
     "First submission: from 768,375 down to 684,455, then stuck."],
    ["<b>Parallel tempering (PT)</b>",
     "Several copies of the search (<i>replicas</i>) run together, each at a different temperature. "
     "Hot ones explore freely, cold ones refine. Now and then two neighbouring replicas swap "
     "solutions: a good region found by a hot replica moves down to the cold ones, and a stuck "
     "cold replica gets \"reheated\".",
     "10 replicas, temperatures from 450 to 2,500. On top of that, out of 60 candidate moves only "
     "the most promising one, by a fast estimate, is scored with the LP."],
    ["<b>Iterated local search (ILS)</b>",
     "Descend to a local minimum, then apply a <i>kick</i>: a few random moves that push the "
     "search out of the area. Descend again, and keep the result if it is good. Repeat with "
     "gradually stronger kicks.",
     "5 chains in parallel, kicks of 2 to 10 moves."],
    ["<b>Deep step</b>",
     "A variant of ILS. Instead of a random kick, take every neighbouring solution that is only "
     "slightly worse (within 1.5%) and run a full descent from each one. A small step back often "
     "opens the way to a bigger improvement.",
     "The step that took the score below the record: from 670,621 to 661,760."],
    ["<b>QAOA with Divi</b>",
     "A quantum optimisation algorithm. The problem is written as a QUBO, a cost over binary "
     "variables, and a circuit with tunable parameters produces samples that favour low-cost "
     "solutions. A classical optimiser tunes the parameters.",
     "Picks 3 swaps to apply together out of 16 candidates, on 16 simulated qubits."],
]
story += [P("The methods, briefly", h2),
          table(methods, [W * 0.17, W * 0.53, W * 0.30])]

story += [KeepTogether([P("How we got there", h2),
          Image(str(chart), width=W, height=W * 2.5 / 7.0)]),
          P("Best banked score on network24 over time, merging the logs of every search. Each "
            "point is a file that passed the checker.", small), Spacer(1, 4)]

rows = [["Phase", "What", "Score", "Gap"],
        ["1 · Safe submission", "Topology with the most direct traffic, then simulated annealing "
         "with single swaps (2 + 10 min). Stuck at 684,455 after 12 steps.", "684,455", "+3.13%"],
        ["2 · Three subagents in parallel", "Parallel tempering, iterated local search (ILS) and "
         "a Divi proposer, 5 cores each, about 40 min. Parallel tempering wins.",
         "673,253", "+1.44%"],
        ["3 · Longer parallel tempering", "Same setup, 30 min, 10 workers.", "670,621", "+1.04%"],
        ["4 · ILS with deep step", "Restarts from 670,621 and drops below the record in about "
         "3 minutes.", "661,760", "−0.29%"],
        ["5 · Parallel tempering from the record", "20 min from 661,760, improvement at round 30. "
         "Verified with the Rust checker.", "657,121", "−0.99%"]]
story += [table(rows, [W * 0.22, W * 0.56, W * 0.12, W * 0.10], bold_rows=(5,))]

story += [P("What worked", h2),
          B("<b>Guided proposals in parallel tempering</b> (<font name=DVM size=8>network_pt.py</font>). "
            "Plain parallel tempering improved nothing: cold replicas accepted 0.1–0.4% of moves. "
            "The breakthrough was a cheap lower bound on the LP (about 0.6 ms): "
            "Σ demand × hop count / 48. Of K=60 generated candidates, only the one with the lowest "
            "bound goes to the LP. The median change per move drops from +25k to +8k."),
          B("<b>Deep step in ILS</b> (<font name=DVM size=8>network_ils.py</font>). It got ILS out "
            "of the minima at 683,887 and 670,621, where random kicks had found nothing in 2–3 runs."),
          B("<b>Incremental LP, about 4× faster</b>. The HiGHS model stays open, each move edits only "
            "the links involved, and the solve restarts from the previous basis: about 15 ms instead "
            "of 55, with values identical to the original LP on 80 test topologies."),
          B("<b>More move types</b>: 2-swaps, swapping the roles of two nodes (up to 8 links), and "
            "reversing directed 3- or 4-node cycles. All three produced banked improvements."),
          B("<b>Independent convergence</b>: at 15:46 ILS found, on its own, the same 657,121 "
            "topology that parallel tempering had found at 15:33. The two files have the same "
            "SHA-256.")]

story += [KeepTogether([P("The role of Divi: a measured negative result", h2),
          P("The quantum proposer (<font name=DVM size=8>network_divi.py</font>) builds a QUBO over "
            "16 candidate swaps around the congested links. Interactions between pairs of swaps are "
            "measured exactly with the LP, and the constraint is to apply exactly 3 swaps. The QUBO "
            "is solved with QAOA p=2 on <b>16 qubits</b>, with a Dicke initial state and an XY "
            "mixer, on the local Maestro simulator. Every step is compared with other samplers on "
            "the same QUBO:"),
          table([["Sampler", "Finds the best group of 3", "In the top 5", "Time per step"],
                 ["Divi QAOA-XY, 16 qubits", "44%", "72%", "≈ 5.8 s"],
                 ["Simulated annealing (dwave)", "29%", "83%", "≈ 0.05 s"],
                 ["Exact enumeration (2<super>16</super> states)", "91%", "100%", "negligible"],
                 ["Random", "1%", "17%", "—"]],
                [W * 0.36, W * 0.26, W * 0.16, W * 0.22])]),
          Spacer(1, 3),
          P("Divi picks groups of swaps much better than chance and on par with simulated "
            "annealing, but loses to exact enumeration, which is trivial at 16 variables. Moreover, "
            "in 93 steps no group of 3 swaps improved the topology: the LP scores of every possible "
            "group, 384 per step on average, show it. <b>The final score comes entirely from "
            "classical search.</b> A program takes about 42 s at 20 qubits and about 203 s at 22, "
            "which limits how far the quantum proposer can scale.")]

story += [P("Checks and limits", h2),
          B("The official QOBLIB Rust checker (<font name=DVM size=8>08-network/check</font>) "
            "returns <b>VALID</b> and a maximum flow of 657,121. Its controls behave as expected: the "
            "published best known is VALID at 663,688, and one of our files with a deliberately "
            "altered flow is rejected as INFEASIBLE."),
          B("No published solution (<font name=DVM size=8>network24.bst.sol</font>, the submissions "
            "folder) was used as a starting point or hint. Every search starts from random "
            "topologies, from the most-direct-traffic topology, or from files we banked ourselves."),
          B("A bug in the first ILS runs mis-scored some moves. It never affected the banked "
            "files, because the checker re-reads every file."),
          B("The result has not been submitted to QOBLIB yet, and <font name=DVM size=8>.sol</font> "
            "files are ignored by git: the solution exists only locally.")]

story += [KeepTogether([P("To reproduce", h2),
          P("NETWORK_SOL_DIR=solutions/agent_pt .venv/bin/python network_pt.py 24 --minutes 20 "
            "--replicas 10 --workers 10 --tmin 450 --tmax 2500 --banked 2 --K 60 --p-double 0.5 "
            "--p-tri 0.03 --steps 15 --seed 8<br/>"
            "NETWORK_SOL_DIR=solutions/agent_ils .venv/bin/python network_ils.py run --chains 5 "
            "--minutes 20 --seed 700 --deep 12 --deep_tol 0.015 --kmax 8 --starts banked --sync<br/>"
            ".venv/bin/python network_pipeline.py status", code),
          P("Replicas and chains run in parallel, so the same seed does not guarantee the same "
            "trajectory. Each command restarts from the file banked in its own folder.", small)])]

def footer(c, doc):
    c.saveState()
    c.setFont("DV", 7)
    c.setFillColor(colors.HexColor(MUTED))
    c.drawString(18 * mm, 10 * mm, "network24 · QOBLIB 08 · Qoro × PushQuantum 2026")
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}")
    c.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                        topMargin=16 * mm, bottomMargin=16 * mm,
                        title="network24: below the best known", author="")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("wrote", OUT, "curve:", [(t.strftime("%H:%M"), s) for t, s in curve])
