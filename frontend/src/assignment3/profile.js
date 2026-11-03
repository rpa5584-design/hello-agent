const URL = '/api/assignment3/profile'
async function request(options = {}) {
  const response = await fetch(URL, { ...options, headers: { 'Content-Type': 'application/json' }, signal: AbortSignal.timeout(5000) })
  if (!response.ok) throw new Error('Preferences are unavailable.')
  const profile = await response.json()
  if (typeof profile.display_name !== 'string' || profile.display_name.length > 60 || !['standard', 'fewer'].includes(profile.guidance_mode)) throw new Error('Preferences are unavailable.')
  return profile
}
export const profileApi = {
  load: () => request(),
  save: profile => request({ method: 'PATCH', body: JSON.stringify(profile) }),
}

export function createProfileStore({ api = profileApi, changed = () => {} } = {}) {
  const state = { displayName: '', guidanceMode: 'standard', loading: false, saving: false, dirty: false, error: '', notice: '' }
  let revision = 0
  const notify = () => changed({ ...state })
  function edit(field, value) {
    if (field === 'guidanceMode' && !['standard', 'fewer'].includes(value)) return
    revision++; state[field] = value; state.dirty = true; state.notice = ''; notify()
  }
  async function load() {
    if (state.loading) return
    const version = revision
    state.loading = true; state.error = ''; notify()
    try {
      const profile = await api.load()
      if (version === revision) {
        state.displayName = profile.display_name; state.guidanceMode = profile.guidance_mode; state.dirty = false
      }
    } catch {
      state.error = 'Saved preferences could not be loaded. You can still choose guidance for this page.'
    } finally { state.loading = false; notify() }
  }
  async function save() {
    if (state.saving || state.loading) return
    if (state.displayName.length > 60) { state.error = 'Use up to 60 characters for a fictional name.'; notify(); return }
    const version = revision
    state.saving = true; state.error = ''; state.notice = ''; notify()
    try {
      const profile = await api.save({ display_name: state.displayName.trim(), guidance_mode: state.guidanceMode })
      if (version === revision) {
        state.displayName = profile.display_name; state.guidanceMode = profile.guidance_mode
        state.dirty = false; state.notice = 'Preferences saved locally.'
      }
    } catch {
      state.error = 'Preferences were not saved. Your choice still applies on this page; you can retry saving.'
    } finally { state.saving = false; notify() }
  }
  return { state, load, save, setName: value => edit('displayName', value), setMode: value => edit('guidanceMode', value) }
}
