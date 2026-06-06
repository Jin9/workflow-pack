#!/usr/bin/env python3
"""spec_to_drawio.py — deterministic, offline architecture.spec.json -> 4-tab .drawio.

Renders ONE consolidated draw.io file with four pages (tabs), doc-altitude L1-L4:

  L1  System Context                     actors -> system -> external systems
  L2  High-Level Design (Containers)     services / datastores / bus / externals (rich vector icons)
  L3  Components & Aggregates            per bounded context: aggregates + process managers
  L4  ER & Aggregate->Table Boundaries   ER tables nested inside labeled DDD aggregate boundaries

Contract (see references/drawio-architecture-conventions.md):
  - Pure function of the input spec: same spec -> byte-identical .drawio. No now()/random/uuid;
    every collection is sorted once in normalize(); every cell id derives from sorted spec keys.
  - OFFLINE by construction: vector mxgraph styles only, never `image=http(s)://`, no src=/CDN.
  - The four <diagram> pages each start at the origin; the review console transcoder stacks them
    (drawio_to_svg.py E1). Native draw.io shows four tabs.

Usage:
  python3 spec_to_drawio.py --input architecture.spec.json --output system-architecture.drawio
  python3 spec_to_drawio.py -i architecture.spec.json -o -          # write to stdout (for diffing)
"""
import argparse
import json
import re
import sys

# ── house palette (offline; mirrors reference/*.drawio + dashboard) ──────────────
# (fill, stroke) assigned to bounded contexts by sorted index — stable per spec.
PALETTE = [
    ("#dae8fc", "#6c8ebf"),  # blue
    ("#d5e8d4", "#82b366"),  # green
    ("#ffe6cc", "#d79b00"),  # orange
    ("#e1d5e7", "#9673a6"),  # purple
    ("#fff2cc", "#d6b656"),  # yellow
    ("#f8cecc", "#b85450"),  # red
    ("#f5f5f5", "#666666"),  # grey
]
LIGHT = "#f5f5f5"
GREY = "#666666"

# ── hivemind house standard (reference/hivemind-high-level.drawio "Standard Template") ──
# Component status colour-coding (fill, stroke). Services/datastores carry an optional
# `status` (new|enhanced|existing|external); externals are always External.
STATUS = {
    "new":      ("#03CCFF", "#0288B0"),  # New component (greenfield)
    "enhanced": ("#92D14F", "#5C8A2B"),  # Enhanced existing component
    "existing": ("#BFBFBF", "#7F7F7F"),  # Existing/untouched component
    "external": ("#EF7D30", "#B85C1A"),  # 3rd-party / external component
}


def status_color(item, default="new"):
    """(fill, stroke) for a component per the house standard; honors item['status']."""
    return STATUS.get((item.get("status") or default).lower(), STATUS["new"])

# ER table cell geometry — mirrors tmp/runs/shoppilot/.../shoppilot-erd.drawio idiom.
START = 33          # table title bar height
ROW_H = 30
FLAG_W, NAME_W, TYPE_W = 50, 200, 260
TBL_W = FLAG_W + NAME_W + TYPE_W   # 510


# ── primitives ───────────────────────────────────────────────────────────────────
def slug(s):
    """Deterministic id fragment: lowercase, non-alnum -> '_', trimmed."""
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(s).lower())).strip("_")


def esc(s):
    """XML-escape a value; literal newlines -> &#10; (draw.io multiline label)."""
    s = "" if s is None else str(s)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    return s.replace("\n", "&#10;")


def fmt(n):
    """Stable number formatting — ints stay int (all layout math is integer)."""
    return str(int(round(n)))


def vcell(cid, value, style, parent, x, y, w, h):
    """A vertex mxCell with absolute (or parent-relative) geometry."""
    geo = '<mxGeometry x="%s" y="%s" width="%s" height="%s" as="geometry"/>' % (
        fmt(x), fmt(y), fmt(w), fmt(h))
    return '<mxCell id="%s" value="%s" style="%s" parent="%s" vertex="1">%s</mxCell>' % (
        cid, esc(value), style, parent, geo)


