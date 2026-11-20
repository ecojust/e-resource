const fs=require('node:fs');
const http=require('node:http');
const assert=require('node:assert/strict');
const path=require('node:path');
const crypto=require('node:crypto');
const {chromium}=require('playwright');
const {parseArgs}=require('node:util');
const {values:args}=parseArgs({options:{
  old:{type:'string'}, new:{type:'string'}, fixed:{type:'string'},out:{type:'string'},
  assets:{type:'string'},'old-glb':{type:'string'},'new-glb':{type:'string'},
  chromium:{type:'string'},help:{type:'boolean'}
}});
const help='node warm-http.cjs --old <original-site-dir-or-URL> --new <revised-site-before-cache-fix-dir-or-URL> --fixed <corrected-site-dir-or-URL> --out <new-output-dir> [--assets <fallback-site>] [--old-glb <path-or-URL>] [--new-glb <path-or-URL>] [--chromium <binary>]';
if(args.help){console.log(help);process.exit(0);}
if(!args.old||!args.new||!args.fixed||!args.out)throw Error(help);
const output=path.resolve(args.out);
fs.mkdirSync(output,{recursive:true});
assert.ok(!fs.existsSync(path.join(output,'actual-http.json')),'Choose a fresh output directory');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const json=(n,x)=>fs.writeFileSync(path.join(output,n),JSON.stringify(x,null,2)+'\n');
const l='data/landmarks.json',v='data/precise-buildings-v6.json',c='data/precise-buildings/catalog.json',m='data/precise-buildings/macros/14-13722-6690/index.json';
const cases={'all-warm':[l,v,c,m],'catalog-warm':[c,m],'index-warm':[m],'landmark-warm':[l],fixed:[l,v,c,m]};
const states={},transfers=[],comparisons={},bytes=new Map();
async function load(location,relative){
 const remote=/^https?:\/\//.test(location);
 if(!remote)return fs.promises.readFile(relative?path.join(location,relative):location);
 const url=relative?new URL(relative,location.replace(/\/?$/,'/')):location;
 const response=await fetch(url);
 if(!response.ok)throw Error('HTTP '+response.status+' for '+url);
 return Buffer.from(await response.arrayBuffer());
}
async function upstream(stage,pathname){
 const key=stage+':'+pathname;
 if(bytes.has(key))return bytes.get(key);
 const origin=stage===77?args.old:args.new;
 let result;
 const expectedGLB=pathname.endsWith('.glb')&&pathname.includes('yangpu-library');
 const override=expectedGLB?(pathname.includes('/revisions/east-entry-relief/')?args['new-glb']:args['old-glb']):null;
 if(override)result=await load(override);
 else{
  try{result=await load(origin,pathname);}
  catch(error){if(!args.assets)throw error;result=await load(args.assets,pathname);}
 }
 bytes.set(key,result);return result;
}
async function adjust(file,data){
 if(!['src/app.js','src/map-scene.js','src/ordinary-building-catalog.js'].includes(file))return data;
 const patched=await load(args.fixed,file);comparisons[file]={original:hash(data),adjusted:hash(patched)};return patched;
}
async function main(){
 const server=http.createServer(async(req,res)=>{
  try{
   const u=new URL(req.url,'http://self'),[,id,...parts]=u.pathname.split('/');const file=parts.join('/');
   if(file==='qa.html'){res.writeHead(200,{'Content-Type':'text/html','Cache-Control':'no-store'});res.end('<!doctype html><title>Ordinary metadata HTTP test</title>');return;}
   if(!cases[id]){res.writeHead(404);res.end();return;}
   const stage=states[id]||77;
   let b=await upstream(stage,file);
   if(id==='fixed'&&stage===78)b=await adjust(file,b);
   const type=file.endsWith('.js')?'text/javascript':file.endsWith('.json')||file.endsWith('.geojson')?'application/json':file.endsWith('.html')?'text/html':'application/octet-stream';
   const warm=[l,v,c,m].includes(file);
   res.writeHead(200,{'Content-Type':type,'Content-Length':b.length,'Cache-Control':warm?'public, max-age=86400':'no-store'});
   res.end(b);transfers.push({case:id,stage,request:file+u.search,bytes:b.length,sha256:hash(b)});
  }catch(e){if(!res.headersSent)res.writeHead(500);res.end(e.message);}
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({executablePath:args.chromium||process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--disable-gpu','--renderer-process-limit=1']});
 const result={started:new Date().toISOString(),browser:browser.version(),sources:{pre:args.old,post:args.new,fixed_modules:args.fixed,asset_fallback:args.assets||null},driver_sha256:hash(fs.readFileSync(__filename)),purpose:'Production bootstrap resource loop, verified-byte reader and ordinary macro registration executed without a map or WebGL; actual HTTP cache primed through the former site.',cases:[]};
 try{
  for(const [name,paths]of Object.entries(cases)){
   const b='http://127.0.0.1:'+server.address().port+'/'+name+'/';
   const ctx=await browser.newContext();const page=await ctx.newPage();
   await page.goto(b+'qa.html');
   await page.evaluate(async paths=>Promise.all(paths.map(async p=>{let r=await fetch(p);if(!r.ok)throw Error(p);await r.arrayBuffer();})),paths);
   states[name]=78;
   const state=await page.evaluate(async()=>{
    const root=new URL('./',location.href).href;
    const html=await(await fetch('index.html')).text();
    const entry=new DOMParser().parseFromString(html,'text/html').querySelector('script[src*="src/app.js"]').getAttribute('src');
    const appURL=new URL(entry,root).href;
    const app=await(await fetch(appURL)).text();
    const match=app.match(/const responses=await Promise\.all\([\s\S]*?\}\)\)\);/);
    if(!match)throw Error('Cannot locate exact production bootstrap fetch loop');
    const declaration=app.match(/const metadataRevision=[^;]+;/)?.[0]||'';
    const expr=(declaration+match[0]).replaceAll('import.meta.url','appURL');
    const AsyncFunction=Object.getPrototypeOf(async()=>{}).constructor;
    const responses=await new AsyncFunction('appURL','let candidateCatalogError;'+expr+'return responses;')(appURL);
    const modulePath=app.match(/from '(\.\/ordinary-building-catalog\.js\?v=[^']+)'/)[1];
    const sceneModule=app.match(/from '(\.\/map-scene\.js\?v=[^']+)'/)[1];
    const sceneSource=await(await fetch(new URL(sceneModule,appURL))).text();
    const nested=sceneSource.match(/OrdinaryBuildingCatalog \} from '(\.\/ordinary-building-catalog\.js\?v=[^']+)'/)[1];
    const {readVerifiedBytes}=await import(new URL(modulePath,appURL).href);
    const {OrdinaryBuildingCatalog}=await import(new URL(nested,appURL).href);
    const adapter=sceneSource.match(/isOrdinaryLandmarkRecord \} from '(\.\/ordinary-scene-adapter\.js\?v=[^']+)'/)[1];
    const {createOrdinaryMacroRegistrar}=await import(new URL(adapter,appURL).href);
    const active=responses[2].find(d=>d.id==='yangpu-library');
    const outcome={entry,bootstrap_loop_executed:true,reader_path:modulePath,scene_reader_path:nested,landmark_model:active.model,landmark_sha256:active.web_sha256,ordinary_catalog_expected:responses[4].ordinary_catalog.sha256,phase:'catalog',errors:[]};
    let oc;
    try{
     const raw=await readVerifiedBytes(responses[4].ordinary_catalog,root,{limit:8*1024*1024});
     const catalog=JSON.parse(new TextDecoder().decode(raw));
     outcome.macro_expected=catalog.macros.find(m=>m.id==='14-13722-6690').sha256;
     let resolve, registered=null;
     const settled=new Promise(r=>{resolve=r;});
     const noop=()=>{};
     const register=createOrdinaryMacroRegistrar({landmarkRecords:new Map([[active.id,active]]),cityDetails:{staticReplacements:{landmarks:new Set([active.id])},installMacroReplacements:noop,setVisibleLandmarks:noop,removeMacroReplacements:noop},landmarkBoundaries:new Map(),preciseLandmarkIds:new Set([active.id]),tileSuppression:{setOwner:noop},disposeModel:noop,updateLandmarkVisibility:noop,updateBuildingExclusions:noop});
     oc=new OrdinaryBuildingCatalog({baseURL:root,districts:responses[0].districts,
      registerMacro:args=>{const session=register(args);registered=args.models.find(m=>m.id==='yangpu-library');resolve();return session;},
      onError:e=>{outcome.errors.push(e.message);resolve();}});
     oc.setCatalog(catalog);outcome.phase='macro';
     oc.update({lng:active.lng,lat:active.lat,zoom:19.2,mode:'walk'});
     await Promise.race([settled,new Promise((_,j)=>setTimeout(()=>j(Error('Ordinary registration timeout')),22000))]);
     if(registered){outcome.registered_web=registered.assets.web.file;outcome.registered_sha256=registered.web_sha256;outcome.phase='verified-asset';
      const mesh=await readVerifiedBytes(registered.assets.web,root);let b=new DataView(mesh);
      outcome.glb={bytes:mesh.byteLength,magic:b.getUint32(0,true),version:b.getUint32(4,true),sha256:[...new Uint8Array(await crypto.subtle.digest('SHA-256',mesh))].map(c=>c.toString(16).padStart(2,'0')).join('')};
      outcome.phase='registered-and-verified';}
    }catch(e){outcome.errors.push(e.message);}finally{oc?.destroy();}
    outcome.resources=performance.getEntriesByType('resource').filter(x=>x.name.includes('data/landmarks.json')||x.name.includes('precise-buildings')).map(x=>({url:x.name.replace(root,''),transfer:x.transferSize,bytes:x.decodedBodySize}));
    return outcome;
   });
   result.cases.push({name,...state});console.log(name,state.phase,state.landmark_sha256.slice(0,9),state.registered_sha256?.slice(0,9),state.errors);
   await ctx.close();json('actual-http.json',{...result,transfers,comparisons});
  }
  const [old,catalogFails,indexFails,conflict,fixed]=result.cases;
  assert.equal(old.phase,'registered-and-verified');assert.equal(fixed.phase,'registered-and-verified');
  assert.equal(old.glb.magic,0x46546c67);assert.equal(fixed.glb.magic,0x46546c67);assert.equal(old.glb.version,2);assert.equal(fixed.glb.version,2);
  assert.notEqual(old.glb.sha256,fixed.glb.sha256);assert.equal(old.landmark_sha256,old.glb.sha256);
  assert.equal(fixed.landmark_sha256,fixed.glb.sha256);assert.equal(catalogFails.phase,'catalog');assert.match(catalogFails.errors.join(' '),/SHA256|byte/);
  assert.equal(indexFails.phase,'macro');assert.match(indexFails.errors.join(' '),/SHA256|byte/);
  assert.equal(conflict.phase,'macro');assert.match(conflict.errors.join(' '),/Conflicting existing precise building record/);
  for(const n of [l,v,c,m]){
   assert.equal(transfers.filter(x=>x.case==='all-warm'&&x.stage===78&&x.request===n).length,0,n);
   assert.ok(transfers.some(x=>x.case==='fixed'&&x.stage===78&&x.request.startsWith(n+'?')),n);
  }
  result.passed=true;
 }finally{result.finished=new Date().toISOString();json('actual-http.json',{...result,transfers,comparisons});await browser.close();server.closeAllConnections();server.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
