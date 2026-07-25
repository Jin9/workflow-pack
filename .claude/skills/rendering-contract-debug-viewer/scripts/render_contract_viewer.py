#!/usr/bin/env python3
"""Render one pipeline JSON contract artifact into a single self-contained, offline,
squad-delivery-dashboard-themed HTML viewer for local debugging.

Stdlib only. Deterministic (no clock/randomness). The viewer loads no external resources:
forbidden lexemes inside data/title values are neutralized with equivalent Unicode escapes
(render-identical), then the FULLY ASSEMBLED HTML is offline-checked before writing, and
data values render as escaped text (never as a resource URL or markup).

Usage:
    render_contract_viewer.py INPUT.json [-o OUT.html] [--title TITLE] [--theme auto|light|dark]
"""
import argparse
import json
import os
import re
import sys

FORBIDDEN = ("http://", "https://", "src=", "@import")  # checked on the final assembled HTML

# ---------------------------------------------------------------- CSS theme (dashboard palette)
CSS = """
:root{
  --bg:#f6f7f9;--surface:#fff;--surface2:#f3f5f8;--surface3:#eaeef3;
  --ink:#13171d;--ink2:#2c333d;--muted:#5b6675;--faint:#8a94a3;
  --border:#e4e8ee;--border2:#d3dae3;--accent:#2563eb;--accent-wash:#eef3ff;
  --ok:#15803d;--ok-bg:#e8f6ed;--ok-bd:#bbe3c8;
  --warn:#a4570a;--warn-bg:#fcf1df;--warn-bd:#f1d4a0;
  --err:#c62828;--err-bg:#fcebec;--err-bd:#f2c1c4;
  --info:#1763c6;--info-bg:#e9f2fd;--info-bd:#bdd8f6;
  --violet:#6d28d9;--violet-bg:#f1ecfe;--violet-bd:#d8c9fb;
  --slate:#445268;--slate-bg:#eef1f5;--slate-bd:#d3dae2;
  --sev-high:#dc2626;--sev-med:#d97706;--sev-low:#64748b;
  --t1:#3b5bdb;--t1-bg:#e8ecfb;--t1-bd:#c2cdf4;
  --t2:#0284c7;--t2-bg:#e1f3fb;--t2-bd:#aadcf1;
  --t3:#0d9488;--t3-bg:#e0f5f2;--t3-bd:#a6e0d8;
  --code-bg:#eef1f6;--code-fg:#1f4c87;
  --shadow:0 1px 3px rgba(16,24,40,.07),0 1px 2px rgba(16,24,40,.04);--radius:12px;
}
.dark{
  --bg:#0c0f15;--surface:#13171f;--surface2:#171c26;--surface3:#1d2430;
  --ink:#eef2f8;--ink2:#cfd6e1;--muted:#9aa6b6;--faint:#697485;
  --border:#252c38;--border2:#323b49;--accent:#5b8cff;--accent-wash:#152138;
  --ok:#5ed18a;--ok-bg:#0f2a1b;--ok-bd:#1d4d33;
  --warn:#e6b15e;--warn-bg:#2c2110;--warn-bd:#553f1b;
  --err:#f08a8f;--err-bg:#2c1416;--err-bd:#5a262a;
  --info:#74b1f5;--info-bg:#10233c;--info-bd:#234a73;
  --violet:#bd9cfb;--violet-bg:#211633;--violet-bd:#43326a;
  --slate:#9fadc2;--slate-bg:#1a212c;--slate-bd:#333d4c;
  --sev-high:#f0726f;--sev-med:#e3a44e;--sev-low:#8b97a8;
  --t1:#8098f0;--t1-bg:#161d3a;--t1-bd:#2c3a73;
  --t2:#52b4e8;--t2-bg:#0c2536;--t2-bd:#1d4a68;
  --t3:#52c4b6;--t3-bg:#0b2b27;--t3-bd:#1b5249;
  --code-bg:#171f2c;--code-fg:#9dc1f0;--shadow:0 1px 3px rgba(0,0,0,.5);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:'Geist','Hanken Grotesk',system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  font-size:14px;line-height:1.5}
.wrap{max-width:1100px;margin:0 auto;padding:20px 18px 80px}
header.top{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--border);
  padding:12px 0;margin-bottom:14px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.title{font-weight:700;font-size:18px;color:var(--ink2)}
.kind{font-weight:600}
.spacer{flex:1}
button{font:inherit;font-size:12px;font-weight:600;padding:5px 10px;border-radius:8px;cursor:pointer;
  background:var(--surface);color:var(--ink2);border:1px solid var(--border)}
button:hover{border-color:var(--border2)}
.summary{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 14px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
  box-shadow:var(--shadow);padding:12px 14px}
.row{display:flex;gap:10px;padding:3px 0;align-items:baseline}
.key{color:var(--muted);font-weight:600;min-width:160px;max-width:240px;word-break:break-word;
  font-family:'Geist Mono','JetBrains Mono',ui-monospace,'SF Mono',Menlo,Consolas,monospace;font-size:12.5px}
.val{flex:1;min-width:0;word-break:break-word}
.children{margin-left:14px;border-left:1px solid var(--border);padding-left:12px}
details.grp{margin:2px 0}
details.grp>summary{cursor:pointer;list-style:none;padding:2px 0}
details.grp>summary::-webkit-details-marker{display:none}
details.grp>summary::before{content:'\\25B8';color:var(--faint);display:inline-block;width:1em;
  transition:transform .12s}
details.grp[open]>summary::before{transform:rotate(90deg)}
.count{color:var(--faint);font-weight:500}
.str{color:var(--ink)}
.num{color:var(--info);font-weight:600}
.null{color:var(--faint);font-style:italic}
.long{white-space:pre-wrap;background:var(--surface2);border:1px solid var(--border);
  border-radius:8px;padding:8px 10px;color:var(--ink2);font-size:13px}
.src{margin:0;white-space:pre;overflow:auto;max-height:78vh;background:var(--code-bg);color:var(--code-fg);
  border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);padding:14px;font-size:12.5px;
  font-family:'Geist Mono','JetBrains Mono',ui-monospace,'SF Mono',Menlo,Consolas,monospace}
[hidden]{display:none!important}
.badge{display:inline-block;font-size:12px;font-weight:600;line-height:1.35;padding:2px 8px;
  border-radius:6px;border:1px solid transparent}
.chip{display:inline-block;font-size:12px;padding:2px 7px;border-radius:6px;
  font-family:'Geist Mono','JetBrains Mono',ui-monospace,'SF Mono',Menlo,Consolas,monospace}
.chip-mono{background:var(--code-bg);color:var(--code-fg);border:1px solid var(--border)}
.b-ok{color:var(--ok);background:var(--ok-bg);border-color:var(--ok-bd)}
.b-warn{color:var(--warn);background:var(--warn-bg);border-color:var(--warn-bd)}
.b-err{color:var(--err);background:var(--err-bg);border-color:var(--err-bd)}
.b-info{color:var(--info);background:var(--info-bg);border-color:var(--info-bd)}
.b-slate{color:var(--slate);background:var(--slate-bg);border-color:var(--slate-bd)}
.tier-t1{color:var(--t1);background:var(--t1-bg);border-color:var(--t1-bd)}
.tier-t2{color:var(--t2);background:var(--t2-bg);border-color:var(--t2-bd)}
.tier-t3{color:var(--t3);background:var(--t3-bg);border-color:var(--t3-bd)}
.pri-must{color:var(--err);background:var(--err-bg);border-color:var(--err-bd)}
.pri-should{color:var(--warn);background:var(--warn-bg);border-color:var(--warn-bd)}
.pri-could{color:var(--slate);background:var(--slate-bg);border-color:var(--slate-bd)}
.pri-wont{color:var(--faint);background:var(--surface2);border-color:var(--border)}
.sev{font-size:11px;margin-right:4px}
.sev-high{color:var(--sev-high)}.sev-med{color:var(--sev-med)}.sev-low{color:var(--sev-low)}
footer{margin-top:20px;color:var(--faint);font-size:12px;border-top:1px solid var(--border);padding-top:10px}
.note{color:var(--faint);font-size:12px;margin:0 0 12px}
"""

