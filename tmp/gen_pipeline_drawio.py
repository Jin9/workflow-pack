#!/usr/bin/env python3
"""Generate delivery-pipeline-flow.drawio from dashboard-data.json.

Renders all 27 pipeline nodes (15 SDLC stages S0-S7 + 12 test/security gates
T1-T12) top-to-bottom in 8 SDLC phase bands, with the Backend and Frontend legs
side-by-side. Each box shows the stage input (in) / output (out); stages needing
a human are colour-graded (strong / review / auto) and tagged with a person glyph.

Two readability rules drive the layout:
  - boxes are sized to their wrapped text (no characters spill past the border);
  - the central spine keeps a box-free corridor, and every edge declares an
    exit/entry anchor, so no arrow is routed through a box.

Deterministic by contract: no now()/random -> byte-identical output for identical
input. Offline by contract: no https://, src=, CDN. Regenerate with:
    python3 tmp/gen_pipeline_drawio.py
"""
import json
import math
import os

# --------------------------------------------------------------- paths
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "dashboard-data.json")
OUT = os.path.join(ROOT, "delivery-pipeline-flow.drawio")

# --------------------------------------------------------------- glyphs / palette
PERSON, WARN, IN, OUT_, LOOP, XMARK, HAND = "\U0001F464", "⚠", "▸", "◂", "↺", "✗", "✋"
COLORS = {
    "strong": ("#e1d5e7", "#9673a6"),   # sync / human named approval
    "review": ("#fff2cc", "#d6b656"),   # async confirm / red-team gate
    "auto":   ("#dae8fc", "#6c8ebf"),   # automated, no human
}

# --------------------------------------------------------------- geometry
W = 300                                 # box width
LINE, PAD, MINH = 18, 24, 130           # text line height / box padding / min height
TOP = 110                               # first band top
HEADER, VGAP, BOTTOMPAD, BANDGAP = 42, 34, 20, 26
SX = 610                                # spine box-left (centre 760)
BEX, FEX = 140, 1080                    # backend / frontend lane box-left
QUAD = [100, 420, 800, 1120]           # band-6 gate row: 2 left + 2 right of the spine corridor
TWO = [300, 900]                        # 2-wide rows (band-5, band-7) flank the corridor
BG_X, BG_W = 100, 1340                  # phase-band background
LX, LY, LW, LH = 1470, 150, 310, 470    # legend box

# --------------------------------------------------------------- load + classify
with open(SRC, encoding="utf-8") as fh:
    data = json.load(fh)

def klass(gate):
    if gate in ("sync", "human"):
        return "strong"
    if gate in ("async", "gate"):
        return "review"
    return "auto"

NODE = {}
for s in data["stages"]:
    g = s["gate"]
    NODE[s["id"]] = {
        "id": s["id"], "name": s["name"], "skill": s["skill"],
        "in": s["input"], "out": s["output"], "gate": g, "tier": s.get("tier", ""),
        "cls": klass(g), "exc": g == "auto+exc", "deferred": bool(s.get("deferred")),
        "shape": "gate" if s["id"].startswith("T") else "stage",
    }

# --------------------------------------------------------------- label + height
def lines(n):
    """Return [(html, plain)] segments; plain is tag-free for width measurement."""
    badge = (PERSON + " ") if n["cls"] in ("strong", "review") else ""
    defer_h = " <font color='#b85450'>(deferred)</font>" if n["deferred"] else ""
    defer_p = " (deferred)" if n["deferred"] else ""
    head = ("<b>%s%s · %s</b>%s" % (badge, n["id"], n["name"], defer_h),
            "%s%s · %s%s" % (badge, n["id"], n["name"], defer_p))
    skill = ("<font color='#777777'>%s</font>" % n["skill"], n["skill"])
    inp = ("%s in: %s" % (IN, n["in"]),) * 2
    out = ("%s out: %s" % (OUT_, n["out"]),) * 2
    meta_h = "<font color='#888888'>gate: %s · tier %s</font>" % (n["gate"], n["tier"])
    meta_p = "gate: %s · tier %s" % (n["gate"], n["tier"])
    if n["exc"]:
        meta_h += " <font color='#cc8800'>%s human on exception</font>" % WARN
        meta_p += "  %s human on exception" % WARN
    return [head, skill, inp, out, (meta_h, meta_p)]

def height(n, segs):
    usable = W - (34 if n["shape"] == "gate" else 20)   # process bars eat width
    cpl = max(12, int(usable / 6.2))
    rows = sum(max(1, math.ceil(len(p) / cpl)) for _, p in segs)
    return max(MINH, rows * LINE + PAD)

