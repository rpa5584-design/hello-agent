<script setup>
import { computed, onMounted, onUnmounted, ref, shallowRef } from 'vue'
import { createDashboardClient } from '../../assignment4/client.js'
import { dashboardApi } from '../../assignment4/api.js'
import { productLabel } from '../../assignment4/chart.js'
import MarketChart from './MarketChart.vue'

const client = createDashboardClient({ changed: (value) => { state.value = value } })
const state = shallowRef({ ...client.state })
const product = ref('interval')
const symbol = ref('BTC-USD')
const busy = ref('')
const actionError = ref('')
const now = ref(Date.now())
let timer
onMounted(() => { client.connect(); timer = setInterval(() => { now.value = Date.now() }, 1000) })
onUnmounted(() => { clearInterval(timer); client.dispose() })
const payload = computed(() => state.value.payload)
const quote = computed(() => !state.value.pending && payload.value?.quotes?.[symbol.value])
const rows = computed(() => {
  if (state.value.pending) return []
  const values = product.value === 'interval' ? payload.value?.interval_bars : payload.value?.stream_candles
  return (values || []).filter((bar) => bar.symbol === symbol.value &&
    bar.provenance === (product.value === 'interval' ? 'yahoo_interval' : 'yahoo_stream'))
})
const latest = computed(() => rows.value.at(-1))
const usage = computed(() => payload.value?.usage || {})
const ageTime = computed(() => state.value.mode === 'replay'
  ? Date.parse(payload.value?.virtual_time) : now.value)
const sourceAge = computed(() => quote.value ? (ageTime.value - quote.value.source_time_ms) / 1000 : null)
const receiptAge = computed(() => quote.value ? (ageTime.value - Date.parse(quote.value.received_at)) / 1000 : null)
const retrievalAge = computed(() => payload.value?.interval_retrievals?.[symbol.value]
  ? (ageTime.value - Date.parse(payload.value.interval_retrievals[symbol.value])) / 1000 : null)
const age = (value) => value === null || !Number.isFinite(value) ? 'Not received'
  : value < -5 ? 'Clock skew' : `${Math.max(0, value).toFixed(1)}s`
