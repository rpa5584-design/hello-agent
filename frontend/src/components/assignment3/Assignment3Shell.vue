<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { createBreathing } from '../../assignment3/breathing.js'
import { createSessionStore } from '../../assignment3/sessions.js'
import ReflectionPanel from './ReflectionPanel.vue'
import { createProfileStore } from '../../assignment3/profile.js'
import PreferencesCard from './PreferencesCard.vue'
import RecentActivity from './RecentActivity.vue'

const heading = ref(null)
const selectedHistory = ref('')
const preferences = createProfileStore({ changed: state => { profile.value = state } })
const profile = ref({ ...preferences.state })
const sessions = createSessionStore({ changed: (state) => { saved.value = state } })
const saved = ref({ ...sessions.state })
const run = createBreathing({ changed: () => { view.value = { ...run.state }; sessions.observe(run.state, { fewerOptions: profile.value.guidanceMode === 'fewer' }) } })
const view = ref({ ...run.state })
watch(() => view.value.screen, screen => {
  heading.value?.focus()
  if (screen === 'home') void sessions.loadHistory()
}, { flush: 'post' })
let timer
async function action(fn) {
  fn()
  await nextTick()
  heading.value?.focus()
}
function visibilityChanged() {
  if (document.hidden) run.interrupt()
}
function pageHidden() { run.interrupt() }
onMounted(() => {
  void preferences.load()
  void (async () => { await sessions.recover(); await sessions.loadHistory() })()
  timer = setInterval(run.tick, 100)
  document.addEventListener('visibilitychange', visibilityChanged)
  window.addEventListener('pagehide', pageHidden)
})
onUnmounted(() => {
  clearInterval(timer)
  document.removeEventListener('visibilitychange', visibilityChanged)
  window.removeEventListener('pagehide', pageHidden)
  run.interrupt()
})
</script>

