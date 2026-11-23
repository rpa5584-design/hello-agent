import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import * as Vue from 'vue'
import { renderToString } from '@vue/server-renderer'
import { parse, compileScript } from '@vue/compiler-sfc'
import { createDashboardClient } from '../src/assignment4/client.js'
import { mountChart, seriesData, productLabel } from '../src/assignment4/chart.js'
import { host, flush } from './helpers/assignment3Presentation.js'

function socketHarness() {
  const instances = [], timers = new Map()
  let next = 0
  class Socket {
    constructor() { this.readyState = 0; this.sent = []; instances.push(this) }
    open() { this.readyState = 1; this.onopen() }
    send(raw) { this.sent.push(JSON.parse(raw)) }
    message(frame) { this.onmessage({ data: JSON.stringify(frame) }) }
    close() { if (this.readyState === 3) return; this.readyState = 3; this.onclose?.() }
  }
  const client = createDashboardClient({ WebSocketImpl: Socket, url: () => 'ws://test',
    schedule: (fn, ms) => { timers.set(++next, { fn, ms }); return next },
    cancel: (id) => timers.delete(id), now: () => 100000 })
  return { client, instances, timers, tick(ms) {
    const item = [...timers.entries()].find(([, v]) => v.ms === ms)
    assert.ok(item, `scheduled ${ms}`); timers.delete(item[0]); item[1].fn()
  } }
}
const frame = (mode, requestId, cursor, maxCursor = 10, price = 100) => ({
  protocol_version: 1, mode, request_id: requestId, cursor,
  payload: { cursor, max_cursor: maxCursor, quotes: { 'BTC-USD': { price } } },
})

test('socket connection sends hello only, never starts an upstream source', () => {
  const h = socketHarness()
  h.client.connect(); h.instances[0].open()
  assert.deepEqual(h.instances[0].sent.map((s) => s.type), ['hello'])
  assert.equal(h.client.state.connection, 'connected')
  assert.equal(h.client.state.pending, true) // socket alone is not received data
  h.instances[0].message(frame('live', 1, 2))
  assert.equal(h.client.state.pending, false)
  h.client.dispose(); assert.equal(h.timers.size, 0)
})

test('mode/request IDs reject future live frames while replaying saved receipts', () => {
  const h = socketHarness(); h.client.connect(); const socket = h.instances[0]; socket.open()
  socket.message(frame('live', 1, 10))
  h.client.setMode('replay')
  assert.equal(h.client.state.pending, true)
  socket.message(frame('live', 1, 11, 11, 999))
  assert.equal(h.client.state.payload.quotes['BTC-USD'].price, 100)
  socket.message(frame('replay', 2, 0, 10, 80))
  assert.equal(h.client.state.payload.quotes['BTC-USD'].price, 80)
  assert.equal(h.client.state.replayEnd, 10)
  h.client.seek(2); socket.message(frame('replay', 3, 2, 10, 90))
  assert.equal(h.client.state.payload.cursor, 2)
  socket.message(frame('replay', 2, 0, 10, 20))
  assert.equal(h.client.state.payload.cursor, 2)
  h.client.dispose()
})

test('browser reconnect is bounded and resends replay cursor without starting Yahoo', () => {
  const h = socketHarness(); h.client.connect(); h.instances[0].open()
  h.instances[0].message(frame('live', 1, 10))
  h.client.setMode('replay'); h.instances[0].message(frame('replay', 2, 4, 10))
  for (const delay of [1000, 2000, 4000]) {
    h.instances.at(-1).close(); h.tick(delay); h.instances.at(-1).open()
    assert.equal(h.instances.at(-1).sent[0].mode, 'replay')
    assert.equal(h.instances.at(-1).sent[0].cursor, 4)
  }
  h.instances.at(-1).close()
  assert.match(h.client.state.error, /limit reached/)
  assert.equal(h.instances.length, 4)
  h.client.dispose()
})

const bars = [
  { source_time_s: 120, open: 100, high: 110, low: 90, close: 105, volume: 0 },
  { source_time_s: 180, open: 105, high: 120, low: 100, close: 115, volume: null },
]
test('interval volume zero stays numeric zero; null is a matching-time whitespace gap', () => {
  const data = seriesData(bars, 'interval')
  assert.equal(data.volume[0].value, 0)
  assert.deepEqual(data.volume[1], { time: 180 })
  assert.deepEqual(data.candles.map((v) => v.time), data.volume.map((v) => v.time))
})
test('stream candles never inherit interval volume', () => {
  const data = seriesData([{ ...bars[0], bucket_start_ms: 120000, volume: 999 }], 'stream')
  assert.deepEqual(data.volume, [{ time: 120 }])
})
test('historical corrections replace complete sorted OHLCV records', () => {
  const revised = { ...bars[0], high: 130, volume: 10 }
  const data = seriesData([bars[1], bars[0], revised], 'interval')
  assert.deepEqual(data.candles.map((v) => v.time), [120, 180])
  assert.equal(data.candles[0].high, 130)
  assert.equal(data.volume[0].value, 10)
})

