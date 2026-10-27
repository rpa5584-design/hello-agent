import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import * as Vue from 'vue'
import { compileScript, parse } from '@vue/compiler-sfc'
import { createReflection } from '../src/assignment3/reflection.js'
import { createBreathing } from '../src/assignment3/breathing.js'

async function component(file, dependencies) {
  const source = await readFile(new URL(file, import.meta.url), 'utf8')
  const { content } = compileScript(parse(source).descriptor, { id: file, inlineTemplate: true })
  const code = content
    .replace(/import \{([^}]+)\} from ['"]vue['"];?/g, (_, names) => `const {${names.replace(/\bas\b/g, ':')}} = Vue;`)
    .replace(/^import .*$/gm, '').replace('export default', 'return')
  return new Function('Vue', ...Object.keys(dependencies), code)(Vue, ...Object.values(dependencies))
}

function host() {
  const node = (type, text = '') => ({ type, text, children: [], props: {}, parent: null, focus() {} })
  const remove = child => {
    if (child.parent) child.parent.children.splice(child.parent.children.indexOf(child), 1)
    child.parent = null
  }
  const renderer = Vue.createRenderer({
    createElement: node, createText: text => node('text', text), createComment: text => node('comment', text),
    setText: (el, text) => { el.text = text },
    setElementText: (el, text) => { el.text = text; el.children = [] },
    patchProp: (el, key, _old, value) => { el.props[key] = value },
    insert(child, parent, anchor = null) {
      remove(child); child.parent = parent
      const index = anchor ? parent.children.indexOf(anchor) : -1
      parent.children.splice(index < 0 ? parent.children.length : index, 0, child)
    },
    remove, parentNode: el => el.parent,
    nextSibling: el => el.parent?.children[el.parent.children.indexOf(el) + 1] || null,
  })
  return { renderer, root: node('root') }
}
const textOf = node => node.text + node.children.map(textOf).join(' ')
const find = (node, predicate) => predicate(node) ? node : node.children.map(child => find(child, predicate)).find(Boolean)
const flush = async () => { for (let i = 0; i < 6; i++) await Vue.nextTick() }

for (const scenario of ['saved', 'empty', 'error']) {
  test(`mounted history click shows ${scenario} state beside its session using only GET`, async t => {
    const original = { fetch: globalThis.fetch, document: globalThis.document, window: globalThis.window }
    const calls = []
    let resolve
    globalThis.fetch = (url, options) => {
      calls.push({ url, method: options.method || 'GET' })
      assert.equal(options.method || 'GET', 'GET')
      return new Promise(done => { resolve = done })
    }
    globalThis.document = { addEventListener() {}, removeEventListener() {} }
    globalThis.window = { addEventListener() {}, removeEventListener() {} }
    let app
    t.after(() => { app?.unmount(); Object.assign(globalThis, original) })
    const Panel = await component('../src/components/assignment3/ReflectionPanel.vue', { createReflection })
    const run = createBreathing(); run.navigate('history')
    const rows = ['selected-session', 'other-session'].map(session_id => ({ session_id, status: 'stopped', started_at: '2026-10-27T14:00:00Z', selected_skill: 'paced_breathing_4_6', measured_duration_seconds: 5.5 }))
    const Shell = await component('../src/components/assignment3/Assignment3Shell.vue', {
      ReflectionPanel: Panel, createBreathing: () => run,
      createSessionStore: () => ({ state: { history: rows }, recover() {} }),
    })
    const { renderer, root } = host()
    app = renderer.createApp(Shell); app.mount(root)
    const button = find(root, el => el.type === 'button' && textOf(el) === 'Open saved session conversation')
    const selectedRow = button.parent
    button.props.onClick(); await flush()
    assert.match(textOf(selectedRow), /Loading saved conversation/)
    const panel = find(root, el => el.props['aria-label'] === 'Saved conversation')
    assert.equal(panel.parent, selectedRow) // Regression: previously below the entire list.
    resolve({ ok: scenario !== 'error', status: scenario === 'error' ? 503 : 200, json: async () => scenario === 'error' ? { detail: 'Session storage is unavailable.' } : scenario === 'empty' ? [] : [
      { message_id: 1, role: 'user', content: 'A fictional saved reflection.' },
      { message_id: 2, role: 'assistant', content: 'The fictional reflection describes a pause.' },
    ] })
    await flush()
    const shown = textOf(selectedRow)
    assert.ok(!shown.includes('Loading saved conversation'))
    if (scenario === 'saved') {
      for (const text of ['Fictional reflection', 'A fictional saved reflection.', 'Model acknowledgment', 'The fictional reflection describes a pause.']) assert.ok(shown.includes(text))
    } else if (scenario === 'empty') {
      assert.match(shown, /No saved conversation for this session/)
    } else {
      assert.match(shown, /Saved conversation could not be loaded/)
      assert.match(shown, /Retry loading conversation/)
      assert.ok(!shown.includes('No saved conversation'))
    }
    assert.deepEqual(calls, [{ url: '/api/assignment3/sessions/selected-session/conversation', method: 'GET' }])
    assert.ok(find(root, el => el.type === 'button' && textOf(el) === 'Crisis Support'))
    assert.equal(run.state.screen, 'history')
    assert.equal(run.state.status, null)
  })
}
