'use strict';
/*
 * emit_data.js — evaluate a decoded dashboard DATA module and print its data
 * structures as JSON on stdout. Invoked by extract.py.
 *
 * The DATA module is pure data: it declares the top-level consts
 *   TIER, stages, EVENTS, TEMPLATES, JSON_ONLY, tests, skillmap
 * (no functions). JSON_ONLY is a Set, which JSON.stringify cannot represent,
 * so it is spread into an array here and rebuilt as `new Set([...])` by build.py.
 *
 * Usage: node emit_data.js <path-to-decoded-data-module.js>
 */
const vm = require('vm');
const fs = require('fs');

const src = fs.readFileSync(process.argv[2], 'utf8');
const ctx = {};
vm.createContext(ctx);

// The module runs 3 top-level forEach statements that merge EVENTS / TEMPLATES /
// JSON_ONLY INTO each stage at load time (s.consumes, s.emits, s.sdlc, s.template,
// s.fmt, s.jsonOnly). Those fields are DERIVED — they must not be stored on the
// raw stage in the contract, or editing events/templates would leave a stale copy.
// build.py reproduces the merge, so here we strip the derived keys back off.
const helper =
  '\n;(function(){' +
  '  var derived = new Set(["template","fmt","jsonOnly"]);' +
  '  for (var ev of Object.values(EVENTS)) for (var k of Object.keys(ev)) derived.add(k);' +
  '  var rawStages = stages.map(function(s){' +
  '    var o = {};' +
  '    for (var e of Object.entries(s)) if (!derived.has(e[0])) o[e[0]] = e[1];' +
  '    return o;' +
  '  });' +
  '  globalThis.__OUT__ = JSON.stringify({' +
  '    tier: TIER, stages: rawStages, events: EVENTS, templates: TEMPLATES,' +
  '    json_only: [...JSON_ONLY], tests: tests, skillmap: skillmap' +
  '  }, null, 2);' +
  '})()';
// Completion value of the script is the helper IIFE call (returns undefined),
// so read the result from the context global instead.
const expr = src + helper + '\n;globalThis.__OUT__';

const out = vm.runInContext(expr, ctx, { filename: 'data-module.js' });
process.stdout.write(out);
