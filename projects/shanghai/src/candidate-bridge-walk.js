// Bridge stations and widths are authored in model metres. MapLibre's altitude
// and metre conversion uses the mean Earth radius, including at the anchor.
const RAD = Math.PI / 180;
const R = 6371008.8;
const finite = Number.isFinite;
const bounded = (number, low, high) => finite(number) && number >= low && number <= high;
const increasing = (stations, i) => i === 0 || stations[i][0] > stations[i - 1][0];

export function validBridgeWalk(row) {
  const b = row.bridge_walk;
  if (!b || b.version !== 1 || !['x', '-z'].includes(b.longitudinal_axis)
      || !bounded(b.shear, -1, 1) || !bounded(b.half_road_m, .25, 50)
      || !bounded(b.half_deck_m, b.half_road_m + .5, 60)
      || !bounded(b.sidewalk_rise_m, 0, .2) || !finite(row.altitude)
      || !finite(row.scale ?? 1) || (row.scale ?? 1) <= 0
      || row.collision_geometry !== null || row.replacement_geometry || row.site_replacement
      || row.owner || row.owners || row.source_owner || row.source_owners || row.source_section_caps
      || row.display_height_clips?.length || row.ground_collision_mode
      || Object.values(row.source_feature_ids || {}).some(ids => ids.length)) return false;
  const ids = b.transportation_feature_ids;
  if (!Array.isArray(ids) || ids.length < 1 || ids.length > 16
      || !ids.every(id => Number.isSafeInteger(id) && id > 0) || new Set(ids).size !== ids.length) return false;
  const stations = b.stations_m;
  if (!Array.isArray(stations) || stations.length < 2 || stations.length > 256
      || !stations.every((p, i) => Array.isArray(p) && p.length === 2 && p.every(finite)
        && bounded(p[0], -1000, 1000) && bounded(p[1], -50, 100) && increasing(stations, i))) return false;
  if (!Array.isArray(b.rails) || b.rails.length < 2 || b.rails.length > 16
      || !b.rails.every(r => r && bounded(r.offset_m, -b.half_deck_m, b.half_deck_m)
        && bounded(r.radius_m, .01, 1) && bounded(r.base_above_road_m, -.3, 2)
        && bounded(r.top_above_road_m, r.base_above_road_m, 4))) return false;
  if (![-1, 1].every(sign => b.rails.some(r => sign * r.offset_m > b.half_road_m))) return false;
  return b.posts === undefined || (Array.isArray(b.posts) && b.posts.length <= 64 && b.posts.every(p =>
    p && bounded(p.station_m, stations[0][0], stations.at(-1)[0])
    && bounded(p.offset_m, -b.half_deck_m, b.half_deck_m)
    && bounded(p.half_length_m, .01, 3) && bounded(p.half_width_m, .01, 3)
    && bounded(p.top_above_road_m, .2, 8)));
}

export function bridgePosition(row, station, across) {
  const b = row.bridge_walk;
  const along = station + b.shear * across;
  const x = b.longitudinal_axis === 'x' ? along : across;
  const north = b.longitudinal_axis === 'x' ? across : along;
  const a = row.heading * RAD, scale = row.scale ?? 1;
  const east = scale * (x * Math.cos(a) + north * Math.sin(a));
  const deltaNorth = scale * (-x * Math.sin(a) + north * Math.cos(a));
  const radius = R * Math.cos(row.lat * RAD);
  const merc = Math.asinh(Math.tan(row.lat * RAD)) + deltaNorth / radius;
  return [row.lng + east / radius / RAD, Math.atan(Math.sinh(merc)) / RAD];
}

