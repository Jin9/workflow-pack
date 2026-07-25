// director.js — pure world mutators: a normalized pack delta drives the office.
// Active stages walk their mapped agent to the mapped room; a pending gate
// parks the approver persona in CONFERENCE; timeline events become feed lines.
// Directed agents carry `directorPost`; when a run releases them (or the
// engine goes offline and applyPack stops being called) the autonomous sim
// takes back over untouched.
import { ROOM_OF, randTileInRoom } from '../map.jsx';
import { bfsPath, pushFeed, releaseSeat } from '../sim.jsx';

// stage id -> [agent name, room id]; every T-gate not listed runs at SERVER/IT.
const POST = {
  intake: ['Mia', 'RECEP'],
  's1-discovery': ['BA Lead', 'PO1'],
  'ba-research': ['BA Lead', 'PO1'],
  'ux-intake': ['Tia', 'HUD1'],
  'tl-design': ['Tech Lead', 'PO2'],
  'plan-review': ['Governance', 'CONF'],
  'contract-design': ['Tech Lead', 'FP2'],
  'backend-implement': ['Dev Squad', 'OPEN'],
  'backend-review': ['Tech Lead', 'OPEN'],
  'frontend-implement': ['Tia', 'OPEN'],
  'frontend-review': ['Tech Lead', 'OPEN'],
  'qa-plan': ['QA Lead', 'PO3'],
  'qa-validate': ['QA Lead', 'PO3'],
  'release-handoff': ['Release Mgr', 'SVR2'],
  'prod-validate': ['On-Call', 'SRVIT'],
  'adversarial-pentest': ['Governance', 'SVR2'],
};
const TEST_POST = ['On-Call', 'SRVIT'];

const APPROVER_AGENT = {
  'ba-lead': 'BA Lead', 'tech-lead': 'Tech Lead', 'qa-lead': 'QA Lead',
  'release-manager': 'Release Mgr', governance: 'Governance',
  'on-call': 'On-Call', 'delivery-ops': 'Delivery Ops',
};

function feedLine(e) {
  const s = e.stage;
  switch (e.kind) {
    case 'run.created': return `RUN ${e.run_id} created (${e.request_type || 'new-product'}, ${e.mode})`;
    case 'stage.started': return `${s} started (${e.executor}${e.model ? ':' + e.model : ''})`;
    case 'stage.executed': return `${s} ✓ contract validated`;
    case 'stage.caveat': return `${s} passed with caveat (${e.verdict})`;
    case 'gate.opened': return `⏸ GATE ${s} awaits ${e.owner_role || 'a human'}`;
    case 'gate.verdict': return `🔒 ${s}: ${e.verdict} — ${e.approver}`;
    case 'stage.failed': return `✗ ${s}: ${String(e.error || '').slice(0, 64)}`;
    case 'stage.retry-scheduled': return `${s} retrying (attempt ${e.next_attempt})`;
    case 'stage.loop-back': return `${s} loops back to ${e.loop_to}`;
    case 'stage.human-queued': return `${s} → human queue ${e.queue}`;
    case 'compensation.triggered': return `SAGA: ${e.action} triggered (${s})`;
    case 'compensation.simulated': return `SAGA: revoke recorded (replay)`;
    case 'run.finished': return `RUN ${e.state}${e.reason ? ' — ' + e.reason : ''}`;
    default: return null;
  }
}

function direct(world, a, room, why, meet) {
  releaseSeat(world, a);
  a.state = meet ? 'MEET' : 'WORK';
  a.target = randTileInRoom(room);
  a.path = bfsPath({ col: a.col, row: a.row }, a.target);
  a.arrived = false;
  if (a.directorPost !== room) pushFeed(world, `${a.name} → ${room} (${why})`);
  a.directorPost = room;
}

export function applyPack(world, view) {
  if (!view) return;
  const con = world.console || (world.console = { feedSeen: -1 });
  con.view = view;

  for (const e of view.timeline) {
    if (e.seq <= con.feedSeen) continue;
    const line = feedLine(e);
    if (line) pushFeed(world, line);
    con.feedSeen = e.seq;
  }

  const terminal = ['done', 'ship-with-caveats', 'failed', 'hard-fail', 'aborted']
    .includes(view.runState);

  const desired = new Map(); // agent name -> {room, why, meet}
  if (!terminal) {
    for (const s of view.stages) {
      if (s.state === 'running' || s.state === 'validating') {
        const [agent, room] = POST[s.id] || TEST_POST;
        if (!desired.has(agent)) desired.set(agent, { room, why: s.id, meet: false });
      }
    }
    for (const g of view.pendingGates) {
      const agent = APPROVER_AGENT[g.ownerRole] || 'Governance';
      desired.set(agent, { room: 'CONF', why: `${g.stageId} gate`, meet: true });
    }
  }

  for (const a of world.agents) {
    const want = desired.get(a.name);
    if (want) {
      const inRoom = ROOM_OF[a.row] && ROOM_OF[a.row][a.col] === want.room;
      if (a.directorPost !== want.room || (a.arrived && !inRoom)) {
        direct(world, a, want.room, want.why, want.meet); // also herds wanderers back
      }
    } else if (a.directorPost) {
      a.directorPost = null; // released — autonomous behavior resumes naturally
    }
  }
}
