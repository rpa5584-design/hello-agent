import { test } from 'node:test'
import assert from 'node:assert/strict'
import { calculateIndicators } from '../src/assignment4/indicators.js'
import { indicatorData } from '../src/assignment4/chart.js'

const base = 1_760_000_000 - (1_760_000_000 % 60)
const closes = [6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3, 2, 3, 4, 5]
function bars(values, formingIndex = -1) {
  return values.map((close, index) => ({ source_time_s: base + index * 60,
    open: close, high: close + 1, low: close - 1, close,
    app_completion: index === formingIndex ? 'forming' : 'interval_elapsed_by_app' }))
}

test('indicators match hand-calculated SMA and crossover reference vectors', () => {
  const result = calculateIndicators(bars(closes), 2, 3)
  assert.deepEqual(result.rows.slice(0, 4).map((row) => [row.fast_sma, row.slow_sma]), [
    [null, null], [5.5, null], [4.5, 5], [3.5, 4],
  ])
  assert.deepEqual(result.confirmedSignals.map((row) => [
    (row.source_time_s - base) / 60, row.signal, row.signal_status,
  ]), [[7, 'UP', 'confirmed'], [11, 'DOWN', 'confirmed'], [14, 'UP', 'confirmed']])
})

test('unfinished candle crossover is provisional and omitted from confirmed events', () => {
  const result = calculateIndicators(bars([6, 5, 4, 3, 2, 1, 2, 4], 7), 2, 3)
  assert.equal(result.confirmedSignals.length, 0)
  assert.equal(result.provisionalSignal.signal, 'UP')
  assert.equal(result.provisionalSignal.signal_status, 'provisional')
})

test('chart crossover arrows stay compact and use color to distinguish signal status', () => {
  const result = indicatorData(bars([6, 5, 4, 3, 2, 1, 2, 4], 7), 2, 3)
  assert.equal(result.markers.length, 1)
  assert.equal(result.markers[0].shape, 'arrowUp')
  assert.equal(result.markers[0].position, 'belowBar')
  assert.equal('text' in result.markers[0], false)
  assert.equal(result.markers[0].color, '#b17b19')
  const confirmed = indicatorData(bars(closes), 2, 3)
  assert.equal(confirmed.markers[0].shape, 'arrowUp')
  assert.equal(confirmed.markers[0].color, '#178252')
  assert.equal(confirmed.markers[1].shape, 'arrowDown')
  assert.equal(confirmed.markers[1].color, '#b5473d')
  assert.ok(confirmed.markers.every((marker) => !('text' in marker)))
})

test('different window lengths are required', () => {
  assert.throws(() => calculateIndicators([], 5, 5), /greater/)
})
