import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import * as Vue from 'vue'
import { renderToString } from '@vue/server-renderer'
import { compileScript, parse } from '@vue/compiler-sfc'
import { createBreathing, PLANNED_MS } from '../src/assignment3/breathing.js'
import { createSessionStore } from '../src/assignment3/sessions.js'

function clock() {
  let time = 0
  const run = createBreathing({ now: () => time })
  return { run, advance(ms) { for (let i = 0; i < ms; i += 100) { time += 100; run.tick() } }, jump(ms) { time += ms; run.tick() } }
}
test('explicit Start, full inhale/exhale sequence and six cycles measure 60 seconds', () => {
  const { run, advance } = clock()
  advance(5000)
  assert.equal(run.state.status, null)
  run.navigate('intro')
  assert.equal(run.state.status, null)
  run.start()
  assert.equal(PLANNED_MS, 60000)
  for (let cycle = 1; cycle <= 6; cycle++) {
    assert.equal(run.state.cycle, cycle)
    assert.equal(run.state.phase, 'Inhale')
    advance(3900); assert.equal(run.state.phase, 'Inhale')
    advance(100); assert.equal(run.state.phase, 'Exhale')
    advance(5900); assert.equal(run.state.phase, 'Exhale')
    advance(100)
  }
  assert.equal(run.state.status, 'completed')
  assert.equal(run.state.screen, 'finished')
  assert.equal(run.state.durationMs, 60000)
})
for (const phaseMs of [0, 4000]) {
  test(`Stop ends timing at ${phaseMs} ms`, () => {
    const { run, advance } = clock()
    run.start(); advance(phaseMs); run.stop(); advance(10000)
    assert.equal(run.state.status, 'stopped')
    assert.equal(run.state.phase, null)
    assert.equal(run.state.durationMs, phaseMs)
  })
  for (const screen of ['home', 'leave', 'support']) {
    test(`${screen} navigation stops timing at ${phaseMs} ms`, () => {
      const { run, advance } = clock()
      run.start(); advance(phaseMs); run.navigate(screen); advance(10000)
      assert.equal(run.state.status, 'stopped')
      assert.equal(run.state.screen, screen)
      assert.equal(run.state.phase, null)
    })
  }
}
test('background interruption and suspension never catch up or resume automatically', () => {
  const { run, advance, jump } = clock()
  run.start(); advance(1000); run.interrupt(); advance(60000)
  assert.equal(run.state.status, 'interrupted')
  run.start(); assert.equal(run.state.phase, 'Inhale')
  jump(60000); assert.equal(run.state.status, 'interrupted')
  assert.equal(run.state.phase, null)
})
test('small delays extend the actual measured duration without skipping cues', () => {
  const { run, advance, jump } = clock()
  run.start(); advance(3900); jump(200)
  assert.equal(run.state.phase, 'Exhale')
  advance(5900); assert.equal(run.state.phase, 'Exhale')
  advance(100); assert.equal(run.state.cycle, 2)
  advance(50000); assert.equal(run.state.durationMs, 60100)
})
test('every rendered screen retains native safety controls and boundaries without an API', async () => {
  const source = await readFile(new URL('../src/components/assignment3/Assignment3Shell.vue', import.meta.url), 'utf8')
  const { descriptor } = parse(source)
  const compiled = compileScript(descriptor, { id: 'assignment3', inlineTemplate: true })
  const code = compiled.content
    .replace(/import \{([^}]+)\} from ['"]vue['"];?/g, (_, names) => `const {${names.replace(/\bas\b/g, ':')}} = Vue;`)
    .replace(/import \{ createBreathing \} from [^\n]+/, '')
    .replace(/import \{ createSessionStore \} from [^\n]+/, '')
    .replace(/import ReflectionPanel from [^\n]+/, 'const ReflectionPanel = { render: () => null }')
    .replace('export default', 'return')
  assert.ok(!source.includes('fetch('))
  for (const screen of ['home', 'intro', 'exercise', 'finished', 'stopped', 'interrupted', 'leave', 'support', 'history']) {
    const run = createBreathing()
    if (screen === 'exercise') run.start()
    else run.navigate(screen)
    const component = new Function('Vue', 'createBreathing', 'createSessionStore', code)(Vue, () => run, createSessionStore)
    const html = await renderToString(Vue.createSSRApp(component))
    for (const text of ['Coursework skills prototype', 'Not therapy or diagnosis', 'Nobody is monitoring this experience', 'Testing uses fictional scenarios only', '>Back</button>', '>Leave</button>', '>Crisis Support</button>']) assert.ok(html.includes(text), `${screen}: ${text}`)
    if (screen === 'exercise') assert.match(html, />Stop<\/button>/)
    if (screen === 'intro') assert.match(html, />Start<\/button>/)
    if (screen === 'support') for (const text of ['Call or text 988', '988 Suicide', '911', 'requires network access']) assert.ok(html.includes(text))
    if (screen === 'home') assert.ok(!html.includes('Cycle 1 of 6'))
  }
  const scenarios = [
    [{ loading: true }, 'Loading Saved History'],
    [{ loaded: true }, 'No saved sessions yet.'],
    [{ historyError: 'Saved History could not be loaded.' }, 'Saved History could not be loaded.'],
    [{ warning: 'Session changes could not be saved.' }, 'Retry saving'],
    [{ history: [{ session_id: 'compare-this-id', started_at: '2026-10-21T14:00:00Z', selected_skill: 'paced_breathing_4_6', status: 'completed', measured_duration_seconds: 60.8 }] }, '60.8 seconds'],
  ]
  for (const [overrides, expected] of scenarios) {
    const run = createBreathing(); run.navigate('history')
    const mockStore = () => ({ state: { history: [], ...overrides } })
    const component = new Function('Vue', 'createBreathing', 'createSessionStore', code)(Vue, () => run, mockStore)
    const html = await renderToString(Vue.createSSRApp(component))
    assert.ok(html.includes(expected), expected)
    assert.ok(html.includes('>Crisis Support</button>'))
    assert.equal(run.state.status, null)
  }
})
test('separate HTML entries preserve RoomTour', async () => {
  const read = (path) => readFile(new URL(path, import.meta.url), 'utf8')
  assert.match(await read('../index.html'), /src="\/src\/main.js"/)
  assert.match(await read('../src/main.js'), /import App from '.\/App.vue'/)
  assert.match(await read('../assignment3.html'), /src="\/src\/assignment3\/main.js"/)
})