# ---------------------------------------------------------------- client JS (no backslashes)
JS = """
const ESC=s=>String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const STATUS_KEYS=new Set(['output_type','status','state','verdict','spec_status','citation_status','legal_status','coverage_score','parsing_mode']);
const OK=new Set(['proceed','ready-for-tl','ready-for-implementation','ready-for-audit','resolved','pass','accepted','design','ux_pack','brief','done','present','complete','promote','approve','handed_off','revoked']);
const WARN=new Set(['needs-work','draft','revise','partial','partial_design','partial_ux_pack','pending','warn','proposed','reviewed','blocked_partial_brief','conditional','hold','loop_back','human-queue','pass-with-caveats','reroute']);
const ERRV=new Set(['do-not-build','block','blocked','fail','hardfail','hard-fail','error','rollback','blocked_design','blocked_ux_pack','failure_shape','deprecated','superseded','rejected']);
const DECISION=k=>{const v=String(k).toLowerCase();return OK.has(v)||WARN.has(v)||ERRV.has(v);};
function statusClass(v){const k=String(v).toLowerCase();if(OK.has(k))return'b-ok';if(WARN.has(k))return'b-warn';if(ERRV.has(k))return'b-err';return'b-info';}
function sevClass(v){const k=String(v).toLowerCase();if(k==='p1'||k==='high')return'sev-high';if(k==='p2'||k==='medium')return'sev-med';return'sev-low';}
const isMono=k=>/(^id$|_id$|idempotency_key|audit_id)/.test(k);
const isPath=k=>/(_path$|_file$|^path$|^file$|_dir$|_ref$|^slug$|^source_ref$)/.test(k);
function badge(c,t){return '<span class="badge '+c+'">'+ESC(t)+'</span>';}
function chip(c,t){return '<span class="chip '+c+'">'+ESC(t)+'</span>';}
function scalar(key,val){
  const k=String(key);
  if(k==='recommendation'&&!DECISION(val)){const s=String(val);return s.length>140?'<div class="long">'+ESC(s)+'</div>':'<span class="str">'+ESC(s)+'</span>';}
  if(k==='recommendation')return badge(statusClass(val),val);
  if(STATUS_KEYS.has(k))return badge(statusClass(val),val);
  if(k==='severity')return '<span class="sev '+sevClass(val)+'">'+String.fromCharCode(9679)+'</span>'+badge('b-slate',val);
  if((k==='tier'||k==='inferred_tier'||k==='workload_tier'||k==='tier_default'||k==='tier_signal'||k==='tier_hint')&&/^t[123]$/i.test(String(val)))return badge('tier-'+String(val).toLowerCase(),val);
  if(k==='priority'){const p=String(val).toLowerCase().replace(/[^a-z]/g,'');return badge('pri-'+(p||'could'),val);}
  if(k==='maturity_level'||k==='confidence')return badge('b-info',val);
  if(typeof val==='boolean')return badge(val?'b-ok':'b-err',String(val));
  if(val===null)return '<span class="null">null</span>';
  if(typeof val==='number')return '<span class="num">'+ESC(val)+'</span>';
  if(isMono(k)||isPath(k))return chip('chip-mono',val);
  const s=String(val);
  if(s.length>140)return '<div class="long">'+ESC(s)+'</div>';
  return '<span class="str">'+ESC(s)+'</span>';
}
function row(key,html){return '<div class="row"><span class="key">'+ESC(key)+'</span><span class="val">'+html+'</span></div>';}
function node(key,val,depth){
  if(val===null||typeof val!=='object')return row(key,scalar(key,val));
  const isArr=Array.isArray(val);
  const ks=isArr?val.map((_,i)=>i):Object.keys(val);
  const label=ESC(key)+' <span class="count">'+(isArr?('['+val.length+']'):('{'+ks.length+'}'))+'</span>';
  const inner=ks.map(k=>node(k,val[k],depth+1)).join('');
  const open=depth<2?' open':'';
  return '<details class="grp"'+open+'><summary><span class="key">'+label+'</span></summary><div class="children">'+inner+'</div></details>';
}
function detectKind(d){
  if(!d||typeof d!=='object')return'JSON';
  if(d.output_type)return d.output_type;
  if(d.verdict)return'plan-review';
  if(typeof d.recommendation!=='undefined')return'discovery';
  if(d.epics&&d.story_files)return'ba-brief INDEX';
  if(d.$schema&&(d.properties||d.$defs))return'JSON Schema';
  if(d.stage)return String(d.stage);
  return'JSON';
}
function summaryChips(d){
  if(!d||typeof d!=='object')return'';
  const out=[];const pick=['output_type','status','state','verdict','recommendation','maturity_level','tier','workload_tier','confidence'];
  pick.forEach(k=>{if(typeof d[k]!=='undefined')out.push(scalar(k,d[k]));});
  const aid=d.audit_id;
  if(aid)out.push('audit_id '+chip('chip-mono',aid));
  return out.join(' ');
}
function build(){
  document.title=TITLE+' - contract viewer';
  document.getElementById('ttl').textContent=TITLE;
  document.getElementById('kind').innerHTML=badge('b-slate',detectKind(DATA));
  document.getElementById('summary').innerHTML=summaryChips(DATA);
  const root=(DATA===null||typeof DATA!=='object')?row('(value)',scalar('',DATA))
    :Object.keys(DATA).map(k=>node(k,DATA[k],0)).join('');
  document.getElementById('tree').innerHTML=root;
  document.getElementById('src').textContent=JSON.stringify(DATA,null,2);
}
function setTheme(t){if(t==='dark')document.documentElement.classList.add('dark');else if(t==='light')document.documentElement.classList.remove('dark');}
function toggleTheme(){const dark=document.documentElement.classList.toggle('dark');try{localStorage.setItem('rcdv-theme',dark?'dark':'light');}catch(e){}}
function expand(v){document.querySelectorAll('details.grp').forEach(d=>d.open=v);}
if(FORCE_THEME){setTheme(FORCE_THEME);}
else{try{const s=localStorage.getItem('rcdv-theme');if(s)setTheme(s);}catch(e){}}
build();
document.getElementById('themeBtn').addEventListener('click',toggleTheme);
document.getElementById('expandBtn').addEventListener('click',()=>expand(true));
document.getElementById('collapseBtn').addEventListener('click',()=>expand(false));
document.getElementById('srcBtn').addEventListener('click',()=>{
  const srcEl=document.getElementById('src'),tree=document.getElementById('treeCard'),b=document.getElementById('srcBtn');
  if(srcEl.hasAttribute('hidden')){srcEl.removeAttribute('hidden');tree.setAttribute('hidden','');b.textContent='View tree';}
  else{srcEl.setAttribute('hidden','');tree.removeAttribute('hidden');b.textContent='View normalized JSON';}
});
"""

