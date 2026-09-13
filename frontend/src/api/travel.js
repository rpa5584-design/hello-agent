export async function searchStays(hotelName, request = fetch) {
  const query = new URLSearchParams({ hotel_name: hotelName })
  const response = await request(`/api/stays?${query}`)
  if (!response.ok) throw new Error('Hotel stays could not be loaded. Please try again.')
  const data = await response.json()
  if (!Array.isArray(data.stays)) throw new Error('The server returned an invalid stays response.')
  return data.stays
}
