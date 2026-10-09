import { searchZipHotels, HotelSearchError } from './zipLocation.js'

export function createLocalHotelsApi(request = fetch) {
  async function send(url, method = 'GET', body) {
    let response
    try {
      response = await request(url, { method, ...(body ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}) })
    } catch {
      throw new HotelSearchError('service', 'Could not reach local hotel storage. Please retry.')
    }
    if (!response.ok) {
      const data = await response.json().catch(() => null)
      throw new HotelSearchError('service', typeof data?.detail === 'string' ? data.detail : 'Local hotel storage request failed. Please retry.')
    }
    if (response.status === 204) return
    const data = await response.json().catch(() => null)
    if (data === null) throw new HotelSearchError('service', 'Local storage returned an invalid response.')
    return data
  }
  return {
    async lookup(zip) {
      const data = await send(`/api/local/hotels?${new URLSearchParams({ zip_code: zip })}`)
      if (data.requested_zip !== zip || data.source !== 'local' || !Array.isArray(data.hotels)
        || !data.hotels.every(h => typeof h.place_id === 'string' && Array.isArray(h.nights))
        || (data.hotels.length && (data.location?.postcode !== zip || !Number.isFinite(data.location.latitude) || !Number.isFinite(data.location.longitude)))) {
        throw new HotelSearchError('service', 'Local storage returned an invalid hotel response.')
      }
      return data
    },
    async ids() {
      const data = await send('/api/local/hotels/ids')
      if (!Array.isArray(data) || !data.every(id => typeof id === 'string')) throw new HotelSearchError('service', 'Local storage returned invalid saved status.')
      return data
    },
    save: (hotel, zip, location) => send('/api/local/hotels', 'POST', {
      hotel: { place_id: hotel.place_id, name: hotel.name ?? null, formatted_address: hotel.formatted_address ?? null, latitude: hotel.latitude, longitude: hotel.longitude },
      zip_code: zip, location,
    }),
    remove: id => send(`/api/local/hotels?${new URLSearchParams({ hotel_id: id })}`, 'DELETE'),
  }
}

export async function searchLocalFirst(zip, local = createLocalHotelsApi(), provider = searchZipHotels) {
  const saved = await local.lookup(zip)
  if (saved.hotels.length) return saved
  const result = await provider(zip)
  const ids = new Set(await local.ids())
  return { ...result, source: 'api', hotels: result.hotels.map(h => ({ ...h, saved: ids.has(h.place_id) })) }
}
