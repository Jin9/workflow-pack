#!/usr/bin/env python3
"""drawio_to_svg.py — deterministic, offline .drawio -> inline <svg> transcoder.

Reads the mxGraph geometry from a draw.io XML file and emits a standalone inline
<svg> string previewing the diagram. The output is meant to be baked INTO an
offline HTML console, so it is offline-clean (no http(s), src=, url(, @font-face,
@import, xlink:href to externals, no <image>) and byte-deterministic (same input
file -> byte-identical SVG every run).

Public API:
    transcode(drawio_path: str) -> str   # returns the "<svg ...>...</svg>" string

CLI:
    python3 drawio_to_svg.py INPUT.drawio [-o OUT.svg]
    # default writes INPUT.svg beside the input; use "-o -" to print to stdout.

Stdlib only. No third-party dependencies.
"""

import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Theme — neutral palette that reads in BOTH light and dark console themes.
# We PREFER the cell's own fillColor/strokeColor (these source files set them);
# the palette below is only a fallback when a cell omits them.
# ---------------------------------------------------------------------------
THEME = {
    "vertex_fill": "#eef2f7",   # neutral light-grey fill (mid-contrast on both themes)
    "vertex_stroke": "#64748b", # slate stroke
    "edge_stroke": "#64748b",   # slate edge
    "text": "#1f2937",          # dark slate text (legible on light fills)
    "text_on_dark": "#f8fafc",  # light text when fill is dark
    "table_title_fill": "#dbe4ee",
}

FONT_STACK = (
    "ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"
)

MARGIN = 24.0
RADIUS = 6.0
FONT_SIZE = 11.0
TITLE_FONT_SIZE = 12.0
LINE_HEIGHT = 13.5
CHAR_W = 6.2  # approx px per char at FONT_SIZE (for clipping long labels)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def esc(s):
    """Escape text for XML/SVG (& < > ")."""
    if s is None:
        return ""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fmt(n):
    """Deterministic numeric formatting: ints stay int, else 2 decimals."""
    f = float(n)
    if f == int(f):
        return str(int(f))
    return "%.2f" % round(f, 2)


def parse_style(style):
    """Parse a draw.io ';'-delimited style string into a dict.

    Bare tokens (e.g. 'rounded') map to '1'. Order is preserved by dict
    insertion (Python 3.7+), which keeps things deterministic.
    """
    out = {}
    if not style:
        return out
    for part in style.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
        else:
            out[part] = "1"
    return out


def html_to_text(value):
    """Decode a draw.io 'value' (may contain HTML) to plain text.

    Converts <br>, </div>, </p> and newlines to line breaks; strips remaining
    tags; unescapes HTML entities. Returns a list of line strings.
    """
    if value is None:
        return []
    s = value
    # Normalise line-break producing tags to a sentinel newline.
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</div>", "\n", s)
    s = re.sub(r"(?i)</p>", "\n", s)
    s = re.sub(r"(?i)<div[^>]*>", "", s)
    s = re.sub(r"(?i)<p[^>]*>", "", s)
    # Strip all remaining tags.
    s = re.sub(r"<[^>]+>", "", s)
    # Unescape entities (&amp; &lt; &#39; ...).
    s = html.unescape(s)
    lines = [ln.strip() for ln in s.split("\n")]
    lines = [ln for ln in lines if ln != ""]
    return lines


def clip_line(text, max_w):
    """Clip a single line to roughly max_w px, adding an ellipsis if cut."""
    if max_w <= 0:
        return text
    max_chars = max(1, int(max_w / CHAR_W))
    if len(text) <= max_chars:
        return text
    if max_chars <= 1:
        return text[:1]
    return text[: max_chars - 1] + "…"


def is_dark(color):
    """Heuristic: is a #rrggbb color dark (so we should use light text)?"""
    if not color or not color.startswith("#") or len(color) not in (7, 4):
        return False
    c = color.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    try:
        r = int(c[0:2], 16)
        g = int(c[2:4], 16)
        b = int(c[4:6], 16)
    except ValueError:
        return False
    # Relative luminance (perceptual-ish).
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return lum < 110


def color_or(value, fallback):
    """Return a usable color from a style value, else the fallback.

    'none' / 'default' / empty -> fallback. We never carry an external ref.
    """
    if not value:
        return fallback
    v = value.strip()
    if v.lower() in ("none", "default", ""):
        return fallback
    return v


