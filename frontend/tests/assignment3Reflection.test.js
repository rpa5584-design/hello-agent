import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import * as Vue from 'vue'
import { renderToString } from '@vue/server-renderer'
import { compileScript, parse } from '@vue/compiler-sfc'
import { createReflection } from '../src/assignment3/reflection.js'

const answer = [{ message_id: 1, role: 'user', content: 'A fictional pause.' }, { message_id: 2, role: 'assistant', content: 'The fictional reflection describes a pause.' }]

test('reflection is optional and never sends automatically; explicit submit saves success', async () => {
  const calls = []
  const reflection = createReflection({ api: { async submit(id, text) { calls.push([id, text]); return answer } } })
  reflection.reset('session')
  reflection.setInput('A fictional pause.')
  assert.deepEqual(calls, [])
  await reflection.submit('session')
  assert.deepEqual(calls, [['session', 'A fictional pause.']])
  assert.equal(reflection.state.success, true)
  assert.deepEqual(reflection.state.messages, answer)
  await reflection.submit('session')
  assert.equal(calls.length, 1)
})

test('pending state prevents duplicate submission', async () => {
  let resolve, calls = 0
  const reflection = createReflection({ api: { submit() { calls++; return new Promise((done) => { resolve = done }) } } })
  reflection.reset('session'); reflection.setInput('A fictional pause.')
  const pending = reflection.submit('session')
  assert.equal(reflection.state.pending, true)
  await reflection.submit('session')
  resolve(answer); await pending
  assert.equal(calls, 1)
  assert.equal(reflection.state.pending, false)
})

test('failure is honest and explicit Retry resends the same reflection only', async () => {
  const calls = []
  let fail = true
  const reflection = createReflection({ api: { async submit(id, text) { calls.push([id, text]); if (fail) throw new Error('That reflection response is unavailable.'); return answer } } })
  reflection.reset('session'); reflection.setInput('A fictional pause.')
  await reflection.submit('session')
  assert.match(reflection.state.error, /unavailable/)
  assert.deepEqual(reflection.state.messages, [])
  reflection.setInput('Cannot replace a submitted reflection')
  fail = false; await reflection.submit('session')
  assert.deepEqual(calls[0], calls[1])
  assert.equal(reflection.state.success, true)
})

test('300-character limit is enforced before a request', async () => {
  let calls = 0
  const reflection = createReflection({ api: { async submit() { calls++; return answer } } })
  reflection.reset('session'); reflection.setInput('x'.repeat(301)); await reflection.submit('session')
  assert.match(reflection.state.error, /1–300/)
  assert.equal(calls, 0)
  reflection.setInput('x'.repeat(300)); await reflection.submit('session')
  assert.equal(calls, 1)
})

test('Saved History reads user/assistant/error records without a model request', async () => {
  let reads = 0, writes = 0
  const records = [...answer, { message_id: 3, role: 'error', content: 'A previous request failed.' }]
  const reflection = createReflection({ api: { async history() { reads++; return records }, async submit() { writes++ } } })
  await reflection.load('saved-session')
  assert.deepEqual(reflection.state.history, records)
  assert.equal(reads, 1); assert.equal(writes, 0)
})

test('stale model responses do not replace a new session', async () => {
  let resolve
  const reflection = createReflection({ api: { submit: () => new Promise((done) => { resolve = done }) } })
  reflection.reset('old'); reflection.setInput('Fictional.')
  const pending = reflection.submit('old')
  reflection.reset('new'); resolve(answer); await pending
  assert.deepEqual(reflection.state.messages, [])
  assert.equal(reflection.state.pending, false)
})

