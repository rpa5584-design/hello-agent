const BASE = '/api/assignment3/sessions'
async function json(url, options = {}) {
  const response = await fetch(url, { ...options, signal: AbortSignal.timeout(5000), headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error('Session storage is unavailable.')
  return response.json()
}
export const sessionApi = {
  create: (body) => json(BASE, { method: 'POST', body: JSON.stringify(body) }),
  finish: (id, body) => json(`${BASE}/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  list: (offset = 0) => json(`${BASE}?limit=100&offset=${offset}`),
}

export function browserSessionStorage() {
  try { return window.sessionStorage } catch { return null }
}

// A per-tab journal contains only unfinished saves, never conversation content.
export function createSessionStore({ api = sessionApi, storage = browserSessionStorage(), now = () => new Date().toISOString(), id = () => crypto.randomUUID(), changed = () => {} } = {}) {
  const key = 'assignment3.pendingSessions'
  const state = { warning: '', saving: false, history: [], loading: false, historyError: '', loaded: false, hasMore: false, sessionId: '' }
  let records = [], current = null, priorStatus = null, busy = null, storageWarning = ''
  try {
    records = JSON.parse(storage?.getItem(key) || '[]')
    if (!Array.isArray(records) || records.some((record) => !record?.start?.session_id || !record.start.started_at || typeof record.created !== 'boolean')) throw new Error('Invalid pending records')
  } catch { records = []; storageWarning = 'Refresh recovery is unavailable.' }
  if (!storage) storageWarning = 'Refresh recovery is unavailable.'
  function journal() {
    try { storage?.setItem(key, JSON.stringify(records)) } catch { storageWarning = 'Refresh recovery is unavailable.' }
  }
  function notify() { changed({ ...state }) }
  async function drain() {
    if (busy) return busy
    state.saving = true; state.warning = storageWarning; notify()
    busy = (async () => {
      try {
        let record
        while ((record = records.find((item) => !item.created || item.end))) {
          if (!record.created) { await api.create(record.start); record.created = true; journal() }
          if (record.end) {
            await api.finish(record.start.session_id, record.end)
            records = records.filter((item) => item !== record); journal()
          }
        }
      } catch {
        state.warning = 'Session changes could not be saved. Breathing and Crisis Support still work. Retry saving when available.'
      } finally { state.warning ||= storageWarning; state.saving = false; notify() }
    })()
    await busy
    busy = null
  }
  function observe(run) {
    if (run.status === priorStatus) return
    priorStatus = run.status
    if (run.status === 'active') {
      current = { start: { session_id: id(), selected_skill: 'paced_breathing_4_6', started_at: now(), fewer_options: false }, created: false }
      records.push(current); state.sessionId = current.start.session_id; journal()
      void drain()
    } else if (current && run.status) {
      current.end = { status: run.status, ended_at: now(), measured_duration_seconds: run.durationMs === null ? null : run.durationMs / 1000 }
      journal()
      // If creation is in flight, its completion is followed by the final update.
      void drain()
    }
  }
  async function recover() {
    for (const record of records) {
      if (!record.end) record.end = { status: 'interrupted', ended_at: now(), measured_duration_seconds: null }
    }
    journal()
    if (records.length) await drain()
    else { state.warning = storageWarning; notify() }
  }
  async function loadHistory(more = false) {
    if (state.loading) return
    state.loading = true; state.historyError = ''; if (!more) { state.history = []; state.loaded = false }
    notify()
    try {
      const rows = await api.list(more ? state.history.length : 0)
      state.history = more ? [...state.history, ...rows] : rows
      state.hasMore = rows.length === 100; state.loaded = true
    } catch { state.historyError = 'Saved History could not be loaded. Please retry.' }
    finally { state.loading = false; notify() }
  }
  return { state, observe, recover, retry: drain, loadHistory }
}
