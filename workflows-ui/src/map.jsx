// map.jsx — HELL FACTORY floor plan, built to the floorplan spec:
// NORTH WING (offices · conference · cafe) → central corridor → MID BAND
// (open-plan + pods · standup · server/it · lounge · service) → SOUTH WING
// (reception · huddles · server room). Tile renderer + walkability helpers.
import React from 'react';

const COLS = 50;
const ROWS = 36;
const TILE = 28;

const W = 0, F = 1, C = 2, D = 3, E = 4;   // wall / room-floor / corridor / door / exit

// Each room: interior rect (inclusive). `door` carves a 2-wide opening in the wall
// onto the adjacent corridor; rooms without a door open directly onto a corridor edge.
const ROOMS = [
  // ── NORTH WING ──────────────────────────────────────────────────────────────
  { id: 'PO1',   label: 'OFFICE 1',   accent: '#c0524e', x0: 1,  y0: 1,  x1: 7,  y1: 8,  door: [3, 9] },
  { id: 'PO2',   label: 'OFFICE 2',   accent: '#c0524e', x0: 9,  y0: 1,  x1: 15, y1: 8,  door: [11, 9] },
  { id: 'PO3',   label: 'OFFICE 3',   accent: '#b0524e', x0: 17, y0: 1,  x1: 23, y1: 8,  door: [19, 9] },
  { id: 'CONF',  label: 'CONFERENCE', accent: '#4f7bb8', x0: 25, y0: 1,  x1: 39, y1: 8,  door: [31, 9] },
  { id: 'CAFE',  label: 'CAFE HUB',   accent: '#d9b24a', x0: 41, y0: 1,  x1: 48, y1: 8,  door: [43, 9] },
  // ── MID BAND ─────────────────────────────────────────────────────────────────
  { id: 'OPEN',  label: 'OPEN-PLAN',  accent: '#5f7464', x0: 1,  y0: 13, x1: 22, y1: 21, door: [10, 12] },
  { id: 'FP1',   label: 'POD',        accent: '#8a6a3e', x0: 26, y0: 13, x1: 27, y1: 15 },
  { id: 'FP2',   label: 'POD',        accent: '#8a6a3e', x0: 29, y0: 13, x1: 30, y1: 15 },
  { id: 'FP3',   label: 'POD',        accent: '#8a6a3e', x0: 32, y0: 13, x1: 33, y1: 15 },
  { id: 'SRVIT', label: 'SERVER/IT',  accent: '#5d8ad4', x0: 35, y0: 13, x1: 40, y1: 15 },
  { id: 'LOUNGE',label: 'LOUNGE',     accent: '#d9b24a', x0: 42, y0: 13, x1: 48, y1: 18 },
  { id: 'SYNC',  label: 'STANDUP',    accent: '#7e5f3a', x0: 26, y0: 18, x1: 32, y1: 21 },
  { id: 'WC',    label: 'RESTROOMS',  accent: '#6f7c86', x0: 42, y0: 20, x1: 44, y1: 21 },
  { id: 'PRINT', label: 'PRINT',      accent: '#74583a', x0: 46, y0: 20, x1: 48, y1: 21 },
  // ── SOUTH WING ───────────────────────────────────────────────────────────────
  { id: 'RECEP', label: 'RECEPTION',  accent: '#c0524e', x0: 1,  y0: 25, x1: 14, y1: 34, door: [6, 24] },
  { id: 'HUD1',  label: 'HUDDLE 1',   accent: '#4f7bb8', x0: 16, y0: 25, x1: 22, y1: 34, door: [18, 24] },
  { id: 'HUD2',  label: 'HUDDLE 2',   accent: '#4f7bb8', x0: 25, y0: 25, x1: 32, y1: 34, door: [28, 24] },
  { id: 'SVR2',  label: 'SERVER RM',  accent: '#5d8ad4', x0: 34, y0: 25, x1: 48, y1: 34, door: [40, 24] },
];
const ROOM_BY_ID = Object.fromEntries(ROOMS.map((r) => [r.id, r]));

