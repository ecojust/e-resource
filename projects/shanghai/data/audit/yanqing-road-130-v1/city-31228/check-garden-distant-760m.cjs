'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');
const digest = value => createHash('sha256').update(value).digest('hex');
const root = __dirname;
const host = process.env.MODEL_BASE_URL;
const output = process.env.QA_OUTPUT_DIR;
const id = 'xuhui-yanqing-road-130-residence';
const evidencePrefix = 'attempts/distant-formal-screenshot-before-reading-input-device/';
const audit = '/workspace/e-resource/projects/shanghai/data/audit/yanqing-road-130-v1/city-31228';
const oldFile = name => fs.readFileSync(path.join(audit,evidencePrefix,name));
const report = JSON.parse(oldFile('main-browser.json'));
const old = JSON.parse(oldFile('failed-exit.json'));
const originalHash = digest(oldFile('failed-exit.json'));
assert.equal(originalHash,'dca68d3900c25c0672f625b240564d4d9c68206c7c6fb81e7732974a812904d5');
assert.equal(digest(oldFile('main-browser.json')),old.report_sha256);
assert.equal(old.exit_code,1);
assert.equal(report.completed,false);
assert.equal(report.screenshots.length,1);
assert.equal(report.views.length,1);
assert.equal(report.files.length,3);
assert.equal(digest(oldFile('map-distant.png')),report.screenshots[0].sha256);
const view = report.views[0];
assert.equal(view.asset.variant,'distant');
assert.equal(view.asset.verifiedAsset.variant,'lod');
assert.equal(view.asset.status,'loaded');
assert.equal(view.asset.visible,true);
assert.equal(view.glError,0);
assert.equal(view.contextLost,false);
assert.equal(report.files.find(f=>f.loadedByScene).sha256,view.asset.verifiedAsset.sha256);
assert.equal(host,report.server);
const inputs=JSON.parse(fs.readFileSync(path.join(root,'viewer-source-bindings.json')));
const prod=JSON.parse(fs.readFileSync(path.join(root,'228-production.json'))).files;
const key='assets/models/candidates/'+id+'/manifest.json';
const manifest=JSON.parse(fs.readFileSync(path.join(root,'viewer-inputs',key)));
const check = {phase:'distant',started:new Date().toISOString(),id,server:host,completed:false,
  evidenceMode:'separate-real-sessions',single_session_passed:false,
  originalRendering:{returned:old.exit_code,completed:report.completed,node:old.node_pid,
    physical:evidencePrefix+'failed-exit.json',physical_sha256:originalHash,report:evidencePrefix+'main-browser.json',
    report_sha256:old.report_sha256,driver_sha256:old.source_code_sha256,
    conclusions:['Visible verified far mesh and anchor','WebGL context and real frame','Rendered screenshot','Three HTTP asset responses','Map directory pointer and navigation']},
  supplemental:{conclusions:['Mouse pointer and input-device state on the ordinary page','Four browser downloads saved from the ordinary production viewer']},
  scriptSha256:digest(fs.readFileSync(__filename)),errors:[],warnings:[],failed:[],
  servedRuntime:report.servedRuntime,catalog:report.catalog,bindings:report.bindings,realDirectoryEntry:report.realDirectoryEntry,
  views:report.views,screenshots:report.screenshots,files:report.files,downloads:{}};
const outputReport=path.join(output,'main-browser.json');
assert(!fs.existsSync(outputReport));
async function run() {
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=19528']});
 try {
  const [width,height]=view.viewport;
  const page=await browser.newPage({viewport:{width,height},hasTouch:false,deviceScaleFactor:1});
  page.on('pageerror',e=>check.errors.push(e.message));
  for(const f of Object.keys(inputs.files)){
   const r=await page.request.get(new URL(f,host).href);
   assert.equal(r.status(),200);assert.equal(digest(await r.body()),inputs.files[f].sha256);assert.equal(prod[f],inputs.files[f].sha256);await r.dispose();
  }
  await page.goto(new URL(manifest.viewer_page,host).href);
  await page.locator('#downloads a').first().waitFor();
  check.inputDevice=await page.evaluate(()=>({touchPoints:navigator.maxTouchPoints,viewport:[innerWidth,innerHeight]}));
  assert.equal(check.inputDevice.touchPoints,0);assert.deepEqual(check.inputDevice.viewport,view.viewport);
  check.supplemental.browser=browser.version();
  await page.evaluate(()=>{window.addEventListener('pointerup',e=>window.__farSupplementPointer={trusted:e.isTrusted,type:e.pointerType,button:e.button,view:e.target.closest('[data-view]')?.dataset.view},{once:true,capture:true});});
  await page.locator('[data-view="front"]').click();
  check.supplemental.realPointer=await page.evaluate(()=>window.__farSupplementPointer);
  assert.deepEqual(check.supplemental.realPointer,{trusted:true,type:'mouse',button:0,view:'front'});
  for(const [role,label] of Object.entries({raw:'原始',full:'网页',lod:'远景',native:'Blender'})){
   const asset=manifest.assets[role];
   const link=page.locator('#downloads a').filter({hasText:label});assert.equal(await link.count(),1);
   const [download]=await Promise.all([page.waitForEvent('download'),link.click()]);
   assert.equal(download.suggestedFilename(),asset.file);
   const temporary=path.join(root,'standalone-scratch-and-reports','distant-saved-'+asset.file);
   await download.saveAs(temporary);
   const bytes=fs.readFileSync(temporary);assert.equal(bytes.length,asset.bytes);assert.equal(digest(bytes),asset.sha256);
   check.downloads[role]={file:asset.file,bytes:bytes.length,sha256:asset.sha256,actualSaved:true,downloadURL:download.url()};
   fs.unlinkSync(temporary);await download.delete();
  }
  assert.equal(Object.keys(check.downloads).length,4);assert.equal(check.errors.length,0);
  assert.equal(digest(fs.readFileSync(path.join(output,'map-distant.png'))),report.screenshots[0].sha256);
  check.completed=true;
 }catch(e){check.failure=e.stack;throw e;}
 finally{await browser.close();check.finished=new Date().toISOString();fs.writeFileSync(outputReport,JSON.stringify(check,null,2)+'\n');}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
