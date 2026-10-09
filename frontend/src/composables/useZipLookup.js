import { computed, ref, watch } from 'vue'
import { HotelSearchError } from '../api/zipLocation.js'
import { createLocalHotelsApi, searchLocalFirst } from '../api/localHotels.js'

export function useZipLookup(request = searchLocalFirst, local = createLocalHotelsApi()) {
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
  const pendingId = ref(null)
  const actionError = ref('')
  const actionSuccess = ref('')
  const status = ref('idle')
  const error = ref('')
  const loading = computed(() => status.value === 'loading')

  async function lookup() {
    if (loading.value || pendingId.value !== null) return
    selectedPlaceId.value = null
    result.value = null
    error.value = ''
    actionError.value = ''
    actionSuccess.value = ''
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

  async function saveHotel(hotel) {
    if (!result.value || hotel.saved || loading.value || pendingId.value !== null) return
    pendingId.value = hotel.place_id
    actionError.value = ''
    actionSuccess.value = ''
    try {
      await local.save(hotel, result.value.requested_zip, result.value.location)
      hotel.saved = true
      actionSuccess.value = 'Hotel saved locally. Demo nights are simulated classroom data.'
    } catch (failure) {
      actionError.value = failure.message || 'Hotel could not be saved. Please retry.'
    } finally {
      pendingId.value = null
    }
  }

  async function removeHotel(hotel) {
    if (!result.value || !hotel.saved || loading.value || pendingId.value !== null) return
    pendingId.value = hotel.place_id
    actionError.value = ''
    actionSuccess.value = ''
    try {
      await local.remove(hotel.place_id)
      hotel.saved = false
      if (result.value.source === 'local') {
        result.value.hotels = result.value.hotels.filter(h => h.place_id !== hotel.place_id)
        if (selectedPlaceId.value === hotel.place_id) selectedPlaceId.value = null
        status.value = result.value.hotels.length ? 'success' : 'empty'
      }
      actionSuccess.value = 'Hotel removed locally, including its ZIP associations and demo nights.'
    } catch (failure) {
      actionError.value = failure.message || 'Hotel could not be removed. Please retry.'
    } finally {
      pendingId.value = null
    }
  }

  return { pendingId, actionError, actionSuccess, saveHotel, removeHotel, zipCode, submittedZip, result, status, loading, error, lookup, selectedPlaceId, selectHotel }
}
