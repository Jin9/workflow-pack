// sim.jsx — simulation: agents path through doorways via BFS, claim seats,
// sit at desks/tables, and emit feed events. Geometry from map.jsx,
// seats from furniture.jsx.
import { COLS, isWalkable, randWalkable } from './map.jsx';
import { SEATS } from './furniture.jsx';

const STATES = {
  WORK:   { key: 'WORK',   label: 'Working', color: '#6dbf67', seatKind: 'work' },
  MEET:   { key: 'MEET',   label: 'Meeting', color: '#5d8ad4', seatKind: 'meet' },
  COFFEE: { key: 'COFFEE', label: 'Coffee',  color: '#dd7b3c', seatKind: 'coffee' },
  IDLE:   { key: 'IDLE',   label: 'Idle',    color: '#8d97a0', seatKind: null },
};
const STATE_ORDER = ['WORK', 'MEET', 'COFFEE', 'IDLE'];
const MODES = ['ROSTER', 'PATROL', 'AUTO'];

const LOOKS = [
  { hair: '#3b2a1d', shirt: '#c75450', skin: '#e8b890' }, // Ada
  { hair: '#1c2233', shirt: '#5d8ad4', skin: '#e0b088' }, // Lin
  { hair: '#5a3320', shirt: '#d9b24a', skin: '#eec79a' }, // Mira
  { hair: '#20242a', shirt: '#6dbf67', skin: '#d6a676' }, // Tao
  { hair: '#6b4a2a', shirt: '#9b6dc4', skin: '#e8b890' },
  { hair: '#2a2a2a', shirt: '#d98c4a', skin: '#e0aa80' },
  { hair: '#3a2a1d', shirt: '#4aada0', skin: '#ecc79a' },
  { hair: '#1d1d1d', shirt: '#c75c8a', skin: '#e8b890' },
  { hair: '#43301c', shirt: '#5fa86a', skin: '#eec79a' }, // Tia
  { hair: '#22324a', shirt: '#c2c8ce', skin: '#e0b088' }, // Mia
];

const NAME_POOL = [
  ['Rex', 'Builder'], ['Nova', 'Analyst'], ['Io', 'Scout'], ['Pip', 'Tester'],
  ['Sol', 'Architect'], ['Kit', 'Writer'], ['Vee', 'Ops'], ['Wren', 'Designer'],
];

const rand = (n) => Math.floor(Math.random() * n);

// Breadth-first path over walkable tiles; returns steps after `start` up to `goal`.
function bfsPath(start, goal) {
  if (start.col === goal.col && start.row === goal.row) return [];
  const key = (c, r) => r * COLS + c;
  const prev = new Map(); prev.set(key(start.col, start.row), null);
  const q = [start]; const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  let found = false;
  while (q.length) {
    const cur = q.shift();
    if (cur.col === goal.col && cur.row === goal.row) { found = true; break; }
    for (const [dc, dr] of dirs) {
      const nc = cur.col + dc, nr = cur.row + dr;
      if (!isWalkable(nc, nr)) continue;
      const k = key(nc, nr);
      if (prev.has(k)) continue;
      prev.set(k, { col: cur.col, row: cur.row });
      q.push({ col: nc, row: nr });
    }
  }
  if (!found) return [];
  const path = []; let cur = goal;
  while (cur && !(cur.col === start.col && cur.row === start.row)) {
    path.unshift(cur); cur = prev.get(key(cur.col, cur.row));
  }
  return path;
}

function buildSeatPool() {
  const pool = { work: [], meet: [], coffee: [] };
  (SEATS || []).forEach((s) => { if (pool[s.kind]) pool[s.kind].push(s); });
  return pool;
}

function releaseSeat(world, a) {
  if (a.seat && world.seatPool[a.seat.kind]) world.seatPool[a.seat.kind].push(a.seat);
  a.seat = null; a.seated = false;
}

// Claim a seat for the agent's current state (or wander if Idle / none free).
function assignSeat(world, a) {
  releaseSeat(world, a);
  const kind = STATES[a.state].seatKind;
  let goal;
  if (kind && world.seatPool[kind] && world.seatPool[kind].length) {
    a.seat = world.seatPool[kind].splice(rand(world.seatPool[kind].length), 1)[0];
    goal = { col: a.seat.col, row: a.seat.row };
  } else {
    a.seat = null;
    goal = randWalkable();
  }
  a.target = goal;
  a.path = bfsPath({ col: a.col, row: a.row }, goal);
  a.arrived = a.col === goal.col && a.row === goal.row;
  a.seated = a.arrived && !!a.seat;
  if (a.seated) a.facing = a.seat.facing;
}

function makeAgent(name, role, stateKey, start, look) {
  return {
    id: name, glyph: name[0].toUpperCase(), name, role, look,
    state: stateKey, col: start.col, row: start.row, facing: 'down',
    seat: null, seated: false,
    target: { col: start.col, row: start.row }, path: [], arrived: true,
    workTimer: 4 + rand(6),
  };
}

