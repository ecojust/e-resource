import test from 'node:test';
import assert from 'node:assert/strict';
import {gzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {registerHooks} from 'node:module';
import {cityModelCodecMetadata,decodeCityModelResponse,CITY_MODEL_BYTE_LIMIT} from '../src/city-model-codec.js';
import {triangleGLB} from './fixtures/city-model-fixture.mjs';
import {countExpandedTriangles,disposeModelResources} from '../src/model-resources.js';
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const glb=triangleGLB(),gzip=gzipSync(glb,{level:6,mtime:0});
function metadata(overrides={}){return {content_encoding:'gzip',size_bytes:gzip.length,sha256:sha(gzip),decoded_size_bytes:glb.length,decoded_sha256:sha(glb),...overrides};}
const codec=(overrides={})=>cityModelCodecMetadata(metadata(overrides));
const decode=(body,overrides={},options={})=>decodeCityModelResponse(new Response(body),codec(overrides),options);

// Resolve only the bare Three import; run the original vendored GLTFLoader.
const resolver=registerHooks({resolve(specifier,context,nextResolve){return specifier==='three'?{url:new URL('../vendor/three.module.js',import.meta.url).href,shortCircuit:true}:nextResolve(specifier,context);}});
const {GLTFLoader}=await import('../vendor/GLTFLoader.js');resolver.deregister();

test('real deterministic gzip roundtrip reaches actual GLTFLoader with exact FLOAT32 positions',async()=>{
 assert.deepEqual(gzip,gzipSync(glb,{level:6,mtime:0}));
 const buffer=await decode(gzip);assert.deepEqual(new Uint8Array(buffer),glb);
 const model=await new GLTFLoader().parseAsync(buffer,'https://fixture.invalid/');
 assert.equal(countExpandedTriangles(model.scene),1);const mesh=model.scene.children[0];
 assert(mesh.geometry.attributes.position.array instanceof Float32Array);assert.equal(mesh.geometry.attributes.position.getX(0),Math.fround(.123456789));
 assert.equal(mesh.geometry.index.count,3);disposeModelResources(model.scene);
});

test('HTTP Content-Encoding already decoded GLB is not decompressed twice',async()=>{
 const response=new Response(glb,{headers:{'Content-Encoding':'gzip','Content-Length':String(gzip.length)}});
 assert.deepEqual(new Uint8Array(await decodeCityModelResponse(response,codec())),glb);
});

test('already decoded GLB still requires decoded SHA and exact declared length',async()=>{
 await assert.rejects(decode(glb,{decoded_sha256:'0'.repeat(64)}),/Decoded city model SHA-256/);
 await assert.rejects(decode(glb,{decoded_size_bytes:glb.length+4}),/Decoded city model size/);
});

test('gzip magic is mandatory before starting the decompressor',async()=>{
 const bad=new Uint8Array(gzip);bad[0]=0;await assert.rejects(decode(bad,{sha256:sha(bad)}),/magic/);
});

test('compressed SHA and length are checked independently from decoded contract',async()=>{
 await assert.rejects(decode(gzip,{sha256:'0'.repeat(64)}),/Compressed city model SHA-256/);
 await assert.rejects(decode(gzip,{size_bytes:gzip.length+1}),/Compressed city model size/);
});

test('corrupt CRC and truncated gzip fail even when transport hash matches those damaged bytes',async()=>{
 const bad=new Uint8Array(gzip);bad[bad.length-8]^=0xff;
 await assert.rejects(decode(bad,{sha256:sha(bad)}));
 const short=gzip.subarray(0,gzip.length-3);await assert.rejects(decode(short,{size_bytes:short.length,sha256:sha(short)}));
});

test('valid gzip with incorrect decoded SHA never reaches a model parser',async()=>{
 await assert.rejects(decode(gzip,{decoded_sha256:'f'.repeat(64)}),/Decoded city model SHA-256/);
});

test('decompression output is bounded by declared size before full output is assembled',async()=>{
 const large=new Uint8Array(512*1024),small=gzipSync(large);
 await assert.rejects(decode(small,{size_bytes:small.length,sha256:sha(small),decoded_size_bytes:4096,decoded_sha256:sha(large)}),/Decoded city model exceeds/);
});

test('exclusive 100 MB declaration limit is validated without allocating a large output',()=>{
 assert.equal(CITY_MODEL_BYTE_LIMIT,100000000);
 assert.throws(()=>codec({decoded_size_bytes:100000000}),/Invalid gzip/);
 assert.throws(()=>codec({size_bytes:100000000}),/Invalid gzip/);
 assert.throws(()=>codec({decoded_size_bytes:NaN}),/Invalid gzip/);
});

test('downward test limit rejects over-budget bytes and cannot relax the production ceiling',async()=>{
 await assert.rejects(decode(gzip,{}, {byteLimit:glb.length}),/file limit/);
 await assert.rejects(decode(gzip,{}, {byteLimit:CITY_MODEL_BYTE_LIMIT+1}),/Invalid city model byte limit/);
});

test('gzip cannot disguise invalid GLB magic, version or embedded length',async()=>{
 for(const edit of [b=>{b[0]=0},b=>{new DataView(b.buffer).setUint32(4,1,true)},b=>{new DataView(b.buffer).setUint32(8,b.length+4,true)}]){
  const bad=new Uint8Array(glb);edit(bad);const encoded=gzipSync(bad);
  await assert.rejects(decode(encoded,{size_bytes:encoded.length,sha256:sha(encoded),decoded_sha256:sha(bad)}),/GLB/);
 }
});

test('missing gzip integrity metadata and unknown content encoding fail before loading',()=>{
 for(const fields of [{decoded_sha256:undefined},{decoded_size_bytes:undefined},{sha256:undefined},{decoded_sha256:'xyz'}])assert.throws(()=>codec(fields),/Invalid gzip/);
 assert.throws(()=>cityModelCodecMetadata({content_encoding:'br'}),/Unsupported/);
});

test('plain legacy GLB remains compatible and optional legacy SHA is honored',async()=>{
 const legacy=cityModelCodecMetadata({size_bytes:glb.length});assert.deepEqual(new Uint8Array(await decodeCityModelResponse(new Response(glb),legacy)),glb);
 const signed=cityModelCodecMetadata({size_bytes:glb.length,sha256:sha(glb)});assert.deepEqual(new Uint8Array(await decodeCityModelResponse(new Response(glb),signed)),glb);
 await assert.rejects(decodeCityModelResponse(new Response(glb),cityModelCodecMetadata({size_bytes:glb.length,sha256:'0'.repeat(64)})),/SHA-256/);
});

test('abort cancels a pending response stream, rejects promptly and does not decode',async()=>{
 const controller=new AbortController();let cancelled=false;
 const stream=new ReadableStream({start(c){c.enqueue(gzip.subarray(0,10));},cancel(){cancelled=true;}});
 const pending=decodeCityModelResponse(new Response(stream),codec(),{signal:controller.signal});controller.abort('parent-hidden');
 await assert.rejects(pending,error=>error.name==='AbortError');assert.equal(cancelled,true);
});

test('already-aborted signal performs no response body read',async()=>{
 const controller=new AbortController();controller.abort('view-changed');let reads=0;
 await assert.rejects(decodeCityModelResponse({arrayBuffer(){reads++;return glb.buffer;}},codec(),{signal:controller.signal}),error=>error.name==='AbortError');assert.equal(reads,0);
});
