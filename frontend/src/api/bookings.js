export function createBookingsApi(request = fetch) {
  async function send(url, method = 'GET', body) {
    const options = { method }
    if (body !== undefined) {
      options.headers = { 'Content-Type': 'application/json' }
      options.body = JSON.stringify(body)
    }
    let response
    try {
      response = await request(url, options)
    } catch {
      throw new Error('Could not reach the server. Please try again.')
    }
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new Error(typeof data.detail === 'string' ? data.detail : 'The booking request failed. Please try again.')
    }
    if (response.status === 204) return
    return response.json()
  }
  async function list(url) {
    const data = await send(url)
    if (!Array.isArray(data)) throw new Error('The server returned an invalid list response.')
    return data
  }
  return {
    listUsers: () => list('/api/users'),
    history: userId => list(`/api/bookings?${new URLSearchParams({ user_id: userId })}`),
    create: (userId, tripId) => send('/api/bookings', 'POST', { user_id: userId, trip_id: tripId }),
    cancel: bookingId => send(`/api/bookings/${encodeURIComponent(bookingId)}`, 'PATCH', { status: 'cancelled' }),
    remove: bookingId => send(`/api/bookings/${encodeURIComponent(bookingId)}`, 'DELETE'),
  }
}
