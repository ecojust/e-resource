/* Exercise the public minus control when the initial 440px far camera remains inside the annex LOD threshold. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const out=path.join(__dirname,'distant-public-zoom.json'),id='xuhui-wukang-mansion-east-annex';
(async()=>{
 const target=(await(await fetch('http://127.0.0.1:19699/json/list')).json()).find(t=>t.type==='page'&&t.url.includes('31199/index.html'));
 assert(target);const sock=new WebSocket(target.webSocketDebuggerUrl);await new Promise((ok,fail)=>{sock.onopen=ok;sock.onerror=fail;});
 let seq=0;const replies=new Map();sock.onmessage=({data})=>{const m=JSON.parse(data);if(replies.has(m.id)){replies.get(m.id)(m);replies.delete(m.id);}};
 const call=(method,params={})=>new Promise((ok,fail)=>{const i=++seq;replies.set(i,r=>r.error?fail(Error(r.error.message)):ok(r.result));sock.send(JSON.stringify({id:i,method,params}));});
 const evalPage=async expression=>(await call('Runtime.evaluate',{expression,returnByValue:true})).result.value;
 const snapshot=()=>evalPage(`(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,a=s.getLandmarkAssetState('${id}'),eye=m.transform.getCameraLngLat(),alt=m.transform.getCameraAltitude(),b=document.querySelector('#zoom-out'),r=b.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {url:location.href,viewport:[innerWidth,innerHeight],zoom:m.getZoom(),eye:[eye.lng,eye.lat,alt],variant:a.variant,model:a.verifiedAsset,control:{id:b.id,x,y,visible:document.elementFromPoint(x,y)===b||b.contains(document.elementFromPoint(x,y))}};})()`);
 const prior=await snapshot();assert.deepEqual(prior.viewport,[440,380]);assert.equal(prior.url,'http://127.0.0.1:31199/index.html#landmark='+id+'&mode=overview');assert.equal(prior.variant,'full');assert.equal(prior.zoom,15.5);assert(prior.control.visible);
 const action={order:199,before:prior,script_sha256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),button:'zoom-out',started:new Date().toISOString(),invoked:false};
 fs.writeFileSync(out,JSON.stringify(action,null,2)+'\n');
 const {x,y}=prior.control;await call('Input.dispatchMouseEvent',{type:'mousePressed',x,y,button:'left',buttons:1,clickCount:1});await call('Input.dispatchMouseEvent',{type:'mouseReleased',x,y,button:'left',buttons:0,clickCount:1});action.invoked=true;fs.writeFileSync(out,JSON.stringify(action,null,2)+'\n');
 for(let i=0;i<25;i++){await new Promise(r=>setTimeout(r,400));const observed=await snapshot();if(observed.variant==='distant'){action.after=observed;break;}}
 assert.equal(action.after?.model?.variant,'lod');action.finished=new Date().toISOString();fs.writeFileSync(out,JSON.stringify(action,null,2)+'\n');sock.close();console.log('Real zoom-out',prior.zoom,action.after.zoom,action.after.model.sha256);
})().catch(e=>{console.error(e);process.exit(1);});
