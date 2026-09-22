<script setup>
import { onMounted, ref } from 'vue'
import ActionFeedback from './components/ActionFeedback.vue'
import UserSelector from './components/UserSelector.vue'
import BookingHistory from './components/BookingHistory.vue'
import HotelStaysTable from './components/HotelStaysTable.vue'
import { useBookings } from './composables/useBookings.js'
import { useHotelSearch } from './composables/useHotelSearch.js'
const { hotelName, stays, loading, error, noResults, search } = useHotelSearch()
const {
  users, selectedUserId, usersLoading, usersError, history, historyLoading,
  historyLoaded, historyError, pending, success, error: bookingError, canBook,
  loadUsers, selectUser, loadHistory, book, cancel, remove,
} = useBookings()
const feedbackArea = ref('search')
onMounted(loadUsers)
</script>

<template>
  <a class="skip-link" href="#main-content">Skip to main content</a>
  <header class="site-header">
    <div class="header-inner">
      <div class="brand"><span class="brand-mark" aria-hidden="true">R</span><h1>RoomTour</h1></div>
      <span class="demo-label">Hotel stays · Demo bookings</span>
    </div>
  </header>
  <main id="main-content" tabindex="-1">
    <UserSelector :users="users" :selected="selectedUserId" :loading="usersLoading" :disabled="pending" :error="usersError" @select="selectUser" @retry="loadUsers" />
    <section class="panel search-panel" aria-labelledby="find-stay-heading">
      <div class="section-intro">
        <p class="eyebrow">Explore listed stays</p>
        <h2 id="find-stay-heading">Find a stay</h2>
        <p class="muted">Search by hotel name, then book a listed stay for your selected demo user.</p>
      </div>
      <form class="search-form" @submit.prevent="search">
        <label for="hotel-name">Hotel name</label>
        <div class="search-controls">
          <input id="hotel-name" v-model="hotelName" type="search" placeholder="e.g. Harbor Lantern Hotel" required :disabled="loading" />
          <button type="submit" :disabled="loading">{{ loading ? 'Searching…' : 'Search' }}</button>
        </div>
      </form>
      <section class="search-results" aria-label="Search results" :aria-busy="loading">
        <p v-if="loading" class="notice" role="status">Searching for hotel stays…</p>
        <p v-else-if="error" class="notice error" role="alert">{{ error }}</p>
        <p v-else-if="noResults" class="empty-state" role="status">No matching hotel stays found.</p>
        <template v-else-if="stays.length">
          <div class="results-heading"><h3>Matching stays</h3><p class="muted" role="status">{{ stays.length }} matching stays found.</p></div>
          <HotelStaysTable :stays="stays" :booking-disabled="!canBook" @book="feedbackArea = 'search'; book($event)" />
        </template>
      </section>
      <ActionFeedback v-if="feedbackArea === 'search'" :pending="pending" :success="success" :error="bookingError" />
    </section>
    <BookingHistory :bookings="history" :user-id="selectedUserId" :loading="historyLoading" :loaded="historyLoaded" :pending="pending" :error="historyError" @refresh="loadHistory" @cancel="feedbackArea = 'history'; cancel($event)" @delete="feedbackArea = 'history'; remove($event)">
      <ActionFeedback v-if="feedbackArea === 'history'" :pending="pending" :success="success" :error="bookingError" />
    </BookingHistory>
  </main>
</template>

<style>
:root { font-family: Arial, sans-serif; color: #182f42; background: #f3f6f8; line-height: 1.5; }
* { box-sizing: border-box; }
body { margin: 0; }
h1, h2, h3, p { margin: 0; }
h1 { font-size: 1.4rem; letter-spacing: -.04em; }
h2 { font-size: 1.65rem; letter-spacing: -.025em; line-height: 1.25; }
h3 { font-size: 1.05rem; }
.site-header { background: #fff; border-bottom: 1px solid #d9e2e8; }
.header-inner { max-width: 1240px; margin: auto; padding: 18px 28px; display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.brand { display: flex; align-items: center; gap: 10px; }
.brand-mark { background: #184e77; color: white; border-radius: 10px; width: 36px; height: 36px; display: grid; place-items: center; font-weight: bold; }
.demo-label, .muted { color: #526575; font-size: .9rem; }
main { max-width: 1240px; margin: auto; padding: 28px; display: grid; gap: 24px; }
.panel { background: #fff; border: 1px solid #d9e2e8; border-radius: 14px; padding: 28px; box-shadow: 0 3px 12px #193b5510; min-width: 0; }
.section-intro { display: grid; gap: 8px; }
.eyebrow { color: #376c87; font-size: .72rem; font-weight: bold; letter-spacing: .12em; text-transform: uppercase; }
label { display: block; font-weight: bold; font-size: .9rem; margin-bottom: 7px; }
input, button, select { font: inherit; border: 1px solid #8093a1; border-radius: 8px; padding: 11px 14px; min-height: 44px; }
input, select { background: #fff; color: #182f42; }
button { background: #184e77; border-color: #184e77; color: white; cursor: pointer; font-weight: bold; font-size: .9rem; }
button:hover:not(:disabled) { background: #103c5e; }
button:disabled, select:disabled, input:disabled { opacity: .6; cursor: not-allowed; }
button.secondary { background: white; color: #184e77; border-color: #bdccd6; }
button.secondary:hover:not(:disabled) { background: #edf4f8; }
button.danger { background: #fff; color: #a12b28; border-color: #d5a3a0; }
button.danger:hover:not(:disabled) { background: #fff0ee; }
button.danger-solid { background: #a12b28; color: white; border-color: #a12b28; }
button.danger-solid:hover:not(:disabled) { background: #80201d; }
:focus-visible { outline: 3px solid #bd6400; outline-offset: 4px; }
.search-form { margin-top: 24px; max-width: 740px; }
.search-controls { display: flex; gap: 12px; }
.search-controls input { flex: 1; min-width: 0; }
.search-controls button { min-width: 112px; }
.search-results { margin-top: 24px; }
.search-results:empty { margin: 0; }
.results-heading { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; margin-bottom: 14px; }
.notice { border-radius: 8px; padding: 12px 16px; margin-top: 14px; background: #edf4f8; color: #234e68; }
.error { color: #8d2522; background: #fff0ee; border-left: 3px solid #b33730; }
.success { color: #20583b; background: #eef8f1; border-left: 3px solid #2d7950; }
.empty-state { background: #f7f9fb; border: 1px dashed #bccbd6; border-radius: 10px; padding: 24px; color: #526575; }
.skip-link { position: absolute; left: 16px; top: -100px; z-index: 10; background: white; color: #184e77; padding: 12px; }
.skip-link:focus { top: 12px; }
@media (max-width: 600px) {
  .header-inner { padding: 16px; flex-wrap: wrap; gap: 8px; }
  .demo-label { font-size: .75rem; }
  main { padding: 16px; gap: 16px; }
  .panel { padding: 20px 16px; }
  .search-controls { flex-direction: column; }
  .results-heading { flex-direction: column; gap: 4px; }
  h2 { font-size: 1.4rem; }
}
</style>
