// furniture.jsx — tile-aligned 8-bit furniture with REAL collision.
// Each solid piece blocks the tiles under its footprint; desks/tables expose
// walkable seat tiles (with armchairs) where agents sit.
//
// NOTE: this module has IMPORT-TIME SIDE EFFECTS — building it registers wall
// obstacles (setObstacle) and computes the reachable SEATS pool. It must be
// imported before the world is initialized; sim.jsx importing SEATS from here
// guarantees that order.
import React from 'react';
import { COLS, TILE, ROOMS, ROOM_OF, setObstacle, isWalkable } from './map.jsx';

const OUT = '#1d140c';

// ── sprites (fill their .ao-furn box, which is sized to the footprint) ────────
function Desk() {
  return (
    <React.Fragment>
      <div style={{ position: 'absolute', left: '4%', bottom: '6%', right: '4%', height: '44%', background: '#b07e44', border: `2px solid ${OUT}` }}>
        <div style={{ position: 'absolute', left: 0, top: 0, right: 0, height: 3, background: '#cb9a59' }} />
        <div style={{ position: 'absolute', left: '46%', top: 2, bottom: 2, width: 2, background: '#8a5f31' }} />
      </div>
      <div style={{ position: 'absolute', left: '8%', top: '8%', width: '36%', height: '42%', background: '#0d2226', border: `2px solid ${OUT}` }}>
        <div style={{ position: 'absolute', left: 1, top: 1, right: 1, height: 3, background: '#5fc7d4' }} />
        <div style={{ position: 'absolute', left: 1, top: 6, width: '60%', height: 2, background: '#356b72' }} />
      </div>
      <div style={{ position: 'absolute', right: '8%', top: '8%', width: '36%', height: '42%', background: '#0d2226', border: `2px solid ${OUT}` }}>
        <div style={{ position: 'absolute', left: 1, top: 1, right: 1, height: 3, background: '#5fc7d4' }} />
        <div style={{ position: 'absolute', left: 1, top: 6, width: '60%', height: 2, background: '#356b72' }} />
      </div>
    </React.Fragment>
  );
}

function Server() {
  const light = (top, c) => <div style={{ position: 'absolute', right: '14%', top, width: 4, height: 4, background: c, boxShadow: `0 0 4px ${c}` }} />;
  return (
    <div style={{ position: 'absolute', inset: '6% 18%', background: '#262d34', border: `2px solid ${OUT}`, transform: 'translateX(1px)' }}>
      {['16%', '42%', '68%'].map((y) => <div key={y} style={{ position: 'absolute', left: 2, right: 2, top: y, height: '16%', background: '#161b20' }} />)}
      {light('18%', '#6fcf5f')}{light('44%', '#e0b34a')}{light('70%', '#6fcf5f')}
    </div>
  );
}

