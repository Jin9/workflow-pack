// adapter.js — the anti-corruption layer (ADR-003 extended to live data).
// The sim consumes ONE normalized shape; backend field names stop here. A live
// pack is just a pack whose timeline grows and which carries run status +
// pending gates; a static replay pack (file in public/) flows through the same
// normalize().
import { getPack } from './engine-client.js';

export function normalizePack(p) {
  if (!p || !p.run) return null;
  return {
    runId: p.run.run_id,
    runState: p.run.state,
    mode: p.run.mode,
    requestType: p.run.request_type,
    terminalReason: p.run.terminal_reason,
    workflow: p.run.workflow,
    seq: p.pack_seq,
    rollup: (p.gates && p.gates.rollup) || 'G',
    stages: (p.stages || []).map((s) => ({
      id: s.id, state: s.state, band: s.band, attempts: s.attempts,
      caveat: !!s.caveat, queue: s.queue,
    })),
    pendingGates: ((p.gates && p.gates.pending) || []).map((g) => ({
      stageId: g.stage_id, gate: g.gate, ownerRole: g.owner_role,
      question: g.question, verdicts: g.verdicts || ['approve', 'reject'],
    })),
    board: (p.gates && p.gates.board) || [],
    timeline: p.timeline || [],
  };
}

// Live source: ETag-aware 2s poller. cb(view) fires only when the pack changed.
export function pollPack(runId, cb, ms = 2000) {
  let etag = null;
  let stopped = false;
  async function once() {
    if (stopped) return;
    const res = await getPack(runId, etag);
    if (res && res.data) {
      etag = res.etag;
      cb(normalizePack(res.data));
    } else if (res === null) {
      cb(null); // offline signal
    } // notModified -> nothing
  }
  once();
  const timer = setInterval(once, ms);
  return () => { stopped = true; clearInterval(timer); };
}

// Static source (serverless replay): one fetch of an exported pack file.
export async function staticPack(url = '/pipeline-pack.json') {
  try {
    const r = await fetch(url);
    if (!r.ok) return null;
    return normalizePack(await r.json());
  } catch {
    return null;
  }
}
