<script setup>
defineProps({ records: { type: Array, default: () => [] }, loading: Boolean, loaded: Boolean, error: { type: String, default: '' }, guidanceMode: { type: String, default: 'standard' } })
defineEmits(['reload'])
</script>

<template>
  <section aria-labelledby="activity-heading" class="card">
    <h3 id="activity-heading">Recent activity</h3>
    <p>Continue with your {{ guidanceMode === 'fewer' ? 'Fewer instructions' : 'Standard guidance' }} preference.</p>
    <p v-if="loading" role="status">Loading recent activity…</p>
    <template v-else-if="error">
      <p role="alert">{{ error }}</p>
      <button type="button" @click="$emit('reload')">Retry recent activity</button>
    </template>
    <template v-else-if="loaded && records.length">
      <p>Last session: Paced Breathing — {{ records[0].status }} — {{ records[0].measured_duration_seconds === null ? 'Duration unavailable' : `${records[0].measured_duration_seconds.toFixed(1)} seconds` }}.</p>
      <p>Saved sessions loaded: {{ records.length }}.</p>
    </template>
    <p v-else-if="loaded">No saved sessions yet.</p>
    <p v-else>Recent activity has not loaded yet.</p>
    <p>History describes application activity, not an emotional or clinical state.</p>
  </section>
</template>

<style scoped>
.card { border: 1px solid #bac8d2; border-radius: 0.6rem; padding: 1rem; margin-block: 1rem; }
h3 { margin-top: 0; }
button { min-height: 44px; font: inherit; cursor: pointer; }
button:focus-visible { outline: 3px solid #164b75; outline-offset: 4px; }
</style>
