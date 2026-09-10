import { computed, ref } from 'vue'
import { calculate } from '../api/calculator.js'

export function useCalculator(request = calculate) {
  const entry = ref('0')
  const stored = ref(null)
  const operation = ref(null)
  const replaceEntry = ref(true)
  const busy = ref(false)
  const error = ref('')
  const hasResult = ref(false)
  const history = ref([])
  let historyId = 0
  const symbols = { add: '+', subtract: '−', multiply: '×', divide: '÷' }
  const caption = computed(() => error.value ? 'Try again' : busy.value ? 'Calculating…'
    : operation.value ? `${stored.value} ${symbols[operation.value]}`
      : hasResult.value ? 'Result' : 'Ready')

  function clear() {
    if (busy.value) return
    entry.value = '0'
    stored.value = null
    operation.value = null
    replaceEntry.value = true
    error.value = ''
    hasResult.value = false
  }

  function digit(value) {
    if (busy.value) return
    if (error.value) clear()
    hasResult.value = false
    if (replaceEntry.value) {
      entry.value = value === '.' ? '0.' : value
      replaceEntry.value = false
    } else if (value === '.') {
      if (!entry.value.includes('.')) entry.value += '.'
    } else if (entry.value.replace(/[-.]/g, '').length < 15) {
      entry.value = entry.value === '0' ? value : entry.value === '-0' ? `-${value}` : entry.value + value
    }
  }

  function toggleSign() {
    if (busy.value || error.value) return
    entry.value = entry.value.startsWith('-') ? entry.value.slice(1) : `-${entry.value}`
    replaceEntry.value = false
  }

  async function run(name, left, right) {
    busy.value = true
    error.value = ''
    try {
      const value = await request(name, left, right)
      if (!Number.isFinite(value)) throw new Error('Result is outside the supported range.')
      entry.value = String(value)
      hasResult.value = true
      history.value = [{ id: ++historyId, expression: `${left} ${symbols[name]} ${right}`, result: value }, ...history.value].slice(0, 5)
      return value
    } catch (failure) {
      error.value = failure instanceof Error ? failure.message : 'Calculation failed.'
      operation.value = null
      stored.value = null
      replaceEntry.value = true
      return null
    } finally {
      busy.value = false
    }
  }

  async function chooseOperation(name) {
    if (busy.value || error.value) return
    if (operation.value && !replaceEntry.value) {
      const value = await run(operation.value, stored.value, Number(entry.value))
      if (value === null) return
      stored.value = value
    } else {
      stored.value = Number(entry.value)
    }
    operation.value = name
    replaceEntry.value = true
  }

  async function equals() {
    if (busy.value || error.value || !operation.value) return
    await run(operation.value, stored.value, Number(entry.value))
    operation.value = null
    stored.value = null
    replaceEntry.value = true
  }

  async function percent() {
    if (busy.value || error.value) return
    // Percentage conversion is arithmetic too, so it goes through FastAPI.
    await run('divide', Number(entry.value), 100)
    replaceEntry.value = false
  }

  return { entry, operation, busy, error, caption, history, clear, digit, toggleSign, chooseOperation, equals, percent }
}