function Shelf() {
  const books = ['#c75450', '#5d8ad4', '#d9b24a', '#6dbf67', '#c75450'];
  return (
    <div style={{ position: 'absolute', inset: '6% 10%', background: '#6a4a2c', border: `2px solid ${OUT}` }}>
      {['8%', '52%'].map((y) => (
        <div key={y} style={{ position: 'absolute', left: 2, right: 2, top: y, height: '40%', display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          {books.map((c, i) => <div key={i} style={{ flex: 1, height: `${72 + i % 2 * 18}%`, background: c, border: `1px solid ${OUT}` }} />)}
        </div>
      ))}
    </div>
  );
}

function Table() {
  return (
    <div style={{ position: 'absolute', inset: '14%', background: '#c79a5b', border: `2px solid ${OUT}`, borderRadius: 10 }}>
      <div style={{ position: 'absolute', left: 5, top: 4, right: 5, height: 5, background: '#ddb777', borderRadius: 6 }} />
    </div>
  );
}

function Couch() {
  return (
    <div style={{ position: 'absolute', inset: '12% 6%', background: '#2f6f6a', border: `2px solid ${OUT}`, borderRadius: 6 }}>
      <div style={{ position: 'absolute', left: 0, top: 0, right: 0, height: '32%', background: '#3a8079', borderRadius: 5 }} />
      <div style={{ position: 'absolute', left: '6%', bottom: '12%', width: '40%', top: '42%', background: '#3a8079', border: `2px solid ${OUT}` }} />
      <div style={{ position: 'absolute', right: '6%', bottom: '12%', width: '40%', top: '42%', background: '#3a8079', border: `2px solid ${OUT}` }} />
    </div>
  );
}

function Coffee() {
  return (
    <div style={{ position: 'absolute', inset: '8% 26%', background: '#2a2320', border: `2px solid ${OUT}` }}>
      <div style={{ position: 'absolute', left: 2, top: 2, right: 2, height: '22%', background: '#444b50' }} />
      <div style={{ position: 'absolute', left: 4, top: 4, width: 4, height: 4, background: '#c75450', boxShadow: '0 0 3px #c75450' }} />
      <div style={{ position: 'absolute', left: '28%', bottom: 3, width: '44%', height: '24%', background: '#e8e0cf', border: `2px solid ${OUT}` }} />
    </div>
  );
}

function Plant() {
  return (
    <React.Fragment>
      <div style={{ position: 'absolute', left: '14%', top: '4%', width: '72%', height: '56%', background: '#4e8a3c', border: `2px solid ${OUT}`, borderRadius: '50% 50% 45% 45%' }}>
        <div style={{ position: 'absolute', left: '18%', top: '14%', width: '30%', height: '30%', background: '#62a44c', borderRadius: '50%' }} />
      </div>
      <div style={{ position: 'absolute', left: '28%', bottom: '6%', width: '44%', height: '36%', background: '#b5623a', border: `2px solid ${OUT}` }}>
        <div style={{ position: 'absolute', left: 0, top: 0, right: 0, height: 3, background: '#4a2f1c' }} />
      </div>
    </React.Fragment>
  );
}

function Tv() {
  return (
    <div style={{ position: 'absolute', inset: '14% 8%', background: '#15181c', border: `2px solid ${OUT}` }}>
      <div style={{ position: 'absolute', inset: 3, background: '#3a6b8c' }} />
      <div style={{ position: 'absolute', left: 5, top: 5, width: '40%', height: 3, background: '#7fb3d4' }} />
      <div style={{ position: 'absolute', left: 5, top: 12, width: '64%', height: 3, background: '#5a8aa8' }} />
    </div>
  );
}

// Armchair — back sits on the side opposite the facing direction.
function Chair({ facing }) {
  const back = facing === 'up' ? { bottom: '8%', left: '16%', right: '16%', height: '20%' }
    : facing === 'down' ? { top: '8%', left: '16%', right: '16%', height: '20%' }
    : facing === 'left' ? { right: '8%', top: '16%', bottom: '16%', width: '20%' }
    : { left: '8%', top: '16%', bottom: '16%', width: '20%' };
  const armA = (facing === 'up' || facing === 'down') ? { left: '8%', top: '24%', bottom: '24%', width: '12%' } : { top: '8%', left: '24%', right: '24%', height: '12%' };
  const armB = (facing === 'up' || facing === 'down') ? { right: '8%', top: '24%', bottom: '24%', width: '12%' } : { bottom: '8%', left: '24%', right: '24%', height: '12%' };
  return (
    <React.Fragment>
      <div style={{ position: 'absolute', inset: '20%', background: '#4a5666', border: `2px solid ${OUT}`, borderRadius: 4 }} />
      <div style={{ position: 'absolute', ...back, background: '#39414d', border: `2px solid ${OUT}`, borderRadius: 3 }} />
      <div style={{ position: 'absolute', ...armA, background: '#39414d', border: `2px solid ${OUT}`, borderRadius: 2 }} />
      <div style={{ position: 'absolute', ...armB, background: '#39414d', border: `2px solid ${OUT}`, borderRadius: 2 }} />
    </React.Fragment>
  );
}

const SPRITES = { desk: Desk, server: Server, shelf: Shelf, table: Table, couch: Couch, coffee: Coffee, plant: Plant, tv: Tv };

// ── layout ───────────────────────────────────────────────────────────────────
const FURN = [];   // { type, col, row, w, h, solid }
const SEATS = [];  // { col, row, facing, kind }
const solid = (type, col, row, w = 1, h = 1) => FURN.push({ type, col, row, w, h, solid: true });
// Workstation: a 2-tile desk + two armchairs below it, agents face up to the desk.
const work2 = (c, r) => {
  solid('desk', c, r, 2, 1);
  SEATS.push({ col: c, row: r + 1, facing: 'up', kind: 'work' }, { col: c + 1, row: r + 1, facing: 'up', kind: 'work' });
};

// A seat tile with an armchair (no desk) — for table/lounge seating.
const seat = (c, r, facing, kind) => SEATS.push({ col: c, row: r, facing, kind });
// Pod: a desk across the top, agent sits below facing up; the alcove opens downward.
const pod = (c) => { solid('desk', c, 13, 2, 1); seat(c, 14, 'up', 'work'); };

// ── PRIVATE OFFICES — exec desk + shelf + plant ───────────────────────────────
work2(2, 3);  solid('shelf', 6, 2); solid('plant', 6, 7);
work2(10, 3); solid('shelf', 14, 2); solid('plant', 14, 7);
work2(18, 3); solid('shelf', 22, 2); solid('plant', 22, 7);

// ── CONFERENCE — long oval table ringed with chairs + wall monitor ────────────
solid('tv', 31, 1, 2, 1);
solid('table', 28, 3, 8, 3);
[29, 30, 31, 32, 33, 34].forEach((c) => seat(c, 2, 'down', 'meet'));
[29, 30, 31, 32, 33, 34].forEach((c) => seat(c, 6, 'up', 'meet'));
solid('plant', 25, 7); solid('plant', 39, 7);

// ── CAFE HUB — drink machine + two cafe tables ────────────────────────────────
solid('coffee', 41, 2); solid('shelf', 41, 5);
solid('table', 44, 2, 2, 1); seat(44, 3, 'up', 'coffee'); seat(45, 3, 'up', 'coffee');
solid('table', 44, 5, 2, 1); seat(44, 6, 'up', 'coffee'); seat(45, 6, 'up', 'coffee');
solid('plant', 47, 7);

// ── OPEN-PLAN WORKSPACE — two rows of desk clusters ───────────────────────────
[[3, 14], [8, 14], [13, 14], [18, 14]].forEach(([c, r]) => work2(c, r));
[[3, 18], [8, 18], [13, 18], [18, 18]].forEach(([c, r]) => work2(c, r));
solid('plant', 21, 13); solid('plant', 21, 20);

// ── FOCUS PODS — three solo desks ─────────────────────────────────────────────
pod(26); pod(29); pod(32);

// ── SERVER / IT — racks + a monitoring desk ───────────────────────────────────
solid('server', 35, 13); solid('server', 38, 13); solid('server', 40, 13);
work2(36, 14);

// ── LOUNGE / BREAKOUT — couches, coffee table, TV ─────────────────────────────
solid('tv', 43, 13, 2, 1); solid('plant', 48, 13);
solid('couch', 42, 15, 2, 1); seat(42, 16, 'up', 'coffee'); seat(43, 16, 'up', 'coffee');
solid('coffee', 45, 15);
solid('couch', 46, 16, 2, 1); seat(46, 17, 'up', 'coffee'); seat(47, 17, 'up', 'coffee');

// ── STANDUP — round table + three chairs ──────────────────────────────────────
solid('table', 28, 19, 3, 1);
seat(28, 20, 'up', 'meet'); seat(29, 20, 'up', 'meet'); seat(30, 20, 'up', 'meet');

// ── RESTROOMS / PRINT — fixtures only ─────────────────────────────────────────
solid('shelf', 42, 20); solid('shelf', 46, 20);

// ── RECEPTION / LOBBY — desk + waiting area (keep cols 5-6 clear for exit) ─────
solid('desk', 2, 26, 3, 1); seat(3, 27, 'up', 'work');
solid('tv', 11, 26, 2, 1); solid('plant', 13, 25); solid('plant', 1, 33);
solid('couch', 8, 31, 2, 1); seat(8, 32, 'up', 'coffee'); seat(9, 32, 'up', 'coffee');
solid('coffee', 11, 32);

// ── HUDDLE ROOMS — small meeting tables ───────────────────────────────────────
solid('table', 18, 29, 3, 2);
seat(18, 28, 'down', 'meet'); seat(19, 28, 'down', 'meet');
seat(18, 31, 'up', 'meet'); seat(19, 31, 'up', 'meet');
solid('plant', 22, 25);
solid('table', 27, 29, 3, 2);
seat(27, 28, 'down', 'meet'); seat(28, 28, 'down', 'meet');
seat(27, 31, 'up', 'meet'); seat(28, 31, 'up', 'meet');
solid('plant', 32, 25);

// ── SERVER ROOM — rack farm + ops desk ────────────────────────────────────────
[[36, 27], [38, 27], [40, 27], [42, 27], [44, 27],
 [36, 30], [38, 30], [40, 30], [42, 30], [44, 30]].forEach(([c, r]) => solid('server', c, r));
work2(35, 32); solid('plant', 47, 25);

// ── register obstacles (skip door-entry tiles & non-room tiles) ──────────────
const DOOR_ENTRY = new Set();
ROOMS.forEach((rm) => { if (!rm.door) return; const [dc, dr] = rm.door; const er = dr < rm.y0 ? rm.y0 : rm.y1; DOOR_ENTRY.add(`${dc},${er}`); DOOR_ENTRY.add(`${dc + 1},${er}`); });
FURN.forEach((f) => {
  if (!f.solid) return;
  for (let r = f.row; r < f.row + f.h; r++) for (let c = f.col; c < f.col + f.w; c++) {
    if (ROOM_OF[r] && ROOM_OF[r][c] && !DOOR_ENTRY.has(`${c},${r}`)) setObstacle(c, r);
  }
});

// ── keep only seats reachable from the corridor ──────────────────────────────
const REACH = (() => {
  const seen = new Set(); const key = (c, r) => r * COLS + c;
  const q = [{ col: 5, row: 10 }]; seen.add(key(5, 10));
  const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  while (q.length) {
    const cur = q.shift();
    for (const [dc, dr] of dirs) {
      const nc = cur.col + dc, nr = cur.row + dr;
      if (!isWalkable(nc, nr)) continue;
      const k = key(nc, nr); if (seen.has(k)) continue;
      seen.add(k); q.push({ col: nc, row: nr });
    }
  }
  return seen;
})();
const SEATS_OK = SEATS.filter((s) => REACH.has(s.row * COLS + s.col));

// ── renderers ────────────────────────────────────────────────────────────────
const OfficeFurniture = React.memo(function OfficeFurniture() {
  return (
    <React.Fragment>
      {FURN.map((f, i) => {
        const S = SPRITES[f.type];
        return (
          <div key={i} className="ao-furn" style={{ left: f.col * TILE, top: f.row * TILE, width: f.w * TILE, height: f.h * TILE }}>
            <S />
          </div>
        );
      })}
    </React.Fragment>
  );
});

const Chairs = React.memo(function Chairs() {
  return (
    <React.Fragment>
      {SEATS_OK.map((s, i) => (
        <div key={i} className="ao-furn ao-chair" style={{ left: s.col * TILE, top: s.row * TILE, width: TILE, height: TILE }}>
          <Chair facing={s.facing} />
        </div>
      ))}
    </React.Fragment>
  );
});

export { SPRITES, SEATS_OK as SEATS, OfficeFurniture, Chairs };