def ecell(eid, value, style, parent, source, target, exit=None, entry=None, points=None):
    """An edge mxCell with optional fixed exit/entry anchors + explicit waypoints.

    Anchors (exit/entry as (x, y) in 0..1) drive draw.io's own orthogonal routing so
    arrows leave/enter box EDGES (not centres) and route around obstacles. Waypoints
    (absolute (x, y) routed through inter-layer gutters) additionally keep the offline
    console transcoder's centre-to-centre polyline out of other boxes. Both are pure
    functions of computed node geometry, so output stays deterministic.
    """
    st = style
    if exit is not None:
        st += "exitX=%s;exitY=%s;exitDx=0;exitDy=0;" % (exit[0], exit[1])
    if entry is not None:
        st += "entryX=%s;entryY=%s;entryDx=0;entryDy=0;" % (entry[0], entry[1])
    pts = ""
    if points:
        inner = "".join('<mxPoint x="%s" y="%s"/>' % (fmt(px), fmt(py)) for px, py in points)
        pts = '<Array as="points">%s</Array>' % inner
    return ('<mxCell id="%s" value="%s" style="%s" parent="%s" edge="1" source="%s" target="%s">'
            '<mxGeometry relative="1" as="geometry">%s</mxGeometry></mxCell>') % (
        eid, esc(value), st, parent, source, target, pts)


def page(name, pid, cells, page_w=1600, page_h=1200):
    """Wrap a list of inner cell-xml strings into one <diagram> page."""
    head = ('<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" '
            'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="%d" pageHeight="%d" '
            'math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>') % (page_w, page_h)
    body = "".join("\n        " + c for c in cells)
    return '  <diagram name="%s" id="%s">\n      %s%s\n      </root></mxGraphModel>\n  </diagram>' % (
        esc(name), pid, head, body)


# ── edge styles — hivemind connection standard ─────────────────────────────────────
# Sync = solid classic arrow · Async = dashed classic · Authorization/system = doubleBlock.
SYNC_E = "edgeStyle=orthogonalEdgeStyle;rounded=0;jettySize=auto;html=1;endArrow=classic;endFill=1;strokeColor=#2E7BBF;"
ASYNC_E = "edgeStyle=orthogonalEdgeStyle;rounded=0;jettySize=auto;html=1;dashed=1;endArrow=classic;endFill=1;strokeColor=#9673a6;"
AUTH_E = "edgeStyle=orthogonalEdgeStyle;rounded=0;jettySize=auto;html=1;endArrow=doubleBlock;endFill=0;strokeColor=#666666;"


def conn_style(kind):
    """House-standard connection style for a topology edge kind."""
    if kind == "async":
        return ASYNC_E
    if kind in ("system_internal", "authorization", "auth"):
        return AUTH_E
    return SYNC_E


FK_E = {
    "intra": "edgeStyle=entityRelationEdgeStyle;html=1;endArrow=ERmany;startArrow=ERone;strokeColor=#82b366;",
    "composition": "edgeStyle=entityRelationEdgeStyle;html=1;endArrow=diamondThin;endFill=1;startArrow=ERmany;strokeColor=#6c8ebf;",
    "cross": "edgeStyle=entityRelationEdgeStyle;html=1;dashed=1;endArrow=ERmany;startArrow=ERone;strokeColor=#b85450;",
}
TITLE_STYLE = "text;html=1;align=left;verticalAlign=middle;fontStyle=1;fontSize=16;"


