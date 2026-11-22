// Exercise the three named views, both mesh variants and the four download links.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const assert = require('node:assert/strict');
const root = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(__dirname,'../../..');
const folder = 'assets/models/candidates/huangpu-meilun-west-nanjing-corner/';
const manifest = JSON.parse(fs.readFileSync(path.join(root,folder,'manifest.json')));
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:31245/';
assert.equal(new URL(base).origin,'http://127.0.0.1:31245');
assert.equal(manifest.id,'huangpu-meilun-west-nanjing-corner');
assert.equal(manifest.viewer_page,'meilun-west-nanjing-corner.html');
assert.deepEqual(Object.keys(manifest.assets).sort(),['full','lod','native','raw']);
const output = path.resolve(process.argv[2] || __dirname);
const hash = content => createHash('sha256').update(content).digest('hex');

async function main() {
  fs.mkdirSync(output,{recursive:true});
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const report={id:manifest.id,base,passed:false,script_sha256:hash(fs.readFileSync(__filename)),files:{},views:[],materials:{},downloads:{},pageChecks:{},errors:[]};
  try {
    for(const [device,width,height,mobile] of [['desktop',1250,820,false],['mobile',390,844,true]]) {
      const page=await browser.newPage({viewport:{width,height},hasTouch:mobile,isMobile:mobile,deviceScaleFactor:1,acceptDownloads:true});
      page.setDefaultTimeout(120000);
      page.on('pageerror',e=>report.errors.push(e.message));
      const seen=new Map([manifest.viewer_page,'src/candidate-asset-viewer.js',folder+'manifest.json',folder+manifest.assets.full.file,folder+manifest.assets.lod.file]
        .map(file=>[file,page.waitForResponse(r=>new URL(r.url()).origin===new URL(base).origin && new URL(r.url()).pathname==='/'+file,{timeout:180000})]));
      await page.goto(base+manifest.viewer_page,{waitUntil:'domcontentloaded'});
      assert.equal(await page.locator('header > a').getAttribute('href'),'index.html#landmark='+manifest.id+'&mode=overview');
      const headings = await page.locator('main#model-view').getAttribute('aria-label');
      assert.equal(headings,'美伦西楼转角的上下山花、石砌窗墙和退入的店面');
      assert.equal(await page.title(),'美伦大楼西楼 · 南京东路西北转角');
      assert.equal(await page.locator('header h1').innerText(),'美伦大楼西楼');
      const scope=await page.locator('.scope').innerText();
      assert.ok(scope.includes('南京东路的两间店面和江西中路的一间店面') && scope.includes('檐顶留有石栏杆'));
      const buttons=await page.locator('[data-view]').evaluateAll(elements=>Object.fromEntries(elements.map(el=>[el.dataset.view,el.textContent.trim()])));
      assert.deepEqual(buttons,{front:'南京东路街面',oblique:'斜看转角山花',above:'俯看檐顶栏杆'});
      report.pageChecks[device]={url:page.url(),title:await page.title(),aria:headings,scope,buttons,resources:{}};
      for(const role of ['full','lod']) {
        await page.locator('#detail').selectOption(role);
        const prefix=role==='full'?'近景':'远景';
        await page.waitForFunction(text=>document.querySelector('#status').textContent.startsWith(text+' ·'),prefix,{timeout:150000});
        if(!mobile)report.materials[role]=await page.evaluate(async({file,expected})=>{
          const [{GLTFLoader},{MeshoptDecoder}]=await Promise.all([import('./vendor/GLTFLoader.js'),import('./vendor/meshopt_decoder.module.js')]);
          const bytes=await (await fetch(file)).arrayBuffer();
          const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
          if(digest!==expected)throw Error('Unexpected downloaded model');
          const gltf=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bytes,'');
          const materialTriangles={};
          gltf.scene.traverse(item=>{
            if (!item.isMesh) return;
            const geometry=item.geometry;
            if (Array.isArray(item.material)) throw Error('Unexpected multi-material primitive');
            const name=item.material.name;
            materialTriangles[name]=(materialTriangles[name]||0)+(geometry.index?.count||geometry.attributes.position.count)/3;
          });
          return {sha256:digest,materialTriangles};
        },{file:folder+manifest.assets[role].file,expected:manifest.assets[role].sha256});
        if(!mobile){
          const expected=JSON.parse(fs.readFileSync(path.join(root,'data/audit/meilun-west-nanjing-corner-v1/geometry-native.json'))).surface_sha256[role];
          const counts=Object.fromEntries(Object.entries(expected).map(([name,surface])=>[name,surface.triangles]));
          assert.deepEqual(report.materials[role].materialTriangles,counts);
        }
        for(const pose of role==='full'?['front','oblique']:['above']) {
          const button=page.locator('[data-view="'+pose+'"]');
          await button.scrollIntoViewIfNeeded();
          const rect=await button.boundingBox();assert.ok(rect&&rect.width>5&&rect.height>5);
          const x=rect.x+rect.width/2,y=rect.y+rect.height/2;
          assert.equal(await page.evaluate(([x,y])=>document.elementFromPoint(x,y)?.closest('[data-view]')?.dataset.view,[x,y]),pose);
          if(mobile)await page.touchscreen.tap(x,y);else await page.mouse.click(x,y);
          await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
          const name='viewer-'+device+'-'+role+'-'+pose+'.png';
          const image=await page.screenshot({path:path.join(output,name),timeout:120000});
          report.views.push({device,role,pose,viewport:[width,height],input:mobile?'touchscreen tap':'mouse click',buttonCenter:[x,y],file:name,sha256:hash(image),bytes:image.length});
        }
      }
      for(const [name,url]of seen) {
        const res=await url,bytes=await res.body();assert.ok(res.ok());assert.equal(hash(bytes),hash(fs.readFileSync(path.join(root,name))));
        report.files[name]={sha256:hash(bytes),bytes:bytes.length};
        report.pageChecks[device].resources[name]={...report.files[name],status:res.status(),url:res.url()};
      }
      if(!mobile)for(const [role,label]of Object.entries({raw:'原始',full:'网页',lod:'远景',native:'Blender'})){
        const item=manifest.assets[role],anchor=page.locator('#downloads a').filter({hasText:label});
        assert.equal(await anchor.count(),1);
        const href=await anchor.getAttribute('href');
        assert.equal(new URL(href,page.url()).href,new URL(folder+item.file,base).href);
        const [download]=await Promise.all([page.waitForEvent('download'),anchor.click()]);const saved=path.join(output,'saved-'+item.file);await download.saveAs(saved);const bytes=fs.readFileSync(saved);
        assert.equal(download.suggestedFilename(),item.file);assert.equal(hash(bytes),item.sha256);assert.equal(bytes.length,item.bytes);
        assert.equal(download.url(),new URL(folder+item.file,base).href);
        report.downloads[role]={file:item.file,bytes:bytes.length,sha256:hash(bytes),saved_and_reread:true,saveAsVerified:true,saved:path.basename(saved),url:download.url()};
        await download.delete();
      }
      await page.close();
    }
    assert.equal(report.views.length,6);
    assert.equal(Object.keys(report.downloads).length,4);
    for(const checks of Object.values(report.pageChecks))assert.equal(Object.keys(checks.resources).length,5);
    assert.deepEqual(report.errors,[]);report.passed=true;
  } finally {
    await browser.close();fs.writeFileSync(path.join(output,'viewer.json'),JSON.stringify(report,null,2)+'\n');
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
