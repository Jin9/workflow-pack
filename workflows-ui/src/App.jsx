// App.jsx — HELL FACTORY TUI dashboard (Pokémon 8-bit terminal aesthetic).
import React, { useRef, useReducer, useEffect, useCallback } from 'react';
import { COLS, ROWS, TILE, isWalkable, isExit, MapLayer } from './map.jsx';
import { STATES, STATE_ORDER, MODES, initWorld, tickWorld, setAgentState, addAgent } from './sim.jsx';
import { OfficeFurniture, Chairs } from './furniture.jsx';
import { NPC, Player, Rugs, Signs } from './avatars.jsx';
import {
  useTweaks, TweaksPanel, TweakSection, TweakSelect, TweakSlider, TweakToggle,
} from './tweaks.jsx';
import ConsoleOverlay from './console/overlay.jsx';

const TWEAK_DEFAULTS = {
  version: 'GOLD',
  speed: 1,
  zoom: 1,
  scanlines: true,
  gridlines: true,
  feed: false,
};

// Cartridge "versions" recolor the frame / titles / focus accents.
const VERSIONS = {
  RED: { frame: '#c75450', title: '#f1d6a8', badge: '#6dbf67' },
  BLUE: { frame: '#5d8ad4', title: '#cfe0f5', badge: '#6dbf67' },
  GOLD: { frame: '#d9b24a', title: '#f1d6a8', badge: '#6dbf67' },
  SILVER: { frame: '#c2c8ce', title: '#e6ebef', badge: '#6dbf67' }
};

// Real wall-clock time from the viewer's machine (HH:MM:SS, 24h).
function machineTime() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const world = useRef(initWorld());
  const [, force] = useReducer((x) => x + 1, 0);
  const tRef = useRef(t);
  tRef.current = t;

  // ── simulation loop ──────────────────────────────────────────────────────
  useEffect(() => {
    let timer;
    const schedule = () => {
      const ms = 320 / (tRef.current.speed || 1);
      timer = setTimeout(() => {
        tickWorld(world.current);
        force();
        schedule();
      }, ms);
    };
    schedule();
    return () => clearTimeout(timer);
  }, []);

  // ── keyboard controls ──────────────────────────────────────────────────────
  const onKey = useCallback((e) => {
    const w = world.current;
    const k = e.key.toLowerCase();
    const moveKeys = { arrowup: 'up', w: 'up', arrowdown: 'down', s: 'down',
      arrowleft: 'left', a: 'left', arrowright: 'right', d: 'right' };

    if (w.terminated) {
      w.terminated = false;w.running = true;
      w.player.col = 6;w.player.row = 33;w.player.facing = 'up';
      force();e.preventDefault();return;
    }
    if (moveKeys[k]) {
      const dir = moveKeys[k];
      const p = w.player;
      const now = performance.now();
      if (now - (p.lastMove || 0) < 160) { e.preventDefault(); return; }
      p.facing = dir;
      const nc = p.col + (dir === 'left' ? -1 : dir === 'right' ? 1 : 0);
      const nr = p.row + (dir === 'up' ? -1 : dir === 'down' ? 1 : 0);
      if (isWalkable(nc, nr)) {
        p.col = nc;p.row = nr;p.lastMove = now;
        if (isExit(nc, nr)) {w.terminated = true;w.running = false;}
      }
      force();e.preventDefault();return;
    }
    if (k === ' ') {w.running = !w.running;force();e.preventDefault();return;}
    if (k === 'tab') {w.selected = (w.selected + 1) % w.agents.length;force();e.preventDefault();return;}
    if (k === 'm') {w.modeIdx = (w.modeIdx + 1) % MODES.length;force();return;}
    if (k === 'n') {addAgent(w);force();return;}
    if (k === 'q') {w.terminated = true;w.running = false;force();return;}
    if (k >= '1' && k <= '4') {setAgentState(w, w.selected, STATE_ORDER[+k - 1]);force();return;}
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onKey]);

  const ver = VERSIONS[t.version] || VERSIONS.GOLD;
  const w = world.current;
  const sel = w.agents[w.selected];

  const rootStyle = {
    '--frame': ver.frame,
    '--title': ver.title,
    '--badge': ver.badge
  };

  return (
    <div className="ao-root" style={rootStyle}>
      <div className="ao-grid">
        <Floor world={w} gridlines={t.gridlines} zoom={t.zoom} />
        <CommandBar world={w} sel={sel} />
      </div>
      {t.scanlines && <div className="ao-scanlines" />}
      {w.terminated && <QuitOverlay />}
      <ConsoleOverlay world={world} force={force} />
      <TweaksUI t={t} setTweak={setTweak} />
    </div>);

}

// ── Floor / map ────────────────────────────────────────────────────────────
function Floor({ world, gridlines, zoom }) {
  const wrapRef = useRef(null);
  const [fit, setFit] = React.useState(1);
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const recalc = () => {
      const pad = 24;
      const sw = (el.clientWidth - pad) / (COLS * TILE);
      const sh = (el.clientHeight - pad) / (ROWS * TILE);
      setFit(Math.max(0.2, Math.min(sw, sh)));
    };
    recalc();
    const ro = new ResizeObserver(recalc);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return (
    <section className="ao-main">
      <span className="ao-paneltitle">HELL FACTORY</span>
      <div className="ao-floorwrap" ref={wrapRef}>
        <div className={'ao-floor' + (gridlines ? '' : ' ao-floor--nogrid')}
        style={{ width: COLS * TILE, height: ROWS * TILE, transform: `scale(${fit * (zoom || 1)})` }}>
          <MapLayer />
          <div className="ao-carpet" style={{ left: 1 * TILE, top: 10 * TILE, width: 47 * TILE, height: 2 * TILE }} />
          <div className="ao-mat" style={{ left: 5 * TILE + 4, top: 34 * TILE + 4, width: 2 * TILE - 8, height: 1 * TILE - 8 }} />
          <Rugs />
          <OfficeFurniture />
          <Chairs />
          <Signs />
          {world.agents.map((a, i) =>
          <NPC key={a.id} a={a} selected={i === world.selected} />
          )}
          <Player p={world.player} />
          <div className="ao-exitsign" style={{ left: 3.4 * TILE, top: 34.3 * TILE }}>▼ ENTRANCE</div>
        </div>
      </div>
    </section>);

}

