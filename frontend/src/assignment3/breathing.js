export const INHALE_MS = 4000
export const EXHALE_MS = 6000
export const CYCLES = 6
export const PLANNED_MS = CYCLES * (INHALE_MS + EXHALE_MS)

// A delayed callback never skips ahead through cues. Each cue gets its full time.
export function createBreathing({ now = Date.now, changed = () => {} } = {}) {
  const state = { screen: 'home', status: null, phase: null, cycle: 0, remaining: 0, durationMs: null }
  let startedAt = 0, phaseAt = 0, lastTick = 0
  const active = () => state.status === 'active'
  function end(status, at = now()) {
    if (!active()) return
    state.durationMs = Math.max(0, at - startedAt)
    state.status = status
    state.phase = null
    state.screen = status === 'completed' ? 'finished' : status
  }
  function navigate(screen) {
    end('stopped')
    state.screen = screen
    changed()
  }
  function start() {
    if (active()) return
    startedAt = phaseAt = lastTick = now()
    Object.assign(state, { screen: 'exercise', status: 'active', phase: 'Inhale', cycle: 1, remaining: 4, durationMs: null })
    changed()
  }
  function tick() {
    if (!active()) return
    const at = now()
    // One second is an engineering interruption threshold, not a clinical rule.
    if (at < lastTick || at - lastTick > 1000 || at - startedAt >= 90000) {
      end('interrupted', at)
    } else {
      const phaseMs = state.phase === 'Inhale' ? INHALE_MS : EXHALE_MS
      if (at - phaseAt >= phaseMs) {
        if (state.phase === 'Inhale') state.phase = 'Exhale'
        else if (state.cycle === CYCLES) end('completed', at)
        else { state.cycle++; state.phase = 'Inhale' }
        phaseAt = at
      }
      if (active()) state.remaining = Math.max(0, Math.ceil(((state.phase === 'Inhale' ? INHALE_MS : EXHALE_MS) - (at - phaseAt)) / 1000))
    }
    lastTick = at
    changed()
  }
  function stop() { end('stopped'); changed() }
  function interrupt() { end('interrupted'); changed() }
  return { state, start, tick, stop, interrupt, navigate }
}