# ── normalization ──────────────────────────────────────────────────────────────────
def normalize(spec):
    """Sort every collection once and cross-check aggregate<->table ownership.

    All builders iterate the sorted lists, so output order is a pure function of content.
    Field aliases accepted: external_systems->externals, connections->topology,
    orchestrators->process_aggregates, root_table->root.
    """
    s = dict(spec)
    s.setdefault("externals", spec.get("external_systems", []))
    s.setdefault("topology", spec.get("connections", []))
    s.setdefault("process_aggregates", spec.get("orchestrators", []))
    s["contexts"] = sorted(spec.get("contexts", []), key=lambda c: c["id"])
    s["actors"] = sorted(spec.get("actors", []), key=lambda a: a["id"])
    s["externals"] = sorted(s["externals"], key=lambda e: e["id"])
    s["services"] = sorted(spec.get("services", []), key=lambda v: v["id"])
    s["datastores"] = sorted(spec.get("datastores", []), key=lambda d: d["id"])
    s["process_aggregates"] = sorted(s["process_aggregates"], key=lambda p: p["id"])
    aggs = []
    for a in spec.get("aggregates", []):
        a = dict(a)
        a.setdefault("root", a.get("root_table"))
        aggs.append(a)
    s["aggregates"] = sorted(aggs, key=lambda a: (a.get("context", ""), a["id"]))
    s["tables"] = dict(spec.get("tables", {}))
    # topology / fks: keep given order but record a stable index for dup-edge ids
    s["topology"] = list(s["topology"])
    s["fks"] = list(spec.get("fks", []))

    # fail-closed: every aggregate.tables[] entry must exist; every table must be claimed once.
    claimed = {}
    for a in s["aggregates"]:
        for t in a.get("tables", []):
            if t not in s["tables"]:
                raise SystemExit("spec error: aggregate %r lists unknown table %r" % (a["id"], t))
            if t in claimed:
                raise SystemExit("spec error: table %r claimed by both %r and %r" % (t, claimed[t], a["id"]))
            claimed[t] = a["id"]
    for t in s["tables"]:
        if t not in claimed:
            raise SystemExit("spec error: table %r is not owned by any aggregate" % t)
    return s


# ── L1: System Context ─────────────────────────────────────────────────────────────
def build_l1(s):
    cells = [vcell("L1_title", "L1 · System Context — %s" % s.get("system", ""),
                   TITLE_STYLE, "1", 40, 24, 900, 30)]
    sys_x, sys_y, sys_w = 380, 100, 440
    ctxs = s["contexts"]
    sys_h = max(len(ctxs) * 64 + 56, 120)
    cells.append(vcell("L1_system", s.get("system", "System"),
                       "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#333333;"
                       "verticalAlign=top;fontStyle=1;fontSize=14;container=1;collapsible=0;",
                       "1", sys_x, sys_y, sys_w, sys_h))
    n_act = len(s["actors"])
    for i, c in enumerate(ctxs):  # context chips inside the system box (relative coords)
        fill, stroke = status_color(c)  # contexts default New unless tagged
        cells.append(vcell("L1_ctx_" + slug(c["id"]), c.get("label", c["id"]) + " context",
                           "rounded=1;whiteSpace=wrap;html=1;fillColor=%s;strokeColor=%s;" % (fill, stroke),
                           "L1_system", 24, 44 + i * 64, sys_w - 48, 48))
    for i, a in enumerate(s["actors"]):  # actors on the left → into system left edge
        ey = round((i + 1) / (n_act + 1), 3)  # distinct entry height per actor (no overlap)
        cells.append(vcell("L1_actor_" + slug(a["id"]), a.get("label", a["id"]),
                           "rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;",
                           "1", 40, sys_y + 20 + i * 110, 180, 70))
        cells.append(ecell("L1_e_actor_" + slug(a["id"]), a.get("edge", "uses"),
                           SYNC_E, "1", "L1_actor_" + slug(a["id"]), "L1_system",
                           exit=(1, 0.5), entry=(0, ey)))
    n_ext = len(s["externals"])
    for i, e in enumerate(s["externals"]):  # external systems on the right ← system right edge
        ey = round((i + 1) / (n_ext + 1), 3)
        efill, estroke = STATUS["external"]
        cells.append(vcell("L1_ext_" + slug(e["id"]), e.get("label", e["id"]),
                           "rounded=0;whiteSpace=wrap;html=1;fillColor=%s;strokeColor=%s;" % (efill, estroke),
                           "1", sys_x + sys_w + 120, sys_y + 20 + i * 110, 200, 70))
        cells.append(ecell("L1_e_ext_" + slug(e["id"]), e.get("edge", "integrates"),
                           AUTH_E, "1", "L1_system", "L1_ext_" + slug(e["id"]),
                           exit=(1, ey), entry=(0, 0.5)))
    return cells


