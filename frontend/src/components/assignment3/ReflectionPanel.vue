<script setup>
import { onMounted, ref, watch } from 'vue'
import { createReflection } from '../../assignment3/reflection.js'

const props = defineProps({ sessionId: { type: String, required: true }, review: Boolean, available: { type: Boolean, default: true } })
const reflection = createReflection({ changed: (state) => { view.value = state } })
const view = ref({ ...reflection.state })
function open() {
  reflection.reset(props.sessionId)
  if (props.review) void reflection.load(props.sessionId)
}
onMounted(open)
watch(() => props.sessionId, open)
</script>

<template>
  <section :aria-label="review ? 'Saved conversation' : 'Optional fictional reflection'">
    <h3>{{ review ? 'Saved conversation' : 'Optional reflection' }}</h3>
    <template v-if="review">
      <p v-if="view.historyLoading" role="status">Loading saved conversation…</p>
      <p v-if="view.historyError" role="alert">{{ view.historyError }}</p>
      <p v-if="!view.historyLoading && !view.historyError && !view.history.length">No saved conversation for this session.</p>
      <ol>
        <li v-for="message in view.history" :key="message.message_id">
          <strong>{{ { user: 'Fictional reflection', assistant: 'Model acknowledgment', error: 'Error' }[message.role] }}</strong>
          <p>{{ message.content }}</p>
        </li>
      </ol>
      <button v-if="view.historyError" type="button" @click="reflection.load(sessionId)">Retry loading conversation</button>
    </template>
    <template v-else>
      <p>You can skip this and return Home. Use fictional text only; do not enter personal or sensitive information.</p>
      <p v-if="!available">Session saving must finish successfully before submitting a reflection.</p>
      <form @submit.prevent="reflection.submit(sessionId)">
        <label :for="`reflection-${sessionId}`">Optional reflection: In one short sentence, how did this fictional exercise feel?</label>
        <textarea :id="`reflection-${sessionId}`" :value="view.input" maxlength="300" rows="3" :readonly="view.submitted" :disabled="!available" :aria-describedby="`reflection-limit-${sessionId}`" @input="reflection.setInput($event.target.value)" />
        <p :id="`reflection-limit-${sessionId}`">{{ view.input.length }} / 300 characters. One successful exchange per session.</p>
        <button v-if="!view.submitted" type="submit" :disabled="!available || !view.input.trim() || view.pending">Submit reflection</button>
      </form>
      <p v-if="view.pending" role="status">Waiting for a reflection response…</p>
      <p v-if="view.error" role="alert">{{ view.error }}</p>
      <button v-if="view.error && !view.supportBlocked" type="button" :disabled="view.pending || !available" @click="reflection.submit(sessionId)">Retry reflection</button>
      <ol>
        <li v-for="message in view.messages" :key="message.message_id">
          <strong>{{ { user: 'Fictional reflection', assistant: 'Model acknowledgment', error: 'Error' }[message.role] }}</strong>
          <p>{{ message.content }}</p>
        </li>
      </ol>
    </template>
  </section>
</template>

<style scoped>
section { margin-block: 1rem; padding-block: 0.75rem; border-top: 1px solid #ccd5dc; }
label, textarea { display: block; }
textarea { width: 100%; box-sizing: border-box; font: inherit; }
button { padding: 0.65rem 1rem; cursor: pointer; font: inherit; }
button:focus-visible, textarea:focus-visible { outline: 3px solid #164b75; outline-offset: 4px; }
</style>
