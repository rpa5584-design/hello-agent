import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createHotelMap, TILE_URL, ATTRIBUTION } from '../src/components/hotelMapLayer.js'

function fixture() {
  const state = { markers: [], centers: [], bounds: [] }
  const map = { setView: p => state.centers.push(p), fitBounds: p => state.bounds.push(p), remove: () => { state.removed = true }, invalidateSize() {}, panInside(point) { state.panned = point } }
  const group = { addTo() { return this }, clearLayers() { state.markers = [] } }
  const L = {
    map: (_el, options) => { state.options = options; return map },
    tileLayer: (url, options) => { state.tile = { url, options }; return { addTo() { return this }, on(_event, fn) { state.failTile = fn } } },
    layerGroup: () => group,
    marker: (point, options) => ({
      point, options,
      bindPopup(popup) { this.popup = popup; state.markers.push(this); return this },
      addTo() { return this },
      on(event, handler) { this[event] = handler; return this },
      getElement() { return { classList: { toggle: (_name, value) => { this.selected = value } } } },
      setZIndexOffset(value) { this.zIndex = value },
      getLatLng() { return point },
      openPopup() { this.open = true }, closePopup() { this.open = false },
    }),
  }
  const doc = { createElement: tag => ({ tag, children: [], appendChild(child) { this.children.push(child) } }) }
  const controller = createHotelMap(L, {}, {}, () => { state.tileError = true }, doc, id => { state.selectedId = id })
  return { controller, state }
}
const center = { latitude: 40.8, longitude: -77.86 }
const hotel = { ...center, name: 'Provider name', formatted_address: 'Provider address' }

test('valid coordinates create exactly one marker each and fit their bounds', () => {
  const { controller, state } = fixture()
  assert.equal(controller.update(center, [hotel, { latitude: 42, longitude: -71 }, { latitude: null, longitude: 1 }, { latitude: 91, longitude: 1 }, { latitude: NaN, longitude: 1 }]), 2)
  assert.deepEqual(state.markers.map(m => m.point), [[40.8, -77.86], [42, -71]])
  assert.deepEqual(state.centers[0], [40.8, -77.86])
  assert.deepEqual(state.bounds[0], [[40.8, -77.86], [42, -71]])
})

test('new ZIP replaces markers, empty results clear them, and teardown removes map', () => {
  const { controller, state } = fixture()
  controller.update(center, [hotel])
  const ny = { latitude: 40.75, longitude: -73.99 }
  controller.update(ny, [{ ...ny, name: 'New hotel' }])
  assert.equal(state.markers.length, 1)
  assert.deepEqual(state.markers[0].point, [40.75, -73.99])
  controller.update(ny, [])
  assert.equal(state.markers.length, 0)
  controller.update(null, [])
  assert.equal(state.markers.length, 0)
  controller.destroy()
  assert.equal(state.removed, true)
})

test('popup contains only literal provider name/address and honest fallback', () => {
  const { controller, state } = fixture()
  controller.update(center, [{ ...hotel, name: '<img onerror=bad>', price: 999, rating: 5, availability: true, booking_status: 'confirmed' }, center])
  const content = state.markers[0].popup.children
  assert.deepEqual(content.map(n => n.textContent), ['<img onerror=bad>', 'Provider address'])
  assert.ok(content.every(n => !('innerHTML' in n)))
  assert.equal(state.markers[1].popup.children[0].textContent, 'Name unavailable')
})

test('documented OSM tiles and attribution are configured without credentials', () => {
  const { state } = fixture()
  assert.equal(TILE_URL, 'https://tile.openstreetmap.org/{z}/{x}/{y}.png')
  assert.equal(state.tile.url, TILE_URL)
  assert.equal(state.tile.options.attribution, ATTRIBUTION)
  assert.match(ATTRIBUTION, /OpenStreetMap contributors/)
  assert.match(ATTRIBUTION, /https:\/\/www.openstreetmap.org\/copyright/)
  assert.equal(state.options.attributionControl, true)
  assert.equal(state.tile.options.keepBuffer, 0)
  state.failTile()
  assert.equal(state.tileError, true)
})


test('selection and marker clicks use provider IDs even with identical names', () => {
  const { controller, state } = fixture()
  controller.update(center, [{ ...hotel, place_id: 'a' }, { ...hotel, place_id: 'b' }])
  controller.select('b')
  assert.equal(state.markers[0].selected, false)
  assert.equal(state.markers[1].selected, true)
  assert.equal(state.markers[1].open, true)
  assert.equal(state.markers[1].zIndex, 1000)
  assert.deepEqual(state.panned, [hotel.latitude, hotel.longitude])
  state.markers[0].click()
  assert.equal(state.selectedId, 'a')
  controller.select(state.selectedId)
  assert.equal(state.markers[0].open, true)
  assert.equal(state.markers[1].open, false)
  controller.update(center, [])
  controller.select('a')
  assert.equal(state.markers.length, 0)
})
