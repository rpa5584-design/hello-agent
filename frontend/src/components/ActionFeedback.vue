<script setup>
defineProps({
  pending: Boolean,
  success: { type: String, default: '' },
  error: { type: String, default: '' },
})
</script>

<template>
  <div class="action-feedback">
    <p v-if="pending" class="notice" role="status">Saving booking changes…</p>
    <p v-if="success" class="notice success" role="status">{{ success }}</p>
    <p v-if="error" class="notice error" role="alert">{{ error }}</p>
  </div>
</template>
