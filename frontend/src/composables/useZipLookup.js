import { computed, ref, watch } from 'vue'
import { searchZipHotels, HotelSearchError } from '../api/zipLocation.js'

export function useZipLookup(request = searchZipHotels) {
  const zipCode = ref('16802')
  const submittedZip = ref('')
  const result = ref(null)
  const selectedPlaceId = ref(null)
  watch(result, () => { selectedPlaceId.value = null }, { flush: 'sync' })
  function selectHotel(placeId) {
    if (result.value?.hotels.some(hotel => hotel.place_id === placeId)) {
      selectedPlaceId.value = placeId
    }
  }
  const status = ref('idle')
  const error = ref('')
  const loading = computed(() => status.value === 'loading')

  async function lookup() {
    if (loading.value) return
    selectedPlaceId.value = null
    result.value = null
    error.value = ''
    submittedZip.value = zipCode.value
    if (!/^[0-9]{5}$/.test(submittedZip.value)) {
      status.value = 'invalid'
      error.value = 'Enter exactly five digits for a U.S. ZIP code.'
      return
    }
    status.value = 'loading'
    try {
      result.value = await request(submittedZip.value)
      status.value = result.value.hotels.length ? 'success' : 'empty'
    } catch (failure) {
      status.value = failure instanceof HotelSearchError ? failure.kind : 'service'
      error.value = failure instanceof HotelSearchError ? failure.message : 'Hotel service is unavailable. Please try again.'
    }
  }

  return { zipCode, submittedZip, result, status, loading, error, lookup, selectedPlaceId, selectHotel }
}
