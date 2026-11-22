/* Check a height-limited courtyard facade on a retained convent wing in the real predecessor and successor maps.
   MODEL_BASE_URL selects the served scene. SHANGHAI_PROJECT_ROOT points to matching signed bytes.
   node check-garden-map.cjs <map-case.json> <before|after> <output-directory> */
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');

const [caseFile,phase,output] = process.argv.slice(2);
assert.ok(['before','after'].includes(phase));
const spec = JSON.parse(fs.readFileSync(caseFile));
const audit = path.dirname(path.resolve(caseFile));
const project = process.env.SHANGHAI_PROJECT_ROOT;
const base = process.env.MODEL_BASE_URL;
assert.ok(project && base && output);
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const local = file => fs.readFileSync(path.join(project,file));
const contract = JSON.parse(fs.readFileSync(path.join(audit,'final-placement-contract.json')));
const catalogFile = 'data/candidate-city-integrations.json';
const catalog = JSON.parse(local(catalogFile));
const selected = phase==='before' ? spec.previous : contract.id;
const row = catalog.models.find(r=>r.id===contract.id);
const site = contract.site_replacement;
assert.equal(Boolean(row),phase==='after');
assert.equal(catalog.resulting_city_count,spec[phase].count);
assert.equal(hash(local(catalogFile)),spec[phase].catalog_sha256);
if(row){
  for(const key of ['lng','lat','heading','collision_geometry','replacement_geometry','site_replacement','model_geometry_sha256']){
    assert.deepEqual(row[key],contract[key]);
  }
}
const report={id:contract.id,phase,started:new Date().toISOString(),base,files:[],views:[],errors:[],complete:false,
  case_sha256:hash(fs.readFileSync(caseFile)),script_sha256:hash(fs.readFileSync(__filename))};