<template>
  <main>
    <header>
      <h1>Assignment 3 Skills Prototype</h1>
      <p>Coursework skills prototype · Not therapy or diagnosis</p>
      <p>Nobody is monitoring this experience</p>
      <p>Testing uses fictional scenarios only</p>
    </header>
    <p v-if="saved.saving" role="status">Saving session changes…</p>
    <div v-if="saved.warning" role="alert">
      <p>{{ saved.warning }}</p>
      <button type="button" :disabled="saved.saving" @click="sessions.retry()">Retry saving</button>
    </div>
    <section aria-labelledby="screen-heading">
      <h2 id="screen-heading" ref="heading" tabindex="-1">{{ {
        home: 'Choose a skill', intro: 'Paced Breathing', exercise: 'Paced Breathing',
        finished: 'Exercise finished.', stopped: 'The exercise was stopped.',
        interrupted: 'The exercise was interrupted.', leave: 'You have left the exercise.',
        support: 'Crisis Support', history: 'Saved History',
      }[view.screen] }}</h2>
      <PreferencesCard v-if="['home', 'intro'].includes(view.screen)" :state="profile" @name="preferences.setName" @mode="preferences.setMode" @save="preferences.save" @reload="preferences.load" />
      <template v-if="view.screen === 'home'">
        <p v-if="profile.displayName">Welcome, {{ profile.displayName }}.</p>
        <p>About 60 seconds. No typing needed.</p>
        <RecentActivity :records="saved.history" :loading="saved.loading" :loaded="saved.loaded" :error="saved.historyError" :guidance-mode="profile.guidanceMode" @reload="sessions.loadHistory()" />
        <button type="button" @click="action(() => run.navigate('intro'))">Paced Breathing</button>
        <button type="button" @click="action(() => { run.navigate('history'); sessions.loadHistory() })">Saved History</button>
      </template>
      <template v-else-if="view.screen === 'intro'">
        <p>Inhale for 4 seconds.</p>
        <p>Exhale for 6 seconds.</p>
        <p>Repeat for 6 cycles. This exercise lasts about 60 seconds.</p>
        <p>You can stop at any time.</p>
        <p>Your chosen guidance: {{ profile.guidanceMode === 'fewer' ? 'Fewer instructions' : 'Standard guidance' }}. This changes text only, not the 4/6 timing.</p>
        <details>
          <summary>Why this walkthrough?</summary>
          <p>Our course research favors a short single skill, one cue at a time, permission to stop, and support that stays available. These inform the six cycles and optional simpler guidance; they are design choices, not evidence of clinical benefit.</p>
        </details>
        <button type="button" @click="action(run.start)">Start</button>
      </template>
      <template v-else-if="view.screen === 'exercise'">
        <p>{{ profile.guidanceMode === 'fewer' ? 'Fewer instructions' : 'Standard guidance' }} · Exercise in progress.</p>
        <p v-if="profile.guidanceMode !== 'fewer'">Follow the text cues: inhale for 4 seconds, then exhale for 6 seconds.</p>
        <p>Cycle {{ view.cycle }} of 6</p>
        <p class="cue" aria-live="polite" aria-atomic="true">{{ view.phase }}</p>
        <p>{{ view.remaining }} seconds remaining in this cue</p>
        <p v-if="profile.guidanceMode !== 'fewer'">You can stop at any time.</p>
      </template>
      <template v-else-if="['finished', 'stopped', 'interrupted'].includes(view.screen)">
        <p v-if="view.durationMs !== null">Measured exercise duration: {{ (view.durationMs / 1000).toFixed(1) }} seconds.</p>
        <p v-if="saved.sessionId">Session ID: {{ saved.sessionId }}</p>
        <ReflectionPanel v-if="['finished', 'stopped'].includes(view.screen) && saved.sessionId" :key="saved.sessionId" :session-id="saved.sessionId" :available="!saved.saving && !saved.warning" />
        <button type="button" @click="action(() => run.navigate('home'))">Back to Home</button>
        <button v-if="view.screen !== 'finished'" type="button" @click="action(run.start)">Start again</button>
      </template>
      <template v-else-if="view.screen === 'history'">
        <p v-if="saved.loading" role="status">Loading Saved History…</p>
        <p v-if="saved.historyError" role="alert">{{ saved.historyError }}</p>
        <p v-if="saved.loaded && !saved.history.length">No saved sessions yet.</p>
        <ul v-if="saved.history.length">
          <li v-for="session in saved.history" :key="session.session_id">
            <p><time :datetime="session.started_at">{{ new Date(session.started_at).toLocaleString() }}</time></p>
            <p>{{ session.selected_skill }} · {{ session.status }}</p>
            <p>Measured duration: {{ session.measured_duration_seconds === null ? 'Unavailable' : `${session.measured_duration_seconds.toFixed(1)} seconds` }}</p>
            <p>Session ID: {{ session.session_id }}</p>
            <button type="button" @click="selectedHistory = session.session_id">Open saved session conversation</button>
            <ReflectionPanel v-if="selectedHistory === session.session_id" :key="selectedHistory" :session-id="selectedHistory" review />
          </li>
        </ul>
        <button type="button" :disabled="saved.loading" @click="sessions.loadHistory()">Reload history</button>
        <button v-if="saved.hasMore" type="button" :disabled="saved.loading" @click="sessions.loadHistory(true)">Load more</button>
      </template>
      <template v-else-if="view.screen === 'support'">
        <p>This coursework prototype is not a crisis service.</p>
        <p>United States: 988 Suicide &amp; Crisis Lifeline.</p>
        <p>Call or text 988:</p>
        <p><a href="tel:988?oai_link_source=model_response_hotline">Call 988</a> · <a href="sms:988?oai_link_source=model_response_hotline">Text 988</a></p>
        <p><a href="https://988lifeline.org/chat/?oai_link_source=model_response_hotline">External Lifeline chat — requires network access</a></p>
        <p>For immediate danger or a medical emergency, call 911.</p>
        <p>This information is bundled with the page. Calls and texts require phone service.</p>
      </template>
      <template v-else-if="view.screen === 'leave'">
        <p>No exercise is running. You can close this tab or return Home.</p>
        <button type="button" @click="action(() => run.navigate('home'))">Return Home</button>
      </template>
    </section>
    <nav aria-label="Exercise and safety controls">
      <button v-if="view.status === 'active'" type="button" @click="action(run.stop)">Stop</button>
      <span v-else>No exercise is running.</span>
      <button type="button" @click="action(() => run.navigate('home'))">Back</button>
      <button type="button" @click="action(() => run.navigate('leave'))">Leave</button>
      <button type="button" @click="action(() => run.navigate('support'))">Crisis Support</button>
    </nav>
  </main>
</template>

<style scoped>
main { max-width: 42rem; margin: 2rem auto; padding: 1rem; font-family: Arial, sans-serif; line-height: 1.6; color: #213547; background: #fff; }
header { border-bottom: 1px solid #ccd5dc; }
section { padding-block: 1rem; }
nav { display: flex; flex-wrap: wrap; align-items: center; gap: 0.75rem; border-top: 1px solid #ccd5dc; padding-block: 1rem; position: sticky; bottom: 0; background: #fff; z-index: 1; }
button { padding: 0.65rem 1rem; cursor: pointer; font: inherit; }
a { color: #164b75; }
button:focus-visible, a:focus-visible, h2:focus-visible, summary:focus-visible { outline: 3px solid #164b75; outline-offset: 4px; }
summary { cursor: pointer; margin-block: 0.5rem; }
.cue { font-size: 2rem; font-weight: bold; }
</style>
