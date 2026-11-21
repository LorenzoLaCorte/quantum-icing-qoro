"""Build network24_report.pdf (Italian) from the banking logs."""
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
ax.text(datetime(2026, 11, 21, 12, 14), BKV / 1000 + 1.6, "best known QOBLIB 663,7k",
        color=INK2, fontsize=7.5)
ann = {768375: ("prima topologia 768,4k", (8, -4)), 684455: ("scambi singoli: stallo a 684,5k", (10, 5)),
       673253: ("parallel tempering 673,3k", (-40, 22)), 661760: ("ILS, passo profondo: 661,8k", (-170, -14)),
       657121: ("657,1k", (46, -3))}
for t, s in curve:
    if s in ann:
        txt, off = ann[s]
        arrow = dict(arrowstyle="-", color=MUTED, lw=0.6) if s in (673253, 661760) else None
        ax.annotate(txt, (t, s / 1000), xytext=off, textcoords="offset points", fontsize=7.5,
                    color=INK, arrowprops=arrow)
ax.set_ylabel("score (migliaia)")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.grid(axis="y", color=GRID, lw=0.6)
ax.set_axisbelow(True)
for side in ["top", "right"]:
    ax.spines[side].set_visible(False)
ax.set_ylim(648, 775)
ax.set_xlim(datetime(2026, 11, 21, 12, 0), datetime(2026, 11, 21, 16, 25))
ax.axvspan(datetime(2026, 11, 21, 12, 14), datetime(2026, 11, 21, 14, 20), color="#f3f2ef", lw=0, zorder=0)
ax.text(datetime(2026, 11, 21, 13, 17), 722, "pausa\n(nessuna ricerca attiva)", ha="center",
        fontsize=7, color=MUTED)
fig.tight_layout()
chart = SCR / "score_chart.png"
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
story += [P("Network design QOBLIB 08: network24 sotto il best known", h1),
          P("Qoro × PushQuantum Hackathon · 21 novembre 2026 · traccia network design, "
            "istanza network24 (552 variabili binarie)", sub)]

# hero box
hero = Table([[P("<font size=22><b>657 121</b></font>", base),
               P("<font size=22><b>−0,99%</b></font>", base),
               P("<b>VALID</b> per il checker ufficiale QOBLIB in Rust e per il referee Python "
                 "<font name=DVM size=7.5>qoblib_tools.py</font>", cell)],
              [P("score della submission (più basso è meglio)", small),
               P("gap dal best known pubblicato, 663 688", small),
               P("file: <font name=DVM size=7>solutions/network24.sol</font>", small)]],
             colWidths=[W * 0.27, W * 0.30, W * 0.43])
hero.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(ACCENT_BG)),
                          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                          ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                          ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
story += [hero, Spacer(1, 6)]

story += [P("Il problema", h2),
          P("Si costruisce una rete orientata su 24 nodi in cui ogni nodo ha esattamente 2 link in "
            "uscita e 2 in entrata. Si instrada tutto il traffico della matrice di domanda, con flussi "
            "che possono dividersi su più percorsi. Lo <b>score</b> è il carico del link più trafficato, "
            "in millesimi di unità di domanda: più è basso, meno la rete è congestionata. Con la "
            "topologia fissata, il routing ottimo è un programma lineare (LP) che si risolve in modo "
            "esatto in circa 55 ms. La parte difficile è scegliere la topologia.")]

story += [P("Il metodo: si propone una topologia, l'LP esatto decide", h2),
          P("Lo schema è lo stesso in tutte le ricerche:"),
          B("un <b>generatore di proposte</b> modifica la topologia corrente senza mai violare la "
            "regola dei 2 link in entrata e 2 in uscita. La mossa base scambia le destinazioni di due "
            "link: (a→b),(c→d) ⇒ (a→d),(c→b);"),
          B("il <b>routing LP esatto</b> valuta ogni proposta. I suoi valori duali indicano quali link "
            "sono congestionati, e le mosse su quei link vengono provate più spesso;"),
          B("una topologia migliore viene <b>salvata</b> solo dopo un controllo completo. Si calcolano "
            "i flussi interi, si scrive il <font name=DVM size=8>.sol</font> e lo si rilegge con il "
            "checker. Il file viene sostituito solo se è valido e strettamente migliore."),
          P("Prima di toccare network24, la pipeline è stata verificata su network05. Partendo da "
            "una topologia casuale ritrova l'ottimo dimostrato di 65 500, e il file passa il checker.")]

