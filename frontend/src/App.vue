<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useCalculator } from './composables/useCalculator.js'

const { entry, operation, busy, error, caption, history, clear, digit, toggleSign, chooseOperation, equals, percent } = useCalculator()
const keys = [
  { label: 'AC', name: 'All clear', kind: 'function', action: clear },
  { label: '+/−', name: 'Change sign', kind: 'function', action: toggleSign },
  { label: '%', name: 'Percent', kind: 'function', action: percent },
  { label: '÷', name: 'Divide', kind: 'operator', operation: 'divide' },
  { label: '7' }, { label: '8' }, { label: '9' },
  { label: '×', name: 'Multiply', kind: 'operator', operation: 'multiply' },
  { label: '4' }, { label: '5' }, { label: '6' },
  { label: '−', name: 'Subtract', kind: 'operator', operation: 'subtract' },
  { label: '1' }, { label: '2' }, { label: '3' },
  { label: '+', name: 'Add', kind: 'operator', operation: 'add' },
  { label: '0', kind: 'zero' },
  { label: '.', name: 'Decimal point' },
  { label: '=', name: 'Equals', kind: 'operator', action: equals },
]
function activate(key) {
  if (key.action) key.action()
  else if (key.operation) chooseOperation(key.operation)
  else digit(key.label)
}
function keyboard(event) {
  if (event.ctrlKey || event.metaKey || event.altKey) return
  const operations = { '+': 'add', '-': 'subtract', '*': 'multiply', '/': 'divide' }
  if (/^[0-9.]$/.test(event.key)) { event.preventDefault(); digit(event.key) }
  else if (operations[event.key]) { event.preventDefault(); chooseOperation(operations[event.key]) }
  else if (event.key === '=' || event.key === 'Enter') { event.preventDefault(); equals() }
  else if (event.key === 'Escape') { event.preventDefault(); clear() }
  else if (event.key === '%') { event.preventDefault(); percent() }
}
onMounted(() => window.addEventListener('keydown', keyboard))
onUnmounted(() => window.removeEventListener('keydown', keyboard))
</script>

<template>
  <main class="page-shell">
    <section class="calculator" aria-label="Hello Agent calculator" :aria-busy="busy">
      <header class="window-header" aria-hidden="true">
        <span class="dot red"></span><span class="dot yellow"></span><span class="dot gray"></span>
      </header>
      <div class="display" :class="{ 'has-error': error }">
        <p class="caption">{{ caption }}</p>
        <output class="number" :class="{ compact: entry.length > 9, small: entry.length > 14 }" aria-label="Calculator display" aria-live="polite">{{ error ? 'Error' : entry }}</output>
        <p v-if="error" class="error-message" role="alert">{{ error }}</p>
      </div>
      <div class="keypad" aria-label="Calculator keypad">
        <button v-for="key in keys" :key="key.label" type="button" class="key" :class="[key.kind, { selected: key.operation && operation === key.operation }]" :aria-label="key.name || key.label" :aria-pressed="key.operation ? operation === key.operation : undefined" :disabled="busy" @click="activate(key)">{{ key.label }}</button>
      </div>
      <section class="history" aria-labelledby="history-heading">
        <h2 id="history-heading">Calculation history</h2>
        <p class="history-note">Last 3 calculations · newest first</p>
        <ol v-if="history.length" aria-label="Recent calculations" aria-live="polite">
          <li v-for="item in history" :key="item.id">
            <span>{{ item.expression }}</span>
            <strong>= {{ item.result }}</strong>
          </li>
        </ol>
        <p v-else class="history-empty">Your completed calculations will appear here.</p>
      </section>
    </section>
  </main>
</template>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(body) { margin: 0; background: #eeede8; color: #f5f5f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
.page-shell { min-height: 100svh; display: grid; place-items: center; padding: 24px 12px; }
.calculator { width: min(100%, 320px); border: 1px solid #50504c; border-radius: 29px; background: #1c1c1c; padding: 22px 12px 14px; box-shadow: 0 20px 50px #00000024; }
.window-header { display: flex; gap: 9px; padding-left: 4px; }
.dot { width: 12px; height: 12px; border-radius: 50%; }
.red { background: #ff4d57; }
.yellow { background: #ffbd2e; }
.gray { background: #484844; }
.display { min-height: 125px; padding: 22px 5px 18px; text-align: right; }
.caption { margin: 0 0 3px; color: #a0a09b; font-size: 17px; min-height: 22px; overflow-wrap: anywhere; }
.number { display: block; font-size: 52px; font-weight: 300; line-height: 1.12; letter-spacing: -.035em; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.number.compact { font-size: 36px; }
.number.small { font-size: 25px; }
.has-error .number { color: #ffb4aa; }
.error-message { background: #482823; color: #ffc6bc; padding: 8px 10px; border-radius: 9px; margin: 10px 0 0; font-size: 13px; line-height: 1.4; }
.keypad { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 9px; }
.key { display: grid; place-items: center; aspect-ratio: 1; width: 100%; padding: 0; border: 0; border-radius: 50%; background: #444442; color: #fff; font: inherit; font-size: 27px; font-weight: 400; cursor: pointer; touch-action: manipulation; transition: background-color 120ms, transform 120ms; -webkit-tap-highlight-color: transparent; }
.key.function { background: #838380; font-size: 25px; }
.key.operator { background: #ff9500; font-size: 33px; }
.key.zero { grid-column: span 2; aspect-ratio: auto; border-radius: 999px; justify-items: start; padding-left: 27px; }
.key:hover:not(:disabled) { background: #63635f; }
.key.function:hover:not(:disabled) { background: #a1a19d; }
.key.operator:hover:not(:disabled) { background: #ffaf38; }
.key.operator.selected { background: #fff3df; color: #e67e00; }
.key:active:not(:disabled) { transform: scale(.94); }
.key:focus-visible { outline: 3px solid #ffd28c; outline-offset: 3px; }
.key:disabled { opacity: .6; cursor: wait; }
.history { margin-top: 22px; padding: 18px 4px 4px; border-top: 1px solid #444442; }
.history h2 { margin: 0; font-size: 16px; font-weight: 500; }
.history-note, .history-empty { color: #aaa9a5; font-size: 12px; line-height: 1.5; }
.history-note { margin: 5px 0 12px; }
.history-empty { margin: 0; }
.history ol { list-style: none; padding: 0; margin: 0; }
.history li { display: grid; gap: 4px; padding: 10px 0; overflow-wrap: anywhere; font-variant-numeric: tabular-nums; }
.history li + li { border-top: 1px solid #333331; }
.history li span { color: #c4c4bf; font-size: 14px; }
.history li strong { color: #ffbd61; text-align: right; font-size: 20px; font-weight: 400; }
@media (max-width: 350px) { .key { font-size: 24px; } .key.function { font-size: 22px; } .key.operator { font-size: 29px; } .key.zero { padding-left: 24px; } }
@media (prefers-reduced-motion: reduce) { .key { transition: none; } }
</style>
