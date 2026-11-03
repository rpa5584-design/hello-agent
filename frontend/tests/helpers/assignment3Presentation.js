import { readFile } from 'node:fs/promises'
import * as Vue from 'vue'
import { compileScript, parse } from '@vue/compiler-sfc'

export async function component(file, dependencies = {}) {
  const source = await readFile(new URL(`../../src/components/assignment3/${file}`, import.meta.url), 'utf8')
  const { content } = compileScript(parse(source).descriptor, { id: file, inlineTemplate: true })
  const code = content
    .replace(/import \{([^}]+)\} from ['"]vue['"];?/g, (_, names) => `const {${names.replace(/\bas\b/g, ':')}} = Vue;`)
    .replace(/^import .*$/gm, '').replace('export default', 'return')
  return new Function('Vue', ...Object.keys(dependencies), code)(Vue, ...Object.values(dependencies))
}

export function host() {
  const node = (type, text = '') => ({ type, text, children: [], props: {}, parent: null, focus() {}, addEventListener() {} })
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
export const textOf = node => node.text + node.children.map(textOf).join(' ')
export const find = (node, predicate) => predicate(node) ? node : node.children.map(child => find(child, predicate)).find(Boolean)
export const flush = async () => { for (let i = 0; i < 8; i++) await Vue.nextTick() }
