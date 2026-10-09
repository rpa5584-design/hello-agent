import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import * as Vue from 'vue'
import { renderToString } from '@vue/server-renderer'
import { compileScript, parse } from '@vue/compiler-sfc'
import { createRagApi } from '../src/api/rag.js'
import { CONVERSATION_STORAGE_KEY, useChat } from '../src/composables/useChat.js'

const cid = '11111111-1111-4111-8111-111111111111'
const result = (rows = [], answer = 'No matching saved records. Simulated classroom data.') => ({ conversation_id: cid, answer, proposed_sql: 'SELECT name FROM saved_hotels LIMIT 3;', executed_sql: 'SELECT name FROM saved_hotels LIMIT 3', retrieved_row_count: rows.length, retrieved_rows: rows })
const response = data => ({ ok: true, json: async () => data })

test('only conversation ID is saved and restored on reload, then trace can be requested', async () => {
  const values = new Map(), writes = []
  const storage = { getItem: key => values.get(key), setItem: (key, value) => { writes.push([key, value]); values.set(key, value) } }
  const state = useChat(async () => ({ ...result(), api_key: 'must-not-store', answer: 'Private answer', retrieved_rows: [] }), undefined, storage)
  state.input.value = 'A hotel question'
  await state.send()
  assert.deepEqual(writes, [[CONVERSATION_STORAGE_KEY, cid]])
  assert.deepEqual([...values.values()], [cid])
  let sends = 0, requestedId
  const reloaded = useChat(async () => { sends++; return result() }, async id => { requestedId = id; return [] }, storage)
  assert.equal(reloaded.conversationId.value, cid)
  assert.deepEqual(reloaded.messages.value, [])
  assert.equal(sends, 0)
  const html = await renderToString(Vue.createSSRApp(await component(reloaded)))
  assert.ok(html.includes(cid) && html.includes('Reload saved trace'))
  await reloaded.reloadTrace()
  assert.equal(requestedId, cid)
  assert.equal(sends, 0)
  assert.equal(reloaded.traceLoaded.value, true)
  assert.deepEqual(writes, [[CONVERSATION_STORAGE_KEY, cid]])
})

test('invalid stored IDs are ignored and blocked storage does not break chat', async () => {
  const invalid = useChat(undefined, undefined, { getItem: () => 'not-a-conversation-id' })
  assert.equal(invalid.conversationId.value, '')
  const blocked = useChat(async () => result(), undefined, {
    getItem() { throw new Error('blocked') }, setItem() { throw new Error('blocked') },
  })
  blocked.input.value = 'Hotels?'
  await blocked.send()
  assert.equal(blocked.conversationId.value, cid)
  assert.equal(blocked.error.value, '')
})

