import { createChart, CandlestickSeries, HistogramSeries } from 'lightweight-charts'

export function seriesData(rows, product) {
  const values = new Map()
  for (const row of rows) {
    const time = product === 'interval' ? row.source_time_s : row.bucket_start_ms / 1000
    if (!Number.isFinite(time) || ['open', 'high', 'low', 'close'].some((k) => !Number.isFinite(row[k]))) continue
    const color = row.close >= row.open ? '#197f68' : '#cf6358'
    values.set(time, { candle: { time, open: row.open, high: row.high, low: row.low, close: row.close },
      volume: product === 'interval' && row.volume !== null && row.volume !== undefined
        ? { time, value: row.volume, color } : { time } })
  }
  const sorted = [...values.values()].sort((a, b) => a.candle.time - b.candle.time)
  return { candles: sorted.map((v) => v.candle), volume: sorted.map((v) => v.volume) }
}

export function mountChart(container, factory = createChart) {
  const chart = factory(container, {
    autoSize: true, height: 390,
    layout: { background: { color: '#fffefb' }, textColor: '#485b57', attributionLogo: true },
    grid: { vertLines: { color: '#f0f1eb' }, horzLines: { color: '#edf0e9' } },
    timeScale: { timeVisible: true, secondsVisible: false },
    rightPriceScale: { borderColor: '#dbe3db' },
  })
  const candles = chart.addSeries(CandlestickSeries, {
    upColor: '#197f68', downColor: '#cf6358', borderVisible: false,
    wickUpColor: '#197f68', wickDownColor: '#cf6358',
  }, 0)
  const volume = chart.addSeries(HistogramSeries, { priceFormat: { type: 'volume' },
    lastValueVisible: false, priceLineVisible: false }, 1)
  chart.panes()[0].setHeight(280)
  chart.panes()[1].setHeight(100)
  let loaded = false, removed = false, previousLength = 0
  return {
    update(rows, product) {
      if (removed) return
      const data = seriesData(rows, product)
      const range = loaded ? chart.timeScale().getVisibleLogicalRange() : null
      candles.setData(data.candles); volume.setData(data.volume)
      if (data.candles.length && !loaded) { chart.timeScale().fitContent(); loaded = true }
      else if (range) {
        const growth = data.candles.length - previousLength
        const follow = range.to >= previousLength - 1
        chart.timeScale().setVisibleLogicalRange(follow && growth > 0
          ? { from: range.from + growth, to: range.to + growth } : range)
      }
      previousLength = data.candles.length
    },
    fit() { if (!removed) chart.timeScale().fitContent() },
    remove() { if (!removed) { chart.remove(); removed = true } },
  }
}

export function productLabel(product) {
  return product === 'interval' ? 'Yahoo interval OHLCV · 1 minute' : 'Stream-observed candles · volume unknown'
}
