export async function sendChat(message, request = fetch) {
  let response
  try {
    response = await request('/api/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    })
  } catch {
    throw new Error('Could not reach RoomTour chat. Please retry.')
  }
  if (!response.ok) throw new Error('Chat is unavailable. Please retry later or check backend configuration.')
  const data = await response.json().catch(() => null)
  if (typeof data?.reply !== 'string' || !data.reply.trim()) throw new Error('Chat returned an invalid answer. Please retry.')
  return data.reply
}