# ---------------------------------------------------------------------------
# Model extraction
# ---------------------------------------------------------------------------
class Cell:
    __slots__ = (
        "cid", "parent", "value", "style", "is_vertex", "is_edge",
        "source", "target", "x", "y", "w", "h", "rel_x", "rel_y",
        "ax", "ay", "points",
    )

    def __init__(self):
        self.cid = None
        self.parent = None
        self.value = None
        self.style = {}
        self.is_vertex = False
        self.is_edge = False
        self.source = None
        self.target = None
        self.x = 0.0
        self.y = 0.0
        self.w = 0.0
        self.h = 0.0
        self.rel_x = 0.0   # geometry x as authored (may be relative to parent)
        self.rel_y = 0.0
        self.ax = 0.0      # absolute x (after parent accumulation)
        self.ay = 0.0
        self.points = []   # edge waypoints (absolute) [(x, y), ...]


def _num(v, default=0.0):
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def load_cells(drawio_path):
    """Parse the file and return (ordered list of Cell, id->Cell map).

    Document order is preserved (ElementTree keeps it), giving a stable z-order
    and a stable, deterministic iteration order for rendering.
    """
    tree = ET.parse(drawio_path)
    root = tree.getroot()
    cell_els = root.findall(".//mxCell")

    cells = []
    by_id = {}
    for el in cell_els:
        c = Cell()
        c.cid = el.get("id")
        c.parent = el.get("parent")
        c.value = el.get("value")
        c.style = parse_style(el.get("style", ""))
        c.is_vertex = el.get("vertex") == "1"
        c.is_edge = el.get("edge") == "1"
        c.source = el.get("source")
        c.target = el.get("target")
        geo = el.find("mxGeometry")
        if geo is not None:
            c.rel_x = _num(geo.get("x"))
            c.rel_y = _num(geo.get("y"))
            c.w = _num(geo.get("width"))
            c.h = _num(geo.get("height"))
            arr = geo.find("Array[@as='points']")
            if arr is not None:
                for pt in arr.findall("mxPoint"):
                    c.points.append((_num(pt.get("x")), _num(pt.get("y"))))
        cells.append(c)
        if c.cid is not None:
            by_id[c.cid] = c
    return cells, by_id


def resolve_absolute(cells, by_id):
    """Compute absolute (ax, ay) for every vertex by walking parent chain.

    draw.io child geometry is relative to its parent container's top-left.
    Root cells "0"/"1" have no geometry and act as origin. We memoise to keep
    this O(n) and deterministic.
    """
    memo = {}

    def origin(cid):
        # Returns absolute (x, y) of the top-left of the cell with id cid.
        if cid is None:
            return (0.0, 0.0)
        if cid in memo:
            return memo[cid]
        c = by_id.get(cid)
        if c is None or not c.is_vertex:
            # parent "1"/"0" or an edge container -> origin
            memo[cid] = (0.0, 0.0)
            return memo[cid]
        px, py = origin(c.parent)
        ax = px + c.rel_x
        ay = py + c.rel_y
        memo[cid] = (ax, ay)
        return memo[cid]

    for c in cells:
        if c.is_vertex:
            c.ax, c.ay = origin(c.cid)
            c.x, c.y = c.ax, c.ay


# ---------------------------------------------------------------------------
# Geometry / bbox
# ---------------------------------------------------------------------------
def compute_bbox(cells):
    xs, ys, x2s, y2s = [], [], [], []
    for c in cells:
        if c.is_vertex and (c.w > 0 or c.h > 0):
            xs.append(c.ax)
            ys.append(c.ay)
            x2s.append(c.ax + c.w)
            y2s.append(c.ay + c.h)
    if not xs:
        # Degenerate: nothing to draw.
        return (0.0, 0.0, 100.0, 100.0)
    return (min(xs), min(ys), max(x2s), max(y2s))


def center(c):
    return (c.ax + c.w / 2.0, c.ay + c.h / 2.0)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def _is_table(c):
    return c.style.get("shape") == "table" or c.style.get("childLayout") == "tableLayout"


def _is_table_part(c, by_id):
    """True if this cell is a row/sub-cell inside a table (we render the table
    as one unit, so we skip its internal partialRectangle parts)."""
    # Row/cell parts use shape=partialRectangle; their value text is gathered
    # by the table renderer.
    if c.style.get("shape") == "partialRectangle":
        return True
    return False


def _row_label(row_cell, by_id, children_by_parent):
    """Compose a single readable label from a table row's child cells.

    Columns are ordered by their relative x. Empty cells are skipped; the
    result is a space-joined line like 'PK customer_id UUID NOT NULL'.
    """
    kids = children_by_parent.get(row_cell.cid, [])
    kids_sorted = sorted(kids, key=lambda k: (k.rel_x, k.cid or ""))
    parts = []
    for k in kids_sorted:
        txt = " ".join(html_to_text(k.value))
        if txt:
            parts.append(txt)
    return "  ".join(parts)


