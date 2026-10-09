import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import * as Vue from 'vue'
import { renderToString } from '@vue/server-renderer'
import { compileScript, parse } from '@vue/compiler-sfc'
import { sendChat } from '../src/api/chat.js'
import { useChat } from '../src/composables/useChat.js'

const ragResult = answer => ({ conversation_id: '11111111-1111-4111-8111-111111111111', answer, proposed_sql: 'SELECT name FROM saved_hotels LIMIT 3;', executed_sql: 'SELECT name FROM saved_hotels LIMIT 3', retrieved_row_count: 0, retrieved_rows: [] })

test('chat posts only the message to our backend and validates replies', async () => {
  assert.equal(await sendChat('Hello', async (url, options) => {
    assert.equal(url, '/api/chat')
    assert.equal(options.method, 'POST')
    assert.deepEqual(JSON.parse(options.body), { message: 'Hello' })
    assert.deepEqual(options.headers, { 'Content-Type': 'application/json' })
    return { ok: true, json: async () => ({ reply: 'Connected' }) }
  }), 'Connected')
  for (const reply of [null, {}, { reply: '' }]) {
    await assert.rejects(sendChat('Hi', async () => ({ ok: true, json: async () => reply })), /invalid answer/)
  }
  await assert.rejects(sendChat('Hi', async () => ({ ok: false })), /unavailable/)
  await assert.rejects(sendChat('Hi', async () => { throw new Error('offline') }), /Could not reach/)
})

test('pending blocks duplicate sends, then success appends assistant and clears input', async () => {
  let finish, calls = 0
  const state = useChat(async () => { calls++; return new Promise(resolve => { finish = resolve }) })
  state.input.value = ' Hello '
  const pending = state.send()
  assert.equal(state.pending.value, true)
  await state.send()
  assert.equal(calls, 1)
  assert.deepEqual(state.messages.value, [{ role: 'user', text: 'Hello' }])
  finish(ragResult('Connected')); await pending
  assert.equal(state.pending.value, false)
  assert.equal(state.input.value, '')
  assert.equal(state.messages.value[1].text, 'Connected')
})

test('failure retains input for retry; blank input never sends', async () => {
  let fail = true, calls = 0
  const state = useChat(async () => { calls++; if (fail) throw new Error('Unavailable'); return ragResult('Recovered') })
  state.input.value = ' '
  await state.send()
  assert.equal(calls, 0)
  state.input.value = 'Hi'
  await state.send()
  assert.equal(state.pending.value, false)
  assert.equal(state.input.value, 'Hi')
  assert.equal(state.error.value, 'Unavailable')
  assert.equal(state.messages.value.length, 1)
  fail = false; await state.send()
  assert.equal(state.error.value, '')
  assert.equal(state.messages.value.at(-1).text, 'Recovered')
})

test('chat renders labels, messages as escaped text, loading and errors', async () => {
  const source = await readFile(new URL('../src/components/BasicChat.vue', import.meta.url), 'utf8')
  const { descriptor } = parse(source)
  const compiled = compileScript(descriptor, { id: 'chat', inlineTemplate: true }).content
    .replace(/import \{([^}]+)\} from ['"]vue['"];?/g, (_, names) => `const {${names.replace(/\bas\b/g, ':')}} = Vue;`)
    .replace(/import \{ useChat \} from [^\n]+/, '')
    .replace('export default', 'return')
  const state = { input: Vue.ref('Hi'), messages: Vue.ref([{ role: 'user', text: '<script>Hi</script>' }, { role: 'assistant', text: 'Hello' }]), pending: Vue.ref(true), error: Vue.ref('Unavailable'), send() {} }
  const component = new Function('Vue', 'useChat', compiled)(Vue, () => state)
  const html = await renderToString(Vue.createSSRApp(component))
  assert.match(html, /for="chat-message"/)
  assert.match(html, /role="log"/)
  assert.match(html, /role="status"/)
  assert.match(html, /role="alert"/)
  assert.match(html, /<button[^>]*disabled/)
  assert.ok(html.includes('You:') && html.includes('Assistant:'))
  assert.ok(html.includes('&lt;script&gt;'))
  assert.ok(!html.includes('<script>'))
})