fs.mkdirSync(output,{recursive:true});
const log=path.join(output,'city-'+phase+'.json');
assert.ok(!fs.existsSync(log));
const save=()=>fs.writeFileSync(log,JSON.stringify(report,null,2)+'\n');
const context={
  selected,id:contract.id,owner:contract.owner.feature_local_id,macro:contract.owner.macro_id,group:spec.group,
  siteId:site?.id||null,required:phase==='after',neighbors:spec.neighbors,
};
async function main(){
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({hasTouch:true,viewport:phase==='after'?{width:390,height:844}:{width:850,height:650}});
  const seen=new Set();
  page.on('response',r=>seen.add(new URL(r.url()).pathname.replace(/^\//,'')));
  page.on('pageerror',e=>report.errors.push(e.message));
  async function receipt(rel,requireRender){
    const r=await page.request.get(new URL(rel,base).href);
    assert.equal(r.status(),200);
    const b=await r.body(),digest=hash(b);assert.equal(digest,hash(local(rel)),rel);
    if(requireRender)assert.ok(seen.has(rel),'Scene must actually fetch '+rel);
    report.files.push({file:rel,bytes:b.length,sha256:digest,seen_in_scene:seen.has(rel)});
  }
  async function snapshot(name,detail,variant){
    await page.waitForFunction(({selected,id,required,macro,group,siteId,detail,variant})=>{
      const s=window.__SHANGHAI_APP__?.scene;
      if(!s || s.map.isMoving())return false;
      const a=s.getLandmarkAssetState(id),ci=s.getCandidateIntegrationState();
      if(required && (!a?.visible || !a.verifiedAsset?.sha256 || (variant && variant!==a.variant)))return false;
      if(!detail)return true;
      const stream=s.getStreamingState();
      if(!stream.detail.active.some(tile=>tile.id===macro+'/'+group))return false;
      const caps=ci.sourceSections.find(v=>v.id===siteId);
      return !siteId || (required?Boolean(caps):!caps);
    },{...context,detail,variant},{timeout:180000,polling:350});
    await page.evaluate(()=>new Promise(resolve=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>resolve());m.triggerRepaint();}));
    const value=await page.evaluate(tx=>{
      const s=window.__SHANGHAI_APP__.scene,m=s.map,c=s.getCandidateIntegrationState(),b=s.getBuildingBeaconState();
      const label=b.labelPositions.find(v=>v.id===tx.selected);
      return {route:location.hash,camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),elevation:m.getCenterElevation()},
        viewport:[innerWidth,innerHeight],asset:s.getLandmarkAssetState(tx.id),label:label?{x:label.x,y:label.y}:null,
        clip:c.displayClips.find(v=>v.id===tx.siteId)||null,sections:c.sourceSections.filter(v=>v.id===tx.siteId),
        ownGroup:c.shader.ownerScopedSources.find(v=>v.id===tx.macro+'/'+tx.group)||null,
        neighbor_ids:tx.neighbors,gl_error:m.painter.context.gl.getError(),context_lost:m.painter.context.gl.isContextLost()};
    },context);
    const view={name,state:value};report.views.push(view);save();
    assert.equal(value.gl_error,0);assert.equal(value.context_lost,false);
    assert.equal(new URLSearchParams(value.route.slice(1)).get('landmark'),selected);
    if(phase==='after'){
      const expected=row.assets[value.asset.variant==='full'?'web':'lod'];
      assert.equal(value.asset.verifiedAsset.sha256,expected.sha256);assert.equal(value.asset.triangles,expected.triangles);
    }
    if(detail){
      const clipped=value.ownGroup?.clip_feature_local_ids||[];
      assert.equal(clipped.includes(context.owner),phase==='after' && Boolean(site));
      assert.ok(context.neighbors.every(id=>!clipped.includes(id)));
      if(phase==='after' && site){
        assert.deepEqual(value.clip.geometry,site.geometry);assert.deepEqual(value.clip.owner,site.owner);
        assert.equal(value.clip.min_height,site.min_height);assert.equal(value.clip.max_height,site.max_height);
        assert.equal(value.sections[0].roof_m,site.source_section_caps.roof_m);
        assert.equal(value.sections[0].segments,spec.section_segments);
      }else{assert.equal(value.clip,null);assert.deepEqual(value.sections,[]);}
    }
    const file=phase+'-'+name+'.png';const bytes=await page.screenshot({path:path.join(output,file),timeout:150000});
    Object.assign(view,{file,bytes:bytes.length,sha256:hash(bytes)});save();
  }
  async function jump(camera){
    await page.evaluate(camera=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(camera);s.loadLandmarks();s.refreshBuildingBeacons();},camera);
  }
  const url=new URL('index.html#landmark='+selected+'&mode=overview',base).href;
  if(phase==='after'){
    await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
    assert.equal(await page.locator('.landmark-card[data-landmark]').count(),catalog.resulting_city_count);
    await page.locator('[data-landmark="'+contract.id+'"] .card-foot a[href="index.html#landmark='+contract.id+'&mode=overview"]').tap();
    await snapshot('mobile-default',false);
    await page.setViewportSize({width:850,height:650});
  }
  await page.goto(url,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()),null,{timeout:180000});
  const toggle=page.locator('#panel-toggle');
  if(await toggle.getAttribute('aria-expanded')==='true')await toggle.click();
  if(phase==='after')await snapshot('desktop-default',false);
  await jump(spec.front);await snapshot('garden-front',true,phase==='after'?'full':null);
  if(phase==='after'){
    await jump(spec.oblique);await snapshot('gable-and-windows',true,'full');
    await jump(spec.distant);await snapshot('distant',false,'distant');
    for(const variant of ['web','lod'])await receipt(row.assets[variant].file,true);
  }
  for(const file of ['index.html',catalogFile,'src/app.js','src/map-scene.js','src/building-beacons.js','src/candidate-city-clipping.js'])await receipt(file,true);
  assert.deepEqual(report.errors,[]);report.complete=true;
 }catch(error){
  report.failure=error.stack;throw error;
 }finally{await browser.close();report.finished=new Date().toISOString();save();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
