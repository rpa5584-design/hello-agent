import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createLocalHotelsApi, searchLocalFirst } from '../src/api/localHotels.js'
import { useZipLookup } from '../src/composables/useZipLookup.js'

const hotel = () => ({ place_id: ' Provider:AbC ', name: null, latitude: 40, longitude: -75, saved: true, nights: [{ stay_date: '2026-10-10', nightly_rate_cents: 10000, rooms_available: 20 }] })
const response = (hotels = [hotel()], source = 'local') => ({ requested_zip: '02108', location: { postcode: '02108', country_code: 'us', latitude: 42, longitude: -71 }, radius_meters: 5000, source, hotels })

test('local-first uses saved data and never calls provider; refresh reloads database status', async () => {
  let calls = 0
  const local = { lookup: async zip => { assert.equal(zip, '02108'); calls++; return response() } }
  const provider = () => { throw new Error('must not call provider') }
  for (let i = 0; i < 2; i++) {
    const state = useZipLookup(zip => searchLocalFirst(zip, local, provider))
    state.zipCode.value = '02108'
    await state.lookup()
    assert.equal(state.result.value.source, 'local')
    assert.equal(state.result.value.hotels[0].saved, true)
    assert.equal(state.result.value.hotels[0].nights[0].rooms_available, 20)
  }
  assert.equal(calls, 2)
})

test('only successful empty local lookup falls back; saved status uses provider identity', async () => {
  const order = []
  const result = await searchLocalFirst('02108', {
    lookup: async () => { order.push('local'); return response([]) },
    ids: async () => { order.push('ids'); return [' Provider:AbC '] },
  }, async () => { order.push('provider'); return response([{...hotel(), saved: false}, {place_id: 'other'}], 'api') })
  assert.deepEqual(order, ['local', 'provider', 'ids'])
  assert.equal(result.source, 'api')
  assert.equal(result.hotels[0].saved, true)
  assert.equal(result.hotels[1].saved, false)
  await assert.rejects(searchLocalFirst('02108', { lookup: async () => { throw new Error('storage unavailable') } }, () => { throw new Error('provider called') }), /storage unavailable/)
})

test('API sends exact identity and searched location; malformed/local failures are errors', async () => {
  const calls = []
  const local = createLocalHotelsApi(async (url, options) => {
    calls.push([url, options])
    return options.method === 'DELETE' ? { ok: true, status: 204 } : { ok: true, json: async () => hotel() }
  })
  await local.save(hotel(), '02108', response().location)
  const body = JSON.parse(calls[0][1].body)
  assert.equal(body.hotel.place_id, ' Provider:AbC ')
  assert.equal(body.zip_code, '02108')
  assert.deepEqual(body.location, response().location)
  await local.remove(' Provider:AbC ')
  assert.equal(calls[1][0], '/api/local/hotels?hotel_id=+Provider%3AAbC+')
  for (const reply of [{ ok: false, status: 503, json: async () => ({detail:'Storage offline'}) }, {ok:true,json:async()=>({})}]) {
    await assert.rejects(createLocalHotelsApi(async () => reply).lookup('02108'))
  }
})

test('save pending prevents duplicate actions and lookup; failure permits retry without marking saved', async () => {
  let finish
  let fail = true
  let saves = 0
  const local = { save: async (...args) => { saves++; assert.equal(args[1], '02108'); await new Promise(resolve => { finish = resolve }); if (fail) throw new Error('save failed'); return hotel() } }
  const state = useZipLookup(async () => response([{...hotel(),saved:false}], 'api'), local)
  state.zipCode.value = '02108'
  await state.lookup()
  const h = state.result.value.hotels[0]
  state.selectHotel(h.place_id)
  const pending = state.saveHotel(h)
  assert.equal(state.pendingId.value, h.place_id)
  assert.equal(h.saved, false)
  await state.saveHotel(h)
  await state.lookup()
  assert.equal(saves, 1)
  finish(); await pending
  assert.equal(h.saved, false)
  assert.match(state.actionError.value, /save failed/)
  fail = false
  const retry = state.saveHotel(h)
  finish(); await retry
  assert.equal(h.saved, true)
  assert.equal(state.selectedPlaceId.value, h.place_id)
  assert.equal(state.actionError.value, '')
})

test('removal failure preserves hotel, selection and status; success removes only matching local result', async () => {
  let fail = true
  const state = useZipLookup(async () => response([hotel(), {...hotel(),place_id:'other'}]), {remove: async () => { if (fail) throw new Error('remove failed') }})
  state.zipCode.value = '02108'
  await state.lookup()
  const h = state.result.value.hotels[0]
  state.selectHotel(h.place_id)
  await state.removeHotel(h)
  assert.equal(state.result.value.hotels.length, 2)
  assert.equal(h.saved, true)
  assert.equal(state.selectedPlaceId.value, h.place_id)
  assert.match(state.actionError.value, /remove failed/)
  fail = false
  await state.removeHotel(h)
  assert.deepEqual(state.result.value.hotels.map(h => h.place_id), ['other'])
  assert.equal(state.selectedPlaceId.value, null)
  await state.removeHotel(state.result.value.hotels[0])
  assert.equal(state.status.value, 'empty')
})

test('API removal leaves provider result and enables saving again', async () => {
  const state = useZipLookup(async () => response([hotel()], 'api'), {remove: async () => {}})
  await state.lookup()
  await state.removeHotel(state.result.value.hotels[0])
  assert.equal(state.result.value.hotels.length, 1)
  assert.equal(state.result.value.hotels[0].saved, false)
})
