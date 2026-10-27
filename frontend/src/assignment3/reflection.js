const BASE = '/api/assignment3/sessions'
export const SUPPORT_MESSAGE = 'This reflection will not be sent to the model. You can open Crisis Support using the always-available Crisis Support button.'
async function request(url, options = {}) {
  const response = await fetch(url, { ...options, headers: { 'Content-Type': 'application/json' }, signal: AbortSignal.timeout(20000) })
  if (!response.ok) {
    const error = await response.json().catch(() => null)
    if (response.status === 400 && error?.detail?.code === 'reflection_support') {
      throw Object.assign(new Error(SUPPORT_MESSAGE), { supportBlocked: true })
    }
    throw new Error(error?.detail || 'Reflection is unavailable. You can skip it or retry.')
  }
  return response.json()
}
export const reflectionApi = {
  submit: (id, reflection) => request(`${BASE}/${id}/reflection`, { method: 'POST', body: JSON.stringify({ reflection }) }),
  history: (id) => request(`${BASE}/${id}/conversation`),
}

export function createReflection({ api = reflectionApi, changed = () => {} } = {}) {
  const state = { input: '', submitted: false, pending: false, error: '', supportBlocked: false, messages: [], success: false, historyId: '', history: [], historyLoading: false, historyError: '' }
  let currentId = '', generation = 0, historyGeneration = 0
  function notify() { changed({ ...state }) }
  function reset(id) {
    if (id === currentId) return
    currentId = id; generation++
    Object.assign(state, { input: '', submitted: false, pending: false, error: '', supportBlocked: false, messages: [], success: false })
    notify()
  }
  function setInput(text) { if (!state.submitted) { state.input = text; notify() } }
  async function submit(id) {
    if (!id || state.pending || state.success || state.supportBlocked) return
    const text = state.input.trim()
    if (!text || state.input.length > 300) { state.error = 'Use 1–300 characters of fictional text.'; notify(); return }
    const version = generation
    state.pending = true; state.submitted = true; state.error = ''; notify()
    try {
      const messages = await api.submit(id, text)
      if (version !== generation) return
      state.messages = messages; state.success = messages.some((message) => message.role === 'assistant')
      if (!state.success) state.error = 'No saved assistant response is available. You can skip this or retry.'
    } catch (error) {
      if (version === generation) {
        state.supportBlocked = error.supportBlocked === true
        state.error = state.supportBlocked ? SUPPORT_MESSAGE : error.message || 'Reflection is unavailable. You can skip it or retry.'
        if (state.supportBlocked) state.input = ''
      }
    } finally { if (version === generation) { state.pending = false; notify() } }
  }
  async function load(id) {
    const version = ++historyGeneration
    state.historyId = id; state.history = []; state.historyLoading = true; state.historyError = ''; notify()
    try {
      const records = await api.history(id)
      if (version === historyGeneration) state.history = records
    } catch {
      if (version === historyGeneration) state.historyError = 'Saved conversation could not be loaded. Please retry.'
    } finally { if (version === historyGeneration) { state.historyLoading = false; notify() } }
  }
  return { state, reset, setInput, submit, load }
}
