import { computed, ref } from 'vue'
import { searchStays } from '../api/travel.js'

export function useHotelSearch(request = searchStays) {
  const hotelName = ref('')
  const stays = ref([])
  const loading = ref(false)
  const error = ref('')
  const completed = ref(false)
  const noResults = computed(() => completed.value && !loading.value && !error.value && stays.value.length === 0)

  async function search() {
    if (loading.value) return
    stays.value = []
    completed.value = false
    error.value = ''
    const name = hotelName.value.trim()
    if (!name) {
      error.value = 'Enter a hotel name.'
      return
    }
    loading.value = true
    try {
      stays.value = await request(name)
      completed.value = true
    } catch {
      error.value = 'Hotel stays could not be loaded. Check your connection and try again.'
    } finally {
      loading.value = false
    }
  }

  return { hotelName, stays, loading, error, noResults, search }
}
