<script setup>
defineProps({
  users: { type: Array, required: true },
  selected: { type: String, required: true },
  loading: Boolean,
  disabled: Boolean,
  error: { type: String, default: '' },
})
defineEmits(['select', 'retry'])
</script>

<template>
  <section class="user-panel" aria-label="Demo user" :aria-busy="loading">
    <div>
      <label for="demo-user">Demo user</label>
      <p id="demo-user-hint" class="muted">Bookings and history belong to the selected user.</p>
    </div>
    <select id="demo-user" :value="selected" aria-describedby="demo-user-hint" :disabled="disabled || loading || !users.length" @change="$emit('select', $event.target.value)">
      <option value="" disabled>Select a demo user</option>
      <option v-for="user in users" :key="user.user_id" :value="user.user_id">{{ user.display_name }} ({{ user.user_id }})</option>
    </select>
    <p v-if="loading" role="status">Loading demo users…</p>
    <div v-else-if="error">
      <p class="notice error" role="alert">{{ error }}</p>
      <button type="button" :disabled="disabled" @click="$emit('retry')">Retry loading users</button>
    </div>
    <p v-else-if="!users.length" role="status">No demo users available.</p>
  </section>
</template>

<style scoped>
.user-panel { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 16px; padding: 18px 22px; background: #e8f0f5; border: 1px solid #ccdae4; border-radius: 12px; }
label { margin-bottom: 3px; }
select { min-width: 250px; max-width: 100%; }
@media (max-width: 600px) { .user-panel { padding: 18px 16px; } select { width: 100%; min-width: 0; } }
</style>