test('chart creates two panes with attribution, updates both, and removes exactly once', () => {
  const calls = [], series = [], paneHeights = [], markerCalls = []
  let removed = 0
  const fake = (_el, options) => {
    assert.equal(options.layout.attributionLogo, true)
    return {
      addSeries(_type, _options, pane) {
        const value = { setData(data) { calls.push({ pane, data }) } }; series.push(value); return value
      },
      panes: () => [0, 1].map((pane) => ({ setHeight(value) { paneHeights[pane] = value } })),
      timeScale: () => ({ fitContent() {}, getVisibleLogicalRange() { return { from: 0, to: 1 } }, setVisibleLogicalRange() {} }),
      remove() { removed++ },
    }
  }
  const chart = mountChart({}, fake, () => ({ setMarkers(value) { markerCalls.push(value) }, detach() {} }))
  chart.update(bars, 'interval')
  assert.equal(series.length, 4)
  assert.deepEqual(paneHeights, [280, 100])
  assert.equal(calls[0].data.length, calls[1].data.length)
  assert.equal(markerCalls.length, 1)
  chart.remove(); chart.remove(); chart.update(bars, 'interval')
  assert.equal(removed, 1); assert.equal(calls.length, 4)
})

async function component(name, dependencies) {
  const text = await readFile(new URL(`../src/components/assignment4/${name}`, import.meta.url), 'utf8')
  const { content } = compileScript(parse(text).descriptor, { id: name, inlineTemplate: true, templateOptions: { compilerOptions: { hoistStatic: false } } })
  const code = content.replace(/import \{([^}]+)\} from ['"]vue['"];?/g,
    (_, names) => `const {${names.replace(/\bas\b/g, ':')}} = Vue;`)
    .replace(/^import .*$/gm, '').replace('export default', 'return')
  return new Function('Vue', ...Object.keys(dependencies), code)(Vue, ...Object.values(dependencies))
}
test('Vue chart component mounts updates and cleans up the imperative chart', async () => {
  let mounted = 0, removed = 0, updates = 0
  const view = await component('MarketChart.vue', { mountChart: () => {
    mounted++; return { update() { updates++ }, remove() { removed++ } }
  } })
  const env = host()
  const app = env.renderer.createApp(view, { rows: bars, product: 'interval' })
  app.mount(env.root); await flush(); app.unmount()
  assert.equal(mounted, 1); assert.equal(removed, 1); assert.ok(updates >= 1)
})

test('rendered dashboard labels replay, unknown provider units and simulated failure honestly', async () => {
  for (const mode of ['live', 'replay']) {
    const state = { connection: 'connected', mode, pending: false, requestId: 1, replayEnd: 10,
      payload: { cursor: 2, max_cursor: 10, effective_feed: 'unavailable', quotes: {},
        control: { simulated: true }, usage: {}, interval_bars: [], recent_receipts: [], quarantine: [] } }
    const view = await component('MarketDashboard.vue', {
      createDashboardClient: () => ({ state }), dashboardApi: {}, productLabel,
      MarketChart: { render: () => null },
    })
    const html = await renderToString(Vue.createSSRApp(view))
    assert.match(html, /Yahoo interval OHLCV/)
    assert.match(html, /provider-reported and unverified/)
    assert.match(html, /Simulated unavailable feed/)
    assert.match(html, /No stream observation received/)
    assert.match(html, /Source-data age/)
    assert.match(html, /Receipt age/)
    if (mode === 'replay') assert.match(html, /saved observations, not a live feed/)
    else assert.match(html, /collecting only after Start live/)
  }
})

test('appended live-edge bars stay visible while a manually panned range is preserved', () => {
  let range = { from: 0, to: 1 }
  const applied = []
  const scale = { fitContent() {}, getVisibleLogicalRange: () => range,
    setVisibleLogicalRange: (value) => applied.push(value) }
  const factory = () => ({
    addSeries: () => ({ setData() {} }),
    panes: () => [{ setHeight() {} }, { setHeight() {} }],
    timeScale: () => scale, remove() {},
  })
  const view = mountChart({}, factory, () => ({ setMarkers() {}, detach() {} }))
  view.update(bars, 'interval')
  view.update([...bars, { ...bars[1], source_time_s: 240 }], 'interval')
  assert.deepEqual(applied.at(-1), { from: 1, to: 2 })
  range = { from: -1, to: 0 }
  view.update([...bars, { ...bars[1], source_time_s: 240 }, { ...bars[1], source_time_s: 300 }], 'interval')
  assert.deepEqual(applied.at(-1), range)
  view.remove()
})

