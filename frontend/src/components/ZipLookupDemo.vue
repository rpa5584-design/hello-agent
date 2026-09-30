<script setup>
import HotelMap from './HotelMap.vue'
import { useZipLookup } from '../composables/useZipLookup.js'

const { zipCode, submittedZip, result, status, loading, error, lookup, selectedPlaceId, selectHotel } = useZipLookup()
</script>

<template>
  <section class="panel zip-panel" aria-labelledby="zip-demo-heading">
    <div class="section-intro">
      <h2 id="zip-demo-heading">Hotels near a ZIP code</h2>
      <p id="zip-demo-hint" class="muted">Find hotels within 5 km of a resolved U.S. ZIP location.</p>
    </div>
    <form class="search-form" novalidate @submit.prevent="lookup">
      <label for="demo-zip">ZIP code</label>
      <div class="search-controls">
        <input id="demo-zip" v-model="zipCode" type="text" inputmode="numeric" pattern="[0-9]{5}" maxlength="5" required :disabled="loading" :aria-invalid="status === 'invalid'" aria-describedby="zip-demo-hint zip-feedback" />
        <button type="submit" :disabled="loading">Search hotels</button>
      </div>
    </form>
    <div id="zip-feedback">
      <p v-if="loading" class="notice" role="status">Searching hotels near ZIP {{ submittedZip }}…</p>
      <p v-else-if="error" class="notice error" role="alert">{{ error }}</p>
    </div>
    <div v-if="result" class="live-results">
      <HotelMap :hotels="result.hotels" :location="result.location" :selected-place-id="selectedPlaceId" @select="selectHotel" />
      <p class="muted">Requested ZIP: {{ result.requested_zip }}<template v-if="result.location.locality"> · {{ result.location.locality }}</template> · Search radius: 5 km</p>
      <p v-if="status === 'empty'" class="empty-state" role="status">No hotels found within 5 km of this ZIP location.</p>
      <template v-else>
        <p role="status">{{ result.hotels.length }} hotels returned.</p>
        <p v-if="result.limit_reached" class="notice">Showing up to {{ result.result_limit }} results. More hotels may be available in this area.</p>
      </template>
      <div class="hotel-results-layout">
        <ul v-if="result.hotels.length" class="live-hotels" aria-label="Nearby hotels">
          <li v-for="hotel in result.hotels" :key="hotel.place_id" :class="{ selected: selectedPlaceId === hotel.place_id }">
            <h3>{{ hotel.name?.trim() || 'Name unavailable' }}</h3>
            <p v-if="hotel.formatted_address" class="muted">{{ hotel.formatted_address }}</p>
            <button type="button" :aria-pressed="selectedPlaceId === hotel.place_id" @click="selectHotel(hotel.place_id)">Select {{ hotel.name?.trim() || 'Name unavailable' }}</button>
            <span v-if="selectedPlaceId === hotel.place_id" class="selection-label">✓ Selected</span>
          </li>
        </ul>
      </div>
      <p class="muted">Hotel location data from Geoapify.</p>
    </div>
    <p v-else class="empty-state map-placeholder">{{ loading ? 'Map will update when the search completes.' : error ? 'Map unavailable until a successful search.' : 'Search a ZIP to see hotels on the map.' }}</p>
  </section>
</template>

<style scoped>
.hotel-results-layout { min-width: 0; }
.map-placeholder { margin-top: 20px; }
.live-results { display: grid; gap: 14px; margin-top: 24px; }
.live-hotels { list-style: none; margin: 0; padding: 0; display: grid; gap: 12px; }
.live-hotels li { border: 1px solid #d9e2e8; border-radius: 10px; padding: 18px; overflow-wrap: anywhere; }
.live-hotels h3 { margin-bottom: 6px; }
.live-hotels li.selected { border: 2px solid #194f75; background: #eef6fb; }
.live-hotels button { margin-top: 12px; }
.live-hotels button:focus-visible { outline: 3px solid #a65f00; outline-offset: 3px; }
.selection-label { display: inline-block; margin-left: 12px; font-weight: 700; }
</style>
