export const FAST_SMA_WINDOW = 5
export const SLOW_SMA_WINDOW = 20

function average(values, window) {
  return values.length < window ? null : values.slice(-window).reduce((sum, value) => sum + value, 0) / window
}

export function calculateIndicators(rows, fastWindow = FAST_SMA_WINDOW, slowWindow = SLOW_SMA_WINDOW) {
  if (!Number.isInteger(fastWindow) || !Number.isInteger(slowWindow) || fastWindow < 1 || slowWindow <= fastWindow) {
    throw new Error('slow window must be greater than the positive fast window')
  }
  const ordered = [...rows].sort((a, b) => a.source_time_s - b.source_time_s)
  const complete = ordered.filter((row) => row.app_completion === 'interval_elapsed_by_app')
  const completeRows = complete.map((row, index) => {
    const fast = average(complete.slice(Math.max(0, index + 1 - fastWindow), index + 1).map((item) => item.close), fastWindow)
    const slow = average(complete.slice(Math.max(0, index + 1 - slowWindow), index + 1).map((item) => item.close), slowWindow)
    return { source_time_s: row.source_time_s, fast_sma: fast, slow_sma: slow,
      signal: null, signal_status: 'confirmed' }
  })
  const confirmedSignals = []
  for (let index = 1; index < completeRows.length; index++) {
    const previous = completeRows[index - 1]
    const current = completeRows[index]
    if ([previous.fast_sma, previous.slow_sma, current.fast_sma, current.slow_sma].some((value) => value === null)) continue
    const before = previous.fast_sma - previous.slow_sma
    const after = current.fast_sma - current.slow_sma
    const direction = before <= 0 && after > 0 ? 'UP' : before >= 0 && after < 0 ? 'DOWN' : null
    if (direction) {
      current.signal = direction
      confirmedSignals.push({ ...current })
    }
  }

  const byTime = new Map(completeRows.map((item) => [item.source_time_s, item]))
  let provisionalSignal = null
  const current = ordered.at(-1)
  if (current?.app_completion === 'forming' && complete.length) {
    const previous = completeRows.at(-1)
    const tail = (window) => window === 1 ? [] :
      complete.slice(-Math.min(window - 1, complete.length)).map((item) => item.close)
    const fast = average([...tail(fastWindow), current.close], fastWindow)
    const slow = average([...tail(slowWindow), current.close], slowWindow)
    if (previous.fast_sma !== null && previous.slow_sma !== null && fast !== null && slow !== null) {
      const before = previous.fast_sma - previous.slow_sma
      const after = fast - slow
      const direction = before <= 0 && after > 0 ? 'UP' : before >= 0 && after < 0 ? 'DOWN' : null
      const provisional = { source_time_s: current.source_time_s, fast_sma: fast, slow_sma: slow,
        signal: direction, signal_status: 'provisional' }
      byTime.set(current.source_time_s, provisional)
      if (direction) provisionalSignal = provisional
    }
  }

  return { fastWindow, slowWindow,
    rows: ordered.map((row) => byTime.get(row.source_time_s) || {
      source_time_s: row.source_time_s, fast_sma: null, slow_sma: null,
      signal: null, signal_status: row.app_completion === 'forming' ? 'provisional' : 'confirmed',
    }), confirmedSignals, provisionalSignal }
}
