/**
 * Keep the original overview style, then express nearby street widths in metres.
 * Width/lanes are used when supplied by the vector tile; class defaults below
 * are visual estimates, not surveyed carriageway or sidewalk boundaries.
 */
const SHANGHAI_LATITUDE = 31.2 * Math.PI / 180;
const EARTH_CIRCUMFERENCE = 2 * Math.PI * 6378137;

export function pixelsPerMetre(zoom) {
  return 512 * 2 ** zoom / (EARTH_CIRCUMFERENCE * Math.cos(SHANGHAI_LATITUDE));
}

export function streetMetresExpression(casing = false) {
  const width = ['to-number', ['get', 'width'], 0];
  const lanes = ['to-number', ['get', 'lanes'], 0];
  const roadClass = ['get', 'class'];
  const footpath = ['match', roadClass, ['path', 'pedestrian', 'footway', 'cycleway'], true, false];
  const estimated = ['case', ['==', ['to-number', ['get', 'ramp'], 0], 1], 4.5,
    ['match', roadClass,
      ['motorway', 'trunk'], 10,
      'primary', 9, 'secondary', 8, 'tertiary', 7,
      ['minor', 'street', 'street_limited'], 6,
      'service', 4, 'track', 3,
      ['path', 'pedestrian', 'footway', 'cycleway'], 2.4,
      'link', 4.5, 6]];
  const metres = ['case',
    ['all', ['>=', width, 0.6], ['<=', width, 45]], width,
    ['all', ['!', footpath], ['>=', lanes, 1], ['<=', lanes, 8]],
      ['*', lanes, ['match', roadClass, ['motorway', 'trunk'], 3.5, 3.1]],
    estimated];
  return casing ? ['+', metres, 0.5] : metres;
}

function interpolationRatio(base, progress, span) {
  return base === 1 ? progress / span : (base ** progress - 1) / (base ** span - 1);
}

/** Numeric Liberty width expressions are sampled without changing the curve. */
export function legacyWidthAtZoom(expression, zoom) {
  if (typeof expression === 'number') return expression;
  if (!Array.isArray(expression) || expression[0] !== 'interpolate'
    || expression[2]?.[0] !== 'zoom') return null;
  const base = expression[1][0] === 'exponential' ? expression[1][1] : 1;
  const stops = expression.slice(3);
  if (stops.some(value => typeof value !== 'number')) return null;
  if (zoom <= stops[0]) return stops[1];
  for (let i = 2; i < stops.length; i += 2) {
    if (zoom <= stops[i]) {
      const t = interpolationRatio(base, zoom - stops[i-2], stops[i] - stops[i-2]);
      return stops[i-1] + (stops[i+1] - stops[i-1]) * t;
    }
  }
  return stops[stops.length-1];
}

export function applyStreetWidths(layer) {
  if (layer.type !== 'line' || layer['source-layer'] !== 'transportation'
    || !/^(road|bridge|tunnel)_/.test(layer.id) || /rail|hatching|one_way/.test(layer.id)) return false;
  const original = layer.paint?.['line-width'];
  const at16 = legacyWidthAtZoom(original, 16);
  if (at16 === null || !Number.isFinite(at16)) return false;
  const expression = Array.isArray(original) ? original.slice(0, 3)
    : ['interpolate', ['linear'], ['zoom']];
  if (Array.isArray(original)) {
    for (let i = 3; i < original.length && original[i] < 16; i += 2) expression.push(original[i], original[i+1]);
  } else expression.push(0, original);
  expression.push(16, at16);
  const metres = streetMetresExpression(layer.id.endsWith('_casing'));
  // Retain Liberty's exponential curve below 16. One-level stops above 17
  // approximate physical doubling within 4.5%; a single 17→22.5 interval with
  // Liberty's original exponent would make the intermediate roads too wide.
  for (const zoom of [17, 18, 19, 20, 21, 22, 22.5, 23, 24]) {
    expression.push(zoom, ['*', pixelsPerMetre(zoom), metres]);
  }
  layer.paint['line-width'] = expression;
  return true;
}

/** Distinguish asphalt, stone paving and the curb without inventing lanes. */
export function applyStreetColors(layer) {
  if (layer.type !== 'line' || layer['source-layer'] !== 'transportation'
    || !/^(road|bridge|tunnel)_/.test(layer.id) || /rail|hatching|one_way/.test(layer.id)) return false;
  const original = layer.paint?.['line-color'];
  const target = layer.id.endsWith('_casing') ? '#c5cbc8'
    : layer.id.includes('path_pedestrian') ? '#cdd2d0' : '#7b8788';
  if (typeof original === 'string') {
    layer.paint['line-color'] = ['interpolate', ['linear'], ['zoom'], 16, original, 18, target];
    return true;
  }
  // Liberty's motorway color has zoom stops at 5 and 6. Preserve them exactly
  // and extend the same top-level expression, instead of nesting a zoom input.
  if (Array.isArray(original) && original[0] === 'interpolate'
    && original[2]?.[0] === 'zoom' && original[original.length-2] <= 16) {
    const expression = [...original];
    if (original[original.length-2] < 16) expression.push(16, original[original.length-1]);
    expression.push(18, target);
    layer.paint['line-color'] = expression;
    return true;
  }
  return false;
}