async function component(state) {
  const source = await readFile(new URL('../src/components/BasicChat.vue', import.meta.url), 'utf8')
  const { descriptor } = parse(source)
  const code = compileScript(descriptor, { id: 'rag', inlineTemplate: true }).content
    .replace(/import \{([^}]+)\} from ['"]vue['"];?/g, (_, names) => `const {${names.replace(/\bas\b/g, ':')}} = Vue;`)
    .replace(/import \{ useChat \} from [^\n]+/, '')
    .replace('export default', 'return')
  return new Function('Vue', 'useChat', code)(Vue, () => state)
}

test('RAG uses our backend, retains allowed response fields and strips credential fields', async () => {
  const calls = []
  const api = createRagApi(async (url, options) => {
    calls.push([url, options])
    return response({ ...result([{ name: 'Saved Hotel', nightly_rate_cents: 10000, rooms_available: 20, api_key: 'do-not-display', Authorization: 'do-not-display' }], 'Saved Hotel: $100.00; simulated classroom data.'), api_key: 'do-not-display', provider_headers: { Authorization: 'do-not-display' } })
  })
  const data = await api.answer('Hotels?', cid)
  assert.equal(calls[0][0], '/api/rag/answer')
  assert.deepEqual(JSON.parse(calls[0][1].body), { question: 'Hotels?', conversation_id: cid })
  assert.deepEqual(calls[0][1].headers, { 'Content-Type': 'application/json' })
  assert.ok(!JSON.stringify(data).includes('do-not-display'))
  assert.equal(data.retrieved_rows[0].nightly_rate_cents, 10000)
  await api.answer('First question')
  assert.deepEqual(JSON.parse(calls[1][1].body), { question: 'First question' })
})

test('invalid/malformed backend responses are errors, never false no-match answers', async () => {
  for (const data of [null, {}, { ...result(), answer: '' }, { ...result(), retrieved_row_count: 21 }, { ...result(), conversation_id: 'bad' }, { ...result(), retrieved_rows: [null] }]) {
    await assert.rejects(createRagApi(async () => response(data)).answer('Hotels?'), /invalid answer/)
  }
  await assert.rejects(createRagApi(async () => { throw new Error('offline') }).answer('Hotels?'), /Could not reach/)
})

test('grounded answers/no-match retain ID for later messages; pending prevents duplicate requests', async () => {
  const calls = []
  let finish
  const state = useChat(async (question, conversationId) => {
    calls.push([question, conversationId])
    return new Promise(resolve => { finish = resolve })
  })
  state.input.value = 'Hotels in 16803?'
  const first = state.send()
  assert.equal(state.pending.value, true)
  await state.send()
  assert.equal(calls.length, 1)
  finish(result()); await first
  assert.equal(state.messages.value[1].text, result().answer)
  assert.equal(state.messages.value[1].details.retrieved_row_count, 0)
  assert.equal(state.conversationId.value, cid)
  state.input.value = 'Another complete question'
  const second = state.send()
  assert.equal(calls[1][1], cid)
  finish(result([{ name: 'Saved Hotel' }], 'Saved Hotel, simulated classroom data.')); await second
  assert.equal(state.messages.value.at(-1).details.retrieved_row_count, 1)
})

test('failed RAG retains error conversation ID and input; retry produces no fabricated earlier answer', async () => {
  let fail = true
  const api = createRagApi(async () => fail ? { ok: false, json: async () => ({ conversation_id: cid, detail: 'provider-secret' }) } : response(result()))
  const state = useChat(api.answer)
  state.input.value = 'Hotels?'
  await state.send()
  assert.equal(state.pending.value, false)
  assert.equal(state.input.value, 'Hotels?')
  assert.equal(state.conversationId.value, cid)
  assert.equal(state.messages.value.length, 1)
  assert.ok(!state.error.value.includes('provider-secret'))
  fail = false; await state.send()
  assert.equal(state.error.value, '')
  assert.equal(state.messages.value.filter(message => message.role === 'assistant').length, 1)
})

test('trace reload uses existing history endpoint and only allowed fields', async () => {
  const record = { message_id: 1, conversation_id: cid, timestamp: '2026-10-08T12:00:00+00:00', role: 'system', content: 'No matching rows', stage: 'retrieval_result', api_key: 'do-not-display' }
  let seen
  const api = createRagApi(async (url, options) => { seen = [url, options]; return response({ conversation_id: cid, messages: [record] }) })
  const state = useChat(async () => result(), api.history)
  state.conversationId.value = cid
  await state.reloadTrace()
  assert.equal(seen[0], `/api/rag/conversations/${cid}`)
  assert.equal(seen[1].method, 'GET')
  assert.equal(state.traceLoaded.value, true)
  assert.equal(state.trace.value[0].stage, 'retrieval_result')
  assert.ok(!JSON.stringify(state.trace.value).includes('do-not-display'))
  const failing = useChat(async () => result(), async () => { throw new Error('Trace unavailable') })
  failing.conversationId.value = cid
  await failing.reloadTrace()
  assert.equal(failing.tracePending.value, false)
  assert.equal(failing.traceError.value, 'Trace unavailable')
})

test('RAG panel renders safe details, escaped messages, no-match and status/error states', async () => {
  const safe = await createRagApi(async () => response({ ...result(), api_key: 'hidden-credential' })).answer('Hotels?')
  const state = useChat(async () => safe)
  state.input.value = '<script>Question</script>'
  await state.send()
  state.pending.value = true
  state.error.value = 'Unavailable'
  const html = await renderToString(Vue.createSSRApp(await component(state)))
  for (const text of ['RAG details', 'Conversation ID', 'Proposed SQL', 'Executed SQL', 'Retrieved row count', 'Retrieved records', cid, 'No matching saved records', 'Reload saved trace']) assert.ok(html.includes(text), text)
  assert.ok(!html.includes('hidden-credential'))
  assert.ok(!html.includes('Authorization') && !html.includes('api_key'))
  assert.ok(!html.includes('<script>Question</script>'))
  assert.match(html, /role="status"/)
  assert.match(html, /role="alert"/)
  assert.match(html, /<button[^>]*disabled/)
  assert.match(html, /<input[^>]*readonly/)
  assert.match(html, /for="chat-message"/)
})

test('native form submit handler supports keyboard submission and prevents navigation', async () => {
  let sent = 0, prevented = false
  const state = useChat(async () => { sent++; return result() })
  state.input.value = 'Hotels?'
  state.send = () => { sent++ }
  const renderer = Vue.createRenderer({
    createElement: tag => ({ tag, props: {}, children: [], addEventListener() {} }),
    createText: text => ({ text }), createComment: text => ({ text }),
    setText(node, text) { node.text = text }, setElementText(node, text) { node.text = text },
    patchProp(node, key, _previous, value) { node.props[key] = value },
    insert(node, parent) { node.parent = parent; parent.children.push(node) },
    remove(node) { node.parent.children = node.parent.children.filter(child => child !== node) },
    parentNode: node => node.parent, nextSibling: () => null,
  })
  const root = { children: [] }
  renderer.createApp(await component(state)).mount(root)
  function find(node, tag) { return node.tag === tag ? node : node.children?.map(child => find(child, tag)).find(Boolean) }
  const form = find(root, 'form'), input = find(root, 'input'), button = find(root, 'button')
  assert.equal(input.props.id, 'chat-message')
  assert.equal(input.props.type, 'text')
  assert.equal(button.props.type, 'submit')
  form.props.onSubmit({ preventDefault() { prevented = true } })
  await Vue.nextTick()
  assert.equal(prevented, true)
  assert.equal(sent, 1)
})