export function bridgeInteraction(row) {
  if (!validBridgeWalk(row)) throw Error('Invalid bridge walking contract: ' + row.id);
  const b = row.bridge_walk, scale = row.scale ?? 1, features = [];
  const world = h => row.altitude + scale * h;
  const vertex = (s, v, h) => [...bridgePosition(row, s, v), world(h)];
  const add = (properties, geometry) => features.push({type: 'Feature', properties, geometry});
  const surface = (a, z, v, w, rise, id) => {
    const ring = [vertex(a[0], v, a[1] + rise), vertex(a[0], w, a[1] + rise),
      vertex(z[0], w, z[1] + rise), vertex(z[0], v, z[1] + rise)];
    ring.push(ring[0]);
    add({id, role: 'walk-surface', height_world_m: ring[0][2], ...(a[1] !== z[1] && {height_plane: true})},
      {type: 'Polygon', coordinates: [ring]});
  };
  const obstacle = (id, low, high, geometry, radius) => add({id, role: 'obstacle', kind: 'bridge-barrier',
    base_world_m: world(low), top_world_m: world(high), blocks_walk: true, blocks_camera: true,
    ...(radius !== undefined && {radius_m: radius * scale})}, geometry);
  for (let i = 1; i < b.stations_m.length; i++) {
    const a = b.stations_m[i - 1], z = b.stations_m[i];
    surface(a, z, -b.half_road_m, b.half_road_m, 0, 'road-' + i);
    surface(a, z, -b.half_deck_m, -b.half_road_m, b.sidewalk_rise_m, 'left-footway-' + i);
    surface(a, z, b.half_road_m, b.half_deck_m, b.sidewalk_rise_m, 'right-footway-' + i);
    for (const [j, r] of b.rails.entries()) {
      obstacle('rail-' + j + '-' + i, Math.min(a[1], z[1]) + r.base_above_road_m,
        Math.max(a[1], z[1]) + r.top_above_road_m,
        {type: 'LineString', coordinates: [bridgePosition(row, a[0], r.offset_m), bridgePosition(row, z[0], r.offset_m)]}, r.radius_m);
    }
  }
  for (const [i, p] of (b.posts || []).entries()) {
    const end = b.stations_m.findIndex(s => s[0] >= p.station_m);
    const a = b.stations_m[Math.max(0, end - 1)], z = b.stations_m[end];
    const road = end === 0 ? z[1] : a[1] + (z[1] - a[1]) * (p.station_m - a[0]) / (z[0] - a[0]);
    // Skew locates the post centre along its cross-section. The lamp pedestal itself has orthogonal faces.
    const ring = [[-1,-1],[1,-1],[1,1],[-1,1],[-1,-1]].map(([u,v]) => {
      const across = v * p.half_width_m;
      return bridgePosition(row, p.station_m + u * p.half_length_m - b.shear * across, p.offset_m + across);
    });
    obstacle('post-' + i, road, road + p.top_above_road_m, {type: 'Polygon', coordinates: [ring]});
  }
  return {type: 'FeatureCollection', metadata: {schema_version: 1, owner: row.id, origin: [row.lng, row.lat],
    web_model_sha256: row.assets.web.sha256, lod_model_sha256: row.assets.lod.sha256}, features};
}

// Called with CandidateCityState.active, which requires a visible,
// attached object and a GLB verification receipt matching this exact variant.
export class CandidateBridgeWalks {
  constructor(street) { this.street = street; this.active = new Map(); }
  sync(verifiedRecords) {
    const retained = new Set();
    for (const r of verifiedRecords) {
      if (!r.bridge_walk) continue;
      retained.add(r.id);
      const hash = r.assets[r.activeVariant === 'full' ? 'web' : 'lod'].sha256;
      const old = this.active.get(r.id);
      if (old?.hash === hash && old.record === r) continue;
      if (!this.street.setOwner(r.id, bridgeInteraction(r), {modelSha256: hash, active: true}))
        throw Error(this.street.lastError.message);
      this.active.set(r.id, {record: r, hash});
    }
    for (const id of this.active.keys()) if (!retained.has(id)) {
      this.street.removeOwner(id);
      this.active.delete(id);
    }
  }
  allowsNativeRoad(featureId, lng, lat, nativeWidth = 13) {
    for (const {record: r} of this.active.values()) {
      const b = r.bridge_walk;
      if (!b.transportation_feature_ids.includes(featureId)) continue;
      const radius = R * Math.cos(r.lat * RAD), scale = r.scale ?? 1;
      const east = (lng - r.lng) * RAD * radius / scale;
      const north = (Math.asinh(Math.tan(lat * RAD)) - Math.asinh(Math.tan(r.lat * RAD))) * radius / scale;
      const a = r.heading * RAD, x = east * Math.cos(a) - north * Math.sin(a);
      const localNorth = east * Math.sin(a) + north * Math.cos(a);
      const across = b.longitudinal_axis === 'x' ? localNorth : x;
      // A source feature can include disconnected segments. Only replace water clearance beside this deck.
      if (Math.abs(across) > b.half_deck_m + nativeWidth / scale) continue;
      const s = (b.longitudinal_axis === 'x' ? x : localNorth) - b.shear * across;
      if (s >= b.stations_m[0][0] && s <= b.stations_m.at(-1)[0]) return false;
    }
    return true;
  }
  coversWater(lng, lat) {
    return this.active.size > 0 && this.active.has(this.street.groundAt(lng, lat)?.ownerId);
  }
}