// ── Sidebar ──────────────────────────────────────────────────────────────────
// NOTE: the final design hides the sidebar (only Floor + CommandBar mount). These
// components are preserved (unused) so the metrics/roster/feed feature isn't lost.
function Sidebar({ world, sel, showFeed }) {
  return (
    <aside className="ao-side">
      <div className="ao-panel ao-panel--agents">
        <span className="ao-paneltitle">AGENTS</span>
        <Roster world={world} />
        <div className="ao-divider" />
        <Metrics world={world} sel={sel} />
      </div>
      {showFeed && <Feed world={world} />}
    </aside>);

}

function Metrics({ world, sel }) {
  const rows = [
  ['RUN', world.running ?
  <span className="ao-badge ao-badge--run">RUNNING</span> :
  <span className="ao-badge ao-badge--pause">PAUSED</span>],
  ['MODE', MODES[world.modeIdx]],
  ['TIME', machineTime()],
  ['AGENTS', String(world.agents.length)],
  ['PROD.', `${world.productivity}%`],
  ['SELECT', sel ? `${sel.name} / ${STATES[sel.state].label}` : '—'],
  ['YOU', `${world.player.col},${world.player.row} · Floor 1`]];

  return (
    <div className="ao-section">
      <div className="ao-subtitle">METRICS</div>
      <div className="ao-metrics">
        {rows.map(([k, v]) =>
        <div className="ao-metric" key={k}>
            <span className="ao-mkey">{k}:</span>
            <span className="ao-mval">{v}</span>
          </div>
        )}
      </div>
    </div>);

}

function Roster({ world }) {
  return (
    <div className="ao-section">
      <div className="ao-subtitle">ROSTER</div>
      <div className="ao-roster">
        {world.agents.map((a, i) => {
          const st = STATES[a.state];
          return (
            <div className={'ao-rrow' + (i === world.selected ? ' ao-rrow--sel' : '')} key={a.id}>
              <span className="ao-rmark">{i === world.selected ? '>' : ' '}</span>
              <span className="ao-rglyph" style={{ color: st.color }}>{a.glyph}</span>
              <span className="ao-rname">{a.name}</span>
              <span className="ao-rrole">{a.role}</span>
              <span className="ao-rstate" style={{ color: st.color }}>{st.label}</span>
            </div>);

        })}
      </div>
    </div>);

}

function Feed({ world }) {
  return (
    <div className="ao-panel ao-panel--feed">
      <span className="ao-paneltitle">FEED</span>
      <div className="ao-feed">
        {world.feed.map((line, i) =>
        <div className="ao-feedline" key={world.feed.length - i} style={{ opacity: Math.max(0.35, 1 - i * 0.07) }}>
            {'> '}{line}
          </div>
        )}
      </div>
    </div>);

}

// ── Command bar ──────────────────────────────────────────────────────────────
function Key({ children }) {return <span className="ao-cbkey">{children}</span>;}
function CommandBar({ world, sel }) {
  return (
    <footer className="ao-cmd">
      <span className={'ao-cbstatus' + (world.running ? '' : ' ao-cbstatus--pause')}>
        {world.running ? 'RUNNING' : 'PAUSED'}
      </span>
      <span className="ao-cbline">
        <span className="ao-cbg ao-cbinfo"><b>AGENTS</b> {world.agents.length}</span>
        <span className="ao-cbg ao-cbinfo"><b>PROD</b> {world.productivity}%</span>
        <span className="ao-cbsep">│</span>
        <span className="ao-cbg"><Key>WASD</Key>MOVE</span>
        <span className="ao-cbg"><Key>SPACE</Key>PAUSE</span>
        <span className="ao-cbg"><Key>Q</Key>QUIT</span>
      </span>
    </footer>);

}

function QuitOverlay() {
  return (
    <div className="ao-quit">
      <div className="ao-quitbox">
        <div className="ao-quittitle">SESSION TERMINATED</div>
        <div className="ao-quitsub">You left the building. The office is offline.</div>
        <div className="ao-quitprompt">▶ PRESS ANY KEY TO RECONNECT</div>
      </div>
    </div>);

}

// ── Tweaks ───────────────────────────────────────────────────────────────────
function TweaksUI({ t, setTweak }) {
  return (
    <TweaksPanel>
      <TweakSection label="Cartridge" />
      <TweakSelect label="Version" value={t.version}
      options={['RED', 'BLUE', 'GOLD', 'SILVER']}
      onChange={(v) => setTweak('version', v)} />
      <TweakSection label="Simulation" />
      <TweakSlider label="Speed" value={t.speed} min={0.25} max={3} step={0.25} unit="×"
      onChange={(v) => setTweak('speed', v)} />
      <TweakSlider label="Zoom" value={t.zoom} min={0.5} max={1.4} step={0.02} unit="×"
      onChange={(v) => setTweak('zoom', v)} />
      <TweakSection label="Display" />
      <TweakToggle label="Floor grid" value={t.gridlines} onChange={(v) => setTweak('gridlines', v)} />
      <TweakToggle label="CRT scanlines" value={t.scanlines} onChange={(v) => setTweak('scanlines', v)} />
    </TweaksPanel>);

}

export default App;
