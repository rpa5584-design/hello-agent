const supportedOperations = new Set(['add', 'subtract', 'multiply', 'divide'])

export async function calculate(operation, a, b) {
  if (!supportedOperations.has(operation)) {
    throw new Error('Choose a supported operation.')
  }

  const query = new URLSearchParams({
    a: String(a),
    b: String(b),
  })
  const response = await fetch(`/api/${operation}?${query}`)
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.detail || 'The calculation could not be completed.')
  }

  return data.result
}
