import { test } from 'node:test'
import assert from 'node:assert/strict'
import * as Vue from 'vue'
import { renderToString } from '@vue/server-renderer'
import { createProfileStore, profileApi } from '../src/assignment3/profile.js'
import { createBreathing } from '../src/assignment3/breathing.js'
import { createSessionStore } from '../src/assignment3/sessions.js'
import { createReflection } from '../src/assignment3/reflection.js'
import { component, host, textOf, find, flush } from './helpers/assignment3Presentation.js'

test('profile saves the choice and reloads it in a new store', async () => {
  let saved = { display_name: '', guidance_mode: 'standard' }
  const api = { async load() { return saved }, async save(body) { saved = body; return saved } }
  const model = createProfileStore({ api })
  await model.load(); model.setName('  Demo  '); model.setMode('fewer'); await model.save()
  assert.deepEqual(saved, { display_name: 'Demo', guidance_mode: 'fewer' })
  assert.equal(model.state.notice, 'Preferences saved locally.')
  const reloaded = createProfileStore({ api }); await reloaded.load()
  assert.equal(reloaded.state.guidanceMode, 'fewer')
  assert.equal(reloaded.state.displayName, 'Demo')
  reloaded.setMode('standard'); await reloaded.save()
  assert.equal(saved.guidance_mode, 'standard')
})

test('failed profile loading/saving leaves a usable local choice and honest error', async () => {
  const model = createProfileStore({ api: { load: async () => { throw new Error() }, save: async () => { throw new Error() } } })
  await model.load(); assert.match(model.state.error, /could not be loaded/)
  model.setMode('fewer'); await model.save()
  assert.equal(model.state.guidanceMode, 'fewer')
  assert.match(model.state.error, /not saved/)
  assert.equal(model.state.notice, '')
  assert.equal(model.state.dirty, true)
})

test('late profile load cannot overwrite the user override', async () => {
  let resolve
  const model = createProfileStore({ api: { load: () => new Promise(done => { resolve = done }) } })
  const pending = model.load(); model.setMode('fewer')
  resolve({ display_name: '', guidance_mode: 'standard' }); await pending
  assert.equal(model.state.guidanceMode, 'fewer')
  assert.equal(model.state.dirty, true)
})

test('late save cannot overwrite a newer choice', async () => {
  let resolve
  const model = createProfileStore({ api: { save: () => new Promise(done => { resolve = done }) } })
  model.setMode('fewer'); const pending = model.save(); model.setMode('standard')
  resolve({ display_name: '', guidance_mode: 'fewer' }); await pending
  assert.equal(model.state.guidanceMode, 'standard')
  assert.equal(model.state.dirty, true)
  assert.equal(model.state.notice, '')
})

test('profile API uses backend GET/PATCH and rejects invalid returned preference', async t => {
  const original = globalThis.fetch; t.after(() => { globalThis.fetch = original })
  const calls = []
  globalThis.fetch = async (url, options) => { calls.push([url, options]); return { ok: true, json: async () => ({ display_name: 'Demo', guidance_mode: 'fewer' }) } }
  await profileApi.load(); await profileApi.save({ display_name: 'Demo', guidance_mode: 'fewer' })
  assert.equal(calls[0][0], '/api/assignment3/profile')
  assert.equal(calls[0][1].method, undefined)
  assert.equal(calls[1][1].method, 'PATCH')
  assert.deepEqual(JSON.parse(calls[1][1].body), { display_name: 'Demo', guidance_mode: 'fewer' })
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ display_name: 'Demo', guidance_mode: 'clinical' }) })
  await assert.rejects(profileApi.load(), /unavailable/)
})

test('profile card has explicit labels, native radios and honest loading/error/status text', async () => {
  const Card = await component('PreferencesCard.vue')
  const html = await renderToString(Vue.createSSRApp({ render: () => Vue.h(Card, { state: { displayName: '<Demo>', guidanceMode: 'fewer', loading: true, error: 'Not saved' } }) }))
  for (const text of ['Your preferences', 'Optional name (fictional)', 'for="fictional-name"', 'How much guidance would you like today?', 'Standard guidance', 'Fewer instructions', 'not a clinical assessment', 'aria-describedby="preference-help"', 'type="radio"', 'role="alert"', 'role="status"', '&lt;Demo&gt;']) assert.ok(html.includes(text), text)
})

