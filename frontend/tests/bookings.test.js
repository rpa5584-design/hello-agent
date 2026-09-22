import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createBookingsApi } from '../src/api/bookings.js'
import { isTestBooking, useBookings } from '../src/composables/useBookings.js'

const users = [{ user_id: 'U001', display_name: 'Demo Traveler 1' }, { user_id: 'U006', display_name: 'Demo Traveler 6' }]
const testId = `B-${'a'.repeat(32)}`
const booking = { booking_id: testId, user_id: 'U001', trip_id: 'T001', status: 'confirmed', hotel_name: 'Harbor Lantern Hotel' }
function mockApi(overrides = {}) {
  return {
    listUsers: async () => users,
    history: async () => [],
    create: async () => booking,
    cancel: async () => ({ ...booking, status: 'cancelled' }),
    remove: async () => undefined,
    ...overrides,
  }
}
function deferred() {
  let resolve, reject
  const promise = new Promise((yes, no) => { resolve = yes; reject = no })
  return { promise, resolve, reject }
}

test('API sends exact user/history/create/cancel/delete requests and handles empty 204', async () => {
  const calls = []
  const api = createBookingsApi(async (url, options) => {
    calls.push([url, options])
    return { ok: true, status: options.method === 'DELETE' ? 204 : 200, json: async () => options.method === 'GET' ? [] : booking }
  })
  await api.listUsers()
  await api.history('U & 1')
  await api.create('U001', 'T001')
  await api.cancel('B/a')
  await api.remove('B/a')
  assert.deepEqual(calls, [
    ['/api/users', { method: 'GET' }],
    ['/api/bookings?user_id=U+%26+1', { method: 'GET' }],
    ['/api/bookings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id: 'U001', trip_id: 'T001' }) }],
    ['/api/bookings/B%2Fa', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: 'cancelled' }) }],
    ['/api/bookings/B%2Fa', { method: 'DELETE' }],
  ])
})

test('API reports server, validation, network, and invalid list errors', async () => {
  const server = createBookingsApi(async () => ({ ok: false, json: async () => ({ detail: 'Instructor bookings cannot be deleted.' }) }))
  await assert.rejects(server.remove('B001'), /Instructor bookings/)
  const validation = createBookingsApi(async () => ({ ok: false, json: async () => ({ detail: [] }) }))
  await assert.rejects(validation.create('', ''), /request failed/)
  const network = createBookingsApi(async () => { throw new Error('offline') })
  await assert.rejects(network.listUsers(), /reach the server/)
  const invalid = createBookingsApi(async () => ({ ok: true, json: async () => ({}) }))
  await assert.rejects(invalid.history('U001'), /invalid list/)
})

test('loads users, selects first user, and loads history for subsequent selection', async () => {
  const calls = []
  const state = useBookings(mockApi({ history: async id => { calls.push(id); return id === 'U001' ? [booking] : [] } }))
  assert.equal(state.canBook.value, false)
  await state.loadUsers()
  assert.deepEqual(state.users.value, users)
  assert.equal(state.selectedUserId.value, 'U001')
  assert.equal(state.canBook.value, true)
  assert.equal(state.history.value.length, 1)
  await state.selectUser('U006')
  assert.equal(state.selectedUserId.value, 'U006')
  assert.deepEqual(state.history.value, [])
  assert.equal(state.historyLoaded.value, true)
  assert.deepEqual(calls, ['U001', 'U006'])
})

test('user loading error supports retry and empty users disable booking', async () => {
  let fail = true
  const state = useBookings(mockApi({ listUsers: async () => { if (fail) throw new Error('Users unavailable'); return users } }))
  await state.loadUsers()
  assert.equal(state.usersLoading.value, false)
  assert.match(state.usersError.value, /unavailable/)
  assert.equal(state.canBook.value, false)
  fail = false
  await state.loadUsers()
  assert.equal(state.usersError.value, '')
  assert.equal(state.selectedUserId.value, 'U001')
  const empty = useBookings(mockApi({ listUsers: async () => [] }))
  await empty.loadUsers()
  assert.equal(empty.canBook.value, false)
  assert.deepEqual(empty.history.value, [])
})

test('creates for selected user and refreshes history with success feedback', async () => {
  let created = false
  const state = useBookings(mockApi({
    create: async (userId, tripId) => {
      assert.equal(userId, 'U006')
      assert.equal(tripId, 'T001')
      created = true
      return { ...booking, user_id: userId }
    },
    history: async userId => created ? [{ ...booking, user_id: userId }] : [],
  }))
  await state.loadUsers()
  await state.selectUser('U006')
  await state.book('T001')
  assert.equal(state.history.value[0].user_id, 'U006')
  assert.match(state.success.value, /created successfully/)
  assert.equal(state.pending.value, false)
  assert.equal(state.error.value, '')
})

