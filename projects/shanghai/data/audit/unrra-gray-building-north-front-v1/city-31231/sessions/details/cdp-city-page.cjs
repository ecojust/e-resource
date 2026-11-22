/* The city test can use a single Chrome DevTools connection on memory-limited
 * workstations. Every action still goes to Chromium's live document or input
 * domain, and every resource receipt uses the production site's real HTTP. */
const fs=require('node:fs');
const path=require('node:path');
const {spawn}=require('node:child_process');
const timers=require('node:timers/promises');
const http=require('node:http');
const https=require('node:https');
async function fetchBytes(url){
  return new Promise((resolve,reject)=>{
    const transport=new URL(url).protocol==='https:'?https:http;
    const request=transport.get(url,response=>{
      const chunks=[];response.on('data',x=>chunks.push(x));
      response.on('error',reject);response.on('end',()=>resolve({code:response.statusCode,body:Buffer.concat(chunks)}));
    });request.on('error',reject);
  });
}
class Devtools {
  constructor(ws) {
    this.ws=ws;this.next=0;this.pending=new Map();this.events=new Map();this.disconnected=false;
    ws.addEventListener('message',event=>{
      const row=JSON.parse(event.data);
      if(row.id){const wait=this.pending.get(row.id);if(!wait)return;this.pending.delete(row.id);
        if(row.error)wait.reject(Error(row.error.message));else wait.resolve(row.result);return;}
      for(const fn of this.events.get(row.method)||[])fn(row.params);
    });
    ws.addEventListener('close',()=>{
      this.disconnected=true;
      for(const back of this.pending.values())back.reject(Error('DevTools target closed'));
      this.pending.clear();
    });
  }
  on(name,fn){if(!this.events.has(name))this.events.set(name,[]);this.events.get(name).push(fn);}
  send(method,params={}){
    if(this.disconnected)return Promise.reject(Error('DevTools target closed'));
    return new Promise((resolve,reject)=>{const id=++this.next;this.pending.set(id,{resolve,reject});
      this.ws.send(JSON.stringify({id,method,params}));});
  }
}
async function connect(url){
  const ws=new WebSocket(url);
  await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
  return new Devtools(ws);
}
class CityPage {
  constructor(rpc,spec){
    this.rpc=rpc;this.spec=spec;this.deadline=180000;this.request={get:async url=>{
      const response=await fetchBytes(url);return {status:()=>response.code,body:async()=>response.body,dispose:async()=>{}};
    }};
    this.mouse={click:(x,y)=>this.pointer(x,y,false)};this.touchscreen={tap:(x,y)=>this.pointer(x,y,true)};
  }
  setDefaultTimeout(ms){this.deadline=ms;}
  context(){return {newCDPSession:async()=>({send:(cmd,params)=>this.rpc.send(cmd,params),detach:async()=>{}})};}
  async setViewportSize({width,height}){
    return this.rpc.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:this.spec.deviceScaleFactor,mobile:false});
  }
  async goto(url){
    const response=await this.rpc.send('Page.navigate',{url});
    if(response.errorText)throw Error(response.errorText);
    await this.waitForFunction(u=>location.href===u&&document.readyState!=='loading',url);
  }
  async waitForURL(predicate){
    const end=Date.now()+this.deadline;
    while(Date.now()<end){try{const href=await this.evaluate(()=>location.href);if(predicate(new URL(href)))return;}catch(e){if(this.rpc.disconnected)throw e;}
      await timers.setTimeout(90);}
    throw Error('Navigation timed out');
  }
  async evaluate(fn,arg){
    const r=await this.rpc.send('Runtime.evaluate',{expression:'('+fn.toString()+')('+(arg===undefined?'undefined':JSON.stringify(arg))+')',returnByValue:true,awaitPromise:true});
    if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);
    return r.result.value;
  }
  async waitForFunction(fn,arg,opts={}){
    const until=Date.now()+(opts.timeout||this.deadline);
    while(Date.now()<until){
      try{if(await this.evaluate(fn,arg))return;}catch(e){if(this.rpc.disconnected||!String(e).includes('context'))throw e;}
      await timers.setTimeout(opts.polling||250);
    }
    throw Error('Timed out in live browser predicate '+fn.toString().slice(0,180));
  }
  async pointer(x,y,touch){
    if(touch){await this.rpc.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
      return this.rpc.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});}
    await this.rpc.send('Input.dispatchMouseEvent',{type:'mouseMoved',x,y});
    await this.rpc.send('Input.dispatchMouseEvent',{type:'mousePressed',x,y,button:'left',clickCount:1});
    return this.rpc.send('Input.dispatchMouseEvent',{type:'mouseReleased',x,y,button:'left',clickCount:1});
  }
  locator(selector){
    const me=this;
    async function physicalClick(touch){
      const how=await me.evaluate(s=>{const el=document.querySelector(s);if(!el)return false;el.scrollIntoView({block:'center',inline:'nearest'});return true;},selector);
      if(!how)throw Error('Missing input '+selector);
      await me.waitForFunction(s=>{const el=document.querySelector(s);if(!el)return false;const b=el.getBoundingClientRect();
        const at=document.elementFromPoint(b.x+b.width/2,b.y+b.height/2);return b.width>0&&b.height>0&&(at===el||el.contains(at));},selector);
      const p=await me.evaluate(s=>{const b=document.querySelector(s).getBoundingClientRect();return [b.x+b.width/2,b.y+b.height/2];},selector);
      return me.pointer(...p,touch);
    }
    return {count:()=>me.evaluate(s=>document.querySelectorAll(s).length,selector),click:()=>physicalClick(false),tap:()=>physicalClick(true),
      getAttribute:key=>me.evaluate(([s,k])=>document.querySelector(s)?.getAttribute(k),[selector,key]),
      innerText:()=>me.evaluate(s=>document.querySelector(s).innerText,selector),
      waitFor:()=>me.waitForFunction(s=>{const e=document.querySelector(s);return e&&e.getBoundingClientRect().width>0&&getComputedStyle(e).visibility==='visible';},selector),
      locator:child=>me.locator(selector+' '+child)};
  }
  on(name,handler){
    const rpc=this.rpc;
    if(name==='pageerror')rpc.on('Runtime.exceptionThrown',p=>handler(Error(p.exceptionDetails.exception?.description||p.exceptionDetails.text)));
    if(name==='console')rpc.on('Runtime.consoleAPICalled',p=>handler({type:()=>p.type,text:()=>p.args.map(a=>a.value??a.description).join(' '),location:()=>({url:p.stackTrace?.callFrames?.[0]?.url||''})}));
    if(name==='response')rpc.on('Network.responseReceived',p=>handler({url:()=>p.response.url,status:()=>p.response.status}));
    if(name==='requestfailed'){
      const pending=new Map();rpc.on('Network.requestWillBeSent',p=>pending.set(p.requestId,p.request.url));
      rpc.on('Network.loadingFinished',p=>pending.delete(p.requestId));
      rpc.on('Network.loadingFailed',p=>{const url=pending.get(p.requestId);pending.delete(p.requestId);handler({url:()=>url,failure:()=>({errorText:p.errorText})});});
    }
  }
}
exports.chromium={launch:async options=>{
  const port=process.env.QA_CDP_PORT;const tmp=fs.mkdtempSync(path.join(process.env.TMPDIR,'cdp-'));
  const child=spawn(options.executablePath,['--headless=new','--no-first-run','--no-default-browser-check','--disable-component-update','--disable-sync','--disable-popup-blocking','--password-store=basic','--noerrdialogs','--user-data-dir='+tmp,...options.args,'about:blank'],{stdio:'ignore'});
  const exit=new Promise(resolve=>child.once('exit',(code,signal)=>resolve({code,signal})));
  let info,target;
  try {
    for(let i=0;i<140;i++){if(child.exitCode!==null)throw Error('Chromium launch failed');
      try{info=JSON.parse((await fetchBytes('http://127.0.0.1:'+port+'/json/version')).body);
      target=JSON.parse((await fetchBytes('http://127.0.0.1:'+port+'/json/list')).body).find(t=>t.type==='page');if(target)break;}catch{}
      await timers.setTimeout(75);}
    if(!target)throw Error('No live page');
    const rpc=await connect(target.webSocketDebuggerUrl);
    let monitoring=false, last=0;
    const memoryTimer=setInterval(async()=>{
      if(monitoring||rpc.disconnected||Date.now()-last<5500)return;
      try {
        const rss=Number(fs.readFileSync('/proc/'+child.pid+'/status','utf8').match(/^VmRSS:\s+(\d+)/m)[1])*1024;
        const current=Number(fs.readFileSync('/sys/fs/cgroup/memory.current','utf8'));
        const maximum=Number(fs.readFileSync('/sys/fs/cgroup/memory.max','utf8'));
        if(rss>465*1024*1024 && maximum-current<190*1024*1024){
          monitoring=true;last=Date.now();
          await rpc.send('Memory.simulatePressureNotification',{level:'moderate'});
          await rpc.send('HeapProfiler.collectGarbage');
          process.stdout.write('[physical-memory] '+JSON.stringify({rss,current,maximum})+'\n');
        }
      } catch(error){} finally{monitoring=false;}
    },1150);
    memoryTimer.unref();
    return {version:()=>info.Browser.split('/').pop(),newPage:async spec=>{
      await rpc.send('Page.enable');await rpc.send('Runtime.enable');await rpc.send('Network.enable',{maxTotalBufferSize:0,maxResourceBufferSize:0});
      const p=new CityPage(rpc,spec);await p.setViewportSize(spec.viewport);
      await rpc.send('Emulation.setTouchEmulationEnabled',{enabled:!!spec.hasTouch,maxTouchPoints:1});return p;
    },close:async()=>{
      clearInterval(memoryTimer);if(!rpc.disconnected)await rpc.send('Browser.close').catch(()=>{});
      await Promise.race([exit,timers.setTimeout(2500)]);if(child.exitCode===null&&child.signalCode===null){child.kill('SIGTERM');await exit;}
      if(!rpc.disconnected)rpc.ws.close();
    }};
  }catch(err){child.kill('SIGTERM');await exit;throw err;}
}};
