<script setup>
defineProps({ state: { type: Object, required: true } })
defineEmits(['name', 'mode', 'save', 'reload'])
</script>

<template>
  <section aria-labelledby="preferences-heading" class="card">
    <h3 id="preferences-heading">Your preferences</h3>
    <p>Fictional local profile. Use a made-up name only; no personal or medical details.</p>
    <form @submit.prevent="$emit('save')">
      <label for="fictional-name">Optional name (fictional)</label>
      <input id="fictional-name" :value="state.displayName" maxlength="60" autocomplete="off" :disabled="state.saving" @input="$emit('name', $event.target.value)">
      <fieldset aria-describedby="preference-help">
        <legend>How much guidance would you like today?</legend>
        <label><input type="radio" name="guidance" value="standard" :checked="state.guidanceMode === 'standard'" @change="$emit('mode', 'standard')"> Standard guidance</label>
        <label><input type="radio" name="guidance" value="fewer" :checked="state.guidanceMode === 'fewer'" @change="$emit('mode', 'fewer')"> Fewer instructions</label>
      </fieldset>
      <p id="preference-help">This is your preference, not a clinical assessment. You can change it at any time.</p>
      <p v-if="state.dirty">Your choice applies on this page. Save preferences to remember it; reflection personalization uses the saved preference.</p>
      <p v-if="state.loading" role="status">Loading saved preferences…</p>
      <p v-if="state.saving" role="status">Saving preferences…</p>
      <p v-if="state.notice" role="status">{{ state.notice }}</p>
      <p v-if="state.error" role="alert">{{ state.error }}</p>
      <button type="submit" :disabled="state.saving || state.loading">{{ state.error ? 'Retry saving preferences' : 'Save preferences' }}</button>
      <button v-if="state.error" type="button" :disabled="state.loading || state.saving" @click="$emit('reload')">Reload saved preferences</button>
    </form>
  </section>
</template>

<style scoped>
.card { border: 1px solid #bac8d2; border-radius: 0.6rem; padding: 1rem; margin-block: 1rem; background: #f5f8fa; }
h3 { margin-top: 0; }
label, legend { font-weight: 600; }
label { display: block; margin-block: 0.5rem; }
fieldset { margin: 1rem 0; border: 1px solid #bac8d2; }
input, button { font: inherit; }
input[type="text"], input:not([type]) { box-sizing: border-box; max-width: 100%; padding: 0.5rem; }
button { min-height: 44px; padding: 0.65rem 1rem; margin: 0.25rem; cursor: pointer; }
button:focus-visible, input:focus-visible { outline: 3px solid #164b75; outline-offset: 4px; }
</style>