test('cancel keeps joined history row and delete removes only the generated booking', async () => {
  const starter = { ...booking, booking_id: 'B001' }
  const state = useBookings(mockApi({
    history: async () => [starter, booking],
    cancel: async id => { assert.equal(id, testId); return { booking_id: id, status: 'cancelled' } },
    remove: async id => { assert.equal(id, testId) },
  }))
  await state.loadUsers()
  await state.cancel(testId)
  assert.equal(state.history.value.length, 2)
  assert.equal(state.history.value[1].status, 'cancelled')
  assert.equal(state.history.value[1].hotel_name, booking.hotel_name)
  assert.match(state.success.value, /remains in your history/)
  await state.remove(testId)
  assert.deepEqual(state.history.value, [starter])
  assert.match(state.success.value, /deleted/)
  await state.remove('B001')
  assert.match(state.error.value, /cannot be deleted/)
  assert.deepEqual(state.history.value, [starter])
  assert.equal(isTestBooking('B001'), false)
  assert.equal(isTestBooking(testId), true)
})

for (const [action, apiAction, argument] of [['book', 'create', 'T001'], ['cancel', 'cancel', testId], ['remove', 'remove', testId]]) {
  test(`${action} failure preserves history and allows retry`, async () => {
    let fail = true
    const state = useBookings(mockApi({
      history: async () => [booking],
      [apiAction]: async () => { if (fail) throw new Error('Request failed'); return { ...booking, status: 'cancelled' } },
    }))
    await state.loadUsers()
    await state[action](argument)
    assert.deepEqual(state.history.value, [booking])
    assert.equal(state.success.value, '')
    assert.equal(state.error.value, 'Request failed')
    assert.equal(state.pending.value, false)
    fail = false
    await state[action](argument)
    assert.equal(state.error.value, '')
    assert.ok(state.success.value)
  })
}

test('history failure has retry and no false empty-history state', async () => {
  let fail = true
  const state = useBookings(mockApi({ history: async () => { if (fail) throw new Error('History unavailable'); return [] } }))
  await state.loadUsers()
  assert.equal(state.historyLoaded.value, false)
  assert.equal(state.historyLoading.value, false)
  assert.equal(state.historyError.value, 'History unavailable')
  fail = false
  await state.loadHistory()
  assert.equal(state.historyError.value, '')
  assert.equal(state.historyLoaded.value, true)
})

test('successful create is not reported as failed when history refresh fails', async () => {
  let fail = false
  const state = useBookings(mockApi({
    create: async () => { fail = true; return booking },
    history: async () => { if (fail) throw new Error('Refresh failed'); return [] },
  }))
  await state.loadUsers()
  await state.book('T001')
  assert.match(state.success.value, /created successfully/)
  assert.equal(state.error.value, '')
  assert.equal(state.historyError.value, 'Refresh failed')
})

test('pending mutation prevents duplicate submission and user switching', async () => {
  const task = deferred()
  let calls = 0
  const state = useBookings(mockApi({ create: () => { calls++; return task.promise } }))
  await state.loadUsers()
  const first = state.book('T001')
  assert.equal(state.pending.value, true)
  assert.equal(state.canBook.value, false)
  await state.book('T001')
  await state.selectUser('U006')
  assert.equal(calls, 1)
  assert.equal(state.selectedUserId.value, 'U001')
  task.resolve(booking)
  await first
  assert.equal(state.pending.value, false)
})

test('slow prior history response cannot overwrite newly selected user history', async () => {
  const old = deferred()
  let delay = false
  const state = useBookings(mockApi({ history: async id => id === 'U001' && delay ? old.promise : [] }))
  await state.loadUsers()
  delay = true
  const previous = state.loadHistory()
  assert.equal(state.historyLoading.value, true)
  await state.selectUser('U006')
  old.resolve([booking])
  await previous
  assert.equal(state.selectedUserId.value, 'U006')
  assert.deepEqual(state.history.value, [])
  assert.equal(state.historyLoading.value, false)
})

test('booking without a selected user never sends a request', async () => {
  const state = useBookings(mockApi({ create: async () => { assert.fail('Must select a user') } }))
  await state.book('T001')
  assert.match(state.error.value, /Select a demo user/)
})
