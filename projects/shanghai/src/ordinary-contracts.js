// JSON object order is not semantic. Array order remains exact for geometry,
// winding, source IDs and near ownership; never sort those arrays implicitly.
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])]));
  }
  return value;
}
export const sameJSON = (a, b) => JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));