methods = [
    ["Metodo", "Come funziona", "Nel nostro caso"],
    ["<b>Ricerca locale</b>",
     "Si parte da una soluzione e la si modifica di poco, una mossa alla volta, tenendo solo le "
     "modifiche che migliorano. Si ferma in un <i>minimo locale</i>: un punto in cui nessuna "
     "piccola modifica aiuta, anche se altrove esistono soluzioni migliori.",
     "Mossa base: scambio di destinazione tra due link. È il mattone di tutti i metodi sotto."],
    ["<b>Simulated annealing (SA)</b>",
     "Ricerca locale che a volte accetta anche mosse peggiorative, con una probabilità che dipende "
     "da una <i>temperatura</i>. All'inizio la temperatura è alta e la ricerca esplora; poi scende "
     "e la ricerca si stabilizza su una buona soluzione. Il nome viene dalla tempra dei metalli.",
     "Prima submission: da 768 375 a 684 455, poi bloccata."],
    ["<b>Parallel tempering (PT)</b>",
     "Più copie della ricerca (<i>repliche</i>) girano insieme, ciascuna a una temperatura diversa. "
     "Le calde esplorano liberamente, le fredde rifiniscono. Ogni tanto due repliche vicine si "
     "scambiano le soluzioni: una buona regione trovata da una replica calda passa a quelle "
     "fredde, e una replica fredda bloccata viene \"riscaldata\".",
     "10 repliche, temperature da 450 a 2 500. In più, delle 60 mosse candidate si valuta "
     "con l'LP solo la più promettente secondo una stima veloce."],
    ["<b>Ricerca locale iterata (ILS)</b>",
     "Si scende fino a un minimo locale, poi si applica un <i>calcio</i>: alcune mosse casuali "
     "che portano fuori dalla zona. Si scende di nuovo, e si tiene il risultato se è buono. Si "
     "ripete con calci via via più forti.",
     "5 catene in parallelo, calci da 2 a 10 mosse."],
    ["<b>Passo profondo</b>",
     "Variante dell'ILS. Invece di un calcio casuale, si prendono tutte le soluzioni vicine che "
     "peggiorano di poco (entro l'1,5%) e da ognuna si ripete la discesa completa. Spesso un "
     "piccolo passo indietro apre la strada a un miglioramento più grande.",
     "È il passo che ha portato lo score sotto il record: da 670 621 a 661 760."],
    ["<b>QAOA con Divi</b>",
     "Algoritmo quantistico di ottimizzazione. Il problema si scrive come QUBO, cioè un costo "
     "sulle variabili binarie, e un circuito con parametri regolabili produce campioni che "
     "favoriscono le soluzioni a costo basso. Un ottimizzatore classico regola i parametri.",
     "Sceglie 3 scambi da applicare insieme fra 16 candidati, su 16 qubit simulati."],
]
story += [P("I metodi, in breve", h2),
          table(methods, [W * 0.17, W * 0.53, W * 0.30])]

story += [KeepTogether([P("Come ci siamo arrivati", h2),
          Image(str(chart), width=W, height=W * 2.5 / 7.0)]),
          P("Miglior score salvato nel tempo su network24, unendo i log di tutte le ricerche. Ogni "
            "punto è un file che ha passato il checker.", small), Spacer(1, 4)]

rows = [["Fase", "Cosa", "Score", "Gap"],
        ["1 · Submission sicura", "Topologia con più traffico diretto, poi simulated annealing a "
         "scambi singoli (2 + 10 min). Si blocca a 684 455 dopo 12 passi.", "684 455", "+3,13%"],
        ["2 · Tre subagent in parallelo", "Parallel tempering, ricerca locale iterata (ILS) e "
         "generatore di proposte con Divi, 5 core ciascuno, circa 40 min. Vince il parallel "
         "tempering.", "673 253", "+1,44%"],
        ["3 · Parallel tempering più lungo", "Stessa configurazione, 30 min, 10 worker.", "670 621", "+1,04%"],
        ["4 · ILS con passo profondo", "Riparte da 670 621 e in circa 3 minuti scende sotto il record.",
         "661 760", "−0,29%"],
        ["5 · Parallel tempering dal record", "20 min da 661 760, miglioramento al round 30. "
         "Verificato col checker in Rust.", "657 121", "−0,99%"]]
story += [table(rows, [W * 0.22, W * 0.56, W * 0.12, W * 0.10], bold_rows=(5,))]

story += [P("Cosa ha funzionato", h2),
          B("<b>Proposte guidate nel parallel tempering</b> (<font name=DVM size=8>network_pt.py</font>). "
            "Il parallel tempering semplice non migliorava nulla: nelle repliche fredde si accettava "
            "lo 0,1–0,4% delle mosse. La svolta è un lower bound economico dell'LP (circa 0,6 ms): "
            "Σ domanda × numero di salti / 48. Dei K=60 candidati generati, solo quello con il bound "
            "più basso va all'LP. La variazione mediana per mossa scende da +25k a +8k."),
          B("<b>Passo profondo nell'ILS</b> (<font name=DVM size=8>network_ils.py</font>). Ha fatto "
            "uscire l'ILS dai minimi a 683 887 e 670 621, dove i calci casuali non trovavano nulla in "
            "2–3 corse."),
          B("<b>LP incrementale circa 4 volte più veloce</b>. Il modello HiGHS resta aperto, ogni mossa "
            "cambia solo i link coinvolti e si riparte dalla base precedente: circa 15 ms invece di 55, "
            "con valori identici all'LP originale su 80 topologie di prova."),
          B("<b>Più tipi di mossa</b>: scambi a 2, scambio dei ruoli di due nodi (fino a 8 link) e "
            "inversione di cicli orientati di 3 o 4 nodi. Tutti e tre hanno prodotto miglioramenti "
            "salvati."),
          B("<b>Convergenza indipendente</b>: alle 15:46 l'ILS ha trovato da solo la stessa topologia "
            "a 657 121 che il parallel tempering aveva trovato alle 15:33. I due file hanno lo stesso "
            "SHA-256.")]

