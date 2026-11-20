import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createServer} from 'node:http';
import {readFile, writeFile} from 'node:fs/promises';
import {resolve, dirname} from 'node:path';
import {pathToFileURL} from 'node:url';
import {performance} from 'node:perf_hooks';

const [moduleDir, manifestPath, output, expected] = process.argv.slice(2);
assert(moduleDir && manifestPath && output && ['success','timeout'].includes(expected));
const {loadOrdinaryLandmarkAsset} = await import(pathToFileURL(resolve(moduleDir,'ordinary-scene-adapter.js')));
const manifest = JSON.parse(await readFile(manifestPath));
const meta = manifest.assets.full;
const data = await readFile(resolve(dirname(manifestPath),meta.file));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
assert.equal(sha(data),meta.sha256);
const transfers = [];
const server = createServer((request,response) => {
  assert.equal(request.url, '/'+meta.file);
  const entry = {ordinal:transfers.length+1, path:request.url, started_ms:Math.round(performance.now()-start)};
  transfers.push(entry);
  response.writeHead(200, {'content-length':data.byteLength,'content-type':'model/gltf-binary','cache-control':'no-store'});
  if (entry.ordinal === 1) {
    response.write(data.subarray(0,16));
    entry.sent_bytes=16;
  } else {
    response.end(data);
    entry.sent_bytes=data.byteLength;
  }
  response.once('close', () => {entry.closed_ms=Math.round(performance.now()-start);});
});
const start=performance.now();
await new Promise(done => server.listen(0,'127.0.0.1',done));
const record = {id:manifest.id,ordinaryBaseURL:'http://127.0.0.1:'+server.address().port+'/',assets:{web:meta,lod:manifest.assets.lod}};
const report = {model:record.id,expected,sha256:meta.sha256,declared_bytes:data.byteLength,started_utc:new Date().toISOString(),
  first_response:'Real local HTTP 200 sends its first 16 GLB bytes and leaves the remaining body pending.',transfers};
let verified=0;
const loader = {async parseAsync(buffer) {
  assert.equal(sha(new Uint8Array(buffer)),meta.sha256);
  const view=new DataView(buffer);
  const doc=JSON.parse(new TextDecoder().decode(new Uint8Array(buffer,20,view.getUint32(12,true))));
  const triangles=doc.meshes.flatMap(mesh=>mesh.primitives).reduce((sum,primitive)=>sum+doc.accessors[primitive.indices].count/3,0);
  verified++;
  return {scene:{userData:{}}, triangles};
}};
try {
  if(expected==='success'){
    const result=await loadOrdinaryLandmarkAsset({record,variant:'full',loader});
    assert.equal(result.scene.userData.__ordinaryVerifiedAsset.sha256,meta.sha256);
    assert.equal(transfers.length,2); assert.equal(verified,1);
    report.verified_web_triangles=result.triangles;
  } else {
    await assert.rejects(loadOrdinaryLandmarkAsset({record,variant:'full',loader}), /timed out/);
    assert.equal(transfers.length,1); assert.equal(verified,0);
  }
  report.passed=true;
} finally {
  server.closeAllConnections();
  await new Promise(done=>server.close(done));
  report.elapsed_ms=Math.round(performance.now()-start);
  report.parser_calls=verified;
  await writeFile(output,JSON.stringify(report,null,2)+'\n');
}
