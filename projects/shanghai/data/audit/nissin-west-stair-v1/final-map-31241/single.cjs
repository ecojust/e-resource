/* Isolated model inspection. The two QA-only documents are supplied by this
   harness. All model bytes, Three.js and the mesh decoder come from the real
   signed release origin. The public directory links to the city walk. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
module.exports=async function({page,phase,exact,home,out,R,save,hash}){
 const prefix='/__private_review_241__/',modelURL=k=>exact.origin+exact.assets[k].path;
 const markup='<!doctype html><meta name="viewport" content="width=device-width, initial-scale=1"><title>日清大楼独立模型检查</title><style>html,body{margin:0;background:#dae1e6}canvas{display:block;width:100%;height:85vh}nav{display:flex;gap:12px;flex-wrap:wrap;font:14px sans-serif;margin:.6rem}button{padding:.35rem}</style><canvas></canvas><nav><button data-level="full">网页近景</button><button data-level="lod">网页远景</button>'+['raw','full','lod','native'].map(k=>'<a data-file="'+k+'" href="'+modelURL(k)+'" download="'+path.basename(exact.assets[k].path)+'">'+k+'</a>').join('')+'</nav><script type="importmap">'+JSON.stringify({imports:{three:exact.origin+'vendor/three.module.js'}})+'</script><script type="module" src="'+prefix+'viewer.mjs"></script>';
 const script="import * as T from 'three';import {GLTFLoader} from '/vendor/GLTFLoader.js';import {MeshoptDecoder} from '/vendor/meshopt_decoder.module.js';const urls="+JSON.stringify({full:modelURL('full'),lod:modelURL('lod')})+";"+String.raw`
 const canvas=document.querySelector('canvas'),renderer=new T.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});
 renderer.outputColorSpace=T.SRGBColorSpace;renderer.setPixelRatio(1);renderer.setSize(canvas.clientWidth,canvas.clientHeight,false);
 const scene=new T.Scene();scene.background=new T.Color(0xdce2e7);const light=new T.HemisphereLight(0xfff9f0,0x778495,2);scene.add(light);
 const sun=new T.DirectionalLight(0xfff3df,2.5);sun.position.set(-60,85,-70);scene.add(sun);
 const camera=new T.PerspectiveCamera(36,canvas.clientWidth/canvas.clientHeight,.05,850),loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
 let mesh=null;let busy=false;
 async function load(k){if(busy)return;busy=true;window.individual=undefined;try{
   let gltf=await loader.loadAsync(urls[k]);if(mesh)scene.remove(mesh);mesh=gltf.scene;scene.add(mesh);
   const bounds=new T.Box3().setFromObject(mesh),c=bounds.getCenter(new T.Vector3()),size=bounds.getSize(new T.Vector3());
   const fit=Math.max(size.length()*.90,size.length()*.95/camera.aspect);camera.position.copy(c).add(new T.Vector3(-.76,.55,.80).normalize().multiplyScalar(fit));
   camera.lookAt(c);camera.updateProjectionMatrix();renderer.render(scene,camera);
   let triangles=0;mesh.traverse(o=>{if(o.isMesh)triangles+=(o.geometry.index?.count??o.geometry.attributes.position.count)/3});
   window.individual={role:k,triangles,renderer:renderer.getContext().getParameter(renderer.getContext().RENDERER),glError:renderer.getContext().getError(),lost:renderer.getContext().isContextLost(),bounds:[bounds.min.toArray(),bounds.max.toArray()]};
 }catch(e){window.individualError=String(e);throw e}finally{busy=false}}
 document.querySelectorAll('[data-level]').forEach(b=>b.onclick=()=>load(b.dataset.level));load('full');`;
 await page.route('**'+prefix+'inspection.html',r=>r.fulfill({contentType:'text/html',body:markup}));await page.route('**'+prefix+'viewer.mjs',r=>r.fulfill({contentType:'text/javascript',body:script}));
 await page.goto(exact.origin+prefix+'inspection.html',{waitUntil:'domcontentloaded'});
 R.isolatedPage={public_route:false,driver_sha256:hash(fs.readFileSync(__filename)),source_site:exact.origin,html_sha256:hash(markup),module_sha256:hash(script),downloads:{}};
 for(const role of ['full','lod']){
  if(role==='lod'){const lodButton=page.locator('button[data-level="lod"]');if(phase==='standalone-phone')await lodButton.tap();else await lodButton.click();}
  await page.waitForFunction(k=>window.individual?.role===k||window.individualError,role,{polling:200,timeout:150000});
  const s=await page.evaluate(()=>({state:window.individual,error:window.individualError}));assert(!s.error);assert.equal(s.state.glError,0);assert.equal(s.state.lost,false);
  assert.equal(s.state.triangles,role==='full'?exact.row.triangles:exact.row.lod_triangles);
  const name=phase+'-'+role+'.png',b=await page.screenshot({path:path.join(out,name)});R.screenshots.push({file:name,sha256:hash(b),bytes:b.length});R.isolatedPage[role]=s.state;save();
 }
 if(phase==='standalone-desktop'){
  for(const k of ['raw','full','lod','native']){
   const item=exact.assets[k],wait=page.waitForEvent('download');await page.locator('a[data-file="'+k+'"]').click();const down=await wait;
   assert.equal(down.suggestedFilename(),path.basename(item.path));
   const file=path.join(process.env.TMPDIR,'verify-'+path.basename(item.path));await down.saveAs(file);
   assert.equal(await down.failure(),null);
   const d=crypto.createHash('sha256');for await (const chunk of fs.createReadStream(file))d.update(chunk);
   assert.equal(d.digest('hex'),item.sha256);assert.equal(fs.statSync(file).size,item.bytes);assert.equal(down.url(),modelURL(k));
   R.isolatedPage.downloads[k]={file:path.basename(file),url:down.url(),suggested:down.suggestedFilename(),bytes:item.bytes,sha256:item.sha256,saved_and_reread:true,saveAsVerified:true,download_failure:null};fs.unlinkSync(file);await down.delete();save();
  }
 }
};
