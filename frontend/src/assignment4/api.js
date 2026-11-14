const BASE = '/api/assignment4'

async function post(path, body) {
  const response = await fetch(BASE + path, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body ?? {}), signal: AbortSignal.timeout(60000),
  })
  const data = await response.json()
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Request failed.')
  return data
}

export const dashboardApi = {
  start: (symbol = 'BTC-USD') => post('/live/start', { symbols: [symbol], seconds: 90 }),
  stop: () => post('/live/stop'),
  history: (symbol) => post('/interval/fetch', { symbol }),
  unavailable: () => post('/demo/unavailable'),
}