story += [KeepTogether([P("Il ruolo di Divi: un risultato negativo, misurato", h2),
          P("Il generatore di proposte quantistico (<font name=DVM size=8>network_divi.py</font>) "
            "costruisce un QUBO su 16 scambi candidati attorno ai link congestionati. Le interazioni "
            "tra coppie di scambi sono misurate esattamente con l'LP, e il vincolo è di applicare "
            "esattamente 3 scambi. Il QUBO si risolve con QAOA p=2 su <b>16 qubit</b>, con stato "
            "iniziale di Dicke e mixer XY, sul simulatore locale Maestro. Ogni passo è confrontato "
            "con altri campionatori sullo stesso QUBO:"),
          table([["Campionatore", "Trova il miglior gruppo da 3", "Nei primi 5", "Tempo per passo"],
                 ["Divi QAOA-XY, 16 qubit", "44%", "72%", "≈ 5,8 s"],
                 ["Simulated annealing (dwave)", "29%", "83%", "≈ 0,05 s"],
                 ["Enumerazione esatta (2<super>16</super> stati)", "91%", "100%", "trascurabile"],
                 ["Casuale", "1%", "17%", "—"]],
                [W * 0.36, W * 0.26, W * 0.16, W * 0.22])]),
          Spacer(1, 3),
          P("Divi sceglie i gruppi di scambi molto meglio del caso e in modo paragonabile alla "
            "simulated annealing, ma perde con l'enumerazione esatta, che a 16 variabili è banale. In "
            "93 passi poi nessun gruppo da 3 scambi migliorava la topologia: lo dice la valutazione "
            "LP di tutti i gruppi possibili, in media 384 per passo. <b>Lo score finale viene "
            "interamente da ricerca classica.</b> Con 20 qubit un programma richiede circa 42 s, con "
            "22 circa 203 s, e questo limita la scala del generatore quantistico.")]

story += [P("Verifiche e limiti", h2),
          B("Il checker ufficiale QOBLIB in Rust (<font name=DVM size=8>08-network/check</font>) dà "
            "<b>VALID</b> e un flusso massimo di 657 121. I controlli dello stesso checker si "
            "comportano come previsto: il best known pubblicato risulta VALID a 663 688, e un nostro "
            "file con un flusso alterato apposta viene scartato come INFEASIBLE."),
          B("Nessuna soluzione pubblicata (<font name=DVM size=8>network24.bst.sol</font>, cartella "
            "submissions) è stata usata come punto di partenza o suggerimento. Ogni ricerca parte da "
            "topologie casuali, dalla topologia con più traffico diretto o da file salvati da noi."),
          B("Un bug nelle prime corse dell'ILS valutava male alcune mosse. Non ha toccato i file "
            "salvati, perché il checker rilegge ogni file."),
          B("Il risultato non è ancora stato inviato a QOBLIB, e i <font name=DVM size=8>.sol</font> "
            "sono esclusi da git: la soluzione esiste solo in locale.")]

story += [KeepTogether([P("Per riprodurre", h2),
          P("NETWORK_SOL_DIR=solutions/agent_pt .venv/bin/python network_pt.py 24 --minutes 20 "
            "--replicas 10 --workers 10 --tmin 450 --tmax 2500 --banked 2 --K 60 --p-double 0.5 "
            "--p-tri 0.03 --steps 15 --seed 8<br/>"
            "NETWORK_SOL_DIR=solutions/agent_ils .venv/bin/python network_ils.py run --chains 5 "
            "--minutes 20 --seed 700 --deep 12 --deep_tol 0.015 --kmax 8 --starts banked --sync<br/>"
            ".venv/bin/python network_pipeline.py status", code),
          P("Le repliche e le catene girano in parallelo, quindi lo stesso seed non garantisce la "
            "stessa traiettoria. Ogni comando riparte dal file salvato nella propria cartella.",
            small)])]


def footer(c, doc):
    c.saveState()
    c.setFont("DV", 7)
    c.setFillColor(colors.HexColor(MUTED))
    c.drawString(18 * mm, 10 * mm, "network24 · QOBLIB 08 · Qoro × PushQuantum 2026")
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}")
    c.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                        topMargin=16 * mm, bottomMargin=16 * mm,
                        title="network24: sotto il best known", author="")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("wrote", OUT, "curve:", [(t.strftime("%H:%M"), s) for t, s in curve])