def render_table(c, by_id, children_by_parent, dx, dy):
    """Render a draw.io table shape as a box + title + stacked row labels.

    Best-effort: not pixel-perfect draw.io table fidelity, just a readable
    offline preview at the real coordinates.
    """
    out = []
    x = c.ax - dx
    y = c.ay - dy
    fill = color_or(c.style.get("fillColor"), THEME["vertex_fill"])
    stroke = color_or(c.style.get("strokeColor"), THEME["vertex_stroke"])
    title = " ".join(html_to_text(c.value)) or (c.cid or "")
    start_size = _num(c.style.get("startSize"), 30.0)

    # Box.
    out.append(
        '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" ry="%s" '
        'fill="%s" stroke="%s" stroke-width="1"/>'
        % (fmt(x), fmt(y), fmt(c.w), fmt(c.h), fmt(RADIUS), fmt(RADIUS),
           esc(fill), esc(stroke))
    )
    # Title bar separator.
    out.append(
        '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"/>'
        % (fmt(x), fmt(y + start_size), fmt(x + c.w), fmt(y + start_size),
           esc(stroke))
    )
    # Title text (centered).
    tcolor = THEME["text_on_dark"] if is_dark(fill) else THEME["text"]
    out.append(
        '<text x="%s" y="%s" text-anchor="middle" '
        'font-size="%s" font-weight="600" fill="%s">%s</text>'
        % (fmt(x + c.w / 2.0), fmt(y + start_size / 2.0 + TITLE_FONT_SIZE / 3.0),
           fmt(TITLE_FONT_SIZE), esc(tcolor),
           esc(clip_line(title, c.w - 12)))
    )

    # Rows: direct vertex children of the table (shape=partialRectangle rows).
    rows = [
        k for k in children_by_parent.get(c.cid, [])
        if k.is_vertex and k.style.get("shape") == "partialRectangle"
    ]
    rows.sort(key=lambda k: (k.rel_y, k.cid or ""))
    text_color = THEME["text"]
    for r in rows:
        label = _row_label(r, by_id, children_by_parent)
        if not label:
            continue
        ry = c.ay + r.rel_y - dy  # row absolute top
        tx = x + 6
        ty = ry + r.h / 2.0 + FONT_SIZE / 3.0
        out.append(
            '<text x="%s" y="%s" font-size="%s" fill="%s">%s</text>'
            % (fmt(tx), fmt(ty), fmt(FONT_SIZE), esc(text_color),
               esc(clip_line(label, c.w - 12)))
        )
    return out


def render_vertex(c, dx, dy):
    """Render a generic (non-table) vertex as a rounded rect + wrapped label."""
    out = []
    x = c.ax - dx
    y = c.ay - dy
    fill = color_or(c.style.get("fillColor"), THEME["vertex_fill"])
    stroke = color_or(c.style.get("strokeColor"), THEME["vertex_stroke"])
    dashed = c.style.get("dashed") == "1"
    dash_attr = ' stroke-dasharray="4 3"' if dashed else ""

    out.append(
        '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" ry="%s" '
        'fill="%s" stroke="%s" stroke-width="1"%s/>'
        % (fmt(x), fmt(y), fmt(c.w), fmt(c.h), fmt(RADIUS), fmt(RADIUS),
           esc(fill), esc(stroke), dash_attr)
    )

    lines = html_to_text(c.value)
    if not lines:
        return out
    text_color = THEME["text_on_dark"] if is_dark(fill) else THEME["text"]
    # Clip each line to box width; stack centered around vertical middle.
    clipped = [clip_line(ln, c.w - 6) for ln in lines]
    n = len(clipped)
    cx = x + c.w / 2.0
    cy = y + c.h / 2.0
    first_y = cy - (n - 1) * LINE_HEIGHT / 2.0 + FONT_SIZE / 3.0
    for i, ln in enumerate(clipped):
        ty = first_y + i * LINE_HEIGHT
        out.append(
            '<text x="%s" y="%s" text-anchor="middle" '
            'font-size="%s" fill="%s">%s</text>'
            % (fmt(cx), fmt(ty), fmt(FONT_SIZE), esc(text_color), esc(ln))
        )
    return out


def _connect_point(cell, by_id):
    """Absolute center point of an edge endpoint cell.

    Endpoints may be row cells inside a table (e.g. 't1_r1'); their absolute
    geometry is already resolved on the Cell, so center() works uniformly.
    """
    c = by_id.get(cell)
    if c is None:
        return None
    return center(c)


