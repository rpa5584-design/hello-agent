import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import * as Vue from 'vue'
import { renderToString } from '@vue/server-renderer'
import { compileScript, parse } from '@vue/compiler-sfc'
import { searchZipHotels } from '../src/api/zipLocation.js'
import { useZipLookup } from '../src/composables/useZipLookup.js'

const sample = (zip = '02108', hotels = [{ place_id: 'one', name: 'Provider hotel', formatted_address: 'Provider address' }]) => ({
  requested_zip: zip, location: { postcode: zip, locality: 'Provider locality' }, radius_meters: 5000, hotels,
})

async function renderPanel(state, mapStub = { render: () => null }) {
  const source = await readFile(new URL('../src/components/ZipLookupDemo.vue', import.meta.url), 'utf8')
  const { descriptor } = parse(source)
  const compiled = compileScript(descriptor, { id: 'zip-demo', inlineTemplate: true })
  const code = compiled.content
    .replace(/import \{([^}]+)\} from ['"]vue['"];?/g, (_, names) => `const {${names.replace(/\bas\b/g, ':')}} = Vue;`)
    .replace(/import \{ useZipLookup \} from [^\n]+/, '')
    .replace(/import HotelMap from [^\n]+/, '')
    .replace('export default', 'return')
  const component = new Function('Vue', 'useZipLookup', 'HotelMap', code)(Vue, () => state, mapStub)
  return renderToString(Vue.createSSRApp(component))
}


test('entered leading-zero ZIP uses only the local hotels endpoint', async () => {
  const state = useZipLookup(zip => searchZipHotels(zip, async url => {
    assert.equal(url, '/api/demo/hotels?zip_code=02108')
    return { ok: true, json: async () => sample() }
  }))
  state.zipCode.value = '02108'
  await state.lookup()
  assert.equal(state.status.value, 'success')
  assert.equal(state.result.value.requested_zip, '02108')
  const html = await renderPanel(state)
  for (const text of ['02108', 'Provider locality', '5 km', 'Provider hotel', 'Provider address', '1 hotels returned.']) assert.ok(html.includes(text))
})

test('invalid ZIPs clear results and make no request', async () => {
  let calls = 0
  const state = useZipLookup(async () => { calls++; return sample() })
  for (const zip of ['', '1234', '123456', 'abcde', '１２３４５']) {
    state.result.value = sample()
    state.zipCode.value = zip
    await state.lookup()
    assert.equal(state.status.value, 'invalid')
    assert.equal(state.result.value, null)
    assert.match(await renderPanel(state), /aria-invalid="true"/)
  }
  assert.equal(calls, 0)
})

test('loading uses submitted ZIP, clears stale results, and blocks duplicate requests', async () => {
  let finish
  let calls = 0
  const state = useZipLookup(() => { calls++; return new Promise(resolve => { finish = resolve }) })
  state.result.value = sample()
  state.zipCode.value = '90210'
  const pending = state.lookup()
  assert.equal(state.result.value, null)
  state.zipCode.value = '02108'
  const html = await renderPanel(state)
  assert.match(html, /Searching hotels near ZIP 90210/)
  assert.doesNotMatch(html, /Searching hotels near ZIP 16802/)
  assert.match(html, /<button[^>]*disabled/)
  await state.lookup()
  assert.equal(calls, 1)
  finish(sample('90210'))
  await pending
  assert.equal(state.loading.value, false)
})

test('successful zero hotels is distinct from service failure', async () => {
  const state = useZipLookup(async () => sample('16802', []))
  await state.lookup()
  assert.equal(state.status.value, 'empty')
  assert.match(await renderPanel(state), /No hotels found within 5 km/)
})

for (const [code, kind] of [[422, 'invalid'], [404, 'unresolved'], [502, 'service'], [503, 'service']]) {
  test(`HTTP ${code} yields ${kind} feedback without empty-results message`, async () => {
    const state = useZipLookup(zip => searchZipHotels(zip, async () => ({ ok: false, status: code })))
    await state.lookup()
    assert.equal(state.status.value, kind)
    assert.equal(state.result.value, null)
    const html = await renderPanel(state)
    assert.match(html, /role="alert"/)
    assert.doesNotMatch(html, /No hotels found/)
  })
}

test('network and malformed responses remain failures and retry recovers', async () => {
  await assert.rejects(searchZipHotels('02108', async () => { throw new Error('private details') }), /Could not reach/)
  await assert.rejects(searchZipHotels('02108', async () => ({ ok: true, json: async () => ({}) })), /invalid response/)
  let fail = true
  const state = useZipLookup(async () => { if (fail) throw new Error('private details'); return sample() })
  state.zipCode.value = '02108'
  await state.lookup()
  assert.equal(state.status.value, 'service')
  assert.doesNotMatch(state.error.value, /private details/)
  fail = false
  await state.lookup()
  assert.equal(state.status.value, 'success')
  assert.equal(state.error.value, '')
})

test('list uses honest missing-name label and excludes commercial fields and booking controls', async () => {
  const state = useZipLookup(async () => sample('16802', [{
    place_id: 'one', price: 123, rating: 5, availability: 'available', booking_status: 'confirmed',
  }]))
  await state.lookup()
  const html = await renderPanel(state)
  assert.match(html, /Name unavailable/)
  assert.doesNotMatch(html, /123|rating|\bavailable\b|confirmed|Book stay/i)
  assert.equal((html.match(/<button/g) || []).length, 2)
  assert.match(html, /<form[^>]*novalidate/)
  assert.match(html, /for="demo-zip"/)
  assert.match(html, /type="submit"/)
})

test('result limit is disclosed with dynamic count', async () => {
  const state = useZipLookup(async () => ({ ...sample('16802'), limit_reached: true, result_limit: 100 }))
  await state.lookup()
  assert.match(await renderPanel(state), /Showing up to 100 results/)
})


test('map receives the same result objects as the list and disappears when results clear', async () => {
  const state = useZipLookup(async () => sample())
  state.zipCode.value = '02108'
  await state.lookup()
  let received
  const stub = { props: ['hotels', 'location'], setup(props) { received = props; return () => null } }
  await renderPanel(state, stub)
  assert.equal(received.hotels, state.result.value.hotels)
  assert.equal(received.location, state.result.value.location)
  state.result.value = null
  received = null
  await renderPanel(state, stub)
  assert.equal(received, null)
})


test('shared selection reaches map and accessible list buttons by place_id', async () => {
  const state = useZipLookup(async () => sample('16802', [
    { place_id: 'a', name: 'Same name' }, { place_id: 'b', name: 'Same name' },
  ]))
  await state.lookup()
  state.selectHotel('b')
  let received
  const stub = { props: ['selectedPlaceId'], emits: ['select'], setup(props) { received = props.selectedPlaceId; return () => null } }
  const html = await renderPanel(state, stub)
  assert.equal(received, 'b')
  assert.equal((html.match(/aria-pressed="true"/g) || []).length, 1)
  assert.match(html, /type="button" aria-pressed="true"/)
  assert.match(html, /✓ Selected/)
  state.selectHotel('unknown')
  assert.equal(state.selectedPlaceId.value, 'b')
  await renderPanel(state, { emits: ['select'], setup(_props, { emit }) { emit('select', 'a'); return () => null } })
  assert.equal(state.selectedPlaceId.value, 'a')
  assert.match(await renderPanel(state), /<li class="selected"><h3>Same name/)
})

for (const outcome of ['success', 'empty', 'error', 'invalid']) {
  test(`new search clears selection through ${outcome} outcome`, async () => {
    let finish
    const state = useZipLookup(() => new Promise((resolve, reject) => { finish = outcome === 'error' ? () => reject(new Error('failure')) : () => resolve(sample('10001', outcome === 'empty' ? [] : undefined)) }))
    state.result.value = sample()
    state.selectHotel('one')
    assert.equal(state.selectedPlaceId.value, 'one')
    state.zipCode.value = outcome === 'invalid' ? '1234' : '10001'
    const pending = state.lookup()
    assert.equal(state.selectedPlaceId.value, null)
    if (finish) finish()
    await pending
    assert.equal(state.selectedPlaceId.value, null)
  })
}
