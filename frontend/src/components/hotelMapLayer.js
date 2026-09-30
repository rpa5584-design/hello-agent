export const TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
export const ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'

export function validCoordinates(point) {
  return point && Number.isFinite(point.latitude) && Number.isFinite(point.longitude)
    && Math.abs(point.latitude) <= 90 && Math.abs(point.longitude) <= 180
}

export function createHotelMap(L, element, icon, onTileError, documentObject = document, onSelect = () => {}) {
  const map = L.map(element, { attributionControl: true, scrollWheelZoom: false })
  const tiles = L.tileLayer(TILE_URL, { attribution: ATTRIBUTION, maxZoom: 19, keepBuffer: 0 }).addTo(map)
  tiles.on('tileerror', onTileError)
  const markers = L.layerGroup().addTo(map)
  const markersById = new Map()
  return {
    update(location, hotels) {
      markers.clearLayers()
      markersById.clear()
      if (!validCoordinates(location)) return 0
      map.setView([location.latitude, location.longitude], 13)
      const points = []
      for (const hotel of hotels) {
        if (!validCoordinates(hotel)) continue
        const point = [hotel.latitude, hotel.longitude]
        const popup = documentObject.createElement('div')
        const name = documentObject.createElement('strong')
        name.textContent = hotel.name?.trim() || 'Name unavailable'
        popup.appendChild(name)
        if (hotel.formatted_address) {
          const address = documentObject.createElement('p')
          address.textContent = hotel.formatted_address
          popup.appendChild(address)
        }
        const marker = L.marker(point, { icon, title: name.textContent, alt: name.textContent })
          .bindPopup(popup).addTo(markers)
        if (hotel.place_id) {
          markersById.set(hotel.place_id, marker)
          marker.on('click', () => onSelect(hotel.place_id))
        }
        points.push(point)
      }
      if (points.length) map.fitBounds(points, { padding: [30, 30], maxZoom: 15 })
      return points.length
    },
    select(placeId) {
      for (const [id, marker] of markersById) {
        const selected = id === placeId
        marker.getElement()?.classList.toggle('hotel-marker-selected', selected)
        marker.setZIndexOffset(selected ? 1000 : 0)
        if (!selected) marker.closePopup()
      }
      const marker = markersById.get(placeId)
      if (marker) {
        map.panInside(marker.getLatLng(), { padding: [40, 40] })
        marker.openPopup()
      }
    },
    resize() { map.invalidateSize() },
    destroy() { map.remove() },
  }
}