# --------------------------------------------------------------- layout (rows -> y)
BANDS = [
    ("1 · Requirements & Design",
        [[("S0", SX)], [("S1a", SX)], [("S1b", SX)], [("S1.5", SX)], [("S2", SX)]]),
    ("2 · Design gate (red-team)", [[("S2.5", SX)]]),
    ("3 · Contracts (BE/FE)", [[("S3a/3b", SX)]]),
    ("4 · Development — Backend ∥ Frontend",
        [[("S4a", BEX), ("S4b", FEX)], [("T1", BEX), ("T3", FEX)],
         [("T2", BEX), ("T4", FEX)], [("S4a-r", BEX), ("S4b-r", FEX)]]),
    ("5 · Cross-cutting CI / security", [[("T5", TWO[0]), ("T7", TWO[1])]]),
    ("6 · QA · SIT → UAT",
        [[("S4c", SX)], [("S5", SX)],
         [("T6", QUAD[0]), ("T8", QUAD[1]), ("T9", QUAD[2]), ("T10", QUAD[3])]]),
    ("7 · Release", [[("S6", SX)], [("T11", TWO[0]), ("T12", TWO[1])]]),
    ("8 · Operate", [[("S7", SX)]]),
]

box = {}            # id -> (x, y, w, h)
segs = {nid: lines(n) for nid, n in NODE.items()}
hgt = {nid: height(n, segs[nid]) for nid, n in NODE.items()}
band_rects = []
y = TOP
for title, rows in BANDS:
    btop = y
    iy = btop + HEADER
    for row in rows:
        rowh = max(hgt[nid] for nid, _ in row)
        for nid, x in row:
            box[nid] = (x, iy, W, hgt[nid])
        iy += rowh + VGAP
    bbot = iy - VGAP + BOTTOMPAD
    band_rects.append((title, BG_X, btop, BG_W, bbot - btop))
    y = bbot + BANDGAP
TOTAL_H = y

# --------------------------------------------------------------- emit helpers
def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))

def slug(nid):
    return "n_" + "".join(c if c.isalnum() else "" for c in nid)

cells = []

def vertex(cid, label, style, x, yy, w, h):
    cells.append(
        '<mxCell id="%s" value="%s" style="%s" vertex="1" parent="1">'
        '<mxGeometry x="%d" y="%d" width="%d" height="%d" as="geometry"/></mxCell>'
        % (cid, esc(label), style, x, yy, w, h))

def edge(eid, src, dst, label, style):
    cells.append(
        '<mxCell id="%s" value="%s" style="%s" edge="1" parent="1" source="%s" target="%s">'
        '<mxGeometry relative="1" as="geometry"/></mxCell>'
        % (eid, esc(label), style, src, dst))

def node_style(n):
    fill, stroke = COLORS[n["cls"]]
    if n["shape"] == "gate":
        st = ("shape=process;whiteSpace=wrap;html=1;backgroundOutline=1;align=left;"
              "verticalAlign=top;spacingLeft=16;spacingRight=12;spacingTop=6;fontSize=11;")
    else:
        st = ("rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;"
              "spacingLeft=8;spacingRight=6;spacingTop=6;fontSize=11;")
    st += "fillColor=%s;strokeColor=%s;" % (fill, stroke)
    if n["deferred"]:
        st += "dashed=1;dashPattern=8 4;"
    return st

# --------------------------------------------------------------- title + legend
vertex("title", "<b>Agentic Delivery Pipeline — workflow stages (top → bottom)</b>"
       "<br><font color='#555555'>From dashboard-data.json · input %s / output %s per stage "
       "· %s marks stages needing human review</font>" % (IN, OUT_, PERSON),
       "text;html=1;fontSize=18;align=left;verticalAlign=middle;", BG_X, 24, BG_W, 60)

vertex("leg_bg", "", "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#999999;",
       LX, LY, LW, LH)
vertex("leg_title", "<b>Legend</b>", "text;html=1;fontSize=14;align=left;verticalAlign=middle;",
       LX + 14, LY + 8, LW - 28, 26)
for i, (cl, txt, dy) in enumerate([
        ("strong", "<b>STRONG</b> %s sync / human named approval" % PERSON, 48),
        ("review", "<b>REVIEW</b> %s async confirm / red-team gate" % PERSON, 96),
        ("auto", "<b>AUTO</b> automated · no human", 144)]):
    fill, stroke = COLORS[cl]
    vertex("leg_sw%d" % i, "", "whiteSpace=wrap;html=1;fillColor=%s;strokeColor=%s;" % (fill, stroke),
           LX + 16, LY + dy, 32, 22)
    vertex("leg_tx%d" % i, txt, "text;html=1;fontSize=11;align=left;verticalAlign=middle;",
           LX + 56, LY + dy - 4, LW - 70, 30)
vertex("leg_body",
       "%s Shapes: rounded = SDLC stage · barred = test/security gate (T#)<br><br>"
       "%s Dashed border = deferred / unbuilt (GAP · OI-003): S0, S3, S5, S7<br><br>"
       "%s Dashed red edge = loop-back / compensation (SAGA rollback)<br><br>"
       "%s %s = human only on exception (auto+exc): T4, T6, T8, T12<br><br>"
       "%s %s in a box header = needs human review (12 of 27)<br><br>"
       "<font color='#777777'>Source: dashboard-data.json · 15 stages (S0–S7) + 12 gates (T1–T12)</font>"
       % (IN, IN, IN, IN, WARN, IN, PERSON),
       "text;html=1;fontSize=10;align=left;verticalAlign=top;spacingLeft=4;",
       LX + 14, LY + 190, LW - 28, LH - 200)

