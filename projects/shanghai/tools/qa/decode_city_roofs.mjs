/** Decode every roof-patched GLB with the viewer's actual Three/Meshopt code. */
import { readFile, writeFile, mkdtemp, rm } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { tmpdir } from 'node:os';
import { pathToFileURL } from 'node:url';

const project = resolve(process.argv[2] || '.');
const city = resolve(process.argv[3] || join(project, 'assets/city'));
const output = process.argv[4];
const manifest = JSON.parse(await readFile(join(city, 'manifest.json'), 'utf8'));
const scratch = await mkdtemp(join(tmpdir(), 'shanghai-roof-decode-'));
const moduleURL = name => pathToFileURL(join(project, 'vendor', name)).href;
try {
  await writeFile(join(scratch, 'package.json'), '{"type":"module"}');
  for (const name of ['GLTFLoader.js', 'BufferGeometryUtils.js']) {
    const code = (await readFile(join(project, 'vendor', name), 'utf8'))
      .replaceAll("from 'three'", `from '${moduleURL('three.module.js')}'`);
    await writeFile(join(scratch, name), code);
  }
  const THREE = await import(moduleURL('three.module.js'));
  const { GLTFLoader } = await import(pathToFileURL(join(scratch, 'GLTFLoader.js')).href);
  const { MeshoptDecoder } = await import(moduleURL('meshopt_decoder.module.js'));
  await MeshoptDecoder.ready;
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const files = [];
  for (const record of manifest.tiles.filter(r => r.source_roof_enhancement)) {
    const bytes = await readFile(join(city, record.file));
    const model = await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
    model.scene.updateMatrixWorld(true);
    const bounds = new THREE.Box3();
    const point = new THREE.Vector3();
    let triangles = 0, vertices = 0;
    model.scene.traverse(mesh => {
      if (!mesh.isMesh) return;
      const position = mesh.geometry.getAttribute('position');
      triangles += (mesh.geometry.index?.count || position.count) / 3;
      for (let i = 0; i < position.count; i++) {
        point.fromBufferAttribute(position, i).applyMatrix4(mesh.matrixWorld);
        if (![point.x, point.y, point.z].every(Number.isFinite)) throw Error(`${record.id}: nonfinite decoded vertex`);
        bounds.expandByPoint(point); vertices++;
      }
      mesh.geometry.dispose();
      for (const material of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) material.dispose();
    });
    if (triangles !== record.triangles || bounds.isEmpty()) throw Error(`${record.id}: triangle count or bounds mismatch`);
    files.push({id: record.id, triangles, decoded_vertices: vertices, bounds: {min: bounds.min.toArray(), max: bounds.max.toArray()}, passed: true});
  }
  if (files.length !== manifest.source_roof_enhancement.affected_owner_cells.length) throw Error('Patch tile decode coverage mismatch');
  const report = {passed: true, decoder: 'The same vendored Three GLTFLoader and MeshoptDecoder used by the web app', scope: 'All current roof-patched GLBs decoded; finite world-space vertices and unchanged declared triangle counts. No physical accuracy claim.', files};
  if (output) await writeFile(output, JSON.stringify(report, null, 2) + '\n');
  console.log('DECODED', files.length, 'roof-patched city GLBs');
} finally {
  await rm(scratch, {recursive: true, force: true});
}
