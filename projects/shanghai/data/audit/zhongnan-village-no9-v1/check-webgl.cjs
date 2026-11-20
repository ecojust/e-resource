// Exercise the three named views, both mesh variants and the four download links.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const assert = require('node:assert/strict');
const root = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(__dirname,'../../..');
const folder = 'assets/models/candidates/xuhui-zhongnan-village-no9-door/';
const manifest = JSON.parse(fs.readFileSync(path.join(root,folder,'manifest.json')));
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const output = path.resolve(process.argv[2] || __dirname);
const hash = content => createHash('sha256').update(content).digest('hex');

async function main() {
  fs.mkdirSync(output,{recursive:true});
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const report={id:manifest.id,base,passed:false,script_sha256:hash(fs.readFileSync(__filename)),files:{},views:[],materials:{},downloads:{},errors:[]};
  try {
    for(const [device,width,height,mobile] of [['desktop',1250,820,false],['mobile',390,844,true]]) {
      const page=await browser.newPage({viewport:{width,height},hasTouch:mobile,isMobile:mobile});
      page.setDefaultTimeout(120000);
      page.on('pageerror',e=>report.errors.push(e.message));
      const seen=new Map([manifest.viewer_page,'src/candidate-asset-viewer.js',folder+'manifest.json',folder+manifest.assets.full.file,folder+manifest.assets.lod.file]
        .map(file=>[file,page.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/'+file),{timeout:180000})]));
      await page.goto(base+manifest.viewer_page,{waitUntil:'domcontentloaded'});
      assert.equal(await page.locator('header > a').getAttribute('href'),'index.html#landmark='+manifest.id+'&mode=overview');
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
          const expected=JSON.parse(fs.readFileSync(path.join(__dirname,'geometry-native.json'))).surface_sha256[role];
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
      }
      if(!mobile)for(const [role,label]of Object.entries({raw:'原始',full:'网页',lod:'远景',native:'Blender'})){
        const item=manifest.assets[role],anchor=page.locator('#downloads a').filter({hasText:label});
        const [download]=await Promise.all([page.waitForEvent('download'),anchor.click()]);const bytes=fs.readFileSync(await download.path());
        assert.equal(download.suggestedFilename(),item.file);assert.equal(hash(bytes),item.sha256);assert.equal(bytes.length,item.bytes);
        report.downloads[role]={file:item.file,bytes:bytes.length,sha256:hash(bytes)};
      }
      await page.close();
    }
    assert.deepEqual(report.errors,[]);report.passed=true;
  } finally {
    await browser.close();fs.writeFileSync(path.join(output,'viewer.json'),JSON.stringify(report,null,2)+'\n');
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
