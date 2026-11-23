(()=>{
 const task=TASK_LITERAL,anchor=ANCHOR_LITERAL,id=ID_LITERAL;
 if(!location.pathname.endsWith('index.html'))return;
 Object.defineProperty(navigator,'deviceMemory',{value:2});
 Object.defineProperty(navigator,'hardwareConcurrency',{value:1});
 let api;
 Object.defineProperty(window,'maplibregl',{configurable:true,get(){return api},set(v){
  api=v;if(v?.setWorkerCount)v.setWorkerCount(1);
  if(!v?.Map)return;
  const Original=v.Map;
  v.Map=class extends Original{
   constructor(opts){super({...opts,center:anchor,zoom:(task==='far'||(task==='reverse'&&!window.acceptSceneZoom))?15.9:17.2,pitch:0,pixelRatio:.25,maxTileCacheSize:2,antialias:false,canvasContextAttributes:{...opts.canvasContextAttributes,antialias:false}});window.realCityMap=this;}
   flyTo(opts,...rest){return super.flyTo((task==='far'||(task==='reverse'&&!window.acceptSceneZoom))?{...opts,zoom:15.9,pitch:0,duration:0}:opts,...rest);}
   easeTo(opts,...rest){return super.easeTo((task==='far'||(task==='reverse'&&!window.acceptSceneZoom))?{...opts,zoom:15.9,pitch:0,duration:0}:opts,...rest);}
  };
 }});
 window.actualOwnerWitness={};
 let installed=false;
 async function install(){
  if(installed||!document.querySelector('script[type=importmap]'))return;
  installed=true;const T=await import('/vendor/three.module.js'),V=await import('/src/ordinary-asset-verification.js'),orig=T.Object3D.prototype.updateMatrixWorld;
  const watched=new WeakSet();
  T.Object3D.prototype.updateMatrixWorld=function(force){
   const ret=orig.call(this,force),tag=this.userData||{};
   if(watched.has(this))return ret;
   const receipt=V.getVerifiedOrdinaryAsset(this);
   const kind=tag.cityPreservedLocalIds?.length===17?'neighbors':tag.cityReplacement?.landmark_id===id?'previousOwner':receipt?.modelId===id?'landmark':null;
   if(!kind)return ret;watched.add(this);const obj=this;
   const witness={kind,ids:tag.cityPreservedLocalIds||tag.cityReplacement?.local_ids,receipt,draws:0,meshCount:0,triangles:0};
   Object.defineProperty(witness,'visible',{enumerable:true,get:()=>obj.visible});window.actualOwnerWitness[kind]=witness;
   obj.traverse(mesh=>{if(!mesh.isMesh)return;witness.meshCount++;witness.triangles+=(mesh.geometry.index?.count||mesh.geometry.attributes.position.count)/3;const prior=mesh.onBeforeRender;mesh.onBeforeRender=function(...args){if(!witness.draws++)console.log('WKG '+JSON.stringify({firstDraw:witness,position:obj.position.toArray(),rotation:obj.rotation.toArray().slice(0,3),scale:obj.scale.toArray()}));return prior.apply(this,args);};});
   return ret;
  };
 }
 document.addEventListener('DOMContentLoaded',install);new MutationObserver(install).observe(document,{childList:true,subtree:true});
})();
