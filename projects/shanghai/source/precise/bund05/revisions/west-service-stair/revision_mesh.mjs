import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

export const sha = bytes => createHash('sha256').update(bytes).digest('hex');

export async function loadDecoder(project) {
  const filename = path.join(project, 'vendor/meshopt_decoder.module.js');
  const { MeshoptDecoder } = await import(pathToFileURL(filename));
  await MeshoptDecoder.ready;
  return MeshoptDecoder;
}

export function readMesh(file, decoder) {
  const all = fs.readFileSync(file);
  assert.equal(all.toString('ascii', 0, 4), 'glTF');
  assert.equal(all.readUInt32LE(4), 2);
  const jsonLength = all.readUInt32LE(12);
  const doc = JSON.parse(all.subarray(20, 20 + jsonLength));
  const bin = all.subarray(28 + jsonLength);
  const decoded = new Map();

  function view(index) {
    if (decoded.has(index)) return decoded.get(index);
    const entry = doc.bufferViews[index];
    const compressed = entry.extensions?.EXT_meshopt_compression ??
      entry.extensions?.KHR_meshopt_compression;
    let bytes;
    if (compressed) {
      const { count, byteStride, byteOffset = 0, byteLength, mode, filter = 'NONE' } = compressed;
      bytes = new Uint8Array(count * byteStride);
      decoder.decodeGltfBuffer(bytes, count, byteStride,
        bin.subarray(byteOffset, byteOffset + byteLength), mode, filter);
    } else {
      const start = entry.byteOffset ?? 0;
      bytes = bin.subarray(start, start + entry.byteLength);
    }
    const data = new DataView(bytes.buffer, bytes.byteOffset, bytes.length);
    decoded.set(index, data);
    return data;
  }

  function read(index) {
    const accessor = doc.accessors[index];
    const buffer = doc.bufferViews[accessor.bufferView];
    const data = view(accessor.bufferView);
    const components = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4 }[accessor.type];
    const layout = {
      5126: [4, 'getFloat32'], 5125: [4, 'getUint32'],
      5123: [2, 'getUint16'], 5121: [1, 'getUint8']
    }[accessor.componentType];
    assert.ok(layout && components, 'Unsupported accessor format');
    const [componentBytes, getter] = layout;
    const stride = buffer.byteStride || componentBytes * components;
    return Array.from({ length: accessor.count }, (_, vertex) => {
      const start = (accessor.byteOffset || 0) + vertex * stride;
      return Array.from({ length: components }, (_, component) =>
        data[getter](start + component * componentBytes, true));
    });
  }
  return { all, doc, view, read };
}
