import fs from 'node:fs';
import * as THREE from '../../../vendor/three.module.js';
import '../../../vendor/maplibre-gl.js';
const maplibre = globalThis.maplibregl;
const origin = maplibre.MercatorCoordinate.fromLngLat([121.4737,31.2304], 0);
const scale = origin.meterInMercatorCoordinateUnits();
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const counts = input.map(geometry => {
  const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates;
  return polygons.reduce((sum, polygon) => {
    const rings = polygon.map(ring => ring.slice(0, -1).map(position => {
      const p = maplibre.MercatorCoordinate.fromLngLat(position, 0);
      return new THREE.Vector2((p.x-origin.x)/scale, (p.y-origin.y)/scale);
    }));
    return sum + THREE.ShapeUtils.triangulateShape(rings[0], rings.slice(1)).length;
  }, 0);
});
process.stdout.write(JSON.stringify(counts));
