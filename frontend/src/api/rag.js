const conversationPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
export const isConversationId = value => typeof value === 'string' && conversationPattern.test(value)
const stages = new Set(['user_question', 'proposed_sql', 'executed_sql', 'retrieval_result', 'assistant_answer', 'error'])
const sensitiveField = /key|authorization|headers|secret|password|token|env/i

function safeText(text) {
  return text.replace(/\bsk-[A-Za-z0-9_-]+/g, '[REDACTED]')
    .replace(/\bBearer\s+[^\s"',}]+/gi, '[REDACTED]')
}

function safeRows(rows) {
  return rows.map(row => Object.fromEntries(Object.entries(row)
    .filter(([key, value]) => !sensitiveField.test(key) && (value === null || ['string', 'number'].includes(typeof value)))
    .slice(0, 20).map(([key, value]) => [key, typeof value === 'string' ? safeText(value) : value])))
}

export function createRagApi(request = fetch) {
  async function send(url, options) {
    let response
    try { response = await request(url, options) } catch {
      throw new Error('Could not reach RoomTour hotel assistant. Please retry.')
    }
    const data = await response.json().catch(() => null)
    if (!response.ok) {
      const error = new Error('Hotel assistant could not complete the request. Please retry, or check backend configuration.')
      if (isConversationId(data?.conversation_id)) error.conversationId = data.conversation_id
      throw error
    }
    return data
  }
  return {
    async answer(question, conversationId) {
      const data = await send('/api/rag/answer', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, ...(isConversationId(conversationId) ? { conversation_id: conversationId } : {}) }),
      })
      if (!isConversationId(data?.conversation_id) || typeof data?.answer !== 'string' || !data.answer.trim()
        || typeof data.proposed_sql !== 'string' || typeof data.executed_sql !== 'string'
        || !Number.isInteger(data.retrieved_row_count) || data.retrieved_row_count < 0 || data.retrieved_row_count > 20
        || !Array.isArray(data.retrieved_rows) || data.retrieved_rows.length !== data.retrieved_row_count
        || !data.retrieved_rows.every(row => row && typeof row === 'object' && !Array.isArray(row))) {
        throw new Error('Hotel assistant returned an invalid answer. Please retry.')
      }
      return {
        conversation_id: data.conversation_id, answer: safeText(data.answer),
        proposed_sql: safeText(data.proposed_sql), executed_sql: safeText(data.executed_sql),
        retrieved_row_count: data.retrieved_row_count, retrieved_rows: safeRows(data.retrieved_rows),
      }
    },
    async history(conversationId) {
      if (!isConversationId(conversationId)) throw new Error('No saved conversation is available yet.')
      const data = await send(`/api/rag/conversations/${encodeURIComponent(conversationId)}`, { method: 'GET' })
      if (data?.conversation_id !== conversationId || !Array.isArray(data.messages) || data.messages.length > 100
        || !data.messages.every(record => Number.isInteger(record.message_id) && record.conversation_id === conversationId
          && typeof record.timestamp === 'string' && ['user', 'system', 'assistant'].includes(record.role)
          && typeof record.content === 'string' && stages.has(record.stage))) {
        throw new Error('Saved conversation returned an invalid trace. Please retry.')
      }
      return data.messages.map(record => ({
        message_id: record.message_id, timestamp: record.timestamp, role: record.role,
        stage: record.stage, content: safeText(record.content),
      }))
    },
  }
}