# ── L2: High-Level Design (Containers) — left→right layered, channel-routed ─────────
# Columns:  web │ services │ datastores │ externals ;  Kafka bus = bottom channel.
# Edges route through inter-column gutters so no arrow crosses a component box.
L2_WEB_X, L2_WEB_W, L2_WEB_H = 40, 150, 80
L2_SVC_X, L2_SVC_W, L2_SVC_H = 440, 180, 90
L2_DB_X,  L2_DB_W,  L2_DB_H = 820, 200, 80
L2_EXT_X, L2_EXT_W, L2_EXT_H = 1240, 190, 90
L2_BODY_Y, L2_BAND_GUT, L2_DB_DY = 110, 46, 96
# routing channels in the web→service gutter (190..440); parallel edges stagger to spread labels
L2_CH_BUS, L2_CH_WEB, L2_CH_SS, L2_GUT_B = 210, 330, 400, 720


def build_l2(s):
    cells = [vcell("L2_title", "L2 · High-Level Design (Containers) — %s" % s.get("system", ""),
                   TITLE_STYLE, "1", 40, 24, 1100, 30)]
    boxes, kind, band_top = {}, {}, {}

    def node(nid, label, style, x, y, w, h, knd, bt=None):
        cid = "L2_" + slug(nid)
        boxes[nid] = (x, y, w, h)
        kind[nid] = knd
        if bt is not None:
            band_top[nid] = bt
        cells.append(vcell(cid, label, style, "1", x, y, w, h))

    def pod(fill, stroke):
        return ("shape=mxgraph.kubernetes.icon;prIcon=pod;html=1;whiteSpace=wrap;fillColor=%s;"
                "strokeColor=%s;verticalLabelPosition=bottom;verticalAlign=top;" % (fill, stroke))

    def cyl(fill, stroke):
        return ("shape=cylinder3;whiteSpace=wrap;html=1;backgroundOutline=1;size=15;fillColor=%s;"
                "strokeColor=%s;" % (fill, stroke))

    BUS = "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontStyle=1;"
    CLIENT_F, CLIENT_S = STATUS["new"]

    ctx_services = [v for v in s["services"] if v.get("context")]
    ds_by_ctx, ext_by_ctx = {}, {}
    for d in s["datastores"]:
        if d.get("kind") != "bus":
            ds_by_ctx.setdefault(d.get("context"), []).append(d)
    for e in s["externals"]:
        ext_by_ctx.setdefault(e.get("from"), []).append(e)

    # one horizontal band per bounded context: service (col1) · datastores (col2) · external (col3)
    y = L2_BODY_Y
    for c in s["contexts"]:
        dbs = ds_by_ctx.get(c["id"], [])
        band_h = max(L2_SVC_H + 24, len(dbs) * L2_DB_DY + 14)
        svc_y = y + band_h // 2 - L2_SVC_H // 2
        for v in [v for v in ctx_services if v.get("context") == c["id"]]:
            f, st = status_color(v)
            node(v["id"], v.get("label", v["id"]), pod(f, st),
                 L2_SVC_X, svc_y, L2_SVC_W, L2_SVC_H, "service", y)
        for k, d in enumerate(dbs):
            f, st = status_color(d)
            node(d["id"], d.get("label", d["id"]), cyl(f, st),
                 L2_DB_X, y + 7 + k * L2_DB_DY, L2_DB_W, L2_DB_H, "db", y)
        for j, e in enumerate(ext_by_ctx.get(c["id"], [])):
            f, st = STATUS["external"]
            node(e["id"], e.get("label", e["id"]), pod(f, st),
                 L2_EXT_X, svc_y + j * 110, L2_EXT_W, L2_EXT_H, "external", y)
        y += band_h + L2_BAND_GUT
    total_h = y - L2_BAND_GUT - L2_BODY_Y

    # web client(s) left of the service column, vertically centred on the body
    clients = [v for v in s["services"] if not v.get("context")]
    for i, v in enumerate(clients):
        node(v["id"], v.get("label", v["id"]),
             "rounded=1;whiteSpace=wrap;html=1;fillColor=%s;strokeColor=%s;fontStyle=1;" % (CLIENT_F, CLIENT_S),
             L2_WEB_X, L2_BODY_Y + total_h // 2 - L2_WEB_H // 2 + i * 100, L2_WEB_W, L2_WEB_H, "web")
    # Kafka bus = bottom channel spanning the service+datastore columns
    bus_y = L2_BODY_Y + total_h + 30
    for i, d in enumerate([d for d in s["datastores"] if d.get("kind") == "bus"]):
        node(d["id"], d.get("label", d["id"]), BUS, L2_SVC_X, bus_y + i * 80,
             (L2_DB_X + L2_DB_W) - L2_SVC_X, 60, "bus")

    def cy(n):
        x, yy, w, h = boxes[n]; return yy + h // 2

    def route(a, b, ka, kb, off):
        """(exit, entry, waypoints). Each edge category routes through a clear gutter;
        `off` staggers parallel edges within a channel so lines + labels don't pile up."""
        if ka == "web" and kb == "service":
            return (1, 0.5), (0, 0.5), [(L2_CH_WEB + off * 12, cy(b))]
        if ka == "service" and kb == "db":
            return (1, 0.5), (0, 0.5), [(L2_GUT_B, cy(b))]
        if ka == "service" and kb == "service":
            cx = L2_CH_SS + off * 14
            return (0, 0.5), (0, 0.5), [(cx, cy(a)), (cx, cy(b))]
        if "bus" in (ka, kb):
            cx = L2_CH_BUS + off * 16
            return (0, 0.5), (0, 0.5), [(cx, cy(a)), (cx, cy(b))]
        if "external" in (ka, kb):           # route over the band top into the external's left
            svc, ext = (a, b) if kb == "external" else (b, a)
            bt = band_top.get(ext, boxes[ext][1]) - 18 - off * 12
            sx, sw = boxes[svc][0], boxes[svc][2]
            ex = boxes[ext][0]
            if ka == "service":
                return (1, 0.2), (0, 0.5), [(sx + sw + 14, bt), (ex - 18, bt), (ex - 18, cy(ext))]
            return (0, 0.5), (1, 0.2), [(ex - 18, cy(ext)), (ex - 18, bt), (sx + sw + 14, bt)]
        return (1, 0.5), (0, 0.5), None      # fallback: simple anchored edge

    def category(ka, kb):
        if ka == "web" and kb == "service":
            return "web"
        if ka == "service" and kb == "db":
            return "db"
        if ka == "service" and kb == "service":
            return "ss"
        if "bus" in (ka, kb):
            return "bus"
        if "external" in (ka, kb):
            return "ext"
        return "other"

    seen, chan = {}, {}
    for t in s["topology"]:
        a, b = t.get("from"), t.get("to")
        if a not in boxes or b not in boxes:
            continue
        key = (a, b)
        seen[key] = seen.get(key, -1) + 1
        suff = "" if seen[key] == 0 else "_%d" % seen[key]
        cat = category(kind[a], kind[b])
        off = chan.get(cat, 0)
        chan[cat] = off + 1
        ex, en, pts = route(a, b, kind[a], kind[b], off)
        cells.append(ecell("L2_e_%s__%s%s" % (slug(a), slug(b), suff),
                           t.get("label", ""), conn_style(t.get("kind")), "1",
                           "L2_" + slug(a), "L2_" + slug(b), exit=ex, entry=en, points=pts))
    return cells


# ── L3: Components & Aggregates ────────────────────────────────────────────────────
def build_l3(s):
    cells = [vcell("L3_title", "L3 · Components & Aggregates (per bounded context)",
                   TITLE_STYLE, "1", 40, 24, 1100, 30)]
    aggs_by_ctx, proc_by_ctx = {}, {}
    for a in s["aggregates"]:
        aggs_by_ctx.setdefault(a.get("context"), []).append(a)
    for p in s["process_aggregates"]:
        proc_by_ctx.setdefault(p.get("context"), []).append(p)
    svc_by_ctx = {}
    for v in s["services"]:
        if v.get("context"):
            svc_by_ctx.setdefault(v["context"], []).append(v)

    y = 80
    for i, c in enumerate(s["contexts"]):
        fill, stroke = PALETTE[i % len(PALETTE)]
        members = aggs_by_ctx.get(c["id"], []) + proc_by_ctx.get(c["id"], [])
        cols = max(len(members), 1)
        box_w = max(40 + cols * 240, 320)
        box_h = 150
        svc_names = ", ".join(v.get("id", "") for v in svc_by_ctx.get(c["id"], [])) or "—"
        cid = "L3_ctx_" + slug(c["id"])
        cells.append(vcell(cid, "%s context   ·   service: %s" % (c.get("label", c["id"]), svc_names),
                           "rounded=1;whiteSpace=wrap;html=1;fillColor=%s;strokeColor=%s;verticalAlign=top;"
                           "fontStyle=1;container=1;collapsible=0;" % (LIGHT, stroke),
                           "1", 40, y, box_w, box_h))
        for j, a in enumerate(aggs_by_ctx.get(c["id"], [])):
            af, ast = status_color(a)  # aggregate component coloured by the house standard
            cells.append(vcell("L3_agg_" + slug(a["id"]),
                               "%s\n(aggregate · root: %s)" % (a.get("label", a["id"]), a.get("root", "?")),
                               "rounded=1;whiteSpace=wrap;html=1;fillColor=%s;strokeColor=%s;" % (af, ast),
                               cid, 20 + j * 240, 48, 220, 84))
        base = len(aggs_by_ctx.get(c["id"], []))
        for j, p in enumerate(proc_by_ctx.get(c["id"], [])):
            cells.append(vcell("L3_proc_" + slug(p["id"]),
                               "%s\n%s" % (p.get("label", p["id"]), p.get("note", "")),
                               "rhombus;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;",
                               cid, 20 + (base + j) * 240, 48, 220, 84))
        y += box_h + 30
    return cells


# ── L4: ER & Aggregate->Table Boundaries ───────────────────────────────────────────
def _split(text):
    """'customer_id : UUID' -> ('customer_id', 'UUID'); fallback whole-text into name."""
    if " : " in text:
        name, typ = text.split(" : ", 1)
        return name.strip(), typ.strip()
    return text.strip(), ""


def _table(cells, tid, name, rows, parent, x, y, is_root):
    fill, stroke = ("#d5e8d4", "#82b366") if is_root else ("#dae8fc", "#6c8ebf")
    title = name + (" «root»" if is_root else "")
    height = START + len(rows) * ROW_H
    cells.append(vcell(tid, title,
                       "shape=table;startSize=33;container=1;collapsible=1;childLayout=tableLayout;"
                       "fixedRows=1;rowLines=0;fontStyle=1;align=center;resizeLast=1;fillColor=%s;strokeColor=%s;"
                       % (fill, stroke), parent, x, y, TBL_W, height))
    row_style = ("shape=partialRectangle;collapsible=0;dropTarget=0;pointerEvents=0;fillColor=none;"
                 "points=[[0,0.5],[1,0.5]];portConstraint=eastwest;top=0;left=0;right=0;bottom=1;")
    for i, row in enumerate(rows):
        flag, text = (row + ["", ""])[:2] if isinstance(row, list) else ("", str(row))
        cname, ctype = _split(text)
        rid = "%s_r%d" % (tid, i)
        cells.append('<mxCell id="%s" value="" style="%s" parent="%s" vertex="1">'
                     '<mxGeometry y="%d" width="%d" height="%d" as="geometry"/></mxCell>'
                     % (rid, row_style, tid, START + i * ROW_H, TBL_W, ROW_H))
        bold = ";fontStyle=1" if flag in ("PK", "FK") else ""
        sub = [("c0", flag, 0, FLAG_W, "fontStyle=1;" if flag else ""),
               ("c1", cname, FLAG_W, NAME_W, "align=left;spacingLeft=6;" + ("fontStyle=1;" if flag == "PK" else "")),
               ("c2", ctype, FLAG_W + NAME_W, TYPE_W, "align=left;spacingLeft=6;")]
        for cc, val, cx, cw, extra in sub:
            cells.append('<mxCell id="%s_%s" value="%s" style="shape=partialRectangle;overflow=hidden;'
                         'connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;%s" parent="%s" vertex="1">'
                         '<mxGeometry x="%d" width="%d" height="%d" as="geometry">'
                         '<mxRectangle width="%d" height="%d" as="alternateBounds"/></mxGeometry></mxCell>'
                         % (rid, cc, esc(val), extra, rid, cx, cw, ROW_H, cw, ROW_H))
    return height


def build_l4(s):
    cells = [vcell("L4_title", "L4 · ER & Aggregate→Table Boundaries (DDD: which aggregate scopes which tables)",
                   TITLE_STYLE, "1", 40, 24, 1400, 30)]
    MAXW, GUT, x, y, row_h = 2500, 40, 40, 80, 0
    ctx_idx = {c["id"]: i for i, c in enumerate(s["contexts"])}
    for a in s["aggregates"]:
        tnames = a.get("tables", [])
        heights = [START + len(s["tables"][t].get("rows", [])) * ROW_H for t in tnames]
        box_w = 40 + len(tnames) * (TBL_W + 20)
        box_h = 48 + (max(heights) if heights else ROW_H) + 20
        if x + box_w > MAXW and x > 40:        # shelf wrap
            x, y, row_h = 40, y + row_h + 40, 0
        fill, stroke = PALETTE[ctx_idx.get(a.get("context"), 0) % len(PALETTE)]
        box_id = "L4_box_" + slug(a["id"])
        cells.append(vcell(box_id, "Aggregate: %s   ·   %s   ·   root=%s"
                           % (a.get("label", a["id"]), a.get("context", "?"), a.get("root", "?")),
                           "rounded=1;dashed=1;whiteSpace=wrap;html=1;fillColor=%s;strokeColor=%s;"
                           "verticalAlign=top;fontStyle=1;container=1;collapsible=0;" % (LIGHT, stroke),
                           "1", x, y, box_w, box_h))
        for j, t in enumerate(tnames):
            _table(cells, "L4_tbl_" + slug(t), t, s["tables"][t].get("rows", []),
                   box_id, 20 + j * (TBL_W + 20), 40, t == a.get("root"))
        x += box_w + GUT
        row_h = max(row_h, box_h)
    # FK edges across aggregate boundaries
    seen = {}
    for f in s["fks"]:
        a, b = f.get("from"), f.get("to")
        if a not in s["tables"] or b not in s["tables"]:
            continue
        key = (a, b)
        seen[key] = seen.get(key, -1) + 1
        suff = "" if seen[key] == 0 else "_%d" % seen[key]
        style = FK_E.get(f.get("class", "cross"), FK_E["cross"])
        cells.append(ecell("L4_fk_%s__%s%s" % (slug(a), slug(b), suff),
                           f.get("from_col", ""), style, "1",
                           "L4_tbl_" + slug(a), "L4_tbl_" + slug(b),
                           exit=(0, 0.5), entry=(1, 0.5)))  # leave/enter table sides
    return cells


# ── Legend / Standard Template (hivemind house style, offline vector) ───────────────
def build_legend(s):
    """Static offline legend reproducing the hivemind Standard Template's relevant
    sections: component status colours, connection types, database states. Vector
    cells only — no embedded icon galleries, no image= / http (stays offline)."""
    HEAD = "text;html=1;fontStyle=1;fontSize=14;align=left;verticalAlign=middle;"
    LAB = "text;html=1;align=left;verticalAlign=middle;"
    items = [("new", "New"), ("enhanced", "Enhanced"), ("existing", "Existing"), ("external", "External")]
    cells = [vcell("LG_title", "Legend · Standard Template — house style (colours · connections · databases)",
                   TITLE_STYLE, "1", 40, 24, 1200, 30),
             vcell("LG_h1", "Standard Colours &amp; Components", HEAD, "1", 40, 80, 380, 26)]
    for i, (k, lab) in enumerate(items):  # colour swatches
        f, st = STATUS[k]
        y = 120 + i * 54
        cells.append(vcell("LG_sw_" + k, "", "rounded=1;whiteSpace=wrap;html=1;fillColor=%s;strokeColor=%s;" % (f, st),
                           "1", 40, y, 60, 38))
        cells.append(vcell("LG_swl_" + k, "%s Component   %s" % (lab, f), LAB, "1", 112, y, 300, 38))

    cells.append(vcell("LG_h2", "Connections", HEAD, "1", 470, 80, 300, 26))
    conns = [("sync", "Sync — request / command", SYNC_E),
             ("async", "Async — event (dashed)", ASYNC_E),
             ("auth", "Authorization / Annotation", AUTH_E)]
    for i, (k, lab, style) in enumerate(conns):  # sample arrows between two dots
        y = 124 + i * 64
        dot = "ellipse;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#333333;"
        cells.append(vcell("LG_ca_" + k, "", dot, "1", 470, y, 18, 18))
        cells.append(vcell("LG_cb_" + k, "", dot, "1", 610, y, 18, 18))
        cells.append(ecell("LG_ce_" + k, "", style, "1", "LG_ca_" + k, "LG_cb_" + k,
                           exit=(1, 0.5), entry=(0, 0.5)))
        cells.append(vcell("LG_cl_" + k, lab, LAB, "1", 648, y - 10, 320, 38))

    cells.append(vcell("LG_h3", "Databases ({Instance}-{DB})", HEAD, "1", 40, 360, 400, 26))
    for i, (k, lab) in enumerate(items):  # database states
        f, st = STATUS[k]
        x = 40 + i * 190
        cells.append(vcell("LG_db_" + k, "{Instance}-{DB}",
                           "shape=cylinder3;whiteSpace=wrap;html=1;backgroundOutline=1;size=12;fillColor=%s;strokeColor=%s;" % (f, st),
                           "1", x, 400, 130, 84))
        cells.append(vcell("LG_dbl_" + k, lab + " DB", "text;html=1;align=center;verticalAlign=middle;",
                           "1", x, 488, 130, 24))
    return cells


# ── assembly ───────────────────────────────────────────────────────────────────────
def build(spec):
    s = normalize(spec)
    pages = [
        page("L1 System Context", "L1-context", build_l1(s)),
        page("L2 High-Level Design (Containers)", "L2-containers", build_l2(s)),
        page("L3 Components & Aggregates", "L3-components", build_l3(s)),
        page("L4 ER & Aggregate→Table Boundaries", "L4-er-boundaries", build_l4(s)),
        page("Legend / Standard Template", "legend-standard", build_legend(s)),
    ]
    return '<mxfile host="spec_to_drawio" pages="5">\n' + "\n".join(pages) + "\n</mxfile>\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Deterministic offline architecture.spec.json -> 4-tab .drawio")
    ap.add_argument("--input", "-i", required=True, help="architecture.spec.json")
    ap.add_argument("--output", "-o", default="-", help="output .drawio path, or '-' for stdout")
    args = ap.parse_args(argv)
    with open(args.input, encoding="utf-8") as fh:
        spec = json.load(fh)
    out = build(spec)
    if args.output == "-":
        sys.stdout.write(out)
    else:
        with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
