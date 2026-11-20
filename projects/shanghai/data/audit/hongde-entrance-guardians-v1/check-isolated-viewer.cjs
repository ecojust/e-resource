/* Compare published V8 and revised complete GLBs through real WebGL + Meshopt.
 * Usage: node check-isolated-viewer.cjs PROJECT MANIFEST OLD_WEB OLD_LOD OUT */
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {createHash}=require('node:crypto');
const assert=require('node:assert/strict');
const [project,manifest,oldWeb,oldLod,out]=process.argv.slice(2).map(x=>path.resolve(x));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const m=JSON.parse(fs.readFileSync(manifest));
const assetFiles=new Map();
const resources={};
for(const [key,file,digest,triangles] of [
    ['before-full',oldWeb,'d8007acbfe2344684e3e05c22cd9f35001b8d71e1833c2d06eeff62f75b11721',378504],
    ['before-lod',oldLod,'c6d7af387f745102702bdf0f2349a2b26a0129d1cfab86ca49b2c455794e0a75',178968],
    ['after-full',path.join(project,m.assets.full.file),m.assets.full.sha256,m.assets.full.triangles],
    ['after-lod',path.join(project,m.assets.lod.file),m.assets.lod.sha256,m.assets.lod.triangles]]) {
  const bytes=fs.statSync(file).size;
  assert.equal(hash(fs.readFileSync(file)),digest);
  assetFiles.set('/'+key+'.glb',file);
  resources[key]={bytes,sha256:digest,triangles};
}
const html=`<!doctype html><meta charset="utf-8"><title>Hongde Church entrance guardians</title>
<style>*{margin:0;padding:0}canvas{display:block}</style>
<script type="importmap">{"imports":{"three":"/vendor/three.module.js"}}</script>
<canvas></canvas><script type="module">
import * as T from '/vendor/three.module.js';
import {GLTFLoader} from '/vendor/GLTFLoader.js';
import {MeshoptDecoder} from '/vendor/meshopt_decoder.module.js';
const renderer = new T.WebGLRenderer({canvas:document.querySelector('canvas'),antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(1);renderer.setSize(innerWidth,innerHeight);
renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;
const scene=new T.Scene();scene.background=new T.Color(0xa5afb5);
scene.add(new T.HemisphereLight(0xfff6e7,0x787b80,1.45));
const sun=new T.DirectionalLight(0xfff0dc,2.33);sun.position.set(12,26,-27);scene.add(sun);
const camera=new T.OrthographicCamera(-1,1,1,-1,.05,360);
const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
let currentModel,receipt;
window.show=async function(key,pose) {
  if(!receipt||receipt.key!==key) {
    if(currentModel){scene.remove(currentModel);currentModel.traverse(n=>{if(n.isMesh){n.geometry.dispose();[].concat(n.material).forEach(q=>q.dispose());}});}
    const res=await fetch('/'+key+'.glb',{cache:'no-store'});if(!res.ok)throw Error('GLB HTTP '+res.status);
    const bytes=await res.arrayBuffer(),digest=await crypto.subtle.digest('SHA-256',bytes);
    currentModel=(await loader.parseAsync(bytes,'/')).scene;scene.add(currentModel);
    let triangles=0;currentModel.traverse(n=>{if(n.isMesh)triangles+=(n.geometry.index?.count||n.geometry.attributes.position.count)/3;});
    receipt={key,bytes:bytes.byteLength,sha256:[...new Uint8Array(digest)].map(q=>q.toString(16).padStart(2,'0')).join(''),triangles};
  }
  const detail=pose==='door',lion=pose==='east-lion', scale=lion?1.22:detail?5.85:38;
  camera.left=-scale/2;camera.right=scale/2;camera.top=scale/2*innerHeight/innerWidth;camera.bottom=-camera.top;
  const target=lion?new T.Vector3(3.414,1.27,-15.41):detail?new T.Vector3(1.47,1.22,-15.6):new T.Vector3(1.21,10.45,-4.7);
  camera.position.copy(target).add(lion?new T.Vector3(2.3,.74,-4.6):detail?new T.Vector3(1.98,.91,-10):new T.Vector3(15,6,-44));
  camera.lookAt(target);camera.updateProjectionMatrix();scene.updateMatrixWorld(true);
  await new Promise(requestAnimationFrame);renderer.render(scene,camera);
  await new Promise(requestAnimationFrame);renderer.render(scene,camera);
  return {...receipt,pose,glError:renderer.getContext().getError(),contextLost:renderer.getContext().isContextLost(),
          drawnTriangles:renderer.info.render.triangles,camera:camera.position.toArray(),target:target.toArray(),orthoWidth:scale};
};
</script>`;
async function main() {
  const server=http.createServer((req,res)=>{
    const route=new URL(req.url,'http://localhost').pathname;
    if(route==='/'){res.setHeader('Content-Type','text/html; charset=utf-8');return res.end(html);}
    let file=assetFiles.get(route);
    if(!file&&/^\/vendor\/(three\.(core|module)|GLTFLoader|meshopt_decoder\.module|BufferGeometryUtils)\.js$/.test(route))file=path.join(project,route);
    if(!file||!fs.existsSync(file)){res.writeHead(404);return res.end();}
    res.writeHead(200,{'Content-Type':file.endsWith('.js')?'text/javascript':'model/gltf-binary','Content-Length':fs.statSync(file).size,'Cache-Control':'no-store'});
    fs.createReadStream(file).pipe(res);
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',
    args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  fs.mkdirSync(out,{recursive:true});
  const result={model:m.id,revision:m.revision,manifest_sha256:hash(fs.readFileSync(manifest)),
    driver_sha256:hash(fs.readFileSync(__filename)),browser:browser.version(),views:[],errors:[],passed:false};
  try {
    const page=await browser.newPage({viewport:{width:816,height:624},deviceScaleFactor:1});
    page.on('pageerror',e=>result.errors.push(e.message));
    await page.goto('http://127.0.0.1:'+server.address().port+'/');
    await page.waitForFunction(()=>typeof window.show==='function',{},{timeout:30000});
    for(const [key,pose] of [['before-full','door'],['after-full','door'],['after-full','east-lion'],['after-full','whole'],['before-lod','door'],['after-lod','door']]) {
      const view=await page.evaluate(([k,p])=>window.show(k,p),[key,pose]);
      const expected=resources[key];for(const field of ['bytes','sha256','triangles'])assert.equal(view[field],expected[field]);
      assert.equal(view.glError,0);assert.equal(view.contextLost,false);assert.ok(view.drawnTriangles>0);
      const file='webgl-'+key+'-'+pose+'.png';
      const png=await page.screenshot({path:path.join(out,file),timeout:120000});
      result.views.push({...view,file,image_bytes:png.length,image_sha256:hash(png)});
    }
    assert.equal(result.errors.length,0);result.passed=true;
  } finally {
    await browser.close();server.closeAllConnections();server.close();
    fs.writeFileSync(path.join(out,'isolated-browser.json'),JSON.stringify(result,null,2)+'\n');
  }
}
main().catch(e=>{console.error(e);process.exitCode=1;});
