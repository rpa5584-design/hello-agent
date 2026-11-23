import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import * as Vue from 'vue'
import { parse, compileScript } from '@vue/compiler-sfc'
import { host, flush, find, textOf } from './helpers/assignment3Presentation.js'
import { productLabel } from '../src/assignment4/chart.js'

async function dashboardComponent(dependencies) {
  const source = await readFile(new URL('../src/components/assignment4/MarketDashboard.vue', import.meta.url), 'utf8')
  const { content } = compileScript(parse(source).descriptor, {
    id: 'assignment4-trading', inlineTemplate: true,
    templateOptions: { compilerOptions: { hoistStatic: false } },
  })
  const code = content.replace(/import \{([^}]+)\} from ['"]vue['"];?/g,
    (_, names) => `const {${names.replace(/\bas\b/g, ':')}} = Vue;`)
    .replace(/^import .*$/gm, '').replace('export default', 'return')
  return new Function('Vue', ...Object.keys(dependencies), code)(Vue, ...Object.values(dependencies))
}

test('browser workflow loads paper account, shows signal status, and runs a backtest', async () => {
  const calls = []
  let finishAccount
  const pendingAccount = new Promise((resolve) => { finishAccount = resolve })
  const bar = { symbol: 'BTC-USD', provenance: 'yahoo_interval', source_time_s: 1_760_000_000,
    open: 100, high: 105, low: 95, close: 102, volume: 0,
    app_completion: 'interval_elapsed_by_app', version_id: 1 }
  const payload = { cursor: 1, max_cursor: 1, virtual_time: new Date().toISOString(),
    effective_feed: 'stopped', quotes: {}, interval_bars: [bar], stream_candles: [],
    recent_receipts: [], quarantine: [], interval_retrievals: {}, control: {}, usage: {} }
  const account = { cash_cents: 1_010_000, realized_pnl_cents: 10_000,
    unrealized_pnl_cents: 0, equity_cents: 1_010_000, positions: [],
    orders: [{ order_id: 1, side: 'BUY', signal_time_s: bar.source_time_s - 60,
      status: 'FILLED', fill_time_s: bar.source_time_s, fill_price: 100, quantity: '10' }],
    fills: [{ fill_id: 1, side: 'BUY', fill_time_s: bar.source_time_s, fill_price: 100,
      quantity: '10', notional_cents: 100_000, realized_pnl_cents: 0 }],
    fast_window: 5, slow_window: 20,
    indicators: { 'BTC-USD': { rows: [], confirmed_signals: [{ signal: 'UP', source_time_s: bar.source_time_s }],
      provisional_signal: { signal: 'DOWN' } } } }
  const api = {
    syncPaper: async () => { calls.push('sync') },
    paperAccount: async () => { calls.push('account'); return pendingAccount },
    latestBacktest: async () => null,
    runBacktest: async (symbol) => {
      calls.push(`backtest:${symbol}`)
      return { run_id: 1, bar_count: 120, ending_cash_cents: 1_010_000,
        realized_pnl_cents: 10_000, unrealized_pnl_cents: 0, equity_cents: 1_010_000,
        pending_order: null, trades: [{ side: 'SELL', signal_time_s: bar.source_time_s,
          fill_time_s: bar.source_time_s + 60, fill_price: 110, quantity: '10', realized_pnl_cents: 10_000 }] }
    },
  }
  const clientState = { connection: 'connecting', mode: 'live', pending: true, requestId: 1, replayEnd: 0 }
  const view = await dashboardComponent({
    createDashboardClient: ({ changed }) => ({ state: clientState,
      connect: () => changed({ ...clientState, connection: 'connected', pending: false, payload }),
      dispose() {} }),
    dashboardApi: api, productLabel, MarketChart: { render: () => null },
  })
  const originalSet = globalThis.setInterval, originalClear = globalThis.clearInterval
  globalThis.setInterval = () => 1
  globalThis.clearInterval = () => {}
  const env = host(); const app = env.renderer.createApp(view)
  try {
    app.mount(env.root)
    await flush(); await flush()
    assert.deepEqual(calls.slice(0, 2), ['sync', 'account'])
    assert.match(textOf(env.root), /Cash Loading…/)
    assert.match(textOf(env.root), /Loading positions…/)
    assert.doesNotMatch(textOf(env.root), /Cash \$0\.00|No open positions\./)
    finishAccount(account)
    await flush(); await flush()
    assert.match(textOf(env.root), /PROVISIONAL DOWN crossover/)
    assert.match(textOf(env.root), /Latest confirmed crossover: UP/)
    assert.match(textOf(env.root), /Cash \$10,100\.00/)
    assert.match(textOf(env.root), /Fill ledger/)

    const button = find(env.root, (node) => node.type === 'button' && textOf(node).includes('Run backtest'))
    await button.props.onClick(); await flush()
    assert.ok(calls.includes('backtest:BTC-USD'))
    assert.match(textOf(env.root), /120 completed bars · 1 fills/)
    assert.match(textOf(env.root), /Ending cash \$10,100\.00/)
    assert.match(textOf(env.root), /SELL/)
  } finally {
    app.unmount()
    globalThis.setInterval = originalSet
    globalThis.clearInterval = originalClear
  }
})
