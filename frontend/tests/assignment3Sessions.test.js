import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createSessionStore } from '../src/assignment3/sessions.js'
import { createBreathing } from '../src/assignment3/breathing.js'

function fixture(overrides = {}) {
  const calls = [], memory = new Map()
  const storage = { getItem: (key) => memory.get(key), setItem: (key, value) => memory.set(key, value) }
  const api = {
    async create(body) { calls.push(['create', body]); return body },
    async finish(id, body) { calls.push(['finish', id, body]); return body },
    async list() { return [] },
    ...overrides,
  }
  const store = createSessionStore({ api, storage, id: () => 'test-session', now: () => '2026-10-21T14:00:00Z' })
  let time = 0
  const run = createBreathing({ now: () => time, changed: () => store.observe(run.state) })
  function advance(ms) { for (let i = 0; i < ms; i += 100) { time += 100; run.tick() } }
  return { store, run, advance, calls, storage, api }
}

test('Start saves once and completion persists actual duration', async () => {
  const { store, run, advance, calls } = fixture()
  assert.equal(calls.length, 0)
  run.start(); await store.retry()
  assert.equal(calls[0][0], 'create')
  advance(60000); await store.retry()
  assert.equal(calls.filter(([op]) => op === 'create').length, 1)
  assert.deepEqual(calls[1], ['finish', 'test-session', { status: 'completed', ended_at: '2026-10-21T14:00:00Z', measured_duration_seconds: 60 }])
})

test('Stop before create completes still persists final stopped state', async () => {
  let release
  const pending = new Promise((resolve) => { release = resolve })
  const { store, run, advance, calls } = fixture({ create: () => pending })
  run.start(); advance(1300); run.stop(); release({})
  await store.retry()
  assert.equal(calls[0][2].status, 'stopped')
  assert.equal(calls[0][2].measured_duration_seconds, 1.3)
})

test('save failure warns while breathing continues, retry uses the same ID', async () => {
  let offline = true
  const ids = []
  const { store, run, advance } = fixture({ async create(body) { ids.push(body.session_id); if (offline) throw new Error('offline') } })
  run.start(); await store.retry()
  assert.match(store.state.warning, /could not be saved/)
  advance(4000); assert.equal(run.state.phase, 'Exhale')
  offline = false; run.stop(); await store.retry()
  assert.deepEqual(ids, ['test-session', 'test-session'])
  assert.equal(store.state.warning, '')
})

test('Saved History loading, empty, success and error states do not start breathing', async () => {
  let resolve
  const { store, run, api } = fixture({ list: () => new Promise((done) => { resolve = done }) })
  const loading = store.loadHistory()
  assert.equal(store.state.loading, true)
  resolve([]); await loading
  assert.equal(store.state.loaded, true)
  assert.deepEqual(store.state.history, [])
  api.list = async () => [{ session_id: 'saved', status: 'completed', measured_duration_seconds: 60.8 }]
  await store.loadHistory()
  assert.equal(store.state.history[0].measured_duration_seconds, 60.8)
  api.list = async () => { throw new Error('offline') }
  await store.loadHistory()
  assert.match(store.state.historyError, /could not be loaded/)
  assert.equal(run.state.status, null)
})

test('refresh recovers a prior active record as interrupted without resuming', async () => {
  const { store, run, storage, api, calls } = fixture()
  run.start(); await store.retry()
  const refreshed = createSessionStore({ api, storage, now: () => '2026-10-21T14:01:00Z' })
  const freshRun = createBreathing()
  await refreshed.recover()
  assert.equal(calls.at(-1)[2].status, 'interrupted')
  assert.equal(calls.at(-1)[2].measured_duration_seconds, null)
  assert.equal(freshRun.state.screen, 'home')
  assert.equal(freshRun.state.status, null)
})

test('unsaved final update survives refresh and is retried without duplicate creation', async () => {
  const { store, run, storage, api, calls } = fixture({ async finish() { throw new Error('offline') } })
  run.start(); await store.retry(); run.stop(); await store.retry()
  assert.match(store.state.warning, /could not be saved/)
  api.finish = async (id, body) => { calls.push(['finish', id, body]) }
  const refreshed = createSessionStore({ api, storage })
  await refreshed.recover()
  assert.equal(calls.at(-1)[2].status, 'stopped')
  assert.equal(calls.filter(([op]) => op === 'create').length, 1)
})

test('blocked or damaged refresh storage warns without blocking a new exercise', async () => {
  for (const storage of [null, { getItem: () => '[null]', setItem() {} }, { getItem() { throw new Error('blocked') }, setItem() { throw new Error('blocked') } }]) {
    const store = createSessionStore({ api: { async create() {} }, storage, id: () => 'safe-id' })
    await store.recover()
    assert.match(store.state.warning, /Refresh recovery is unavailable/)
    const run = createBreathing({ changed: () => store.observe(run.state) })
    run.start(); await store.retry()
    assert.equal(run.state.phase, 'Inhale')
  }
})
