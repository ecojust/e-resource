const fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),{createHash}=require('crypto'),{spawn}=require('child_process');
const {chromium}=require('playwright'),{runCandidateClipCapacityFixture}=require('./qa-clip-capacity-gpu.cjs');
const W=__dirname,P='/workspace/e-resource/projects/shanghai',B='http://127.0.0.1:8782/',sha=b=>createHash('sha256').update(b).digest('hex');
async function main(){
 assert(!fs.existsSync(path.join(W,'gpu-capacity.json')),'Do not overwrite GPU evidence');
 assert.equal(await fetch(B+'qa-blank.html',{signal:AbortSignal.timeout(1000)}).then(()=>true).catch(()=>false),false,'Port8782 active');
 const log=fs.openSync(path.join(W,'gpu-server.log'),'w'),server=spawn('python',['-B',path.join(W,'server.py')],{stdio:['ignore',log,log]}),startedAt=new Date().toISOString();let browser,result;
 try{
  let ready=false;for(let i=0;i<20;i++){if(await fetch(B+'qa-blank.html',{signal:AbortSignal.timeout(1000)}).then(r=>r.ok).catch(()=>false)){ready=true;break;}await new Promise(r=>setTimeout(r,100));}assert(ready,'Private server ready');
  browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=9223']});
  const page=await browser.newPage({viewport:{width:320,height:240}}),errors=[],warnings=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());if(m.type()==='warning')warnings.push(m.text());});
  await page.goto(B+'qa-blank.html',{waitUntil:'domcontentloaded',timeout:10000});
  const files=['src/candidate-city-clipping.js','vendor/three.module.js'],bindings=files.map(file=>({url:B+file,sha256:sha(fs.readFileSync(path.join(P,file)))}));
  result=await page.evaluate(runCandidateClipCapacityFixture,{clipper:bindings[0],three:bindings[1]});
  Object.assign(result,{startedAt,completedAt:new Date().toISOString(),browserVersion:browser.version(),scriptSha256:sha(fs.readFileSync(path.join(W,'qa-clip-capacity-gpu.cjs'))),runnerSha256:sha(fs.readFileSync(__filename)),errors,warnings,browserClosed:false,serverClosed:false,scope:'Small detached-canvas fixture only; main scene and model assets were not loaded.'});
  assert(result.passed,JSON.stringify(result));assert.deepEqual(errors,[]);assert.deepEqual(warnings,[]);
 }finally{
  if(browser)await browser.close();server.kill('SIGTERM');await new Promise(resolve=>server.once('exit',resolve));fs.closeSync(log);
  if(result){result.browserClosed=true;result.serverClosed=true;result.closedAt=new Date().toISOString();fs.writeFileSync(path.join(W,'gpu-capacity.json'),JSON.stringify(result,null,2)+'\n');}
 }
 console.log(JSON.stringify({passed:result.passed,cases:result.cases.length,actualDraws:result.cases.reduce((n,c)=>n+c.passes.length,0)+result.overflow.passes.length,programs:result.programs.length,browserClosed:result.browserClosed,serverClosed:result.serverClosed,clipperSha256:result.sourceReceipts[0].sha256}));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
