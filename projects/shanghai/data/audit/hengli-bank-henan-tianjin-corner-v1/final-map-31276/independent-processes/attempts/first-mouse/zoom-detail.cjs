const fs=require('node:fs');
const path=require('node:path');
const id='huangpu-hengli-bank-henan-tianjin-corner';
const endpoint='http://127.0.0.1:19476';
const dir=process.argv[2];
const out=path.join(dir,'zoom-input.json');
const delay=ms=>new Promise(res=>setTimeout(res,ms));
(async()=>{
 const tab=(await(await fetch(endpoint+'/json/list')).json()).find(t=>t.type==='page');
 const s=new WebSocket(tab.webSocketDebuggerUrl); const promises=new Map();let seq=0;
 await new Promise((res,rej)=>{s.onopen=res;s.onerror=rej;});
 s.onmessage=e=>{const j=JSON.parse(e.data);if(!j.id)return;const [ok,no]=promises.get(j.id);promises.delete(j.id);if(j.error)no(Error(j.error.message));else ok(j.result);};
 const rpc=(method,params)=>new Promise((ok,no)=>{const id=++seq;promises.set(id,[ok,no]);s.send(JSON.stringify({id,method,params}));});
 const status=async()=>{const r=await rpc('Runtime.evaluate',{expression:`(()=>{const a=window.__SHANGHAI_APP__,m=a.scene.map,d=a.scene.getStreamingState().detail.active.map(x=>x.id),z=document.querySelector('#zoom-in'),b=z.getBoundingClientRect(),x=b.x+b.width/2,y=b.y+b.height/2;return{selected:new URLSearchParams(location.hash.slice(1)).get('landmark'),zoom:m.getZoom(),center:m.getCenter(),detail:d,button:{x,y,hit:document.elementFromPoint(x,y)?.closest('button')?.id}};})()`,returnByValue:true});return r.result.value;};
 const rec={control:'拉近视角',device:'mouse',started:new Date().toISOString(),inputs:[]};const save=()=>fs.writeFileSync(out,JSON.stringify(rec,null,2)+'\n');rec.before=await status();save();
 if(rec.before.selected!==id||rec.before.zoom>18)throw Error('Unexpected starting selection or scale');
 for(let n=0;n<3;n++){const state=await status();if(state.zoom>=18.5||state.detail.includes('14-13720-6694/14-13720-6694-1_-5-s1'))break;const {x,y,hit}=state.button;if(hit!=='zoom-in')throw Error('Zoom control is covered');for(const type of ['mousePressed','mouseReleased'])await rpc('Input.dispatchMouseEvent',{type,x,y,button:'left',buttons:type==='mousePressed'?1:0,clickCount:1});await delay(750);rec.inputs.push({x,y,after:await status()});save();}
 rec.finished=new Date().toISOString();rec.after=await status();save();s.close();if(rec.after.selected!==id||!rec.inputs.length||rec.after.zoom<=rec.before.zoom)throw Error('Zoom input did not take effect');
})().catch(e=>{console.error(e);process.exitCode=1;});
