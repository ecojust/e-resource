/** Point containment in the published WGS84 district polygons, including holes. */
function inRing(ring, x, y) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [ax, ay] = ring[i], [bx, by] = ring[j];
    if ((ay > y) !== (by > y) && x < (bx - ax) * (y - ay) / (by - ay) + ax) inside = !inside;
  }
  return inside;
}
function inPolygon(rings, x, y) {
  return rings.length && inRing(rings[0], x, y) && !rings.slice(1).some(r => inRing(r, x, y));
}
export function districtAt(collection, lng, lat) {
  if (!Number.isFinite(lng) || !Number.isFinite(lat)) return null;
  for (const feature of collection?.features || []) {
    const geometry = feature.geometry;
    const polygons = geometry.type === 'Polygon' ? [geometry.coordinates]
      : geometry.type === 'MultiPolygon' ? geometry.coordinates : [];
    if (polygons.some(p => inPolygon(p, lng, lat))) return feature.properties;
  }
  return null;
}
