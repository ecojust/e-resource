// Exercise the three named views, both mesh variants and the four download links.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const assert = require('node:assert/strict');
const root = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(__dirname,'../../..');
const folder = 'assets/models/candidates/huangpu-gibb-livingston-corner/';
const manifest = JSON.parse(fs.readFileSync(path.join(root,folder,'manifest.json')));
const base = 'http://127.0.0.1:31237/';
const descriptor = JSON.parse(fs.readFileSync(process.env.SIGNED_INPUTS))['237'].fetched;
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
      const copy=await page.evaluate(()=>({title:document.title,heading:document.querySelector('h1')?.textContent.trim(),eyebrow:document.querySelector('.eyebrow')?.textContent.trim(),scope:document.querySelector('p.scope')?.textContent.trim(),poseLabels:[...document.querySelectorAll('[data-view]')].map(b=>b.textContent.trim())}));
      assert.equal(copy.title, "仁记洋行大楼东南转角与相连街墙");
      assert.equal(copy.heading, "仁记洋行大楼");
      assert.equal(copy.eyebrow, "黄浦区 · 滇池路100–110号");
      assert.equal(copy.scope, "2007年和2017年街照可见红砖贴柱、弧形阳台与顶部鼓座。1908年出版的旧照另见锥形尖顶。柱距、窗宽与高度据照片估计。");
      assert.deepEqual(copy.poseLabels,["正看滇池路街墙", "斜看圆角与阳台", "俯看鼓座"]);
      (report.scope_copy??={})[device]=copy;
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
          const expected=JSON.parse(fs.readFileSync(path.join(root,'data/audit/gibb-livingston-corner-v1/geometry-native.json'))).surface_sha256[role];
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
        const res=await url,bytes=await res.body();assert.ok(res.ok());assert.equal(hash(bytes),descriptor[name].sha256);assert.equal(bytes.length,descriptor[name].bytes);
        report.files[name]={sha256:hash(bytes),bytes:bytes.length};
      }
      if(!mobile)for(const [role,label]of Object.entries({raw:'原始',full:'网页',lod:'远景',native:'Blender'})){
        const item=manifest.assets[role],anchor=page.locator('#downloads a').filter({hasText:label});
        const [download]=await Promise.all([page.waitForEvent('download'),anchor.click()]);const saved=path.join('saved-downloads',item.file); fs.mkdirSync(path.join(output,'saved-downloads'),{recursive:true}); await download.saveAs(path.join(output,saved)); const bytes=fs.readFileSync(path.join(output,saved));
        assert.equal(download.suggestedFilename(),item.file);assert.equal(hash(bytes),item.sha256);assert.equal(bytes.length,item.bytes);
        report.downloads[role]={file:item.file,saved,saveAsVerified:true,bytes:bytes.length,sha256:hash(bytes)};
      }
      await page.close();
    }
    assert.deepEqual(report.errors,[]);report.passed=true;
  } finally {
    await browser.close();fs.writeFileSync(path.join(output,'viewer.json'),JSON.stringify(report,null,2)+'\n');
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
