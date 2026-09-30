import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import * as Vue from 'vue'
import { compileScript, parse } from '@vue/compiler-sfc'
import { useZipLookup } from '../src/composables/useZipLookup.js'
import { searchZipHotels } from '../src/api/zipLocation.js'
import { createHotelMap, validCoordinates } from '../src/components/hotelMapLayer.js'

async function component(file, dependencies) {
  const source = await readFile(new URL(file, import.meta.url), 'utf8')
  const { descriptor } = parse(source)
  const { content } = compileScript(descriptor, { id: file, inlineTemplate: true })
  const code = content
    .replace(/import \{([^}]+)\} from ['"]vue['"];?/g, (_, names) => `const {${names.replace(/\bas\b/g, ':')}} = Vue;`)
    .replace(/^import .*$/gm, '')
    .replace('export default', 'return')
  return new Function('Vue', ...Object.keys(dependencies), code)(Vue, ...Object.values(dependencies))
}

// A minimal host for Vue's real mount/update/unmount lifecycle, without browser IO.
function host() {
  const node = (type, text = '') => ({ type, text, children: [], props: {}, parent: null, addEventListener() {}, getRootNode() { return {} } })
  const remove = child => {
    if (child.parent) {
      const siblings = child.parent.children
      siblings.splice(siblings.indexOf(child), 1)
      child.parent = null
    }
  }
  const renderer = Vue.createRenderer({
    createElement: node, createText: text => node('text', text), createComment: text => node('comment', text),
    setText: (el, text) => { el.text = text },
    setElementText: (el, text) => { el.text = text; el.children = [] },
    patchProp: (el, key, _old, value) => { el.props[key] = value },
    insert(child, parent, anchor = null) {
      remove(child)
      child.parent = parent
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

test('mounted success to service-error lifecycle removes stale hotel map and markers', async t => {
  const originalDocument = globalThis.Document
  const originalShadowRoot = globalThis.ShadowRoot
  globalThis.Document = class {}
  globalThis.ShadowRoot = class {}
  t.after(() => {
    if (originalDocument === undefined) delete globalThis.Document
    else globalThis.Document = originalDocument
    if (originalShadowRoot === undefined) delete globalThis.ShadowRoot
    else globalThis.ShadowRoot = originalShadowRoot
  })
  const maps = []
  const L = {
    icon: () => ({}),
    map(element) {
      const map = { element, markers: [], removed: false, setView(point) { this.center = point }, fitBounds() {}, invalidateSize() {},
        remove() { this.removed = true; this.markers.length = 0 } }
      maps.push(map)
      return map
    },
    tileLayer: () => ({ addTo() { return this }, on() {} }),
    layerGroup: () => ({ addTo(map) { this.map = map; return this }, clearLayers() { this.map.markers.length = 0 } }),
    marker: point => ({ point, bindPopup() { return this }, addTo(group) { group.map.markers.push(this); return this }, on() {},
      getElement: () => null, setZIndexOffset() {}, closePopup() {} }),
  }
  const document = { createElement: () => ({ appendChild() {} }) }
  let disconnected = false
  const HotelMap = await component('../src/components/HotelMap.vue', {
    L, markerUrl: '', markerRetinaUrl: '', shadowUrl: '', createHotelMap, validCoordinates, document,
    ResizeObserver: class { observe() {} disconnect() { disconnected = true } },
  })
  const data = {
    requested_zip: '16802', radius_meters: 5000,
    location: { postcode: '16802', latitude: 40.8, longitude: -77.86 },
    hotels: [{ place_id: 'provider-one', name: 'Previous hotel', latitude: 40.801, longitude: -77.86 }],
  }
  let failSecond
  const urls = []
  const state = useZipLookup(zip => searchZipHotels(zip, async url => {
    urls.push(url)
    if (urls.length === 1) return { ok: true, json: async () => data }
    return new Promise(resolve => { failSecond = () => resolve({ ok: false, status: 502 }) })
  }))
  const Panel = await component('../src/components/ZipLookupDemo.vue', { HotelMap, useZipLookup: () => state })
  const { renderer, root } = host()
  const app = renderer.createApp(Panel)
  app.mount(root)
  try {
    await state.lookup()
    await Vue.nextTick()
    assert.equal(maps.length, 1)
    const previousMap = maps[0]
    assert.equal(previousMap.removed, false)
    assert.deepEqual(previousMap.center, [40.8, -77.86])
    assert.deepEqual(previousMap.markers.map(marker => marker.point), [[40.801, -77.86]])
    assert.ok(find(root, node => node === Vue.toRaw(previousMap.element)))
    assert.match(textOf(root), /Previous hotel/)

    state.zipCode.value = '10001'
    const pending = state.lookup()
    await Vue.nextTick()
    assert.equal(state.result.value, null)
    assert.equal(previousMap.removed, true)
    assert.equal(previousMap.markers.length, 0)
    assert.equal(disconnected, true)
    assert.equal(find(root, node => node === Vue.toRaw(previousMap.element)), undefined)
    assert.doesNotMatch(textOf(root), /Previous hotel/)

    failSecond()
    await pending
    await Vue.nextTick()
    assert.deepEqual(urls, ['/api/demo/hotels?zip_code=16802', '/api/demo/hotels?zip_code=10001'])
    assert.equal(state.status.value, 'service')
    assert.equal(state.result.value, null)
    assert.equal(maps.length, 1)
    assert.equal(previousMap.markers.length, 0)
    assert.equal(find(root, node => node === Vue.toRaw(previousMap.element)), undefined)
    assert.match(textOf(find(root, node => node.props.role === 'alert')), /Hotel service is unavailable/)
    assert.doesNotMatch(textOf(root), /Previous hotel|No hotels found/)
  } finally {
    app.unmount()
  }
})