test('disconnected browser retains explicitly cached data without starting any source', () => {
  const h = socketHarness(); h.client.connect(); const socket = h.instances[0]; socket.open()
  const current = frame('live', 1, 10)
  current.payload.mode = 'live'
  socket.message(current)
  socket.close()
  assert.equal(h.client.state.connection, 'disconnected')
  assert.equal(h.client.state.pending, false)
  assert.equal(h.client.state.payload.quotes['BTC-USD'].price, 100)
  h.client.dispose()
})

test('Stop live remains usable while an independent interval request is pending', async () => {
  const { find, textOf } = await import('./helpers/assignment3Presentation.js')
  let release, stopCalls = 0
  const api = { history: () => new Promise((resolve) => { release = resolve }),
    stop: async () => { stopCalls++ } }
  const state = { connection: 'connected', mode: 'live', pending: false, requestId: 1, replayEnd: 0,
    payload: { cursor: 1, max_cursor: 1, effective_feed: 'receiving', quotes: {},
      control: { running: true }, usage: {}, interval_bars: [], recent_receipts: [], quarantine: [] } }
  const view = await component('MarketDashboard.vue', {
    createDashboardClient: () => ({ state, connect() {}, dispose() {} }),
    dashboardApi: api, productLabel, MarketChart: { render: () => null },
  })
  const env = host(); const app = env.renderer.createApp(view); app.mount(env.root); await flush()
  const fetchButton = find(env.root, (n) => n.type === 'button' && textOf(n).includes('Fetch BTC-USD'))
  const pending = fetchButton.props.onClick()
  await flush()
  const stopButton = find(env.root, (n) => n.type === 'button' && textOf(n) === 'Stop live')
  assert.ok(!stopButton.props.disabled)
  await stopButton.props.onClick()
  assert.equal(stopCalls, 1)
  release(); await pending; app.unmount()
})


test('rendered interval refresh status stays distinct from stream freshness and retrieval age', async () => {
  const state = { connection: 'connected', mode: 'live', pending: false, replayEnd: 0,
    payload: { cursor: 3, effective_feed: 'stale', quotes: {},
      last_interval_retrieval: new Date().toISOString(),
      control: { running: true, interval_refresh: 'backoff', history: 'unavailable' },
      usage: { history_fetches: 2 }, interval_bars: [], recent_receipts: [], quarantine: [] } }
  const view = await component('MarketDashboard.vue', {
    createDashboardClient: () => ({ state }), dashboardApi: {}, productLabel,
    MarketChart: { render: () => null },
  })
  const html = await renderToString(Vue.createSSRApp(view))
  assert.match(html, /every 60s after completion/)
  assert.match(html, /Polled snapshot: matching OHLC and volume/)
  assert.match(html, /Interval refresh <strong>backoff/)
  assert.match(html, /Interval fetch <strong>unavailable/)
  assert.match(html, /Retrieval age/)
  assert.match(html, /feed-pill[^>]*>stale/)
  assert.doesNotMatch(html, /feed-pill fresh/)
})


test('selected instrument retrieval age does not borrow another symbol freshness', async () => {
  const state = { connection: 'connected', mode: 'live', pending: false, replayEnd: 0,
    payload: { cursor: 3, effective_feed: 'stopped', quotes: {},
      last_interval_retrieval: new Date().toISOString(),
      interval_retrievals: { 'ETH-USD': new Date().toISOString() },
      control: {}, usage: {}, interval_bars: [], recent_receipts: [], quarantine: [] } }
  const view = await component('MarketDashboard.vue', {
    createDashboardClient: () => ({ state }), dashboardApi: {}, productLabel,
    MarketChart: { render: () => null },
  })
  const html = await renderToString(Vue.createSSRApp(view))
  assert.match(html, /Retrieval age <strong>Not received/)
})


test('offline recorded-data mode explicitly labels stored Yahoo data and disables upstream controls', async () => {
  const state = { connection: 'connected', mode: 'live', pending: false, replayEnd: 0,
    payload: { cursor: 3, effective_feed: 'stopped', quotes: {}, control: { offline: true },
      usage: {}, interval_bars: [], recent_receipts: [], quarantine: [] } }
  const view = await component('MarketDashboard.vue', {
    createDashboardClient: () => ({ state }), dashboardApi: {}, productLabel,
    MarketChart: { render: () => null },
  })
  const html = await renderToString(Vue.createSSRApp(view))
  assert.match(html, /OFFLINE RECORDED DATA/)
  assert.match(html, /Upstream access disabled/)
  assert.match(html, /button[^>]*disabled[^>]*>Start live/)
  assert.match(html, /button[^>]*disabled[^>]*>Fetch BTC-USD/)
})
