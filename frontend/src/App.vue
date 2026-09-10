<script setup>
import { nextTick, ref } from 'vue'

import { calculate } from './api/calculator'

const a = ref('')
const b = ref('')
const result = ref(null)
const error = ref('')
const isLoading = ref(false)
const firstInput = ref(null)

const operations = [
  { name: 'add', label: 'Add', symbol: '+', tone: 'terracotta' },
  { name: 'subtract', label: 'Subtract', symbol: '−', tone: 'plum' },
  { name: 'multiply', label: 'Multiply', symbol: '×', tone: 'ochre' },
  { name: 'divide', label: 'Divide', symbol: '÷', tone: 'olive' },
]

async function focusFirstInput() {
  await nextTick()
  firstInput.value?.focus()
}

async function submitCalculation(event) {
  const operation = event.submitter?.value ?? 'add'

  error.value = ''
  result.value = null
  isLoading.value = true

  try {
    result.value = await calculate(operation, Number(a.value), Number(b.value))
  } catch (requestError) {
    error.value = requestError instanceof Error ? requestError.message : 'Calculation failed.'
  } finally {
    isLoading.value = false
  }
}

function clearInputs() {
  a.value = ''
  b.value = ''
  focusFirstInput()
}

function resetCalculator() {
  a.value = ''
  b.value = ''
  result.value = null
  error.value = ''
  focusFirstInput()
}
</script>

<template>
  <main class="page-shell">
    <header class="intro">
      <p class="eyebrow">Hello Agent · arithmetic workbench</p>
      <h1>Make the numbers make sense.</h1>
      <p id="calculator-help" class="lede">
        Write two numbers, then choose the operation you want to run.
      </p>
    </header>

    <div class="worksheet">
      <form
        class="calculator"
        aria-describedby="calculator-help"
        @submit.prevent="submitCalculation"
      >
        <div class="input-grid">
          <div class="field">
            <label for="a">First number</label>
            <input
              id="a"
              ref="firstInput"
              v-model="a"
              name="a"
              type="number"
              step="any"
              inputmode="decimal"
              placeholder="For example, 7"
              required
            />
          </div>

          <div class="field">
            <label for="b">Second number</label>
            <input
              id="b"
              v-model="b"
              name="b"
              type="number"
              step="any"
              inputmode="decimal"
              placeholder="For example, 6"
              required
            />
          </div>
        </div>

        <fieldset class="operation-fieldset">
          <legend>Choose an operation</legend>
          <div class="operation-grid">
            <button
              v-for="operation in operations"
              :key="operation.name"
              class="operation-button"
              :class="operation.tone"
              type="submit"
              :value="operation.name"
              :disabled="isLoading"
              :aria-label="`${operation.label} the two numbers`"
            >
              <span class="operation-symbol" aria-hidden="true">{{ operation.symbol }}</span>
              <span>{{ operation.label }}</span>
            </button>
          </div>
        </fieldset>

        <div class="utility-actions" aria-label="Calculator clearing actions">
          <button class="utility-button" type="button" :disabled="isLoading" @click="clearInputs">
            Clear inputs
          </button>
          <button
            class="utility-button reset-button"
            type="button"
            :disabled="isLoading"
            @click="resetCalculator"
          >
            Reset calculator
          </button>
        </div>
      </form>

      <section
        class="answer-card"
        :class="{ 'has-result': result !== null, 'has-error': error }"
        :aria-busy="isLoading"
        aria-labelledby="answer-heading"
      >
        <p class="answer-kicker">Your working note</p>
        <h2 id="answer-heading">Answer</h2>

        <p v-if="isLoading" class="answer-message" aria-live="polite">Working it out…</p>
        <p v-else-if="error" class="error-message" role="alert">
          <strong>Check the calculation</strong>
          <span>{{ error }}</span>
        </p>
        <output v-else-if="result !== null" class="result-message" aria-live="polite">
          <span>Result:</span>
          <strong>{{ result }}</strong>
        </output>
        <p v-else class="answer-message">Your result will land here.</p>

        <p class="answer-hint">Clear inputs keeps this note. Reset calculator removes it.</p>
      </section>
    </div>
  </main>
</template>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

