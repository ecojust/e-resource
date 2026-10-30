/* Verify every new global model through the production browser asset loader. MIT. */
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),{createHash}=require('crypto');
const base=process.env.MODEL_BASE_URL||'http://127.0.0.1:8782/';
const output=process.env.QA_OUTPUT_DIR||__dirname;
const sha=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex');
(async()=>{
 const inventoryPath=path.join(__dirname,'inventory.json'),inventory=JSON.parse(fs.readFileSync(inventoryPath));
 const catalogPath=path.resolve(__dirname,'../../../data/candidate-city-integrations.json');
 const catalog=fs.existsSync(catalogPath)?JSON.parse(fs.readFileSync(catalogPath)):null;
 const records=catalog?catalog.models.map(r=>({...r,geometry:{bounds_glb:r.bounds_glb}})):inventory.records.filter(r=>!r.already_in_city);
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/__asset_audit__.html',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><meta charset="utf-8"><title>Model asset decode audit</title><script type="importmap">'+JSON.stringify({imports:{three:base+'vendor/three.module.js'}})+'</script>'}));
  await page.goto(base+'__asset_audit__.html');
  const results=[];
  for(const row of records){
   for(const variant of ['full','distant']){
    const result=await page.evaluate(async({row,variant,base})=>{
     const THREE=await import(base+'vendor/three.module.js');
     const {GLTFLoader}=await import(base+'vendor/GLTFLoader.js');
     const {MeshoptDecoder}=await import(base+'vendor/meshopt_decoder.module.js');
     const {loadOrdinaryLandmarkAsset}=await import(base+'src/ordinary-scene-adapter.js');
     const {countExpandedTriangles,disposeModelResources}=await import(base+'src/model-resources.js');
     const loader=new GLTFLoader();loader.setMeshoptDecoder(MeshoptDecoder);
     const record={id:row.id,kind:'building',assets:row.assets,ordinaryBaseURL:base};
     const data=await loadOrdinaryLandmarkAsset({record,variant,loader});
     data.scene.updateMatrixWorld(true);
     const bounds=new THREE.Box3().setFromObject(data.scene);
     const result={id:row.id,variant,triangles:countExpandedTriangles(data.scene),bounds:{min:bounds.min.toArray(),max:bounds.max.toArray()},meshes:0,vertices:0,nonFiniteValues:0,asset:row.assets[variant==='full'?'web':'lod']};
     data.scene.traverse(o=>{if(!o.isMesh)return;result.meshes++;const p=o.geometry.attributes.position;result.vertices+=p.count;for(let i=0;i<p.count;i++)if(![p.getX(i),p.getY(i),p.getZ(i)].every(Number.isFinite))result.nonFiniteValues++;});
     disposeModelResources(data.scene);return result;
    },{row,variant,base});
    assert.equal(result.triangles,result.asset.triangles,row.id+' '+variant+' decoded triangle count');
    assert.ok(result.meshes>0&&result.vertices>0);assert.equal(result.nonFiniteValues,0);
    if(variant==='full')for(const endpoint of ['min','max'])for(let axis=0;axis<3;axis++)assert.ok(Math.abs(result.bounds[endpoint][axis]-row.geometry.bounds_glb[endpoint][axis])<.05,row.id+' compressed/full raw bound mismatch');
    results.push(result);console.log('PASS decode',row.id,variant,result.triangles);
   }
  }
  assert.equal(results.length,60);assert.deepEqual(errors,[]);
  fs.mkdirSync(output,{recursive:true});
  fs.writeFileSync(path.join(output,'browser-assets.json'),JSON.stringify({generatedAt:new Date().toISOString(),browserVersion:browser.version(),base,inventory_sha256:sha(inventoryPath),catalog_sha256:catalog?sha(catalogPath):null,scope:'All 30 final global records including the split stele corridors, full and LOD: actual HTTP bytes, production byte/SHA verification, GLTFLoader/Meshopt decode, finite positions, triangle counts, full-vs-author bounds. This is an asset decode check; geographic visibility and placement are checked separately.',models:records.length,variants:results.length,results,errors},null,2)+'\n');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
