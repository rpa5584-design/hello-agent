export async function lookupDemoZip(zipCode = '16802', request = fetch) {
  let response
  try {
    response = await request(`/api/demo/zip-location?${new URLSearchParams({ zip_code: zipCode })}`)
  } catch {
    throw new Error('Could not reach the server. Please try again.')
  }
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === 'string' ? data.detail : 'ZIP lookup failed. Please try again.')
  }
  if (data?.postcode !== zipCode || !Number.isFinite(data.latitude) || !Number.isFinite(data.longitude)) {
    throw new Error('The server returned an invalid ZIP location.')
  }
  return data
}

export class HotelSearchError extends Error {
  constructor(kind, message) {
    super(message)
    this.kind = kind
  }
}

export async function searchZipHotels(zipCode, request = fetch) {
  let response
  try {
    response = await request(`/api/demo/hotels?${new URLSearchParams({ zip_code: zipCode })}`)
  } catch {
    throw new HotelSearchError('service', 'Could not reach the hotel service. Please try again.')
  }
  if (!response.ok) {
    if (response.status === 422) throw new HotelSearchError('invalid', 'Enter exactly five digits for a U.S. ZIP code.')
    if (response.status === 404) throw new HotelSearchError('unresolved', 'This ZIP location could not be resolved. Check the ZIP and try again.')
    throw new HotelSearchError('service', response.status === 503
      ? 'Hotel search is not configured on the server.' : 'Hotel service is unavailable. Please try again.')
  }
  const data = await response.json().catch(() => null)
  if (data?.requested_zip !== zipCode || data?.location?.postcode !== zipCode || data.radius_meters !== 5000
    || !Array.isArray(data.hotels) || !data.hotels.every(hotel => hotel && typeof hotel.place_id === 'string')) {
    throw new HotelSearchError('service', 'The hotel service returned an invalid response. Please try again.')
  }
  return data
}