function initWorld() {
  const world = {
    agents: [], poolIdx: 0, selected: 0, seatPool: buildSeatPool(),
    player: { col: 6, row: 33, facing: 'up' },
    clock: 3 * 60 + 56, productivity: 88,
    running: true, terminated: false, modeIdx: 0,
    feed: [
      'HELL FACTORY booted: squad is online.',
      'Mia opened the reception desk.',
      'Governance took a seat in a huddle room.',
      'Tia logged into the open-plan floor.',
    ],
  };
  world.agents = [
    makeAgent('Tech Lead', 'Engineering', 'WORK', { col: 6, row: 10 }, LOOKS[0]),
    makeAgent('BA Lead', 'Analysis', 'WORK', { col: 12, row: 11 }, LOOKS[1]),
    makeAgent('QA Lead', 'Quality', 'WORK', { col: 18, row: 10 }, LOOKS[2]),
    makeAgent('Dev Squad', 'Build', 'WORK', { col: 28, row: 11 }, LOOKS[3]),
    makeAgent('Governance', 'Risk', 'MEET', { col: 34, row: 10 }, LOOKS[4]),
    makeAgent('Delivery Ops', 'Delivery', 'MEET', { col: 40, row: 11 }, LOOKS[5]),
    makeAgent('Release Mgr', 'Releases', 'COFFEE', { col: 44, row: 10 }, LOOKS[6]),
    makeAgent('On-Call', 'Support', 'IDLE', { col: 24, row: 14 }, LOOKS[7]),
    makeAgent('Tia', 'Open-Plan', 'WORK', { col: 10, row: 14 }, LOOKS[8]),
    makeAgent('Mia', 'Reception', 'WORK', { col: 4, row: 28 }, LOOKS[9]),
  ];
  world.agents.forEach((a) => assignSeat(world, a));
  return world;
}

function pushFeed(world, msg) { world.feed.unshift(msg); if (world.feed.length > 40) world.feed.pop(); }

function stepAgent(world, a) {
  const tgt = a.target;
  if (a.col === tgt.col && a.row === tgt.row) {
    if (!a.arrived) {
      a.arrived = true;
      if (a.seat) { a.seated = true; a.facing = a.seat.facing; }
      pushFeed(world, `${a.name} arrived at ${STATES[a.state].label}.`);
    }
    a.workTimer -= 1;
    if (a.workTimer <= 0) {
      a.workTimer = 4 + rand(7);
      if (a.state === 'WORK') {
        pushFeed(world, `${a.name} completed a task slice.`);
        world.productivity = Math.min(100, world.productivity + 1);
        if (Math.random() < 0.18) pushFeed(world, 'Wild bug fixed!');
      } else if (a.state === 'MEET' && Math.random() < 0.5) {
        pushFeed(world, `${a.name} shared an update.`);
      } else if (a.state === 'COFFEE' && Math.random() < 0.4) {
        pushFeed(world, `${a.name} refilled their mug.`);
      }
      // Idle agents keep wandering; seated agents stay put.
      if (!a.seat) { a.target = randWalkable(); a.path = bfsPath({ col: a.col, row: a.row }, a.target); a.arrived = false; }
    }
    return;
  }
  if (!a.path || a.path.length === 0) {
    a.path = bfsPath({ col: a.col, row: a.row }, tgt);
    if (a.path.length === 0) { a.target = { col: a.col, row: a.row }; return; }
  }
  const next = a.path.shift();
  const dc = next.col - a.col, dr = next.row - a.row;
  a.facing = dc > 0 ? 'right' : dc < 0 ? 'left' : dr > 0 ? 'down' : 'up';
  a.col = next.col; a.row = next.row;
}

function tickWorld(world) {
  if (!world.running || world.terminated) return;
  world.clock = (world.clock + 3) % (100 * 60);
  world.agents.forEach((a) => stepAgent(world, a));
  const working = world.agents.filter((a) => a.state === 'WORK').length;
  const targetProd = 20 + Math.round(70 * (working / Math.max(1, world.agents.length)));
  const drift = Math.sign(targetProd - world.productivity);
  if (drift !== 0 && Math.random() < 0.6) world.productivity += drift;
  world.productivity = Math.max(0, Math.min(100, world.productivity));
}

function setAgentState(world, idx, stateKey) {
  const a = world.agents[idx];
  if (!a || a.state === stateKey) return;
  a.state = stateKey;
  assignSeat(world, a);
  pushFeed(world, `${a.name} is heading to ${STATES[stateKey].label}.`);
}

function addAgent(world) {
  if (world.agents.length >= 12) return;
  const [name, role] = NAME_POOL[world.poolIdx % NAME_POOL.length];
  world.poolIdx += 1;
  const stateKey = STATE_ORDER[rand(STATE_ORDER.length)];
  const look = LOOKS[(3 + world.poolIdx) % LOOKS.length];
  const a = makeAgent(name, role, stateKey, { col: 24, row: 12 }, look);
  world.agents.push(a);
  assignSeat(world, a);
  pushFeed(world, `${name} joined the floor as ${role}.`);
}

function fmtClock(total) {
  const m = Math.floor(total / 60), s = total % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export {
  STATES, STATE_ORDER, MODES, LOOKS,
  initWorld, tickWorld, setAgentState, addAgent, fmtClock,
  // consumed by console/director.js (live-run choreography); additive, no chain reorder
  bfsPath, pushFeed, releaseSeat,
};
