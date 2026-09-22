<script setup>
import { ref, watch } from 'vue'
import { isTestBooking } from '../composables/useBookings.js'

const props = defineProps({
  bookings: { type: Array, required: true },
  userId: { type: String, required: true },
  loading: Boolean,
  loaded: Boolean,
  pending: Boolean,
  error: { type: String, default: '' },
})
const emit = defineEmits(['cancel', 'delete', 'refresh'])
const confirming = ref('')
watch(() => props.userId, () => { confirming.value = '' })
function confirmDelete(bookingId) {
  confirming.value = ''
  emit('delete', bookingId)
}
</script>

<template>
  <section class="panel history-panel" aria-labelledby="booking-history-heading" :aria-busy="loading || pending">
    <div class="history-heading">
      <div class="section-intro">
        <p class="eyebrow">Your selected user</p>
        <h2 id="booking-history-heading">Booking history</h2>
        <p v-if="userId" class="muted">Bookings for {{ userId }} · Confirmed and cancelled stays</p>
      </div>
      <button v-if="userId" class="secondary" type="button" :disabled="loading || pending" @click="$emit('refresh')">Refresh history</button>
    </div>
    <slot />
    <p v-if="!userId" class="empty-state">Select a demo user to view booking history.</p>
    <template v-else>
      <p v-if="loading" class="notice" role="status">Loading booking history…</p>
      <p v-else-if="error" class="notice error" role="alert">{{ error }} Use Refresh history to try again.</p>
      <p v-else-if="loaded && !bookings.length" class="empty-state" role="status">No bookings for this user.</p>
      <ul v-else-if="bookings.length" class="booking-list" aria-label="Bookings">
        <li v-for="booking in bookings" :key="booking.booking_id" class="booking-card">
          <div class="booking-heading">
            <div>
              <h3>{{ booking.hotel_name }}</h3>
              <p class="stay-name">{{ booking.trip_name }}</p>
              <p class="muted">{{ booking.city }}, {{ booking.state }}</p>
            </div>
            <span class="status-badge" :class="booking.status">
              <span aria-hidden="true">{{ booking.status === 'confirmed' ? '✓' : '−' }}</span>
              {{ booking.status === 'confirmed' ? 'Confirmed' : 'Cancelled' }}
            </span>
          </div>
          <dl class="booking-dates">
            <div><dt>Check-in</dt><dd>{{ booking.check_in }}</dd></div>
            <div><dt>Check-out</dt><dd>{{ booking.check_out }}</dd></div>
            <div><dt>Booked on</dt><dd>{{ booking.booked_on }}</dd></div>
          </dl>
          <div class="booking-footer">
            <p class="booking-id">Booking ID <span>{{ booking.booking_id }}</span></p>
            <div class="booking-actions">
              <button v-if="booking.status === 'confirmed'" class="secondary" type="button" :disabled="pending || loading" :aria-label="`Cancel booking ${booking.booking_id}`" @click="$emit('cancel', booking.booking_id)">Cancel booking</button>
              <button v-if="isTestBooking(booking.booking_id) && confirming !== booking.booking_id" class="danger" type="button" :disabled="pending || loading" :aria-label="`Delete test booking ${booking.booking_id}`" @click="confirming = booking.booking_id">Delete test booking</button>
            </div>
          </div>
          <div v-if="isTestBooking(booking.booking_id) && confirming === booking.booking_id" class="delete-confirmation" role="group" :aria-label="`Confirm deletion of ${booking.trip_name}`">
            <p><strong>Permanently delete this test booking?</strong><br>{{ booking.trip_name }} · {{ booking.check_in }} – {{ booking.check_out }}<br>This removes the booking from history.</p>
            <div class="booking-actions">
              <button class="secondary" type="button" :disabled="pending" @click="confirming = ''">Keep booking</button>
              <button class="danger-solid" type="button" :disabled="pending || loading" @click="confirmDelete(booking.booking_id)">Confirm delete</button>
            </div>
          </div>
        </li>
      </ul>
    </template>
  </section>
</template>

<style scoped>
.history-panel { border-top: 4px solid #184e77; }
.history-heading { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 22px; }
.history-heading > button { flex-shrink: 0; }
.booking-list { list-style: none; padding: 0; margin: 20px 0 0; display: grid; gap: 16px; }
.booking-card { border: 1px solid #d9e2e8; border-radius: 10px; padding: 22px; min-width: 0; }
.booking-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.booking-heading h3 { color: #183e59; font-size: 1.12rem; }
.stay-name { margin: 4px 0; }
.status-badge { display: inline-flex; gap: 6px; align-items: center; border-radius: 20px; padding: 5px 12px; font-size: .8rem; font-weight: bold; white-space: nowrap; }
.confirmed { background: #eaf6ed; color: #25603b; border: 1px solid #b6d9c1; }
.cancelled { background: #eef1f4; color: #52606d; border: 1px solid #cdd6dd; }
.booking-dates { display: flex; flex-wrap: wrap; gap: 16px 42px; margin: 20px 0; }
dt { font-size: .75rem; color: #526575; margin-bottom: 4px; }
dd { margin: 0; font-size: .9rem; font-weight: bold; }
.booking-footer { border-top: 1px solid #e5ebef; padding-top: 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px; }
.booking-id { font-size: .72rem; color: #62717d; min-width: 0; }
.booking-id span { display: block; overflow-wrap: anywhere; }
.booking-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.delete-confirmation { margin-top: 16px; padding: 18px; background: #fff5f3; border: 1px solid #e1b9b2; border-radius: 8px; font-size: .88rem; }
.delete-confirmation .booking-actions { margin-top: 14px; }
@media (max-width: 600px) {
  .history-heading { align-items: flex-start; flex-direction: column; }
  .booking-card { padding: 16px; }
  .booking-heading { flex-direction: column; gap: 10px; }
  .booking-dates { gap: 14px 24px; }
  .booking-actions { width: 100%; }
  .booking-actions button { flex: 1 1 150px; }
}
</style>
