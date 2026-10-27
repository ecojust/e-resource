/** Resolve shared links without moving to an unrecognized or malformed destination. */
export function resolveNavigationRoute(hash, {districts = [], landmarks = [], bund, activePlace = bund, coordinatePlace} = {}) {
  const fragment = String(hash || '').replace(/^#/, '');
  const params = new URLSearchParams(fragment);
  const requestedMode = params.get('mode');
  if (requestedMode !== null && !['walk', 'overview'].includes(requestedMode)) {
    return {error: '漫游模式无效，请从地标直达列表重新选择。'};
  }
  let place = activePlace;
  if (params.has('landmark')) {
    const id = params.get('landmark');
    place = id === bund?.id ? bund : landmarks.find(item => item.id === id);
    if (!place) return {error: '找不到该地标，请从地标直达列表重新选择。'};
  } else if (params.has('district')) {
    const id = params.get('district');
    // Earlier Bund links used the district key; keep those bookmarks working.
    place = id === bund?.id ? bund : districts.find(item => String(item.id) === id);
    if (!place) return {error: '找不到该行政区，请从列表重新选择。'};
  } else if (params.has('lng') || params.has('lat')) {
    const lng = params.get('lng'), lat = params.get('lat');
    if (!lng?.trim() || !lat?.trim() || !Number.isFinite(Number(lng)) || !Number.isFinite(Number(lat))
      || Math.abs(Number(lng)) > 180 || Math.abs(Number(lat)) > 85) {
      return {error: '漫游坐标无效，请从地标直达列表重新选择。'};
    }
    place = coordinatePlace?.(Number(lng), Number(lat));
    if (!place) return {error: '该位置不在上海行政区范围内，请重新选择。'};
  } else if (fragment && !params.has('mode')) {
    return {error: '无法识别此位置链接，请从地标直达列表重新选择。'};
  }
  const mode = requestedMode || (!fragment || params.has('landmark') || place?.id === bund?.id ? 'walk' : 'overview');
  return {place, mode};
}
