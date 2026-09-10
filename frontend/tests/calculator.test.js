import { test } from 'node:test'
import assert from 'node:assert/strict'
import { useCalculator } from '../src/composables/useCalculator.js'

test('all four operations send operands to the existing API on equals', async () => {
  for (const [operation, expected] of [['add', 13], ['subtract', 1], ['multiply', 42], ['divide', 7 / 6]]) {
    const calls = []
    const calculator = useCalculator(async (...args) => { calls.push(args); return expected })
    calculator.digit('7')
    await calculator.chooseOperation(operation)
    calculator.digit('6')
    assert.equal(calls.length, 0)
    await calculator.equals()
    assert.deepEqual(calls, [[operation, 7, 6]])
    assert.equal(calculator.entry.value, String(expected))
    calculator.digit('2')
    assert.equal(calculator.entry.value, '2')
  }
})

test('decimal, sign, percent, and clear preserve operand entry', async () => {
  const calls = []
  const calculator = useCalculator(async (...args) => { calls.push(args); return -0.025 })
  for (const value of ['2', '.', '.', '5']) calculator.digit(value)
  calculator.toggleSign()
  assert.equal(calculator.entry.value, '-2.5')
  await calculator.percent()
  assert.deepEqual(calls, [['divide', -2.5, 100]])
  assert.equal(calculator.entry.value, '-0.025')
  calculator.clear()
  assert.equal(calculator.entry.value, '0')
  assert.equal(calculator.operation.value, null)
})

test('operator replacement and chaining use backend results', async () => {
  const calls = []
  const calculator = useCalculator(async (...args) => { calls.push(args); return calls.length === 1 ? 42 : 44 })
  calculator.digit('7')
  await calculator.chooseOperation('add')
  await calculator.chooseOperation('multiply')
  calculator.digit('6')
  await calculator.chooseOperation('add')
  calculator.digit('2')
  await calculator.equals()
  assert.deepEqual(calls, [['multiply', 7, 6], ['add', 42, 2]])
})

test('failed requests recover on new entry and pending requests block duplicate input', async () => {
  let reject
  const calculator = useCalculator(() => new Promise((_, fail) => { reject = fail }))
  calculator.digit('8')
  await calculator.chooseOperation('divide')
  calculator.digit('0')
  const pending = calculator.equals()
  assert.equal(calculator.busy.value, true)
  calculator.digit('3')
  calculator.clear()
  assert.equal(calculator.entry.value, '0')
  reject(new Error('Cannot divide by zero.'))
  await pending
  assert.equal(calculator.error.value, 'Cannot divide by zero.')
  assert.equal(calculator.busy.value, false)
  calculator.digit('4')
  assert.equal(calculator.error.value, '')
  assert.equal(calculator.entry.value, '4')
})

test('history retains the last five successes, survives clear, and excludes failures', async () => {
  let result = 0
  const calculator = useCalculator(async () => {
    if (result === 6) throw new Error('Request failed')
    return ++result
  })
  assert.deepEqual(calculator.history.value, [])
  for (let i = 1; i <= 6; i++) {
    calculator.clear()
    calculator.digit(String(i))
    await calculator.chooseOperation('add')
    calculator.digit('0')
    await calculator.equals()
  }
  assert.deepEqual(calculator.history.value.map(({ expression, result }) => [expression, result]), [
    ['6 + 0', 6], ['5 + 0', 5], ['4 + 0', 4], ['3 + 0', 3], ['2 + 0', 2],
  ])
  calculator.clear()
  await calculator.chooseOperation('divide')
  await calculator.equals()
  assert.equal(calculator.error.value, 'Request failed')
  assert.deepEqual(calculator.history.value.map(item => item.result), [6, 5, 4, 3, 2])
})