# --------------------------------------------------------------- bands + nodes
for i, (title, x, yy, w, h) in enumerate(band_rects):
    vertex("band%d" % i, title,
           "rounded=1;whiteSpace=wrap;html=1;fillColor=#f2f2f2;strokeColor=#cccccc;"
           "verticalAlign=top;align=left;fontStyle=1;fontSize=13;spacingLeft=12;spacingTop=8;"
           "fontColor=#333333;", x, yy, w, h)
for nid, n in NODE.items():
    x, yy, w, h = box[nid]
    vertex(slug(nid), "<br>".join(seg[0] for seg in segs[nid]), node_style(n), x, yy, w, h)

# --------------------------------------------------------------- edges
DOWN = "exitX=0.5;exitY=1;entryX=0.5;entryY=0;"
SOLID = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;strokeColor=#555555;fontSize=10;fontColor=#333333;"
LOOPB = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;dashed=1;strokeColor=#b85450;fontColor=#b85450;fontSize=10;"

forward = [
    ("S0", "S1a", "", DOWN),
    ("S1a", "S1b", "gate: proceed %s   |   needs-work %s / do-not-build %s" % (HAND, LOOP, XMARK), DOWN),
    ("S1b", "S1.5", "", DOWN),
    ("S1.5", "S2", "", DOWN),
    ("S2", "S2.5", "", DOWN),
    ("S2.5", "S3a/3b", "pass", DOWN),
    ("S3a/3b", "S4a", "%s BE" % OUT_, DOWN),
    ("S3a/3b", "S4b", "%s FE" % OUT_, DOWN),
    ("S4a", "T1", "", DOWN), ("T1", "T2", "", DOWN), ("T2", "S4a-r", "", DOWN),
    ("S4b", "T3", "", DOWN), ("T3", "T4", "", DOWN), ("T4", "S4b-r", "", DOWN),
    ("S4a-r", "T5", "", DOWN), ("S4b-r", "T7", "", DOWN),
    ("T5", "S4c", "", "exitX=0.5;exitY=1;entryX=0;entryY=0.5;"),
    ("T7", "S4c", "", "exitX=0.5;exitY=1;entryX=1;entryY=0.5;"),
    ("S4c", "S5", "", DOWN),
    ("S5", "T6", "", "exitX=0.18;exitY=1;entryX=0.5;entryY=0;"),
    ("S5", "T8", "", "exitX=0.36;exitY=1;entryX=0.5;entryY=0;"),
    ("S5", "T9", "", "exitX=0.64;exitY=1;entryX=0.5;entryY=0;"),
    ("S5", "T10", "", "exitX=0.82;exitY=1;entryX=0.5;entryY=0;"),
    ("S5", "S6", "signoff → deploy", DOWN),
    ("T10", "S6", "security pass", "exitX=0.2;exitY=1;entryX=1;entryY=0.5;"),
    ("S6", "T11", "", "exitX=0.4;exitY=1;entryX=0.5;entryY=0;"),
    ("T11", "T12", "", "exitX=1;exitY=0.5;entryX=0;entryY=0.5;"),
    ("T12", "S7", "", "exitX=0.5;exitY=1;entryX=0.5;entryY=0;"),
]
loopbacks = [
    ("S4a-r", "S4a", "loop-back ×2", "exitX=0;exitY=0.5;entryX=0;entryY=0.5;"),
    ("S4b-r", "S4b", "loop-back ×2", "exitX=1;exitY=0.5;entryX=1;entryY=0.5;"),
    ("S2.5", "S2", "reroute", "exitX=1;exitY=0.5;entryX=1;entryY=0.5;"),
    ("S2.5", "S1b", "reroute", "exitX=0;exitY=0.5;entryX=0;entryY=0.5;"),
    ("S7", "S6", "rollback %s handoff-revoke" % LOOP, "exitX=0.6;exitY=0;entryX=0.6;entryY=1;"),
]
ei = 0
for s, d, lbl, extra in forward:
    edge("e%d" % ei, slug(s), slug(d), lbl, SOLID + extra); ei += 1
for s, d, lbl, extra in loopbacks:
    edge("e%d" % ei, slug(s), slug(d), lbl, LOOPB + extra); ei += 1

# --------------------------------------------------------------- write
xml = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" '
       'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1840" '
       'pageHeight="%d" math="0" shadow="0" adaptiveColors="auto">' % (TOTAL_H + 40),
       "<root>", '<mxCell id="0"/>', '<mxCell id="1" parent="0"/>',
       *cells, "</root>", "</mxGraphModel>"]
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(xml) + "\n")

print("wrote", OUT)
print("nodes:", len(NODE), "| edges:", ei, "| canvas H:", TOTAL_H)
human = [k for k, n in NODE.items() if n["cls"] in ("strong", "review")]
print("human-marked (%d):" % len(human), ", ".join(human))
