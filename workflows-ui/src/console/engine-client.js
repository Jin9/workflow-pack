// engine-client.js — bare fetch wrapper for the local engine API. Knows URLs
// only; every failure resolves to null so the sim loop never sees an exception
// (engine down => the office simply runs autonomously).
const BASE = ''; // same origin: vite dev proxies /api, prod is served by FastAPI

async function call(method, url, body, headers) {
  try {
    const r = await fetch(BASE + url, {
      method,
      headers: body ? { 'Content-Type': 'application/json', ...(headers || {}) } : headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    if (r.status === 304) return { notModified: true };
    if (!r.ok) return { error: (await r.text()).slice(0, 300), status: r.status };
    return { data: await r.json(), etag: r.headers.get('ETag') };
  } catch {
    return null; // offline
  }
}

export const listRuns = () => call('GET', '/api/runs');
export const createRun = (payload) => call('POST', '/api/runs', payload);
export const getPack = (runId, etag) =>
  call('GET', `/api/runs/${runId}/pack`, null, etag ? { 'If-None-Match': etag } : undefined);
export const postVerdict = (runId, stageId, body) =>
  call('POST', `/api/runs/${runId}/gates/${stageId}/verdict`, body);
export const abortRun = (runId) => call('POST', `/api/runs/${runId}/abort`);
