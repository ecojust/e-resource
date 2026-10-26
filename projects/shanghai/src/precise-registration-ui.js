/** Display only explicitly declared district/provider metadata. */
export function placeDescription(place, districts = []) {
  if (Number.isInteger(place.bund_number) && place.bund_number > 0) {
    return `外滩 ${place.bund_number} 号 · ${place.architecture_style || '历史建筑'}`;
  }
  const district = place.district_name || place.district?.name
    || districts.find(item => String(item.id) === String(place.districtId))?.name || '上海市';
  const description = place.architecture_style || (place.kind === 'building' ? '逐栋复原' : `${place.height_m} m`);
  return `${district} · ${description}`;
}
export function isArchitecturalBuilding(record) {
  return record.detail_level === 'architectural' || Boolean(record.candidate_id);
}
export function modelSurfaceKind(record) {
  if (record.id === 'bund-streets') return 'street';
  return isArchitecturalBuilding(record) ? 'architecture' : 'modern';
}

/** null means overview-only: every navigation entry point uses this guard. */
export function walkingPose(place) {
  if (place.kind === 'building') {
    if (place.navigation?.listed !== true) return null;
    const {walkStart, bearing} = place.navigation;
    if (!Array.isArray(walkStart) || walkStart.length !== 2 || !walkStart.every(Number.isFinite)
      || !Number.isFinite(bearing)) throw Error('Ordinary navigation lacks a reviewed walking pose');
    return {lng: walkStart[0], lat: walkStart[1], bearing};
  }
  const [lng, lat] = place.walkStart || place.center || [place.lng, place.lat];
  return {lng, lat, bearing: place.bearing ?? 45};
}
