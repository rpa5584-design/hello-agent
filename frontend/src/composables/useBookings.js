import { computed, ref } from 'vue'
import { createBookingsApi } from '../api/bookings.js'

export const isTestBooking = bookingId => /^B-[0-9a-f]{32}$/.test(bookingId)

export function useBookings(api = createBookingsApi()) {
  const users = ref([])
  const selectedUserId = ref('')
  const usersLoading = ref(false)
  const usersError = ref('')
  const history = ref([])
  const historyLoading = ref(false)
  const historyLoaded = ref(false)
  const historyError = ref('')
  const pending = ref(false)
  const success = ref('')
  const error = ref('')
  const canBook = computed(() => !!selectedUserId.value && !pending.value && !usersLoading.value)
  let historyRequest = 0

  async function loadHistory() {
    const requestId = ++historyRequest
    const userId = selectedUserId.value
    history.value = []
    historyLoaded.value = false
    historyError.value = ''
    historyLoading.value = !!userId
    if (!userId) return
    try {
      const rows = await api.history(userId)
      if (requestId !== historyRequest) return
      history.value = rows
      historyLoaded.value = true
    } catch (cause) {
      if (requestId === historyRequest) historyError.value = cause.message
    } finally {
      if (requestId === historyRequest) historyLoading.value = false
    }
  }

  async function selectUser(userId) {
    if (pending.value) return
    selectedUserId.value = users.value.some(user => user.user_id === userId) ? userId : ''
    success.value = ''
    error.value = ''
    await loadHistory()
  }

  async function loadUsers() {
    if (usersLoading.value || pending.value) return
    usersLoading.value = true
    usersError.value = ''
    try {
      users.value = await api.listUsers()
      const current = users.value.find(user => user.user_id === selectedUserId.value)
      await selectUser(current?.user_id ?? users.value[0]?.user_id ?? '')
    } catch (cause) {
      users.value = []
      await selectUser('')
      usersError.value = cause.message
    } finally {
      usersLoading.value = false
    }
  }

  async function mutate(action, message, apply) {
    if (pending.value) return
    success.value = ''
    error.value = ''
    if (!selectedUserId.value) {
      error.value = 'Select a demo user first.'
      return
    }
    pending.value = true
    try {
      const result = await action()
      await apply(result)
      success.value = message
    } catch (cause) {
      error.value = cause.message
    } finally {
      pending.value = false
    }
  }

  const book = tripId => mutate(
    () => api.create(selectedUserId.value, tripId),
    'Booking created successfully.',
    () => loadHistory(),
  )
  const cancel = bookingId => mutate(
    () => api.cancel(bookingId),
    'Booking cancelled. It remains in your history.',
    result => { history.value = history.value.map(row => row.booking_id === bookingId ? { ...row, ...result } : row) },
  )
  function remove(bookingId) {
    if (!isTestBooking(bookingId)) {
      success.value = ''
      error.value = 'Instructor bookings cannot be deleted.'
      return
    }
    return mutate(
      () => api.remove(bookingId),
      'Test booking deleted.',
      () => { history.value = history.value.filter(row => row.booking_id !== bookingId) },
    )
  }

  return {
    users, selectedUserId, usersLoading, usersError, history, historyLoading,
    historyLoaded, historyError, pending, success, error, canBook,
    loadUsers, selectUser, loadHistory, book, cancel, remove,
  }
}