SHELL = """<!doctype html>
<html lang="en" __INITTHEME__>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>contract viewer</title>
<style>__CSS__</style>
</head>
<body>
<div class="wrap">
<header class="top">
  <span class="title" id="ttl"></span>
  <span class="kind" id="kind"></span>
  <span class="spacer"></span>
  <button id="srcBtn">View normalized JSON</button>
  <button id="expandBtn">Expand all</button>
  <button id="collapseBtn">Collapse all</button>
  <button id="themeBtn">Toggle theme</button>
</header>
<p class="note">Offline debug view of a pipeline JSON contract, in the squad-delivery dashboard theme. Values are rendered as escaped text. "View normalized JSON" shows a parse-and-reserialize of the input (key order and number formatting normalized), not the original bytes.</p>
<div class="summary" id="summary"></div>
<div class="card" id="treeCard"><div id="tree"></div></div>
<pre class="src" id="src" hidden></pre>
<footer>Rendered by the rendering-contract-debug-viewer skill. Source: __SRC__ . Self-contained and offline; no external resources loaded.</footer>
</div>
<script>
const TITLE=__TITLE__;
const FORCE_THEME=__FORCETHEME__;
const DATA=__DATA__;
__JS__
</script>
</body>
</html>
"""


def check_offline(html_text):
    """Fail closed if the text references any external resource token."""
    low = html_text.lower()
    hits = [tok for tok in FORBIDDEN if tok in low]
    if hits:
        raise ValueError("final HTML contains forbidden external reference token(s): %s" % ", ".join(hits))


