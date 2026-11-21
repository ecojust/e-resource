import assert from 'node:assert/strict';
import fs from 'node:fs';
import { loadDecoder, readMesh, sha } from './revision_mesh.mjs';

const [project,prior,raw,near,far,output] = process.argv.slice(2);
const decoder = await loadDecoder(project);
function inspect(file) {
  const { all, doc, view, read } = readMesh(file, decoder);
  const photographed=doc.meshes.flatMap(m=>m.primitives).filter(p=>doc.materials[p.material]?.pbrMetallicRoughness?.baseColorTexture);
  const result={file_sha256:sha(all),bytes:all.length,texture_materials:photographed.length,image_sha256:(doc.images||[]).map(x=>{const d=view(x.bufferView);return sha(Buffer.from(d.buffer,d.byteOffset,d.byteLength));}),triangles:0,unique_uvs:0};
  if (!photographed.length) return result;
  assert.equal(photographed.length,1);
  const primitive=photographed[0],positions=read(primitive.attributes.POSITION), uv=read(primitive.attributes.TEXCOORD_0),indices=read(primitive.indices).flat();
  const points=positions.map((point,i)=>[...point,...uv[i]].map(x=>Math.round(x*1e6)).join(','));
  const triangles=[];for (let i=0;i<indices.length;i+=3) triangles.push(indices.slice(i,i+3).map(k=>points[k]).sort().join('/'));
  result.triangles=triangles.length;result.unique_uvs=new Set(uv.map(a=>a.map(x=>Math.round(x*1e7)).join(','))).size;
  result.triangle_position_uv_sha256=sha(triangles.sort().join('\n'));result.material=doc.materials[primitive.material].name;
  return result;
}
const [original_web,new_raw,new_web,new_lod]=[prior,raw,near,far].map(inspect);
for (const row of [original_web,new_raw,new_web]) {
  assert.deepEqual(row.image_sha256,['3cff1c24a4762a0c099d8b96d663fc704871421853b8904a95327f5352f574b3']);assert.equal(row.triangles,112*12);assert.equal(row.unique_uvs,112*4);
  assert.equal(row.triangle_position_uv_sha256,original_web.triangle_position_uv_sha256);
}
assert.deepEqual(new_lod.image_sha256,[]);assert.equal(new_lod.texture_materials,0);
fs.writeFileSync(output,JSON.stringify({comparison:'True meshopt decode of all original and revised textured triangles. Position/UV values normalized to one micrometre / 1e-6 texture unit for orientation-independent comparison.',original_web,new_raw,new_web,new_lod},null,2)+'\n');
