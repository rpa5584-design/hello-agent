import { test } from 'node:test'
import assert from 'node:assert/strict'
import { searchStays } from '../src/api/travel.js'
import { useHotelSearch } from '../src/composables/useHotelSearch.js'

test('search sends an encoded hotel name to the stays API and preserves multiple stays', async () => {
  const rows = [{ trip_id: 'T001', hotel_id: 'H001' }, { trip_id: 'T009', hotel_id: 'H001' }]
  const search = useHotelSearch(name => searchStays(name, async url => {
    assert.equal(url, '/api/stays?hotel_name=Harbor+%26+Lantern')
    return { ok: true, json: async () => ({ stays: rows }) }
  }))
  search.hotelName.value = '  Harbor & Lantern  '
  await search.search()
  assert.deepEqual(search.stays.value, rows)
  assert.equal(search.noResults.value, false)
  assert.equal(search.loading.value, false)
})

test('no-results state appears only after a successful empty search', async () => {
  let finish
  const search = useHotelSearch(() => new Promise(resolve => { finish = resolve }))
  assert.equal(search.noResults.value, false)
  search.hotelName.value = 'Unknown'
  const pending = search.search()
  assert.equal(search.loading.value, true)
  assert.equal(search.noResults.value, false)
  finish([])
  await pending
  assert.equal(search.noResults.value, true)
  assert.equal(search.error.value, '')
})

test('request failures clear previous results and allow retry without showing no matches', async () => {
  let fail = false
  const search = useHotelSearch(async () => {
    if (fail) throw new Error('Network failed')
    return [{ trip_id: 'T001' }]
  })
  search.hotelName.value = 'Harbor'
  await search.search()
  fail = true
  await search.search()
  assert.deepEqual(search.stays.value, [])
  assert.ok(search.error.value)
  assert.equal(search.noResults.value, false)
  assert.equal(search.loading.value, false)
  fail = false
  await search.search()
  assert.equal(search.error.value, '')
  assert.equal(search.stays.value.length, 1)
})

test('blank input does not send a request', async () => {
  let calls = 0
  const search = useHotelSearch(async () => { calls++; return [] })
  search.hotelName.value = '   '
  await search.search()
  assert.equal(calls, 0)
  assert.equal(search.error.value, 'Enter a hotel name.')
  assert.equal(search.noResults.value, false)
})

test('API rejects HTTP failures and invalid response envelopes', async () => {
  await assert.rejects(searchStays('Harbor', async () => ({ ok: false })), /could not be loaded/)
  await assert.rejects(searchStays('Harbor', async () => ({ ok: true, json: async () => ({}) })), /invalid stays/)
})