// ── build the map ────────────────────────────────────────────────────────────
const MAP = Array.from({ length: ROWS }, () => Array(COLS).fill(W));
const ROOM_OF = Array.from({ length: ROWS }, () => Array(COLS).fill(null));
const ROOM_TILES = {};

const setRange = (r0, r1, c0, c1, v) => {
  for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) MAP[r][c] = v;
};

// Corridors (the circulation network).
setRange(10, 11, 1, 48, C);     // main spine, just below the north wing
setRange(10, 23, 24, 25, C);    // central artery: spine ↓ to south hall
setRange(16, 17, 26, 41, C);    // mid-right sub-hall (pods / server-it / lounge / standup)
setRange(18, 21, 33, 41, C);    // mid-right breakout circulation
setRange(22, 23, 1, 48, C);     // south hall, between mid band and south wing

// Rooms.
ROOMS.forEach((rm) => {
  ROOM_TILES[rm.id] = [];
  for (let r = rm.y0; r <= rm.y1; r++) for (let c = rm.x0; c <= rm.x1; c++) {
    MAP[r][c] = F; ROOM_OF[r][c] = rm.id; ROOM_TILES[rm.id].push({ col: c, row: r });
  }
});

// Doors carve the wall between a room and its corridor.
ROOMS.forEach((rm) => { if (rm.door) { const [dc, dr] = rm.door; MAP[dr][dc] = D; MAP[dr][dc + 1] = D; } });

// Building entrance: double doors in the south wall below reception — walk out to quit.
MAP[35][5] = E; MAP[35][6] = E;

const WALKABLE = [];
for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) if (MAP[r][c] !== W) WALKABLE.push({ col: c, row: r });

// Furniture obstacle layer (populated by furniture.jsx at load).
const OBSTACLE = Array.from({ length: ROWS }, () => Array(COLS).fill(false));
function setObstacle(c, r) { if (c >= 0 && c < COLS && r >= 0 && r < ROWS) OBSTACLE[r][c] = true; }

function isWalkable(c, r) { return c >= 0 && c < COLS && r >= 0 && r < ROWS && MAP[r][c] !== W && !OBSTACLE[r][c]; }
function isExit(c, r) { return c >= 0 && c < COLS && r >= 0 && r < ROWS && MAP[r][c] === E; }
function randTileInRoom(id) {
  const t = ROOM_TILES[id].filter((p) => isWalkable(p.col, p.row));
  if (!t.length) { const rm = ROOM_BY_ID[id]; return { col: rm.x0, row: rm.y0 }; }
  return { ...t[Math.floor(Math.random() * t.length)] };
}
function randWalkable() {
  // bias toward the spine so idlers mill in the main corridor
  if (Math.random() < 0.6) { const r = 10 + (Math.random() < 0.5 ? 0 : 1); return { col: 2 + Math.floor(Math.random() * 46), row: r }; }
  for (let i = 0; i < 30; i++) { const t = WALKABLE[Math.floor(Math.random() * WALKABLE.length)]; if (isWalkable(t.col, t.row)) return { ...t }; }
  return { col: 24, row: 11 };
}

// ── tile renderer (static; memoized so the sim loop never re-renders it) ──────
const MapLayer = React.memo(function MapLayer() {
  const cells = [];
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    const t = MAP[r][c]; const alt = (c + r) % 2 === 1;
    let cls = 't';
    if (t === W) cls += ' t-wall';
    else if (t === E) cls += ' t-exit';
    else if (t === C) cls += ' t-corr' + (alt ? ' alt' : '');
    else if (t === D) cls += ' t-door';
    else cls += ' t-floor' + (alt ? ' alt' : '');
    cells.push(<div key={r * COLS + c} className={cls} />);
  }
  return (
    <div className="ao-mapgrid" style={{
      width: COLS * TILE, height: ROWS * TILE,
      gridTemplateColumns: `repeat(${COLS}, ${TILE}px)`, gridAutoRows: `${TILE}px`,
    }}>{cells}</div>
  );
});

export {
  COLS, ROWS, TILE, MAP, ROOMS, ROOM_BY_ID, ROOM_TILES, ROOM_OF, F,
  isWalkable, isExit, setObstacle, randTileInRoom, randWalkable, MapLayer,
};