test('recent activity shows only actual saved facts, empty and error states', async () => {
  const Activity = await component('RecentActivity.vue')
  const render = props => renderToString(Vue.createSSRApp({ render: () => Vue.h(Activity, props) }))
  const html = await render({ loaded: true, guidanceMode: 'fewer', records: [{ status: 'completed', measured_duration_seconds: 60.6 }] })
  for (const text of ['Fewer instructions', 'Paced Breathing', 'completed', '60.6 seconds', 'Saved sessions loaded: 1']) assert.ok(html.includes(text), text)
  assert.match(await render({ loaded: true, records: [] }), /No saved sessions yet/)
  assert.match(await render({ loaded: true, records: [{ status: 'interrupted', measured_duration_seconds: null }] }), /Duration unavailable/)
  const failed = await render({ error: 'History unavailable' })
  assert.match(failed, /History unavailable/)
  assert.ok(!failed.includes('No saved sessions yet'))
})

for (const mode of ['standard', 'fewer']) {
  test(`mounted ${mode} preference can be overridden on Home/intro; timing and safety stay intact`, async t => {
    const original = { document: globalThis.document, window: globalThis.window }
    globalThis.document = { addEventListener() {}, removeEventListener() {} }
    globalThis.window = { addEventListener() {}, removeEventListener() {} }
    let app
    t.after(() => { app?.unmount(); Object.assign(globalThis, original) })
    const PreferencesCard = await component('PreferencesCard.vue')
    const RecentActivity = await component('RecentActivity.vue')
    const ReflectionPanel = await component('ReflectionPanel.vue', { createReflection })
    const created = []
    let run, time = 0
    const Shell = await component('Assignment3Shell.vue', { PreferencesCard, RecentActivity, ReflectionPanel,
      createSessionStore: options => createSessionStore({ storage: { getItem: () => null, setItem() {} }, id: () => 'demo-session', api: {
        async list() { return [] }, async create(body) { created.push(body) }, async finish() {},
      }, ...options }), createProfileStore: options => {
        // Exercise the real store with the shell's update callback.
        return createProfileStore({ api: { async load() { return { display_name: 'Demo', guidance_mode: mode } }, async save(body) { return body } }, ...options })
      },
      createBreathing: options => { run = createBreathing({ ...options, now: () => time }); return run },
    })
    const { renderer, root } = host(); app = renderer.createApp(Shell); app.mount(root); await flush()
    assert.match(textOf(root), /Your preferences/)
    assert.match(textOf(root), /Welcome, Demo/)
    assert.match(textOf(root), /No saved sessions yet/)
    const opposite = mode === 'fewer' ? 'standard' : 'fewer'
    find(root, el => el.type === 'input' && el.props.value === opposite).props.onChange(); await flush()
    assert.equal(find(root, el => el.type === 'input' && el.props.value === opposite).props.checked, true)
    find(root, el => el.type === 'button' && textOf(el) === 'Paced Breathing').props.onClick(); await flush()
    assert.ok(find(root, el => el.type === 'input' && el.props.value === mode))
    find(root, el => el.type === 'input' && el.props.value === mode).props.onChange(); await flush()
    find(root, el => el.type === 'button' && textOf(el) === 'Start').props.onClick(); await flush()
    assert.equal(created[0].fewer_options, mode === 'fewer')
    assert.equal(textOf(root).includes('Follow the text cues'), mode === 'standard')
    for (const label of ['Stop', 'Back', 'Leave', 'Crisis Support']) assert.ok(find(root, el => el.type === 'button' && textOf(el) === label))
    assert.match(textOf(root), /Exercise in progress/)
    assert.match(textOf(root), /Inhale/)
    for (time = 100; time <= 4000; time += 100) run.tick()
    await flush(); assert.equal(run.state.phase, 'Exhale')
    for (time = 4100; time <= 60000; time += 100) run.tick()
    await flush()
    assert.equal(run.state.status, 'completed')
    assert.equal(run.state.durationMs, 60000)
  })
}
