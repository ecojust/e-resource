// Run with MODEL_BASE_URL pointing to the Shanghai project root.
const fs = require('node:fs');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const output = process.argv[2];
if (!output) throw new Error('Pass a JSON audit output path');
(async () => {
  const browser = await chromium.launch({executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
  try {
    // Keep the site origin and load its actual unmodified Three / clipping modules.
    await page.route('**/macro-texture-test',r=>r.fulfill({contentType:'text/html',body:'<link rel="icon" href="data:,">'}));
    await page.goto(new URL('macro-texture-test',base).href);
    const moduleURL=new URL('src/candidate-city-clipping.js',base).href;
    const bytes=await (await page.request.get(moduleURL)).body();
    const result = await page.evaluate(async () => {
      const T=await import('./vendor/three.module.js');
      const {CandidateCityClipper}=await import('./src/candidate-city-clipping.js');
      const renderer=new T.WebGLRenderer({antialias:false});
      const target=new T.WebGLRenderTarget(160,64);
      const scene=new T.Scene();
      const camera=new T.OrthographicCamera(-5,5,2,-2,.1,50);
      camera.position.set(0,10,0);camera.up.set(0,0,-1);camera.lookAt(0,0,0);
      const clipper=new CandidateCityClipper({THREE:T,geographicPosition:(x,z)=>new T.Vector3(x,0,z)});
      const probes=[[-2.5,0],[-1.5,0],[1.5,0],[2.5,0]];
      const owners=[{macro_id:'a',feature_local_id:17},{macro_id:'b',feature_local_id:29}];
      const geometries=[],materials=[];
      const rect=(x,owner)=>({owner,geometry:{type:'Polygon',coordinates:[[[x,-1.1],[x+.97,-1.1],[x+.97,1.1],[x,1.1],[x,-1.1]]]}});
      const padding=Array.from({length:318},(_,i)=>{
        const x=100+3*i;
        return {owner:owners[0],geometry:{type:'Polygon',coordinates:[[[x,10],[x+1,10],[x,11],[x,10]]]}};
      });
      function paint() {
        renderer.setRenderTarget(target);renderer.render(scene,camera);
        return probes.map(([x,z])=>{
          const p=new Uint8Array(4);
          renderer.readRenderTargetPixels(target,Math.floor((x+5)*16),Math.floor((2-z)*16),1,1,p);
          return p[1]>150;
        });
      }
      const variants={};
      for(const variant of ['far','near']){
        const groups=owners.map((owner,i)=>{
          const group=new T.Group(),geometry=new T.PlaneGeometry(2,2);
          geometry.rotateX(-Math.PI/2);geometries.push(geometry);
          if(variant==='far')geometry.setAttribute('_feature_id_0',new T.Float32BufferAttribute(new Array(4).fill(owner.feature_local_id),1));
          const material=new T.MeshBasicMaterial({color:0x00ff00});materials.push(material);
          group.add(new T.Mesh(geometry,material));group.position.x=i?2:-2;scene.add(group);
          const record=variant==='far'?{id:owner.macro_id}:{id:owner.macro_id+'-near',parent:{id:owner.macro_id},ids:[owner.feature_local_id]};
          clipper.bindObject(group,record);return group;
        });
        clipper.update([]);const before=paint();
        clipper.update([...padding,rect(-3.01,owners[0]),rect(2.04,owners[1])]);
        const active=paint(),{triangles,macroTextures,triangleLimit}=clipper.getState();
        clipper.update([rect(-3.01,owners[0])]);const reduced=paint();
        clipper.update([]);const restored=paint();
        variants[variant]={before,active,reduced,restored,triangles,macroTextures,triangleLimit};
        for(const group of groups){clipper.releaseObject(group);group.removeFromParent();}
      }
      const gl=renderer.getContext();const glError=gl.getError();const contextLost=gl.isContextLost();
      clipper.dispose();for(const g of geometries)g.dispose();for(const m of materials)m.dispose();
      target.dispose();renderer.dispose();
      return {variants,glError,contextLost};
    });
    for(const v of Object.values(result.variants)){
      assert.deepEqual(v.before,[true,true,true,true]);
      assert.deepEqual(v.active,[false,true,true,false]);
      assert.deepEqual(v.reduced,[false,true,true,true]);
      assert.deepEqual(v.restored,v.before);
      assert.equal(v.triangles,322);assert.equal(v.macroTextures,2);assert.equal(v.triangleLimit,320);
    }
    assert.equal(result.glError,0);assert.equal(result.contextLost,false);assert.deepEqual(errors,[]);
    fs.writeFileSync(output,JSON.stringify({...result,passed:true,browser:browser.version(),base,checked_at_utc:new Date().toISOString(),
      module_sha256:createHash('sha256').update(bytes).digest('hex'),
      checker_sha256:createHash('sha256').update(fs.readFileSync(__filename)).digest('hex')},null,2)+'\n');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
