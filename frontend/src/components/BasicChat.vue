<script setup>
import { useChat } from '../composables/useChat.js'
const { input, messages, pending, error, conversationId, trace, tracePending, traceError, traceLoaded, send, reloadTrace } = useChat()
</script>

<template>
  <section class="panel" aria-labelledby="chat-heading">
    <div class="section-intro">
      <p class="eyebrow">Saved hotel assistant</p>
      <h2 id="chat-heading">RoomTour chatbot</h2>
      <p id="chat-hint" class="muted">Ask about saved hotels with a ZIP and stay dates. Rates and room availability are simulated classroom data. Saved results are a subset of hotels in the area. Each question is answered independently; include its full ZIP/date context. Chat cannot make bookings.</p>
    </div>
    <div class="chat-messages" role="log" aria-label="Chat messages" aria-live="polite" :aria-busy="pending">
      <article v-for="(message, index) in messages" :key="index" class="notice chat-message">
        <p><strong>{{ message.role === 'user' ? 'You' : 'Assistant' }}:</strong> {{ message.text }}</p>
        <p v-if="message.details?.retrieved_row_count === 0" class="muted">No matching saved records were retrieved; missing availability is unknown.</p>
        <details v-if="message.details" class="rag-details">
          <summary>RAG details — how this answer was produced</summary>
          <dl>
            <dt>Conversation ID</dt><dd>{{ message.details.conversation_id }}</dd>
            <dt>Proposed SQL</dt><dd><pre>{{ message.details.proposed_sql }}</pre></dd>
            <dt>Executed SQL</dt><dd><pre>{{ message.details.executed_sql }}</pre></dd>
            <dt>Retrieved row count</dt><dd>{{ message.details.retrieved_row_count }}</dd>
            <dt>Retrieved records (bounded)</dt><dd><pre>{{ JSON.stringify(message.details.retrieved_rows, null, 2) }}</pre></dd>
          </dl>
        </details>
      </article>
    </div>
    <form class="search-form" @submit.prevent="send">
      <label for="chat-message">Hotel question</label>
      <div class="search-controls">
        <input id="chat-message" v-model="input" type="text" maxlength="2000" required aria-describedby="chat-hint" :readonly="pending" />
        <button type="submit" :disabled="pending || tracePending || !input.trim()">{{ pending ? 'Sending…' : 'Send' }}</button>
      </div>
    </form>
    <p v-if="pending" class="notice" role="status">Checking saved hotels and preparing an answer… Please wait before sending another question.</p>
    <p v-if="error" class="notice error" role="alert">{{ error }} Your message remains in the input for retry.</p>
    <section v-if="conversationId" class="saved-trace" aria-label="Saved conversation trace" :aria-busy="tracePending">
      <p class="muted">Conversation: {{ conversationId }}</p>
      <button class="secondary" type="button" :disabled="pending || tracePending" @click="reloadTrace">{{ tracePending ? 'Reloading…' : 'Reload saved trace' }}</button>
      <p v-if="tracePending" role="status">Reloading saved conversation trace…</p>
      <p v-if="traceError" class="notice error" role="alert">{{ traceError }}</p>
      <details v-if="traceLoaded">
        <summary>Saved conversation trace (up to 100 records)</summary>
        <p v-if="!trace.length" class="muted">No saved trace records were returned.</p>
        <ol v-else>
          <li v-for="record in trace" :key="record.message_id"><strong>{{ record.stage }}</strong> · {{ record.role }} · {{ record.timestamp }}<pre>{{ record.content }}</pre></li>
        </ol>
      </details>
    </section>
  </section>
</template>

<style scoped>
.chat-message { white-space: pre-wrap; overflow-wrap: anywhere; }
.rag-details, .saved-trace { margin-top: 16px; }
summary { cursor: pointer; font-weight: bold; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; font-size: .85rem; }
dt { font-weight: bold; margin-top: 10px; }
dd { margin-left: 0; }
.saved-trace button { margin-top: 8px; }
</style>
