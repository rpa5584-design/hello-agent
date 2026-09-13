<script setup>
defineProps({ stays: { type: Array, required: true } })
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
        </tr>
      </thead>
      <tbody>
        <tr v-for="stay in stays" :key="stay.trip_id">
          <td>{{ stay.hotel_name }}</td>
          <td>{{ stay.city }}</td>
          <td>{{ stay.state }}</td>
          <td>{{ stay.trip_name }}</td>
          <td class="nowrap">{{ stay.check_in }}</td>
          <td class="nowrap">{{ stay.check_out }}</td>
          <td class="nowrap">{{ rate.format(stay.nightly_rate_usd) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
caption { text-align: left; font-weight: bold; margin-bottom: 8px; }
th, td { border: 1px solid #adb5bd; padding: 10px; text-align: left; }
th { background: #f0f3f5; }
.nowrap { white-space: nowrap; }
</style>
