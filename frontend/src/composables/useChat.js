import { ref } from 'vue'
import { createRagApi, isConversationId } from '../api/rag.js'

export const CONVERSATION_STORAGE_KEY = 'roomtour.currentConversationId'

function browserStorage() {
  try { return typeof window === 'undefined' ? null : window.localStorage } catch { return null }
}

export function useChat(request = createRagApi().answer, loadHistory = createRagApi().history, storage = browserStorage()) {
  let restoredId = ''
  try {
    const saved = storage?.getItem(CONVERSATION_STORAGE_KEY)
    if (isConversationId(saved)) restoredId = saved
  } catch { /* Chat remains usable when browser storage is unavailable. */ }
  const input = ref(''), messages = ref([]), pending = ref(false), error = ref('')
  const conversationId = ref(restoredId), trace = ref([]), tracePending = ref(false), traceError = ref(''), traceLoaded = ref(false)
  function rememberConversation(id) {
    if (!isConversationId(id)) return
    conversationId.value = id
    try { storage?.setItem(CONVERSATION_STORAGE_KEY, id) } catch { /* Preserve the current session if storage is blocked. */ }
  }
  async function send() {
    const message = input.value.trim()
    if (pending.value || tracePending.value || !message) return
    pending.value = true
    error.value = ''
    trace.value = []
    traceLoaded.value = false
    traceError.value = ''
    messages.value.push({ role: 'user', text: message })
    try {
      const result = await request(message, conversationId.value)
      rememberConversation(result.conversation_id)
      messages.value.push({ role: 'assistant', text: result.answer, details: result })
      trace.value = []
      traceLoaded.value = false
      input.value = ''
    } catch (cause) {
      rememberConversation(cause.conversationId)
      error.value = cause.message || 'Chat failed. Please retry.'
    } finally {
      pending.value = false
    }
  }
  async function reloadTrace() {
    if (!conversationId.value || pending.value || tracePending.value) return
    tracePending.value = true
    traceError.value = ''
    try {
      trace.value = await loadHistory(conversationId.value)
      traceLoaded.value = true
    } catch (cause) {
      traceError.value = cause.message || 'Could not reload the saved trace. Please retry.'
    } finally {
      tracePending.value = false
    }
  }
  return { input, messages, pending, error, conversationId, trace, tracePending, traceError, traceLoaded, send, reloadTrace }
}
