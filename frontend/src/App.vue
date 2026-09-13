<script setup>
import HotelStaysTable from './components/HotelStaysTable.vue'
import { useHotelSearch } from './composables/useHotelSearch.js'
const { hotelName, stays, loading, error, noResults, search } = useHotelSearch()
</script>

<template>
  <main>
    <h1>RoomTour</h1>
    <p>Search by hotel name to find listed stays.</p>
    <form @submit.prevent="search">
      <label for="hotel-name">Hotel name</label>
      <div class="search-controls">
        <input id="hotel-name" v-model="hotelName" type="search" required :disabled="loading" />
        <button type="submit" :disabled="loading">Search</button>
      </div>
    </form>
    <section aria-label="Search results" :aria-busy="loading">
      <p v-if="loading" role="status">Searching for hotel stays…</p>
      <p v-else-if="error" class="error" role="alert">{{ error }}</p>
      <p v-else-if="noResults" role="status">No matching hotel stays found.</p>
      <template v-else-if="stays.length">
        <p role="status">{{ stays.length }} matching stays found.</p>
        <HotelStaysTable :stays="stays" />
      </template>
    </section>
  </main>
</template>

<style>
* { box-sizing: border-box; }
body { margin: 0; background: #fff; color: #20252b; font-family: Arial, sans-serif; line-height: 1.5; }
main { max-width: 1100px; margin: 0 auto; padding: 24px 16px; }
h1 { font-size: 1.8rem; }
label { display: block; font-weight: bold; margin-bottom: 6px; }
.search-controls { display: flex; flex-wrap: wrap; gap: 10px; }
input, button { font: inherit; border: 1px solid #65717c; border-radius: 4px; padding: 10px; }
input { flex: 1 1 220px; min-width: 0; max-width: 440px; }
button { background: #184e77; color: white; cursor: pointer; }
button:disabled { opacity: .65; cursor: wait; }
:focus-visible { outline: 3px solid #c76b00; outline-offset: 3px; }
.error { color: #a11b1b; }
</style>
