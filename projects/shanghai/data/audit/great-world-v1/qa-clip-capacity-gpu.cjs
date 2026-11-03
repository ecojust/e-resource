/* Real GPU capacity/owner fixture for the production clipper. MIT. */
async function runCandidateClipCapacityFixture(config){
 const r={passed:false,capacity:320,cases:[],programs:[],sourceReceipts:[],glErrors:[],shaderErrors:[],cleanup:{rendererDisposed:false,canvasDetached:false,contextLostRequested:false}};
 const check=(v,m)=>{if(!v)throw Error(m);},sha=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
 let renderer,clipper,target,canvas;const resources=new Set(),groups=new Set();
 try{
  for(const b of [config.clipper,config.three]){const response=await fetch(b.url,{cache:'no-store'});check(response.ok,'Fixture source HTTP '+b.url);const bytes=await response.arrayBuffer(),actual=await sha(bytes);check(actual===b.sha256,'Fixture source byte binding '+b.url);r.sourceReceipts.push({url:b.url,status:response.status,bytes:bytes.byteLength,sha256:actual});}
  const THREE=await import(config.three.url),{CandidateCityClipper}=await import(config.clipper.url);
  canvas=document.createElement('canvas');canvas.width=128;canvas.height=128;
  renderer=new THREE.WebGLRenderer({canvas,alpha:true,antialias:false,preserveDrawingBuffer:true});renderer.setPixelRatio(1);renderer.setSize(128,128,false);renderer.setClearColor(0,0);renderer.outputColorSpace=THREE.LinearSRGBColorSpace;renderer.toneMapping=THREE.NoToneMapping;
  renderer.debug.checkShaderErrors=true;renderer.debug.onShaderError=(gl,p,vs,fs)=>r.shaderErrors.push({program:gl.getProgramInfoLog(p),vertex:gl.getShaderInfoLog(vs),fragment:gl.getShaderInfoLog(fs)});
  const gl=renderer.getContext();r.context={version:gl.getParameter(gl.VERSION),attributes:gl.getContextAttributes(),drawingBuffer:[gl.drawingBufferWidth,gl.drawingBufferHeight],canvasAttached:canvas.isConnected};
  target=new THREE.WebGLRenderTarget(128,128,{format:THREE.RGBAFormat,type:THREE.UnsignedByteType,depthBuffer:true,stencilBuffer:false});
  clipper=new CandidateCityClipper({THREE,geographicPosition:(x,z,y=0)=>new THREE.Vector3(x,y,z)});
  const triangle=(points,id=1519)=>({geometry:{type:'Polygon',coordinates:[[...points,points[0]]]},owner:{macro_id:'fixture',feature_local_id:id}});
  const clips=Array.from({length:318},(_,i)=>triangle([[100+i*3,100],[101+i*3,100],[100+i*3,101]],10000+i));
  clips.push(triangle([[-1,-1],[0,-1],[-1,1]]),triangle([[0,-1],[0,1],[-1,1]]));clipper.update(clips);
  check(clipper.getState().triangleLimit===320&&clipper.getState().triangles===320,'320-row allocation');
  check(clipper.texture.image.height===320&&clipper.data.byteLength===20480,'320-row texture layout');
  r.rowBindings=[318,319].map(index=>({index,owner:clipper.data[index*16+12],positions:Array.from(clipper.data.slice(index*16,index*16+6))}));
  const scene=new THREE.Scene(),camera=new THREE.OrthographicCamera(-1.25,1.25,1.25,-1.25,.1,20);camera.position.set(0,10,0);camera.up.set(0,0,-1);camera.lookAt(0,0,0);camera.updateMatrixWorld();camera.updateProjectionMatrix();
  const probes=[{name:'row319',world:[-.75,0,-.75],clipped:true},{name:'row320',world:[-.25,0,.75],clipped:true},{name:'unclipped-left-height',world:[.6,0,-.6],clipped:false},{name:'unclipped-right-height',world:[.6,0,.6],clipped:false}].map(p=>{const q=new THREE.Vector3(...p.world).project(camera);return {...p,pixel:[Math.floor((q.x+1)*64),Math.floor((q.y+1)*64)]};});
  r.probes=probes;const programs=new Map();let active=[];
  const uniform=(p,n)=>{const l=gl.getUniformLocation(p,n);if(l===null)return null;const v=gl.getUniform(p,l);return ArrayBuffer.isView(v)?Array.from(v):v;};
  const recordProgram=p=>{if(!programs.has(p)){const id='capacity-program-'+(programs.size+1);programs.set(p,id);const shaders=(gl.getAttachedShaders(p)||[]).map(s=>{const source=gl.getShaderSource(s);return {type:gl.getShaderParameter(s,gl.SHADER_TYPE),compiled:gl.getShaderParameter(s,gl.COMPILE_STATUS),infoLog:gl.getShaderInfoLog(s),source};});r.programs.push({id,linked:gl.getProgramParameter(p,gl.LINK_STATUS),infoLog:gl.getProgramInfoLog(p),shaders});}return programs.get(p);};
  const draw=(fixture,pass,label)=>{
   const {mesh,ownerMatched,count}=fixture;mesh.material=pass==='standard'?fixture.visible:pass==='depth'?mesh.customDepthMaterial:mesh.customDistanceMaterial;
   if(pass==='distance'){const light=new THREE.PointLight();light.position.set(0,10,0);light.shadow.camera.near=.1;light.shadow.camera.far=30;light.updateMatrixWorld();renderer.properties.get(mesh.material).light=light;}
   active=[];renderer.setRenderTarget(target);renderer.clear(true,true,true);renderer.render(scene,camera);
   const samples=probes.map(p=>{const bytes=new Uint8Array(4);renderer.readRenderTargetPixels(target,p.pixel[0],p.pixel[1],1,1,bytes);const rgba=Array.from(bytes),clear=rgba.every(v=>v===0),expected=ownerMatched&&p.clipped?'clear':'retained';return {...p,expected,rgba,passed:expected==='clear'?clear:!clear};});
   const error=gl.getError();if(error)r.glErrors.push({label,error});check(samples.every(p=>p.passed),label+' pixel assertion '+JSON.stringify(samples));check(active.length===1,label+' one actual draw');check(active[0].candidateClipCount===count,label+' actual uniform count');check(!r.shaderErrors.length&&!r.glErrors.length,label+' shader/GL error');return {label,pass,draws:active,samples};
  };
  for(const tagged of [true,false])for(const ownerMatched of [true,false]){
   const owner=ownerMatched?1519:2367,geometry=new THREE.PlaneGeometry(2,2);geometry.rotateX(-Math.PI/2);resources.add(geometry);
   if(tagged)geometry.setAttribute('_feature_id_0',new THREE.Float32BufferAttribute(new Float32Array(geometry.getAttribute('position').count).fill(owner),1));
   const visible=new THREE.MeshStandardMaterial({color:0,emissive:0xffffff,roughness:1}),mesh=new THREE.Mesh(geometry,visible),group=new THREE.Group();resources.add(visible);group.add(mesh);scene.add(group);groups.add(group);
   clipper.bindObject(group,{id:'fixture/'+owner+(tagged?'-tagged':'-near'),parent:{id:'fixture'},...(tagged?{}:{ids:[owner]})});resources.add(mesh.customDepthMaterial);resources.add(mesh.customDistanceMaterial);
   mesh.onAfterRender=function(){const p=gl.getParameter(gl.CURRENT_PROGRAM);active.push({program:recordProgram(p),materialType:mesh.material.type,candidateClipCount:uniform(p,'candidateClipCount'),candidateHasFeatureIds:uniform(p,'candidateHasFeatureIds'),candidateMacro:uniform(p,'candidateMacro'),modelMatrix:uniform(p,'modelMatrix')});};
   const fixture={mesh,visible,ownerMatched,count:tagged?320:ownerMatched?2:0};
   const label=(tagged?'per-vertex':'near-scope')+'-'+owner;
   const passes=['standard','depth','distance'].map(pass=>draw(fixture,pass,label+'-'+pass));
   r.cases.push({name:label,owner,ownerMatched,tagged,passed:true,scope:clipper.getState().ownerScopedSources.find(s=>s.id==='fixture/'+owner+'-near')||null,passes});
   if(!tagged&&ownerMatched){
    const state=clipper.getState(),globalBefore=new Float32Array(clipper.data),scope=clipper.objects.get(group).scope,scopeBefore=new Float32Array(scope.data),texture=clipper.texture,scopeTexture=scope.texture;
    let rejected=false,message=null;try{clipper.update([...clips,triangle([[9000,100],[9001,100],[9000,101]])]);}catch(e){message=e.message;rejected=/候选模型局部边界过于复杂/.test(e.message);}
    check(rejected,'321-row update must reject');check(clipper.getState().revision===state.revision&&clipper.getState().triangles===320,'Overflow leaves live count/revision');check(clipper.texture===texture&&scope.texture===scopeTexture,'Overflow retains texture objects');check(clipper.data.every((v,i)=>v===globalBefore[i])&&scope.data.every((v,i)=>v===scopeBefore[i]),'Overflow preserves global/scoped bytes');
    r.overflow={attempted:321,rejected,message,revisionBefore:state.revision,revisionAfter:clipper.getState().revision,globalDataSha256:await sha(globalBefore.buffer),scopeDataSha256:await sha(scopeBefore.buffer),texturesRetained:true,bytesUnchanged:true,passes:['standard','depth','distance'].map(pass=>draw(fixture,pass,'after-rejected-overflow-'+pass))};
   }
   scene.remove(group);clipper.releaseObject(group);groups.delete(group);
  }
  for(const p of r.programs){check(p.linked,'GPU program linked');for(const s of p.shaders){check(s.compiled,'GPU shader compiled');s.sha256=await sha(new TextEncoder().encode(s.source));if(s.type===gl.FRAGMENT_SHADER){check(s.source.includes('i<320'),'Actual fragment shader has320 bound');check(s.source.includes('/320.0'),'Actual fragment shader samples320-row texture');}delete s.source;}}
  r.finalState=clipper.getState();check(r.cases.length===4&&r.cases.every(c=>c.passed)&&r.overflow?.bytesUnchanged,'All required owner/pass cases');r.passed=true;
 }catch(e){r.error=String(e.stack||e);r.passed=false;}
 finally{if(clipper){for(const g of groups)clipper.releaseObject(g);clipper.dispose();}for(const v of resources)v.dispose?.();target?.dispose();if(renderer){renderer.setRenderTarget(null);renderer.dispose();r.cleanup.rendererDisposed=true;renderer.forceContextLoss();r.cleanup.contextLostRequested=true;}canvas?.remove();r.cleanup.canvasDetached=!canvas?.isConnected;}
 return r;
}
module.exports={runCandidateClipCapacityFixture};
