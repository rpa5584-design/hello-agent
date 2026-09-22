<script setup>
defineProps({ stays: { type: Array, required: true }, bookingDisabled: Boolean })
defineEmits(['book'])
const rate = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
</script>

<template>
  <div class="table-scroll" role="region" aria-label="Hotel stays table" tabindex="0">
    <table>
      <caption>Matching hotels and listed stays</caption>
      <thead>
        <tr>
          <th scope="col">Hotel name</th>
          <th scope="col">City</th>
          <th scope="col">State</th>
          <th scope="col">Stay name</th>
          <th scope="col">Check-in</th>
          <th scope="col">Check-out</th>
          <th scope="col">Nightly rate (USD)</th>
          <th scope="col">Booking</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="stay in stays" :key="stay.trip_id">
          <td class="hotel-name">{{ stay.hotel_name }}</td>
          <td>{{ stay.city }}</td>
          <td>{{ stay.state }}</td>
          <td>{{ stay.trip_name }}</td>
          <td class="nowrap">{{ stay.check_in }}</td>
          <td class="nowrap">{{ stay.check_out }}</td>
          <td class="nowrap price">{{ rate.format(stay.nightly_rate_usd) }}<span>per night</span></td>
          <td><button type="button" :disabled="bookingDisabled" :aria-label="`Book ${stay.trip_name}`" @click="$emit('book', stay.trip_id)">Book stay</button></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-scroll { overflow-x: auto; border: 1px solid #d9e2e8; border-radius: 10px; }
table { width: 100%; min-width: 940px; border-collapse: collapse; font-size: .88rem; }
caption { text-align: left; padding: 12px 16px; color: #526575; background: #f8fafc; }
th, td { padding: 16px; text-align: left; border-bottom: 1px solid #e2e9ee; }
th { background: #edf3f7; color: #445e70; font-size: .75rem; font-weight: bold; }
tbody tr:last-child td { border-bottom: 0; }
tbody tr:hover { background: #f8fbfd; }
.hotel-name { font-weight: bold; color: #183e59; min-width: 155px; }
.price { font-weight: bold; font-size: 1rem; }
.price span { display: block; font-size: .72rem; font-weight: normal; color: #526575; }
.nowrap { white-space: nowrap; }
button { white-space: nowrap; }
</style>
