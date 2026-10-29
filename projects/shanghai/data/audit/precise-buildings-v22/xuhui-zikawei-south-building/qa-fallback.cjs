const {chromium}=require('playwright'),fs=require('fs'),assert=require('node:assert/strict');
const id='xuhui-zikawei-south-building',base=process.argv[2]||'http://127.0.0.1:8001/';
(async()=>{const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});try{const results=[];
 for(const test of ['osm-fallback','asset-failure']){
 const p=await b.newPage({viewport:{width:1100,height:800}});const errors=[];p.on('pageerror',e=>errors.push(e.message));
 if(test==='osm-fallback')await p.route('**/*overturemaps.org/**',r=>r.abort('failed'));
 else await p.route('**/xuhui-zikawei-south-building-web.glb',r=>r.abort('failed'));
 await p.goto(base+'index.html#landmark='+id+'&mode=walk');await p.waitForFunction(()=>!!window.__SHANGHAI_APP__,null,{timeout:180000});
 await p.waitForFunction(({id,test})=>{const a=window.__SHANGHAI_APP__,s=a.scene.getLandmarkAssetState(id);return test==='asset-failure'?s.status==='error':s.visible&&a.scene.getCollisionState().buildingSource!=='overture'}, {id,test},{timeout:120000});
 const result=await p.evaluate(id=>{const a=window.__SHANGHAI_APP__,r=a.landmarks.find(x=>x.id===id);return {asset:a.scene.getLandmarkAssetState(id),collision:a.scene.getCollisionState(),inside:a.scene.collisionAt(r.lng,r.lat),correction:a.scene.getSourceGeometryCorrectionState(),stream:a.scene.getStreamingState(),osm:a.scene.getRealismState().osmFallback}},id);
 assert.equal(result.inside,'building');assert.equal(result.correction.active.some(x=>x.id===id),test==='osm-fallback');assert.equal(result.stream.detail.precise.visible.includes(id),test==='osm-fallback');assert.deepEqual(errors,[]);
 if(test==='osm-fallback')assert.ok(Object.keys(result.correction.uniqueMatchedComponents).some(k=>k.includes(id+':openmaptiles:')));
 results.push({test,...result,errors});await p.screenshot({path:__dirname+'/'+test+'.png'});await p.close();console.log('PASS',test);
 }
 fs.writeFileSync(__dirname+'/fallback.json',JSON.stringify(results,null,2)+'\n');
}finally{await b.close()}})().catch(e=>{console.error(e);process.exit(1)});
