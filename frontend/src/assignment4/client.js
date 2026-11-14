/** Socket connection is distinct from upstream feed freshness. No source starts here. */
export function createDashboardClient({
  WebSocketImpl = globalThis.WebSocket,
  url = () => `${globalThis.location.protocol === 'https:' ? 'wss' : 'ws'}://${globalThis.location.host}/api/assignment4/ws`,
  schedule = setTimeout, cancel = clearTimeout, now = Date.now, changed = () => {},
} = {}) {
  const state = { connection: 'disconnected', mode: 'live', payload: null, error: '',
    pending: true, requestId: 1, replayEnd: 0, lastFrameAt: 0, playing: false }
  let socket = null, retryTimer = null, watchdog = null, playTimer = null
  let disposed = false, generation = 0, retries = 0
  const notify = () => changed({ ...state })
  const send = (value) => {
    if (socket?.readyState === 1) { socket.send(JSON.stringify(value)); return true }
    state.error = 'Browser connection unavailable. Reconnect to reload saved state.'
    notify()
    return false
  }
  function pause() { cancel(playTimer); playTimer = null; state.playing = false; notify() }
  function seek(cursor) {
    if (state.mode !== 'replay') return
    state.requestId += 1; state.pending = true
    send({ type: 'replay', cursor: Math.max(0, Math.min(state.replayEnd, Number(cursor))), request_id: state.requestId })
    notify()
  }
  function setMode(mode) {
    pause()
    if (!['live', 'replay'].includes(mode)) throw new Error('Invalid mode')
    state.mode = mode
    state.requestId += 1; state.pending = true
    if (mode === 'replay') state.replayEnd = state.payload?.max_cursor ?? 0
    send({ type: mode, cursor: 0, request_id: state.requestId })
    notify()
  }
  function play() {
    if (state.mode !== 'replay') return
    state.playing = true
    function advance() {
      if (!state.playing || disposed) return
      if (!state.pending) {
        const cursor = state.payload?.cursor ?? 0
        if (cursor >= state.replayEnd) { pause(); return }
        seek(cursor + 1)
      }
      playTimer = schedule(advance, 700)
    }
    advance(); notify()
  }
  function connect() {
    if (disposed) return
    const token = ++generation
    cancel(retryTimer); cancel(watchdog)
    socket?.close()
    state.connection = 'connecting'; state.pending = state.payload?.mode !== state.mode; notify()
    const current = new WebSocketImpl(url())
    socket = current
    current.onopen = () => {
      if (token !== generation || disposed) return
      state.connection = 'connected'; state.lastFrameAt = now()
      current.send(JSON.stringify({ type: 'hello', mode: state.mode,
        cursor: state.payload?.cursor ?? 0, end: state.replayEnd,
        request_id: state.requestId }))
      watch(); notify()
    }
    function watch() {
      cancel(watchdog)
      watchdog = schedule(() => {
        if (token !== generation || disposed) return
        if (now() - state.lastFrameAt >= 15000) {
          state.error = 'Backend heartbeat missing; reconnecting.'
          current.close()
        } else watch()
      }, 5000)
    }
    current.onmessage = ({ data }) => {
      if (token !== generation || disposed) return
      try {
        const frame = JSON.parse(data)
        if (frame.protocol_version !== 1 || !frame.payload) throw new Error('Invalid server snapshot')
        state.lastFrameAt = now()
        if (frame.mode !== state.mode || frame.request_id !== state.requestId) return
        if (frame.mode === 'replay') state.replayEnd = frame.payload.max_cursor
        state.payload = frame.payload; state.pending = false; state.error = ''
        notify()
      } catch { state.error = 'Unusable server message. Reconnect to resync.'; notify() }
    }
    current.onerror = () => { if (token === generation) current.close() }
    current.onclose = () => {
      if (token !== generation || disposed) return
      cancel(watchdog); pause()
      state.connection = 'disconnected'; state.pending = state.payload?.mode !== state.mode
      if (retries < 3) {
        state.error = 'Browser disconnected; retrying saved-state connection.'
        retryTimer = schedule(connect, [1000, 2000, 4000][retries++])
      } else state.error = 'Browser reconnect limit reached. Use Reconnect.'
      notify()
    }
  }
  function reconnect() { retries = 0; connect() }
  function dispose() {
    disposed = true; generation += 1
    cancel(retryTimer); cancel(watchdog); pause(); socket?.close()
  }
  return { state, connect, reconnect, setMode, seek, play, pause, dispose }
}
