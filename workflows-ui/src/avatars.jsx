// avatars.jsx — top-down "NPC" person sprites (head + body, facing-aware),
// status pip, name tag, and the player avatar (with cap). Also rugs + room signs.
import React from 'react';
import { TILE, ROOMS } from './map.jsx';
import { STATES } from './sim.jsx';

// Skin face overlay on the head, positioned by facing direction.
function Face({ facing, skin }) {
  const eye = { position: 'absolute', width: 2, height: 2, background: '#15110b' };
  if (facing === 'up') return null;
  if (facing === 'left') {
    return (
      <div style={{ position: 'absolute', left: 0, top: 3, width: 8, bottom: 1, background: skin }}>
        <div style={{ ...eye, left: 1, top: 3 }} />
      </div>
    );
  }
  if (facing === 'right') {
    return (
      <div style={{ position: 'absolute', right: 0, top: 3, width: 8, bottom: 1, background: skin }}>
        <div style={{ ...eye, right: 1, top: 3 }} />
      </div>
    );
  }
  // down
  return (
    <div style={{ position: 'absolute', left: 1, right: 1, bottom: 0, height: 8, background: skin }}>
      <div style={{ ...eye, left: 3, top: 2 }} />
      <div style={{ ...eye, right: 3, top: 2 }} />
    </div>
  );
}

function Person({ look, facing, cap, moving }) {
  const { hair, shirt, skin } = look;
  const pants = look.pants || '#37404b';
  const brim = facing === 'up' ? { top: -2, left: 4, width: 12, height: 4 }
    : facing === 'left' ? { left: -2, top: 5, width: 5, height: 7 }
    : facing === 'right' ? { right: -2, top: 5, width: 5, height: 7 }
    : { top: 8, left: 4, width: 12, height: 4 };
  return (
    <div className={'ao-person' + (moving ? ' ao-person--walk' : '')}>
      <div className="ao-shadow" />
      <div className="ao-legs">
        <div className="ao-leg ao-leg-l" style={{ background: pants }} />
        <div className="ao-leg ao-leg-r" style={{ background: pants }} />
      </div>
      <div className="ao-body" style={{ background: shirt }}>
        <div className="ao-body-collar" style={{ background: skin }} />
      </div>
      <div className="ao-head" style={{ background: hair }}>
        <Face facing={facing} skin={skin} />
      </div>
      {cap && <div className="ao-cap" style={{ background: cap }} />}
      {cap && <div className="ao-cap-brim" style={{ background: cap, ...brim }} />}
    </div>
  );
}

function NPC({ a, selected }) {
  const st = STATES[a.state];
  const moving = a.seat ? !a.seated : !a.arrived;
  return (
    <div className={'ao-npc' + (selected ? ' ao-npc--sel' : '') + (a.seated ? ' ao-npc--sit' : '')}
         style={{ left: a.col * TILE, top: a.row * TILE, width: TILE, height: TILE, zIndex: 20 + a.row }}>
      <span className="ao-npcname" style={selected ? { color: '#fff', background: 'rgba(20,32,42,0.92)' } : null}>{a.name}</span>
      <span className="ao-pip" style={{ background: st.color, boxShadow: `0 0 5px ${st.color}` }} />
      <Person look={a.look} facing={a.facing} moving={moving} />
    </div>
  );
}

const PLAYER_LOOK = { hair: '#2a2018', shirt: '#3f6fb0', skin: '#ecc79a', pants: '#2c3a52' };
function Player({ p }) {
  const moving = (typeof performance !== 'undefined' ? performance.now() : Date.now()) - (p.lastMove || 0) < 160;
  return (
    <div className="ao-player ao-npc" style={{ left: p.col * TILE, top: p.row * TILE, width: TILE, height: TILE, zIndex: 60 + p.row }}>
      <span className="ao-npcname ao-youname">YOU</span>
      <Person look={PLAYER_LOOK} facing={p.facing} cap="#d24a4a" moving={moving} />
    </div>
  );
}

// Accent rug + name sign per room.
function Rugs() {
  return (
    <React.Fragment>
      {ROOMS.map((rm) => {
        const x = (rm.x0 + 0.6) * TILE, y = (rm.y0 + 0.6) * TILE;
        const w = (rm.x1 - rm.x0 - 0.2) * TILE, h = (rm.y1 - rm.y0 - 0.2) * TILE;
        return <div key={rm.id} className="ao-rug" style={{ left: x, top: y, width: w, height: h, background: rm.accent }} />;
      })}
    </React.Fragment>
  );
}

function Signs() {
  return (
    <React.Fragment>
      {ROOMS.map((rm) => (
        <span key={rm.id} className="ao-sign" style={{ left: rm.x0 * TILE + 4, top: rm.y0 * TILE + 3, borderColor: rm.accent }}>{rm.label}</span>
      ))}
    </React.Fragment>
  );
}

export { Person, NPC, Player, Rugs, Signs };