async function renderPanel(state, review = false) {
  const source = await readFile(new URL('../src/components/assignment3/ReflectionPanel.vue', import.meta.url), 'utf8')
  const { descriptor } = parse(source)
  const compiled = compileScript(descriptor, { id: 'reflection', inlineTemplate: true })
  const code = compiled.content
    .replace(/import \{([^}]+)\} from ['"]vue['"];?/g, (_, names) => `const {${names.replace(/\bas\b/g, ':')}} = Vue;`)
    .replace(/import \{ createReflection \} from [^\n]+/, '')
    .replace('export default', 'return')
  const model = createReflection()
  Object.assign(model.state, state)
  const component = new Function('Vue', 'createReflection', code)(Vue, () => model)
  return renderToString(Vue.createSSRApp({ render: () => Vue.h(component, { sessionId: 'saved-session', review }) }))
}

test('form renders optional wording, visible character limit, loading, success and retry', async () => {
  const form = await renderPanel({})
  assert.match(form, /You can skip this/)
  assert.match(form, /maxlength="300"/)
  assert.match(form, /0 \/ 300 characters/)
  assert.match(form, /Optional reflection: In one short sentence/)
  assert.match(await renderPanel({ pending: true, submitted: true }), /Waiting for a reflection response/)
  assert.match(await renderPanel({ error: 'Unavailable', submitted: true }), /Retry reflection/)
  assert.match(await renderPanel({ messages: answer, success: true, submitted: true }), /Model acknowledgment/)
})

test('saved conversation renders roles and escapes content as display-only text', async () => {
  const html = await renderPanel({ history: [...answer, { message_id: 3, role: 'error', content: '<script>unsafe()</script>' }] }, true)
  for (const label of ['Fictional reflection', 'Model acknowledgment', 'Error']) assert.ok(html.includes(label))
  assert.ok(html.includes('&lt;script&gt;'))
  assert.ok(!html.includes('<script>'))
  assert.match(await renderPanel({ historyError: 'Could not load' }, true), /Retry loading conversation/)
})

test('model error stays beside visible Crisis Support in the actual Assignment 3 shell', async () => {
  const panelSource = await readFile(new URL('../src/components/assignment3/ReflectionPanel.vue', import.meta.url), 'utf8')
  const parentSource = await readFile(new URL('../src/components/assignment3/Assignment3Shell.vue', import.meta.url), 'utf8')
  const compile = (source) => compileScript(parse(source).descriptor, { id: 'model-error', inlineTemplate: true }).content
    .replace(/import \{([^}]+)\} from ['"]vue['"];?/g, (_, names) => `const {${names.replace(/\bas\b/g, ':')}} = Vue;`)
    .replace(/import (?:\{[^}]+\}|ReflectionPanel) from [^\n]+/g, '')
    .replace('export default', 'return')
  let calls = 0
  const model = createReflection({ api: { async submit() { calls++ } } })
  Object.assign(model.state, { submitted: true, error: 'That reflection response is unavailable.' })
  const Panel = new Function('Vue', 'createReflection', compile(panelSource))(Vue, () => model)
  const { createBreathing } = await import('../src/assignment3/breathing.js')
  const run = createBreathing(); run.start(); run.stop()
  const component = new Function('Vue', 'createBreathing', 'createSessionStore', 'ReflectionPanel', compile(parentSource))(Vue, () => run, () => ({ state: { sessionId: 'saved-session' } }), Panel)
  const html = await renderToString(Vue.createSSRApp(component))
  assert.ok(html.includes('That reflection response is unavailable.'))
  assert.ok(html.includes('Retry reflection'))
  assert.ok(html.includes('>Crisis Support</button>'))
  assert.equal(calls, 0)
})


test('local support response clears text, suppresses retry, and uses fixed wording', async () => {
  const { SUPPORT_MESSAGE } = await import('../src/assignment3/reflection.js')
  let calls = 0
  const model = createReflection({ api: { async submit() {
    calls++
    throw Object.assign(new Error('untrusted wording'), { supportBlocked: true })
  } } })
  model.reset('session'); model.setInput('Fictional suicidal text.')
  await model.submit('session'); await model.submit('session')
  assert.equal(calls, 1)
  assert.equal(model.state.input, '')
  assert.equal(model.state.error, SUPPORT_MESSAGE)
  assert.equal(model.state.success, false)
  const html = await renderPanel(model.state)
  assert.ok(html.includes(SUPPORT_MESSAGE))
  assert.ok(!html.includes('Retry reflection'))
  model.reset('another-session')
  assert.equal(model.state.supportBlocked, false)
})


test('API maps only the local support error code to the fixed support state', async () => {
  const { reflectionApi, SUPPORT_MESSAGE } = await import('../src/assignment3/reflection.js')
  const original = globalThis.fetch
  globalThis.fetch = async () => ({ ok: false, status: 400, json: async () => ({ detail: { code: 'reflection_support', message: 'ignored' } }) })
  try {
    await assert.rejects(reflectionApi.submit('session', 'Fictional.'), (error) => error.supportBlocked === true && error.message === SUPPORT_MESSAGE)
  } finally { globalThis.fetch = original }
})