const price = (value) => value === undefined ? '—' : new Intl.NumberFormat('en-US',
  { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(value)
const timestamp = (value) => value ? new Date(value).toISOString().replace('T', ' ').replace('.000Z', ' UTC') : 'Not received'
const feed = computed(() => payload.value?.effective_feed || 'stopped')
const green = computed(() => state.value.connection === 'connected' && state.value.mode === 'live' && feed.value === 'receiving' && sourceAge.value !== null && sourceAge.value < 30)
async function stopLive() {
  actionError.value = ''
  try { await dashboardApi.stop() }
  catch (error) { actionError.value = error.message }
}
async function action(name, operation) {
  if (busy.value) return
  busy.value = name; actionError.value = ''
  try { await operation() }
  catch (error) { actionError.value = error.message }
  finally { busy.value = '' }
}
</script>

<template>
  <div class="observatory">
    <header class="topbar">
      <a class="wordmark" href="/assignment4.html"><span aria-hidden="true" class="mark">◉</span> MARKET OBSERVATORY</a>
      <span class="local-tag">LOCALHOST <span aria-hidden="true">/</span> ASSIGNMENT 4.1</span>
    </header>
    <main>
      <section class="intro">
        <div><p class="eyebrow">A CLEAR VIEW OF THE SOURCE</p><h1>Watch the market.<br><em>Keep the context.</em></h1>
          <p class="lead">Streaming price observations and reported interval bars.<br>Two products, with their differences kept visible.</p></div>
        <div class="mode-box">
          <span class="caption">VIEWING MODE</span>
          <div class="segmented" aria-label="Live or replay">
            <button :class="{ active: state.mode === 'live' }" @click="client.setMode('live')">Live</button>
            <button :class="{ active: state.mode === 'replay' }" @click="client.setMode('replay')">Replay saved receipts</button>
          </div>
          <p>{{ state.mode === 'replay' ? 'Historical receipt order · ages use saved event time' : 'Live view · collecting only after Start live' }}</p>
          <span class="browser-status">Browser socket: <strong>{{ state.connection }}</strong></span>
          <button v-if="state.connection !== 'connected'" class="text-button" @click="client.reconnect()">Reconnect</button>
        </div>
      </section>

      <div v-if="state.mode === 'replay'" class="replay-banner" role="status">
        <strong>REPLAY — saved observations, not a live feed.</strong>
        <span>Live collection continues separately until Stop live.</span>
        <div class="replay-controls">
          <button @click="client.seek(0)">Rewind</button>
          <button v-if="!state.playing" @click="client.play()">Play saved receipts</button>
          <button v-else @click="client.pause()">Pause replay</button>
          <button :disabled="state.pending" @click="client.seek((payload?.cursor || 0) + 1)">Step</button>
          <label>Saved event cursor
            <input type="range" min="0" :max="state.replayEnd" :value="payload?.cursor || 0"
              @input="client.pause(); client.seek($event.target.value)">
          </label>
          <span>{{ payload?.cursor || 0 }} / {{ state.replayEnd }}</span>
        </div>
      </div>
      <p v-if="state.error || actionError" class="notice error" role="alert">{{ actionError || state.error }}</p>
      <p v-if="payload?.control?.offline" class="notice" role="status"><strong>OFFLINE RECORDED DATA.</strong> Upstream access disabled. Saved Yahoo observations are not a current live feed.</p>
      <p v-if="payload?.control?.simulated" class="notice simulated" role="status"><strong>Simulated unavailable feed.</strong> No Yahoo request was made by this demonstration.</p>

      <section class="workspace" aria-label="Market data workspace">
        <aside class="source-card">
          <div class="card-top"><span class="caption">STREAM OBSERVATION</span><span :class="['feed-pill', { fresh: green }]">{{ feed }}</span></div>
          <div class="instrument-tabs" aria-label="Instrument">
            <button v-for="item in ['BTC-USD', 'ETH-USD']" :key="item" :class="{ selected: symbol === item }" @click="symbol = item">{{ item }}</button>
          </div>
          <p class="instrument-name">{{ symbol === 'BTC-USD' ? 'Bitcoin / US dollar' : 'Ethereum / US dollar' }}</p>
          <div class="price" aria-live="polite">{{ price(quote?.price) }}</div>
          <p class="price-description">{{ state.pending ? 'Loading saved server state…' : quote ? 'Last received stream price · USD' : 'No stream observation received' }}</p>
          <dl class="source-metadata">
            <div><dt>Source</dt><dd>Yahoo Finance stream</dd></div>
            <div><dt>Interval</dt><dd>1 minute, UTC</dd></div>
            <div><dt>Source-data age</dt><dd>{{ age(sourceAge) }}</dd></div>
            <div><dt>Receipt age</dt><dd>{{ age(receiptAge) }}</dd></div>
            <div><dt>Source time</dt><dd>{{ timestamp(quote?.source_time_ms) }}</dd></div>
            <div><dt>Receipt time</dt><dd>{{ timestamp(quote?.received_at) }}</dd></div>
          </dl>
          <div class="live-controls">
            <button class="primary" :disabled="!!busy || payload?.control?.offline || state.mode === 'replay' || !!payload?.control?.running || (usage.stream_reserved_seconds || 0) + 93 > 180 || (usage.attempts || 0) >= 2 || usage.blocked"
              @click="action('Starting live', () => dashboardApi.start(symbol))">Start live · 90s</button>
            <button @click="stopLive">Stop live</button>
          </div>
          <p class="fine-print">No automatic connection. Selected instrument streams; interval OHLCV refreshes immediately then every 60s after completion, within the saved three-fetch limit. Up to two instruments, 180 seconds reserved including cleanup, and one reconnect per saved development budget.</p>
          <div class="usage">
            <span>Stream time <b>{{ usage.stream_seconds?.toFixed?.(1) || '0.0' }}s</b></span>
            <span>Reserved <b>{{ usage.stream_reserved_seconds || 0 }} / 180s</b></span>
            <span>Reconnects <b>{{ usage.reconnects || 0 }} / 1</b></span>
            <span>History fetches <b>{{ usage.history_fetches || 0 }} / 3</b></span>
            <span>History HTTP calls <b>{{ usage.http_calls?.length || 0 }}</b></span>
          </div>
        </aside>

        <section class="chart-card" aria-label="Price and volume chart">
          <div class="chart-heading"><div><span class="caption">THE DATA PRODUCT</span><h2>{{ productLabel(product) }}</h2></div><span class="interval-tag">1m / UTC</span></div>
          <div class="product-controls">
            <div class="segmented">
              <button :class="{ active: product === 'interval' }" @click="product = 'interval'">Yahoo interval OHLCV</button>
              <button :class="{ active: product === 'stream' }" @click="product = 'stream'">Stream-observed candles</button>
            </div>
            <button :disabled="!!busy || payload?.control?.offline || state.mode === 'replay' || payload?.control?.history === 'fetching' || (usage.history_fetches || 0) >= 3 || usage.blocked" @click="action('Fetching intervals', () => dashboardApi.history(symbol))">Fetch {{ symbol }} intervals</button>
          </div>
          <p class="product-note">{{ product === 'interval' ? 'Polled snapshot: matching OHLC and volume from each Yahoo interval record. Volume units are provider-reported and unverified.' : 'Built only from streaming observations received by this app. Coverage is partial and volume is unknown.' }}</p>
          <MarketChart :key="symbol + product" :rows="rows" :product="product" />
          <div v-if="!rows.length" class="empty-chart" role="status">{{ state.pending ? 'Loading server snapshot…' : product === 'interval' ? 'No valid interval bars saved. Start live for bounded automatic refresh, or use Fetch intervals.' : 'No streamed candle data saved. Use Start live.' }}</div>
          <div class="chart-summary">
            <span>Bars in view <strong>{{ rows.length }}</strong></span>
            <span>Auto-refresh instrument <strong>{{ payload?.control?.refresh_symbol || 'None' }}</strong></span>
            <span>Interval refresh <strong>{{ payload?.control?.interval_refresh || 'stopped' }}</strong></span>
            <span>Interval fetch <strong>{{ payload?.control?.history || 'not_fetched' }}</strong></span>
            <span>Retrieval age <strong>{{ age(retrievalAge) }}</strong></span>
            <span>Interval state <strong>{{ latest?.app_completion || 'No interval' }}</strong></span>
            <span>Corrections <strong>{{ latest?.corrected || latest?.late_corrected ? 'App revision / late correction' : 'None recorded for latest' }}</strong></span>
          </div>
          <div v-if="latest" class="latest-record" aria-label="Latest chart record">
            <span>{{ timestamp(product === 'interval' ? latest.source_time_s * 1000 : latest.bucket_start_ms) }}</span>
            <span>O <b>{{ price(latest.open) }}</b></span><span>H <b>{{ price(latest.high) }}</b></span>
            <span>L <b>{{ price(latest.low) }}</b></span><span>C <b>{{ price(latest.close) }}</b></span>
            <span>Volume <b>{{ product === 'stream' || latest.volume === null ? 'Unknown' : new Intl.NumberFormat('en-US').format(latest.volume) }}</b></span>
          </div>
          <p class="fine-print">Application interval closure is not exchange finality. Reported zero volume is kept as zero; missing volume is a gap. Historical volume is never attached to stream-derived OHLC.</p>
        </section>
      </section>

      <section class="evidence-row">
        <details><summary>Persisted receipt trail <span>cursor {{ payload?.cursor || 0 }}</span></summary>
          <p class="fine-print">This cursor includes source receipts, interval responses and control events in their saved receipt order. IDs below belong to this application.</p>
          <div v-for="receipt in payload?.recent_receipts || []" :key="receipt.receipt_seq" class="receipt">
            <strong>#{{ receipt.receipt_seq }} · {{ receipt.kind }} · version {{ receipt.version_id }}</strong>
            <small>{{ receipt.received_at }}</small><code>{{ receipt.raw_payload_json }}</code>
          </div>
          <p v-if="!payload?.recent_receipts?.length">No source receipts saved yet.</p>
        </details>
        <details><summary>Interval quality review <span>{{ payload?.quarantine_count || 0 }} quarantined</span></summary>
          <p>Malformed OHLC and unaligned timestamps are preserved outside the chart.</p>
          <div v-for="item in payload?.quarantine || []" :key="item.receipt_seq" class="receipt"><strong>{{ item.symbol }} #{{ item.receipt_seq }}</strong><span>{{ item.reason }}</span></div>
          <p v-if="!payload?.quarantine?.length">No quarantined interval rows in this snapshot.</p>
        </details>
        <div class="failure-demo"><span class="caption">FAILURE BEHAVIOR</span><p>Keep saved data visible when the feed cannot update.</p>
          <button :disabled="!!busy" @click="action('Simulating unavailable', dashboardApi.unavailable)">Simulate unavailable feed</button>
        </div>
      </section>
      <p class="action-state" role="status">{{ busy ? busy + '…' : payload?.control?.reason || 'Waiting for backend snapshot.' }}</p>
      <footer><span>Yahoo Finance via yfinance · educational, local demonstration · no trading or financial advice</span>
        <span>TradingView Lightweight Charts™ · Copyright (с) 2025 TradingView, Inc. <a href="https://www.tradingview.com/" target="_blank" rel="noopener noreferrer">TradingView</a> · <a href="/assignment4-third-party-notices.txt">License & notices</a></span>
      </footer>
    </main>
  </div>
</template>

<style>
:root { font-family: "Segoe UI", Arial, sans-serif; color: #243e37; background: #f5f5ed; font-synthesis: none; }
* { box-sizing: border-box; }
body { margin: 0; }
button, input { font: inherit; }
button { cursor: pointer; border: 1px solid #d4ded3; color: #29483e; border-radius: 7px; padding: 9px 13px; background: #fffefb; font-size: 13px; font-weight: 600; }
button:hover:enabled { background: #e4eee4; border-color: #7d9f8c; }
button:disabled { opacity: .48; cursor: not-allowed; }
button:focus-visible, input:focus-visible, summary:focus-visible, a:focus-visible { outline: 3px solid #de9c36; outline-offset: 3px; }
.topbar { background: #132f2b; color: #d9e6d8; display: flex; align-items: center; justify-content: space-between; padding: 19px max(28px, calc((100vw - 1280px)/2)); gap: 20px; }
.wordmark { text-decoration: none; color: #fffef3; font-size: 13px; font-weight: 700; letter-spacing: 2px; display: flex; align-items: center; gap: 12px; }
.mark { color: #b9dc9f; font-size: 26px; }
.local-tag { font-size: 10px; letter-spacing: 1.6px; color: #a6bdae; }
.local-tag span { margin: 0 12px; }
main { max-width: 1340px; margin: 0 auto; padding: 38px 30px 20px; }
.intro { display: flex; align-items: end; justify-content: space-between; gap: 25px; margin-bottom: 32px; }
.eyebrow, .caption { font-size: 10px; letter-spacing: 1.7px; font-weight: 700; color: #667e69; }
.eyebrow { margin: 0 0 12px; }
h1 { font: 42px/1.12 Georgia, serif; letter-spacing: -1.4px; margin: 0 0 15px; font-weight: 400; }
h1 em { color: #5d765b; font-weight: 400; }
.lead { font-size: 13px; line-height: 1.7; color: #6d7a6b; margin: 0; }
.mode-box { text-align: right; padding-bottom: 4px; }
.mode-box p { font-size: 11px; color: #71816e; margin-bottom: 8px; }
.segmented { display: inline-flex; background: #e9ede2; padding: 3px; border-radius: 8px; gap: 3px; }
.segmented button { border-color: transparent; background: transparent; padding: 8px 12px; font-size: 12px; }
.segmented .active { background: #fffefb; box-shadow: 0 1px 4px #203f2415; border-color: #d8dfd1; }
.mode-box .segmented { display: flex; margin-top: 9px; }
.browser-status { font-size: 11px; }
.text-button { background: transparent; border: 0; font-size: 11px; text-decoration: underline; padding: 3px 8px; }
.workspace { display: grid; grid-template-columns: 300px minmax(0,1fr); gap: 20px; align-items: start; }
.source-card, .chart-card { background: #fffefb; border: 1px solid #dce2d4; border-radius: 13px; }
.source-card { padding: 21px; }
.card-top { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.feed-pill { background: #f0e8d4; color: #846d32; border-radius: 20px; font-size: 10px; padding: 5px 8px; max-width: 120px; }
.feed-pill.fresh { background: #e4f1df; color: #32794d; }
.instrument-tabs { display: flex; margin: 22px 0 15px; border-bottom: 1px solid #dfe6db; }
.instrument-tabs button { border: 0; border-radius: 0; padding: 8px 8px 12px; background: transparent; color: #84917c; font-size: 12px; }
.instrument-tabs .selected { color: #1f563e; border-bottom: 2px solid #2d7557; }
.instrument-name { color: #6d7d6a; font-size: 12px; }
.price { font-size: 33px; letter-spacing: -1px; font-weight: 500; font-variant-numeric: tabular-nums; margin-top: 7px; }
.price-description { font-size: 11px; color: #75866e; margin-top: 6px; min-height: 28px; }
.source-metadata { margin: 22px 0; font-size: 11px; }
.source-metadata div { display: flex; justify-content: space-between; gap: 10px; padding: 7px 0; border-bottom: 1px solid #eff0e9; }
dt { color: #7f8a78; flex-shrink: 0; } dd { margin: 0; text-align: right; overflow-wrap: anywhere; }
.live-controls { display: flex; gap: 7px; }
.primary { background: #1c5141; color: #fff; border-color: #1c5141; }
.primary:hover:enabled { background: #286a54; color: white; }
.fine-print { font-size: 10px; color: #7a8572; line-height: 1.65; }
.usage { display: grid; gap: 7px; font-size: 10px; margin-top: 17px; padding-top: 14px; border-top: 1px solid #e3e8dc; }
.usage span { display: flex; justify-content: space-between; color: #7f8a78; }
.usage b { color: #50634d; font-weight: 600; }
.chart-card { padding: 22px 24px 17px; position: relative; min-width: 0; }
.chart-heading { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
h2 { font: 22px/1.2 Georgia, serif; margin: 7px 0 14px; }
.interval-tag { background: #eef1e7; border-radius: 4px; padding: 5px 8px; font-size: 10px; white-space: nowrap; }
.product-controls { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.product-note { font-size: 11px; color: #72806b; line-height: 1.6; min-height: 34px; }
.empty-chart { position: absolute; top: 45%; left: 50%; transform: translateX(-50%); color: #6e8169; font-size: 12px; text-align: center; max-width: 70%; pointer-events: none; padding: 12px; background: #fffefbe8; border-radius: 8px; }
.chart-summary { display: flex; flex-wrap: wrap; gap: 15px; border-top: 1px solid #e3e8dc; padding-top: 13px; }
.latest-record { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 15px; padding: 10px; background: #f1f4ea; border-radius: 6px; font-size: 10px; color: #61755b; }
.chart-summary span { color: #89917f; font-size: 10px; }
.chart-summary strong { display: block; color: #51634d; font-size: 11px; font-weight: 600; margin-top: 6px; }
.evidence-row { display: grid; grid-template-columns: 1fr 1fr .85fr; gap: 15px; margin-top: 20px; }
details, .failure-demo { background: #eeefe5; border: 1px solid #dce2d4; border-radius: 9px; padding: 16px; font-size: 11px; min-width: 0; }
summary { cursor: pointer; font-size: 12px; font-weight: 600; }
summary span { display: block; margin: 8px 0 0 12px; font-size: 10px; color: #7b8974; font-weight: 400; }
.receipt { margin-top: 14px; display: grid; gap: 7px; }
.receipt small { color: #7d8874; } .receipt code { overflow-wrap: anywhere; font-size: 9px; line-height: 1.6; }
.failure-demo p { color: #728067; line-height: 1.5; margin: 8px 0 12px; }
.failure-demo button { font-size: 11px; }
.notice, .replay-banner { padding: 14px 18px; margin: 0 0 18px; border-radius: 8px; font-size: 12px; line-height: 1.6; }
.error { background: #f7e6de; color: #914d3d; }
.simulated, .replay-banner { background: #f4e9cf; color: #80642d; border: 1px solid #e5d5a5; }
.replay-banner > span { display: block; font-size: 11px; }
.replay-controls { display: flex; align-items: center; flex-wrap: wrap; gap: 9px; margin-top: 12px; }
.replay-controls label { font-size: 10px; display: flex; gap: 10px; align-items: center; }
.replay-controls input { width: 170px; }
.action-state { font-size: 11px; min-height: 18px; color: #6c7b62; margin: 18px 0; }
footer { display: grid; gap: 8px; color: #8a9580; font-size: 9px; border-top: 1px solid #dce2d4; padding-top: 16px; line-height: 1.6; }
footer a { color: #52705d; }
@media (max-width: 1000px) { .workspace { grid-template-columns: 260px minmax(0,1fr); gap: 12px; } .chart-card { padding: 18px 14px; } .source-card { padding: 18px; } .evidence-row { grid-template-columns: 1fr 1fr; } .failure-demo { grid-column: 1 / -1; } }
@media (max-width: 720px) { main { padding: 26px 16px; } .topbar { padding: 15px 16px; } .wordmark { font-size: 10px; letter-spacing: 1px; } .local-tag { display: none; } .intro { display: block; margin-bottom: 22px; } h1 { font-size: 36px; } .mode-box { text-align: left; margin-top: 24px; } .mode-box .segmented { display: inline-flex; } .workspace { grid-template-columns: 1fr; } .source-card { display: block; } .price { font-size: 34px; } .source-metadata { display: grid; grid-template-columns: 1fr 1fr; gap: 5px 18px; } .source-metadata div { display: block; } dd { text-align: left; margin-top: 4px; } .usage { grid-template-columns: 1fr 1fr; column-gap: 22px; } .evidence-row { grid-template-columns: 1fr; } .chart-heading h2 { font-size: 20px; } .product-controls .segmented { display: flex; width: 100%; } .segmented button { padding: 8px; font-size: 11px; } }
</style>
