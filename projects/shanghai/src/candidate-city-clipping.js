/** Geographic display clipping for inferred candidate placement. Authored models
 * are never clipped. Source geometry is retained unchanged in its GLB assets.
 */
// Keep the all-city correction within a bounded shader loop.
const MAX_TRIANGLES=128;
const materialUniforms=new WeakMap();
const hash=value=>{let n=2166136261;for(const c of value||''){n^=c.charCodeAt(0);n=Math.imul(n,16777619);}return (n>>>0)%16777215;};
const polygons=g=>g?.type==='Polygon'?[g.coordinates]:g?.type==='MultiPolygon'?g.coordinates:[];

export class CandidateCityClipper {
  constructor({THREE,geographicPosition}){
    Object.assign(this,{THREE,geographicPosition});this.bindings=new Map();this.objects=new Map();this.triangleCount=0;this.triangleOwners=[];
    this.data=new Float32Array(4*4*MAX_TRIANGLES);
    this.texture=new THREE.DataTexture(this.data,4,MAX_TRIANGLES,THREE.RGBAFormat,THREE.FloatType);
    this.texture.magFilter=this.texture.minFilter=THREE.NearestFilter;this.texture.generateMipmaps=false;this.texture.needsUpdate=true;
    this.uniforms={texture:{value:this.texture},count:{value:0}};this.revision=0;
  }
  update(clips){
    const {THREE,geographicPosition}=this,triangles=[];
    for(const clip of clips)for(const rings of polygons(clip.geometry)){
      const contour=rings.map(r=>r.slice(0,-1).map(p=>{const v=geographicPosition(...p);return new THREE.Vector2(v.x,v.z);}));
      const points=contour.flat(),faces=THREE.ShapeUtils.triangulateShape(contour[0],contour.slice(1));
      for(const owner of clip.owners?.length?clip.owners:[clip.owner||{}]){
        const localId=owner.feature_local_id??owner.local_id??clip.source_local_id??0;
        const macroId=owner.macro_id||clip.source_macro,macro=macroId?hash(macroId):0;
        for(const face of faces)triangles.push({p:face.map(i=>points[i]),localId,macro});
      }
    }
    if(triangles.length>MAX_TRIANGLES)throw Error('候选模型局部边界过于复杂');
    this.data.fill(0);
    triangles.forEach(({p:[a,b,c],localId,macro},i)=>this.data.set([a.x,a.y,b.x,b.y,c.x,c.y,-100,1000,
      Math.min(a.x,b.x,c.x),Math.min(a.y,b.y,c.y),Math.max(a.x,b.x,c.x),Math.max(a.y,b.y,c.y),localId,macro,0,0],i*16));
    this.triangleOwners=triangles.map(({localId,macro})=>({localId,macro}));
    this.uniforms.count.value=this.triangleCount=triangles.length;this.texture.needsUpdate=true;this.revision++;
    for(const {scope} of this.objects.values())if(scope)this.updateOwnerScope(scope);
    for(const {uniforms,scope} of this.bindings.values()){
      uniforms.texture.value=scope?.texture||this.texture;uniforms.count.value=scope?scope.triangles:this.triangleCount;
    }
  }
  updateOwnerScope(scope){
    scope.data.fill(0);scope.triangles=0;scope.clipIds.clear();
    this.triangleOwners.forEach(({localId,macro},index)=>{
      if((macro===0||macro===scope.macro)&&(localId===0||scope.ids.has(localId))){
        scope.data.set(this.data.subarray(index*16,index*16+16),scope.triangles++*16);scope.clipIds.add(localId);
      }
    });
    scope.texture.needsUpdate=true;
  }
  bindMaterial(material,{featureIds,macroId,scope=null}){
    if(!material||this.bindings.has(material))return;
    const previous=material.onBeforeCompile,cacheKey=material.customProgramCacheKey,previousKey=cacheKey?.call(material)||'';
    // Cached Three programs keep these holders when a near object is rebound.
    let uniforms=materialUniforms.get(material);
    if(!uniforms){uniforms={texture:{value:null},count:{value:0}};materialUniforms.set(material,uniforms);}
    uniforms.texture.value=scope?.texture||this.texture;uniforms.count.value=scope?scope.triangles:this.triangleCount;
    const macro=hash(macroId);
    const hook=(shader,renderer)=>{
      previous?.call(material,shader,renderer);
      if(!shader.vertexShader.includes('#include <project_vertex>')||!shader.fragmentShader.includes('#include <common>'))throw Error('Unsupported candidate clipping shader');
      Object.assign(shader.uniforms,{candidateClipTexture:uniforms.texture,candidateClipCount:uniforms.count,
        candidateMacro:{value:macro},candidateHasFeatureIds:{value:featureIds?1:0}});
      const attribute=featureIds&&!shader.vertexShader.includes('attribute float _feature_id_0;')?'attribute float _feature_id_0;':'';
      shader.vertexShader=shader.vertexShader.replace('#include <common>',`#include <common>\n${attribute}\nvarying vec3 vCandidatePosition;\nvarying float vCandidateFeatureId;`)
        .replace('#include <project_vertex>',`#include <project_vertex>\nvec4 candidatePosition=vec4(transformed,1.0);\n#ifdef USE_BATCHING\ncandidatePosition=batchingMatrix*candidatePosition;\n#endif\n#ifdef USE_INSTANCING\ncandidatePosition=instanceMatrix*candidatePosition;\n#endif\nvCandidatePosition=(modelMatrix*candidatePosition).xyz;\nvCandidateFeatureId=${featureIds?'_feature_id_0':'0.0'};`);
      shader.fragmentShader=shader.fragmentShader.replace('#include <common>',`#include <common>
uniform sampler2D candidateClipTexture;
uniform float candidateClipCount;
uniform float candidateMacro;
uniform float candidateHasFeatureIds;
varying vec3 vCandidatePosition;
varying float vCandidateFeatureId;
float candidateCross(vec2 a,vec2 b){return a.x*b.y-a.y*b.x;}
bool candidateInside(){
  vec2 p=vCandidatePosition.xz;
  for(int i=0;i<${MAX_TRIANGLES};i++){
    if(float(i)>=candidateClipCount)break;
    float row=(float(i)+0.5)/${MAX_TRIANGLES}.0;
    vec4 box=texture2D(candidateClipTexture,vec2(0.625,row));
    if(p.x<box.x||p.y<box.y||p.x>box.z||p.y>box.w)continue;
    vec4 owner=texture2D(candidateClipTexture,vec2(0.875,row));
    if(owner.y>0.0&&abs(owner.y-candidateMacro)>0.5)continue;
    if(candidateHasFeatureIds>0.5&&owner.x>0.0&&abs(owner.x-vCandidateFeatureId)>0.5)continue;
    vec4 ab=texture2D(candidateClipTexture,vec2(0.125,row));
    vec4 cy=texture2D(candidateClipTexture,vec2(0.375,row));
    if(vCandidatePosition.y<cy.z||vCandidatePosition.y>cy.w)continue;
    float a=candidateCross(ab.zw-ab.xy,p-ab.xy),b=candidateCross(cy.xy-ab.zw,p-ab.zw),c=candidateCross(ab.xy-cy.xy,p-cy.xy);
    if((a>=-0.001&&b>=-0.001&&c>=-0.001)||(a<=0.001&&b<=0.001&&c<=0.001))return true;
  }
  return false;
}`).replace(/void\s+main\s*\(\s*\)\s*\{/,'void main(){\nif(candidateInside())discard;');
    };
    material.onBeforeCompile=hook;material.customProgramCacheKey=()=>`${previousKey}|candidate-city-clip-v2|${featureIds?1:0}|${scope?1:0}`;
    material.needsUpdate=true;this.bindings.set(material,{previous,cacheKey,hook,uniforms,scope});
  }
  bindObject(group,record){
    if(this.objects.has(group))return;
    const materials=new Set(),created=[],macroId=record.parent?.id||record.id;
    let scope=null;
    // Near tiles can contain several buildings without per-vertex owner IDs.
    // Their validated tile ownership still excludes clips for unrelated tiles.
    if(Array.isArray(record.ids)&&record.ids.length&&record.ids.every(id=>Number.isInteger(id)&&id>0)){
      let needed=false;group.traverse(mesh=>{if(mesh.isMesh&&!mesh.geometry?.getAttribute('_feature_id_0'))needed=true;});
      if(needed){
        const data=new Float32Array(this.data.length),texture=new this.THREE.DataTexture(data,4,MAX_TRIANGLES,this.THREE.RGBAFormat,this.THREE.FloatType);
        texture.magFilter=texture.minFilter=this.THREE.NearestFilter;texture.generateMipmaps=false;
        scope={id:record.id,macroId,macro:hash(macroId),ids:new Set(record.ids),data,texture,triangles:0,clipIds:new Set()};
        this.updateOwnerScope(scope);
      }
    }
    group.traverse(mesh=>{
      if(!mesh.isMesh)return;
      const featureIds=Boolean(mesh.geometry?.getAttribute('_feature_id_0'));
      const config={featureIds,macroId,scope:featureIds?null:scope};
      for(const material of Array.isArray(mesh.material)?mesh.material:[mesh.material]){this.bindMaterial(material,config);materials.add(material);}
      for(const [property,make] of [['customDepthMaterial',()=>new this.THREE.MeshDepthMaterial({depthPacking:this.THREE.RGBADepthPacking})],['customDistanceMaterial',()=>new this.THREE.MeshDistanceMaterial()]]){
        if(!mesh[property]){mesh[property]=make();created.push({mesh,property,material:mesh[property]});}
        this.bindMaterial(mesh[property],config);materials.add(mesh[property]);
      }
    });
    this.objects.set(group,{materials,created,scope});
  }
  releaseObject(group){
    const binding=this.objects.get(group);if(!binding)return;
    for(const material of binding.materials){const b=this.bindings.get(material);if(!b)continue;
      if(material.onBeforeCompile===b.hook){material.onBeforeCompile=b.previous;material.customProgramCacheKey=b.cacheKey;material.needsUpdate=true;}
      b.uniforms.texture.value=null;b.uniforms.count.value=0;
      this.bindings.delete(material);
    }
    for(const {mesh,property,material} of binding.created){if(mesh[property]===material)mesh[property]=undefined;material.dispose();}
    binding.scope?.texture.dispose();this.objects.delete(group);
  }
  getState(){return {triangles:this.triangleCount,sourceObjects:this.objects.size,boundMaterials:this.bindings.size,revision:this.revision,
    ownerScopedSources:[...this.objects.values()].filter(({scope})=>scope).map(({scope})=>({id:scope.id,macro_id:scope.macroId,
      feature_local_ids:[...scope.ids],triangles:scope.triangles,clip_feature_local_ids:[...scope.clipIds]}))};}
  dispose(){for(const object of [...this.objects.keys()])this.releaseObject(object);this.texture.dispose();}
}
