import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import * as Vue from 'vue'
import { renderToString } from '@vue/server-renderer'
import { compileScript, parse } from '@vue/compiler-sfc'
import { isTestBooking } from '../src/composables/useBookings.js'

// Render actual SFC templates using the Vue tools already installed with Vite.
async function renderComponent(name, props) {
  const source = await readFile(new URL(`../src/components/${name}.vue`, import.meta.url), 'utf8')
  const { descriptor } = parse(source)
  const compiled = compileScript(descriptor, { id: name, inlineTemplate: true })
  const code = compiled.content
    .replace(/import \{([^}]+)\} from ['"]vue['"];?/g, (_, names) => `const {${names.replace(/\bas\b/g, ':')}} = Vue;`)
    .replace(/import \{ isTestBooking \} from [^\n]+/, '')
    .replace('export default', 'return')
  const component = new Function('Vue', 'isTestBooking', code)(Vue, isTestBooking)
  return renderToString(Vue.createSSRApp({ render: () => Vue.h(component, props) }))
}

const stay = {
  hotel_name: 'Harbor Lantern Hotel', city: 'Boston', state: 'MA', trip_id: 'T001',
  trip_name: 'Boston Harbor Weekend', check_in: '2026-09-18', check_out: '2026-09-20',
  nightly_rate_usd: 150,
}

test('redesigned results retain every column, stay field, rate, and disabled booking action', async () => {
  const html = await renderComponent('HotelStaysTable', { stays: [stay], bookingDisabled: true })
  for (const label of ['Hotel name', 'City', 'State', 'Stay name', 'Check-in', 'Check-out', 'Nightly rate (USD)', 'Booking']) {
    assert.ok(html.includes(label), label)
  }
  for (const value of ['Harbor Lantern Hotel', 'Boston', 'MA', 'Boston Harbor Weekend', '2026-09-18', '2026-09-20', '$150.00', 'Book stay']) {
    assert.ok(html.includes(value), value)
  }
  assert.match(html, /<button[^>]*disabled/)
  assert.match(html, /tabindex="0"/)
})

test('history renders both status labels, full IDs, and distinct permitted actions', async () => {
  const id = `B-${'a'.repeat(32)}`
  const html = await renderComponent('BookingHistory', {
    userId: 'U001', loaded: true,
    bookings: [
      { ...stay, booking_id: 'B001', booked_on: '2026-09-01', status: 'confirmed' },
      { ...stay, booking_id: id, booked_on: '2026-09-21', status: 'cancelled' },
    ],
  })
  assert.match(html, /class="status-badge confirmed"/)
  assert.match(html, /class="status-badge cancelled"/)
  assert.ok(html.includes('Confirmed'))
  assert.ok(html.includes('Cancelled'))
  assert.ok(html.includes(id))
  assert.ok(html.includes('Cancel booking B001'))
  assert.ok(!html.includes(`Cancel booking ${id}`))
  assert.ok(html.includes(`Delete test booking ${id}`))
  assert.ok(!html.includes('Delete test booking B001'))
})

test('history loading, empty, error, and disabled states stay distinct', async () => {
  const props = { userId: 'U001', bookings: [], loaded: true }
  const loading = await renderComponent('BookingHistory', { ...props, loading: true })
  assert.ok(loading.includes('Loading booking history'))
  assert.ok(!loading.includes('No bookings for this user'))
  assert.match(loading, /<button[^>]*disabled/)
  const error = await renderComponent('BookingHistory', { ...props, error: 'History unavailable' })
  assert.ok(error.includes('role="alert"'))
  assert.ok(!error.includes('No bookings for this user'))
  const empty = await renderComponent('BookingHistory', props)
  assert.ok(empty.includes('No bookings for this user'))
})

test('user selector keeps accessible label and pending disabled state', async () => {
  const html = await renderComponent('UserSelector', {
    users: [{ user_id: 'U001', display_name: 'Demo Traveler 1' }], selected: 'U001', disabled: true,
  })
  assert.ok(html.includes('for="demo-user"'))
  assert.match(html, /<select[^>]*disabled/)
  assert.ok(html.includes('Demo Traveler 1 (U001)'))
  assert.ok(html.includes('aria-describedby="demo-user-hint"'))
})

test('action feedback exposes success and errors with accessible roles', async () => {
  const success = await renderComponent('ActionFeedback', { success: 'Booking created successfully.' })
  assert.ok(success.includes('role="status"'))
  assert.ok(success.includes('Booking created successfully.'))
  const error = await renderComponent('ActionFeedback', { error: 'Request failed' })
  assert.ok(error.includes('role="alert"'))
  assert.ok(error.includes('Request failed'))
})