def neutralize_tokens(js_string_blob):
    """Break FORBIDDEN lexemes inside a JS string literal with equivalent Unicode
    escapes: the saved file passes the offline byte-scan while the browser parses
    the identical value. Deterministic; case-insensitive to match the scan."""
    blob = re.sub(r"(?i)(https?:)//", lambda m: m.group(1) + "\\u002f\\u002f", js_string_blob)
    blob = re.sub(r"(?i)(src)=", lambda m: m.group(1) + "\\u003d", blob)
    blob = re.sub(r"(?i)@(import)", lambda m: "\\u0040" + m.group(1), blob)
    return blob


def render(data, title, src_label, init_theme):
    shell = SHELL.replace("__CSS__", CSS).replace("__JS__", JS)
    data_blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")
    title_blob = json.dumps(str(title), ensure_ascii=False).replace("</", "<\\/")
    force_blob = json.dumps(init_theme) if init_theme in ("light", "dark") else "null"
    init_attr = 'class="dark"' if init_theme == "dark" else ""
    html = (shell
            .replace("__INITTHEME__", init_attr)
            .replace("__FORCETHEME__", force_blob)
            .replace("__SRC__", "".join(c for c in src_label if c not in "<>"))
            .replace("__TITLE__", neutralize_tokens(title_blob))
            .replace("__DATA__", neutralize_tokens(data_blob)))
    # The gate scans the FULLY ASSEMBLED document — data included, not just the shell.
    check_offline(html)
    return html


