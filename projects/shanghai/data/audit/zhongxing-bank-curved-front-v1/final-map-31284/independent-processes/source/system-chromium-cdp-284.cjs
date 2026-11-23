/* A direct Chromium DevTools client for the existing city photography and hit tests. */
'use strict';
const fs = require('node:fs');
const http = require('node:http');
const WebSocket = globalThis.WebSocket;
const path = require('node:path');
const {once} = require('node:events');
const {spawn} = require('node:child_process');
const {setTimeout: wait} = require('node:timers/promises');
const events = require('node:events');
function httpGet(url) {
  return new Promise((resolve,reject)=>{
    const request=http.get(url,r=>{const chunks=[];r.on('error',reject);r.on('data',b=>chunks.push(b));r.on('end',()=>resolve({status:()=>r.statusCode,body:async()=>Buffer.concat(chunks)}));});request.on('error',reject);
  });
}
async function endpoint(url){
  const socket=new WebSocket(url),pending=new Map(),emitter=new events.EventEmitter();let serial=0;
  await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',event=>reject(event.error??new Error('DevTools handshake failed')),{once:true});});socket.onmessage=e=>{
    const d=JSON.parse(e.data);if(d.id){const item=pending.get(d.id);if(!item)return;pending.delete(d.id);if(d.error)item.reject(new Error(d.error.message));else item.resolve(d.result);}
    else emitter.emit(d.method,d.params);
  };
  socket.onclose=()=>{for(const item of pending.values())item.reject(new Error('Chromium closed the DevTools connection'));pending.clear();};
  return {emitter,send(method,params={}){return new Promise((resolve,reject)=>{if(socket.readyState!==1){reject(new Error('Chromium is closed'));return;}const id=++serial;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});},detach:async()=>{},finish:()=>socket.close()};
}
async function launch(options){
  const dir=fs.mkdtempSync(path.join(process.env.TMPDIR,'c-')),port=Number(process.env.QA_CDP_PORT);
  const log=fs.openSync(path.join(process.env.QA_OUTPUT_DIR,'chromium-direct.log'),'a');
  const proc=spawn(options.executablePath,[...options.args,'--test-type','--disable-infobars','--no-first-run','--no-default-browser-check','--disable-extensions','--disable-breakpad','--disable-translate','--user-data-dir='+dir,'about:blank'],{env:options.env||process.env,stdio:['ignore',log,log]});fs.closeSync(log);
  let info;
  for(let i=0;i<130;i++){if(proc.exitCode!==null)throw new Error('Chromium startup exit '+proc.exitCode);try{info=JSON.parse((await(await httpGet('http://127.0.0.1:'+port+'/json/version')).body()));break;}catch{await wait(100);}}
  if(!info)throw new Error('Chromium DevTools endpoint did not open');
  const browser=await endpoint(info.webSocketDebuggerUrl);let tab;
  const instance={version:()=>info.Browser,newBrowserCDPSession:async()=>browser,close:async()=>{
    const exited=proc.exitCode===null&&proc.signalCode===null?once(proc,'exit'):Promise.resolve();
    try{await browser.send('Browser.close');}catch{}await exited;if(tab)tab.finish();browser.finish();
  },newPage:async(opts)=>{
    const tabs=JSON.parse((await(await httpGet('http://127.0.0.1:'+port+'/json/list')).body()));const target=tabs.find(t=>t.type==='page');
    tab=await endpoint(target.webSocketDebuggerUrl);const c=tab;const active=new Map(),bodies=new Map(),em=new events.EventEmitter();const routes=[];let current=opts.viewport,timeout=180000;
    for(const cmd of ['Page.enable','Runtime.enable'])await c.send(cmd);
    await c.send('Network.enable',{maxTotalBufferSize:2097152,maxResourceBufferSize:524288});
    await c.send('Network.setCacheDisabled',{cacheDisabled:true});
    async function size(v){current=v;await c.send('Emulation.setDeviceMetricsOverride',{...v,deviceScaleFactor:opts.deviceScaleFactor||1,mobile:false});}
    await size(current);await c.send('Emulation.setTouchEmulationEnabled',{enabled:!!opts.hasTouch,maxTouchPoints:1});
    async function evaluate(fn,arg){
      const expression=typeof fn==='string'?fn:'('+fn.toString()+')('+(arg===undefined?'undefined':JSON.stringify(arg))+')';
      const r=await c.send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,userGesture:false});
      if(r.exceptionDetails)throw new Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;
    }
    async function until(fn,arg,opts={}){
      const end=Date.now()+(opts.timeout||timeout);
      while(Date.now()<end){try{const value=await evaluate(fn,arg);if(value)return {jsonValue:async()=>value};}catch(err){if(!/context.*destroyed|Cannot find context|navigation/i.test(err.message))throw err;}await wait(typeof opts.polling==='number'?opts.polling:180);}
      throw new Error('Timeout waiting for '+fn.toString().slice(0,145));
    }
    async function click(x,y,touch){
      if(touch){await c.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y,radiusX:1,radiusY:1,force:1}]});await c.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});}
      else{for(const type of ['mouseMoved','mousePressed','mouseReleased'])await c.send('Input.dispatchMouseEvent',{type,x,y,button:type==='mouseMoved'?'none':'left',buttons:type==='mousePressed'?1:0,clickCount:type==='mouseMoved'?0:1});}
    }
    function locator(selector){
      const at=(fn)=>evaluate(([q,src])=>{const els=document.querySelectorAll(q);if(els.length!==1)throw new Error('Expected one matching '+q+', found '+els.length);return (0,eval)('('+src+')')(els[0]);},[selector,fn.toString()]);
      const box=()=>at(el=>{el.scrollIntoView({behavior:'instant',block:'center',inline:'nearest'});const r=el.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};});
      const press=async touch=>{await box();await until(q=>{const e=document.querySelector(q),r=e.getBoundingClientRect(),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return h===e||e.contains(h);},selector);await wait(180);const p=await box();const position={x:p.x+p.width/2,y:p.y+p.height/2};fs.appendFileSync(path.join(process.env.QA_OUTPUT_DIR,'direct-pointer-events.jsonl'),JSON.stringify({selector,position,touch,at:Date.now()})+'\n');await click(position.x,position.y,touch);};
      return {count:()=>evaluate(q=>document.querySelectorAll(q).length,selector),click:()=>press(false),tap:()=>press(true),getAttribute:key=>evaluate(([q,k])=>document.querySelector(q)?.getAttribute(k),[selector,key]),boundingBox:box};
    }
    c.emitter.on('Runtime.exceptionThrown',e=>em.emit('pageerror',new Error(e.exceptionDetails.exception?.description||e.exceptionDetails.text)));
    c.emitter.on('Runtime.consoleAPICalled',e=>em.emit('console',{type:()=>e.type==='warning'?'warning':e.type,text:()=>e.args.map(a=>a.value??a.description).join(' '),location:()=>e.stackTrace?.callFrames[0]||{}}));
    c.emitter.on('Network.requestWillBeSent',e=>active.set(e.requestId,e.request.url));
    c.emitter.on('Network.responseReceived',e=>em.emit('response',{url:()=>e.response.url,status:()=>e.response.status,body:()=>new Promise((resolve,reject)=>bodies.set(e.requestId,{resolve,reject}))}));
    c.emitter.on('Network.loadingFinished',e=>{
      const waiter=bodies.get(e.requestId);
      if(waiter){bodies.delete(e.requestId);c.send('Network.getResponseBody',{requestId:e.requestId}).then(body=>waiter.resolve(Buffer.from(body.body,body.base64Encoded?'base64':'utf8')),waiter.reject);}
      const url=active.get(e.requestId);if(url)em.emit('requestfinished',{url:()=>url,sizes:async()=>({responseBodySize:e.encodedDataLength})});active.delete(e.requestId);});
    c.emitter.on('Network.loadingFailed',e=>{const url=active.get(e.requestId);if(url)em.emit('requestfailed',{url:()=>url,failure:()=>({errorText:e.errorText})});active.delete(e.requestId);});
    c.emitter.on('Fetch.requestPaused',async e=>{const item=routes.find(r=>r.pattern instanceof RegExp&&r.pattern.test(e.request.url));const resume=()=>c.send('Fetch.continueRequest',{requestId:e.requestId});try{if(item)await item.cb({request:()=>({url:()=>e.request.url}),continue:resume});else await resume();}catch{/* The real browser may close after all physical evidence has been recorded. */}});
    return {evaluate,waitForFunction:until,locator,context:()=>({newCDPSession:async()=>({send:async(method,params)=>{const val=await c.send(method,params);if(method==='Browser.setWindowBounds'){await size(current);}return val;},detach:async()=>{}})}),mouse:{click:(x,y)=>click(x,y,false)},touchscreen:{tap:(x,y)=>click(x,y,true)},on:(k,fn)=>em.on(k,fn),request:{get:httpGet},setDefaultTimeout:v=>{timeout=v;},viewportSize:()=>current,setViewportSize:size,bringToFront:()=>c.send('Page.bringToFront'),isClosed:()=>proc.exitCode!==null||proc.signalCode!==null,
      setContent:async html=>{const {frameTree}=await c.send('Page.getFrameTree');await c.send('Page.setDocumentContent',{frameId:frameTree.frame.id,html});},
      addInitScript:(fn,arg)=>c.send('Page.addScriptToEvaluateOnNewDocument',{source:'('+fn.toString()+')('+(arg===undefined?'undefined':JSON.stringify(arg))+');'}),
      route:async(pattern,cb)=>{routes.push({pattern,cb});await c.send('Fetch.enable',{patterns:[{urlPattern:'*.glb*'},{urlPattern:'*.gltf*'},{urlPattern:'*.pbf*'},{urlPattern:'*/assets/materials/realism-v*/*'},{urlPattern:'*/macros/*/READY.json*'}]});},
      goto:async url=>{const {errorText}=await c.send('Page.navigate',{url});if(errorText)throw new Error(errorText);await until(h=>location.href.split('#')[0]===h.split('#')[0]&&document.readyState!=='loading',url);}
    };
  }};
  return instance;
}
module.exports={chromium:{launch}};
