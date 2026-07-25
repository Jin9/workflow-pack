// overlay.jsx — the pipeline console chrome over the office sim: run picker +
// request form (new-product | fix | enhance), gate-approval inbox, status
// strip, and a live feed (the sim's world.feed, which the director also
// writes). State for FORM INPUTS is React state; run/world state stays on the
// mutable world ref (world.console.*) — world never enters React state.
import React, { useEffect, useRef, useState } from 'react';
import { createRun, listRuns, postVerdict } from './engine-client.js';
import { pollPack } from './adapter.js';
import { applyPack } from './director.js';

const TERMINAL = ['done', 'ship-with-caveats', 'failed', 'hard-fail', 'aborted'];

export default function ConsoleOverlay({ world, force }) {
  const [open, setOpen] = useState(true);
  const [online, setOnline] = useState(false);
  const [runs, setRuns] = useState([]);
  const [runId, setRunId] = useState(null);
  const [view, setView] = useState(null);
  const [approver, setApprover] = useState(localStorage.getItem('hf-approver') || '');
  const [raw, setRaw] = useState('');
  const [requester, setRequester] = useState(localStorage.getItem('hf-requester') || '');
  const [reqType, setReqType] = useState('new-product');
  const [mode, setMode] = useState('replay');
  const [busy, setBusy] = useState(false);
  const runIdRef = useRef(runId);
  runIdRef.current = runId;

  // hotkey C toggles the console (ignored while typing in a field)
  useEffect(() => {
    const onKey = (e) => {
      if (e.key.toLowerCase() !== 'c') return;
      const tag = (e.target && e.target.tagName) || '';
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      setOpen((o) => !o);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  // engine discovery: poll the run list; ONLINE/OFFLINE badge falls out of it
  useEffect(() => {
    let stopped = false;
    const tick = async () => {
      const res = await listRuns();
      if (stopped) return;
      if (res && res.data) {
        setOnline(true);
        setRuns(res.data);
        if (!runIdRef.current && res.data.length) setRunId(res.data[res.data.length - 1].run_id);
      } else {
        setOnline(false);
      }
    };
    tick();
    const t = setInterval(tick, 2500);
    return () => { stopped = true; clearInterval(t); };
  }, []);

  // pack poll for the selected run -> director drives the office
  useEffect(() => {
    if (!runId) return undefined;
    const stop = pollPack(runId, (v) => {
      if (!v) { setOnline(false); return; }
      setOnline(true);
      setView(v);
      applyPack(world.current, v);
      force();
    });
    return stop;
  }, [runId]);

  const submit = async () => {
    if (!raw.trim() || !requester.trim() || busy) return;
    setBusy(true);
    localStorage.setItem('hf-requester', requester);
    const res = await createRun({
      raw_request: raw, requester, request_type: reqType, mode,
      idempotency_key: crypto.randomUUID(),
    });
    setBusy(false);
    if (res && res.data) { setRunId(res.data.run_id); setRaw(''); }
  };

  const verdict = async (g, value) => {
    if (!approver.trim()) return;
    localStorage.setItem('hf-approver', approver);
    await postVerdict(runId, g.stageId, { verdict: value, approver, note: 'console verdict' });
    // truth arrives on the next poll
  };

  if (!open) {
    return <button className="hfc-fab" onClick={() => setOpen(true)}>C▸CONSOLE</button>;
  }

  const stagesDone = view ? view.stages.filter((s) => s.state === 'succeeded').length : 0;
  const feed = (world.current.feed || []).slice(0, 8);

  return (
    <div className="hfc-panel">
      <div className="hfc-head">
        <span className="hfc-title">PIPELINE CONSOLE</span>
        <span className={'hfc-badge ' + (online ? 'hfc-badge--on' : 'hfc-badge--off')}>
          {online ? 'ENGINE ONLINE' : 'ENGINE OFFLINE'}
        </span>
        <button className="hfc-x" onClick={() => setOpen(false)} title="hide (C)">✕</button>
      </div>

      {!online &&
        <div className="hfc-note">No engine at /api — the office runs autonomously.
          Start it with: python3 -m engine serve</div>}

      {online && <>
        <div className="hfc-row">
          <select className="hfc-input hfc-grow" value={runId || ''}
            onChange={(e) => setRunId(e.target.value || null)}>
            <option value="">— select a run —</option>
            {runs.map((r) =>
              <option key={r.run_id} value={r.run_id}>
                {r.run_id} · {r.state} · {r.request_type}
              </option>)}
          </select>
        </div>

        {view &&
          <div className="hfc-status">
            <span className={'hfc-chip hfc-chip--' + view.runState}>{view.runState}</span>
            <span className="hfc-dim">{stagesDone}/{view.stages.length} stages</span>
            <span className={'hfc-rag hfc-rag--' + view.rollup}>{view.rollup}</span>
            <span className="hfc-dim">{view.mode}</span>
            {view.terminalReason && <span className="hfc-dim">{view.terminalReason}</span>}
          </div>}

        {view && view.pendingGates.length > 0 &&
          <div className="hfc-section">
            <div className="hfc-subtitle">⏸ GATE INBOX ({view.pendingGates.length})</div>
            <input className="hfc-input" placeholder="your name (named approver)"
              value={approver} onChange={(e) => setApprover(e.target.value)} />
            {view.pendingGates.map((g) =>
              <div className="hfc-gate" key={g.stageId}>
                <div className="hfc-gateq">{g.question}</div>
                <div className="hfc-gaterow">
                  {g.verdicts.map((v) =>
                    <button key={v} className="hfc-btn" disabled={!approver.trim()}
                      onClick={() => verdict(g, v)}>{v}</button>)}
                </div>
              </div>)}
          </div>}

        <div className="hfc-section">
          <div className="hfc-subtitle">NEW REQUEST</div>
          <textarea className="hfc-input hfc-ta" rows={3} value={raw}
            placeholder="raw requirement…" onChange={(e) => setRaw(e.target.value)} />
          <div className="hfc-row">
            <input className="hfc-input hfc-grow" placeholder="requester"
              value={requester} onChange={(e) => setRequester(e.target.value)} />
          </div>
          <div className="hfc-row">
            {['new-product', 'fix', 'enhance'].map((t) =>
              <label key={t} className="hfc-radio">
                <input type="radio" checked={reqType === t} onChange={() => setReqType(t)} />{t}
              </label>)}
          </div>
          <div className="hfc-row">
            {['replay', 'live'].map((m) =>
              <label key={m} className="hfc-radio">
                <input type="radio" checked={mode === m} onChange={() => setMode(m)} />{m}
              </label>)}
            <button className="hfc-btn hfc-btn--go" disabled={busy || !raw.trim() || !requester.trim()}
              onClick={submit}>{busy ? '…' : 'RUN ▶'}</button>
          </div>
        </div>

        <div className="hfc-section">
          <div className="hfc-subtitle">FEED</div>
          {feed.map((line, i) =>
            <div className="hfc-feedline" key={i} style={{ opacity: Math.max(0.4, 1 - i * 0.08) }}>
              {'> '}{line}
            </div>)}
        </div>
      </>}
    </div>
  );
}