def render_edge(c, by_id, dx, dy):
    out = []
    sp = _connect_point(c.source, by_id)
    tp = _connect_point(c.target, by_id)
    if sp is None or tp is None:
        return out
    stroke = color_or(c.style.get("strokeColor"), THEME["edge_stroke"])
    dashed = c.style.get("dashed") == "1"
    dash_attr = ' stroke-dasharray="5 4"' if dashed else ""

    pts = [sp] + list(c.points) + [tp]
    coords = " ".join("%s,%s" % (fmt(px - dx), fmt(py - dy)) for px, py in pts)
    out.append(
        '<polyline points="%s" fill="none" stroke="%s" stroke-width="1.2"%s/>'
        % (coords, esc(stroke), dash_attr)
    )
    # Edge label at midpoint of the polyline.
    label_lines = html_to_text(c.value)
    if label_lines:
        mx = (sp[0] + tp[0]) / 2.0 - dx
        my = (sp[1] + tp[1]) / 2.0 - dy
        label = " ".join(label_lines)
        # Small white-ish backing via a subtle rect for legibility on edges.
        w = max(8.0, len(label) * CHAR_W + 6)
        out.append(
            '<rect x="%s" y="%s" width="%s" height="%s" rx="3" ry="3" '
            'fill="%s" stroke="%s" stroke-width="0.5" opacity="0.92"/>'
            % (fmt(mx - w / 2.0), fmt(my - 8), fmt(w), fmt(16),
               esc(THEME["vertex_fill"]), esc(stroke))
        )
        out.append(
            '<text x="%s" y="%s" text-anchor="middle" font-size="%s" '
            'fill="%s">%s</text>'
            % (fmt(mx), fmt(my + FONT_SIZE / 3.0), fmt(FONT_SIZE),
               esc(THEME["text"]), esc(label))
        )
    return out


# ---------------------------------------------------------------------------
# Top-level transcode
# ---------------------------------------------------------------------------
def transcode(drawio_path):
    """Transcode a .drawio file into a standalone inline <svg> string."""
    cells, by_id = load_cells(drawio_path)
    resolve_absolute(cells, by_id)

    # Index children by parent for table rendering (document order preserved).
    children_by_parent = {}
    for c in cells:
        if c.parent is not None:
            children_by_parent.setdefault(c.parent, []).append(c)

    minx, miny, maxx, maxy = compute_bbox(cells)
    dx = minx - MARGIN
    dy = miny - MARGIN
    width = (maxx - minx) + 2 * MARGIN
    height = (maxy - miny) + 2 * MARGIN

    body = []

    # 1) Edges first (drawn under vertices) — but skip table-internal edges only
    #    when source/target are missing. Edges connecting table rows are fine.
    edge_body = []
    for c in cells:
        if c.is_edge:
            edge_body.extend(render_edge(c, by_id, dx, dy))

    # 2) Vertices. Tables rendered as a unit; their internal partialRectangle
    #    parts are skipped (gathered by the table renderer). Top-level vertices
    #    (parent "1"/"0" or any non-part) render as rects.
    #    A cell is a "table part" if it is itself a partialRectangle OR its
    #    ancestor chain includes a table (rows + cells live under the table).
    table_ids = {c.cid for c in cells if c.is_vertex and _is_table(c)}

    def under_table(c):
        seen = 0
        pid = c.parent
        while pid is not None and seen < 64:
            if pid in table_ids:
                return True
            p = by_id.get(pid)
            if p is None:
                return False
            pid = p.parent
            seen += 1
        return False

    vertex_body = []
    for c in cells:
        if not c.is_vertex:
            continue
        if c.w <= 0 and c.h <= 0:
            continue
        if _is_table(c):
            vertex_body.extend(
                render_table(c, by_id, children_by_parent, dx, dy)
            )
        elif under_table(c):
            # internal table row/cell — already rendered by render_table
            continue
        else:
            vertex_body.extend(render_vertex(c, dx, dy))

    body = edge_body + vertex_body

    style_block = (
        "<style>text{font-family:%s;}"
        "rect,polyline,line{vector-effect:non-scaling-stroke;}</style>"
        % FONT_STACK
    )

    # NOTE: no xmlns attribute — this SVG is baked INLINE into an HTML console
    # (HTML parsing puts <svg> in the SVG namespace automatically). Emitting the
    # SVG-namespace URI would also trip the hard offline grep for "http://".
    svg = (
        '<svg viewBox="0 0 %s %s" width="%s" height="%s" '
        'font-family="%s" role="img">'
        "%s%s</svg>"
        % (
            fmt(width), fmt(height), fmt(width), fmt(height),
            FONT_STACK, style_block, "".join(body),
        )
    )
    return svg


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Transcode a .drawio file into an offline inline <svg>."
    )
    ap.add_argument("input", help="path to the .drawio file")
    ap.add_argument(
        "-o", "--output",
        help="output .svg path (default: INPUT.svg beside input; '-' = stdout)",
    )
    args = ap.parse_args(argv)

    svg = transcode(args.input)

    out = args.output
    if out is None:
        if args.input.endswith(".drawio"):
            out = args.input[: -len(".drawio")] + ".svg"
        else:
            out = args.input + ".svg"

    if out == "-":
        sys.stdout.write(svg)
        if not svg.endswith("\n"):
            sys.stdout.write("\n")
        return 0

    with open(out, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
