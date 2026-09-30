<script setup>
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import markerUrl from 'leaflet/dist/images/marker-icon.png'
import markerRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'
import { createHotelMap, validCoordinates } from './hotelMapLayer.js'

const props = defineProps({
  hotels: { type: Array, default: () => [] },
  location: { type: Object, default: null },
  selectedPlaceId: { type: String, default: null },
})
const emit = defineEmits(['select'])
const container = ref(null)
const tileError = ref(false)
const count = ref(0)
const usable = computed(() => validCoordinates(props.location))
let controller
let observer
function update() {
  tileError.value = false
  count.value = controller?.update(props.location, props.hotels) || 0
  controller?.select(props.selectedPlaceId)
}
onMounted(() => {
  const icon = L.icon({ iconUrl: markerUrl, iconRetinaUrl: markerRetinaUrl, shadowUrl,
    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] })
  controller = createHotelMap(L, container.value, icon, () => { tileError.value = true }, document, placeId => emit('select', placeId))
  update()
  observer = new ResizeObserver(() => controller.resize())
  observer.observe(container.value)
})
watch(() => [props.location, props.hotels], update, { deep: true })
watch(() => props.selectedPlaceId, placeId => controller?.select(placeId))
onBeforeUnmount(() => { observer?.disconnect(); controller?.destroy() })
</script>

<template>
  <section class="hotel-map" aria-label="Hotel map">
    <h3>Hotel map</h3>
    <p v-if="!usable" class="muted">Map unavailable for this search.</p>
    <p v-else-if="!count" class="muted">No hotel markers to display for this search.</p>
    <p v-if="tileError" class="notice error" role="status">Map tiles could not be loaded. Hotel details remain in the list.</p>
    <div ref="container" class="map-canvas" aria-label="Map of returned hotels" />
    <p class="map-credit">© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a></p>
  </section>
</template>

<style scoped>
.hotel-map { min-width: 0; align-self: start; display: grid; gap: 10px; }
.map-canvas { height: 420px; width: 100%; border: 1px solid #bdccd6; border-radius: 10px; z-index: 0; }
.map-credit { font-size: .75rem; }
:deep(.leaflet-control-attribution) { white-space: normal; }
:deep(.hotel-marker-selected) { outline: 3px solid #194f75; outline-offset: 3px; border-radius: 12px; filter: drop-shadow(0 0 5px white); }
@media (max-width: 800px) { .hotel-map { position: static; } .map-canvas { height: 320px; } }
</style>