:global(body) {
  min-width: 20rem;
  min-height: 100vh;
  margin: 0;
  color: #27231f;
  background:
    radial-gradient(circle at 8% 8%, rgb(185 99 71 / 14%), transparent 24rem),
    linear-gradient(135deg, #f8f1e6 0%, #efe4d5 100%);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

button,
input {
  font: inherit;
}

button:focus-visible,
input:focus-visible {
  outline: 0.22rem solid #f0a51b;
  outline-offset: 0.2rem;
}

.page-shell {
  width: min(70rem, 100%);
  min-height: 100vh;
  margin: 0 auto;
  padding: clamp(2rem, 6vw, 5.5rem) clamp(1rem, 4vw, 3rem);
}

.intro {
  max-width: 46rem;
  margin-bottom: clamp(1.75rem, 4vw, 3rem);
}

.eyebrow,
.answer-kicker {
  margin: 0 0 0.55rem;
  color: #8c3f2c;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.13em;
  text-transform: uppercase;
}

h1,
h2,
p {
  margin-top: 0;
}

h1 {
  max-width: 12ch;
  margin-bottom: 0.8rem;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(2.25rem, 7vw, 5rem);
  font-weight: 700;
  letter-spacing: -0.045em;
  line-height: 0.98;
}

.lede {
  max-width: 38rem;
  margin-bottom: 0;
  color: #62584f;
  font-size: clamp(1rem, 2vw, 1.16rem);
  line-height: 1.6;
}

.worksheet {
  display: grid;
  gap: clamp(1rem, 3vw, 2rem);
  align-items: stretch;
}

.calculator,
.answer-card {
  border: 1px solid #cbbba8;
  border-radius: 1.15rem;
  box-shadow: 0 1.25rem 3rem rgb(80 52 36 / 10%);
}

.calculator {
  padding: clamp(1rem, 4vw, 2rem);
  background: rgb(255 252 246 / 88%);
}

.input-grid {
  display: grid;
  gap: 1rem;
}

.field {
  display: grid;
  gap: 0.45rem;
}

label,
legend {
  font-size: 0.86rem;
  font-weight: 800;
  letter-spacing: 0.025em;
}

input {
  width: 100%;
  min-height: 3.15rem;
  border: 1px solid #9a8a79;
  border-radius: 0.65rem;
  padding: 0.7rem 0.85rem;
  color: #27231f;
  background: #fffdfa;
}

input::placeholder {
  color: #85786c;
}

.operation-fieldset {
  min-width: 0;
  margin: 1.5rem 0 0;
  border: 0;
  padding: 0;
}

.operation-fieldset legend {
  margin-bottom: 0.7rem;
}

.operation-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.7rem;
}

.operation-button,
.utility-button {
  min-height: 3.2rem;
  border-radius: 0.7rem;
  cursor: pointer;
  font-weight: 800;
  transition:
    transform 150ms ease,
    box-shadow 150ms ease,
    filter 150ms ease;
}

.operation-button {
  display: flex;
  gap: 0.65rem;
  align-items: center;
  justify-content: center;
  border: 0;
  padding: 0.65rem 0.8rem;
  color: #fffdf7;
  box-shadow: 0 0.35rem 0 rgb(54 38 30 / 24%);
}

.operation-button:hover:not(:disabled),
.utility-button:hover:not(:disabled) {
  filter: brightness(1.07);
  transform: translateY(-0.12rem);
}

.operation-button:active:not(:disabled),
.utility-button:active:not(:disabled) {
  box-shadow: none;
  transform: translateY(0.12rem);
}

.operation-button:disabled,
.utility-button:disabled {
  cursor: wait;
  opacity: 0.58;
}

.operation-symbol {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.5rem;
  line-height: 1;
}

.terracotta {
  background: #9f432d;
}

.plum {
  background: #743d60;
}

.ochre {
  background: #7b5c16;
}

.olive {
  background: #4f613b;
}

.utility-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
  margin-top: 1.35rem;
  padding-top: 1.1rem;
  border-top: 1px dashed #cbbba8;
}

.utility-button {
  flex: 1 1 9rem;
  border: 1px solid #5f544b;
  padding: 0.65rem 0.85rem;
  color: #3f3731;
  background: #fffaf0;
  box-shadow: 0 0.25rem 0 #c9b9a5;
}

.reset-button {
  color: #722f25;
  background: #f5dfd6;
}

.answer-card {
  position: relative;
  overflow: hidden;
  min-height: 18rem;
  padding: clamp(1.4rem, 4vw, 2.3rem);
  background: #2f2925;
  color: #fff8ed;
  transition:
    background-color 180ms ease,
    border-color 180ms ease;
}

.answer-card::after {
  position: absolute;
  right: -2rem;
  bottom: -3.5rem;
  width: 10rem;
  height: 10rem;
  border: 1.2rem solid rgb(255 255 255 / 8%);
  border-radius: 50%;
  content: "";
}

.answer-card.has-result {
  border-color: #596b43;
  background: #35432e;
}

.answer-card.has-error {
  border-color: #d2755d;
  background: #6e3029;
}

.answer-card .answer-kicker {
  color: #f0b25d;
}

.answer-card h2 {
  margin-bottom: 2rem;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(1.8rem, 4vw, 2.5rem);
}

.answer-message {
  color: #ddd2c5;
  font-size: 1.05rem;
}

.result-message {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  color: #f7e7bd;
}

.result-message span {
  font-size: 0.9rem;
  font-weight: 800;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

.result-message strong {
  overflow-wrap: anywhere;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(3rem, 10vw, 6rem);
  font-weight: 700;
  line-height: 0.95;
}

.error-message {
  display: grid;
  gap: 0.45rem;
  padding: 1rem;
  border: 1px solid #efb4a1;
  border-radius: 0.7rem;
  color: #fff2ed;
  background: rgb(58 15 12 / 28%);
}

.error-message strong {
  font-size: 1.08rem;
}

.answer-hint {
  position: absolute;
  right: 1.4rem;
  bottom: 1.2rem;
  left: 1.4rem;
  z-index: 1;
  margin-bottom: 0;
  color: #d7cabe;
  font-size: 0.78rem;
  line-height: 1.45;
}

@media (min-width: 40rem) {
  .input-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 54rem) {
  .worksheet {
    grid-template-columns: minmax(0, 1.25fr) minmax(18rem, 0.75fr);
  }

  .answer-card {
    transform: rotate(0.6deg);
  }
}

@media (max-width: 25rem) {
  .operation-grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .operation-button,
  .utility-button,
  .answer-card {
    transition: none;
  }
}
</style>