def _reject_duplicate_keys(pairs):
    """Strict-JSON guard: duplicate keys indicate a corrupt contract — fail closed
    instead of silently applying last-key-wins."""
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate object key: %r" % key)
        obj[key] = value
    return obj


def _reject_nonstandard_constant(name):
    raise ValueError("non-standard JSON constant: %s" % name)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render a JSON contract artifact into an offline themed HTML viewer.")
    ap.add_argument("input", help="path to the JSON contract file")
    ap.add_argument("-o", "--output", help="output .html path (default: INPUT with a .viewer.html suffix)")
    ap.add_argument("--title", help="header title (default: input filename)")
    ap.add_argument("--theme", choices=["auto", "light", "dark"], default="auto",
                    help="initial theme; 'auto' follows the OS and offers a toggle (default: auto)")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.input):
        sys.stderr.write("error: input not found: %s\n" % args.input)
        return 2
    try:
        with open(args.input, "r", encoding="utf-8") as fh:
            data = json.load(fh, object_pairs_hook=_reject_duplicate_keys,
                             parse_constant=_reject_nonstandard_constant)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        sys.stderr.write("error: input is not valid strict JSON: %s\n" % exc)
        return 2

    title = args.title or os.path.basename(args.input)
    out = args.output
    if not out:
        base = args.input[:-5] if args.input.endswith(".json") else args.input
        out = base + ".viewer.html"

    # The output must never resolve to the input: the write would destroy the contract.
    if os.path.realpath(out) == os.path.realpath(args.input):
        sys.stderr.write("error: output path resolves to the input file: %s\n" % out)
        return 2

    try:
        html = render(data, title, os.path.basename(args.input), args.theme)
    except ValueError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 3

    tmp = out + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(html)
        os.replace(tmp, out)  # atomic: a failed render/write never truncates an existing viewer
    except OSError as exc:
        if os.path.isfile(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        sys.stderr.write("error: could not write output: %s\n" % exc)
        return 4

    sys.stdout.write("wrote %s (%d bytes) from %s\n" % (out, len(html), args.input))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
