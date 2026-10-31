/* Read-only receipt for a near asset loaded across the stopped QA adapter.
 * Does not set viewport, camera, source state, model data or DOM. MIT. */
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),{createHash}=require('crypto');
const sha=b=>createHash('sha256').update(b).digest('hex');
async function run(){
 const footprint=JSON.parse(fs.readFileSync(path.join(__dirname,'footprint-review.json'))),expected=footprint.baseline_western_near_preservation_check.asset_binding;
 const relative='assets/city-detail/macros/'+footprint.proposed_placement_contract.owner.macro_id+'/'+footprint.near_group_owner_isolation_requirement.western_near_tile;
 const tabs=await (await fetch('http://127.0.0.1:9223/json/list')).json();assert.equal(tabs.filter(t=>t.type==='page').length,1);const tab=tabs.find(t=>t.type==='page');assert.equal(new URL(tab.url).pathname,'/index.html');
 const ws=new WebSocket(tab.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
 const expression=async relative=>{const url=new URL(relative,location.href).href,a=window.__SHANGHAI_APP__,s=a.scene.getStreamingState(),scope=a.scene.getCandidateIntegrationState().shader.ownerScopedSources.find(r=>r.feature_local_ids.includes(4270));
  const originalResourceTimings=performance.getEntriesByName(url).map(r=>({name:r.name,startTime:r.startTime,duration:r.duration,transferSize:r.transferSize,encodedBodySize:r.encodedBodySize,decodedBodySize:r.decodedBodySize,initiatorType:r.initiatorType}));
  const response=await fetch(url,{cache:'no-cache'}),bytes=await response.arrayBuffer(),digest=await crypto.subtle.digest('SHA-256',bytes);
  return {url,status:response.status,bytes:bytes.byteLength,sha256:[...new Uint8Array(digest)].map(b=>b.toString(16).padStart(2,'0')).join(''),origin:response.headers.get('x-audit-origin'),originalResourceTimings,scope,nearVisible:scope&&s.detail.active.some(r=>r.id===scope.id),note:'Explicit read-only HTTP body revalidation after the initial native asset request crossed the stopped adapter. The existing model remains untouched; initial requests, if retained by PerformanceResourceTiming, are reported separately.'};};
 const value=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Receipt request timed out')),120000);ws.onmessage=event=>{const r=JSON.parse(event.data);if(r.id!==1)return;clearTimeout(timer);if(r.error||r.result.exceptionDetails)reject(Error(JSON.stringify(r.error||r.result.exceptionDetails)));else resolve(r.result.result.value);};ws.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression:`(${expression.toString()})(${JSON.stringify(relative)})`,awaitPromise:true,returnByValue:true}}));});
 ws.close();assert.equal(value.status,200);assert.equal(value.bytes,expected.bytes);assert.equal(value.sha256,expected.sha256);assert.equal(value.scope.triangles,0);
 const report={generatedAt:new Date().toISOString(),script:{file:'data/audit/grosvenor-house-v1/qa-western-source-receipt.cjs',sha256:sha(fs.readFileSync(__filename))},footprintSha256:sha(fs.readFileSync(path.join(__dirname,'footprint-review.json'))),expected,receipt:value};
 fs.writeFileSync(path.join(__dirname,'western-source-http-receipt.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}
run().catch(error=>{console.error(error);process.exitCode=1;});
