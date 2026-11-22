// Preserve exact Float64 source-decoder output in a compact, private computation directory.
const fs = require('node:fs');
const {gzipSync} = require('node:zlib');
const write = fs.writeFileSync;
fs.writeFileSync = function (path, data, ...options) {
  if (typeof path === 'string' && /baseline-(?:near|far)-(?:triangles\.f64|owners\.u32)$/.test(path)) {
    return write(path + '.gz', gzipSync(data, {level: 3}), ...options);
  }
  return write(path, data, ...options);
};
