/** Geographic display clipping for inferred candidate placement. Authored models
 * are never clipped. Source geometry is retained unchanged in its GLB assets.
 */
// Current all-city catalogue needs 56 triangles; keep a bounded shader loop.
const MAX_TRIANGLES=128;
const hash=value=>{let n=2166136261;for(const c of value||''){n^=c.charCodeAt(0);n=Math.imul(n,16777619);}return (n>>>0)%16777215;};
const polygons=g=>g?.type==='Polygon'?[g.coordinates]:g?.type==='MultiPolygon'?g.coordinates:[];

export class CandidateCityClipper {
  constructor({THREE,geographicPosition}){
    Object.assign(this,{THREE,geographicPosition});this.bindings=new Map();this.objects=new Map();this.triangleCount=0;
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
    this.uniforms.count.value=this.triangleCount=triangles.length;this.texture.needsUpdate=true;this.revision++;
  }
  bindMaterial(material,{featureIds,macroId}){
    if(!material||this.bindings.has(material))return;
    const previous=material.onBeforeCompile,cacheKey=material.customProgramCacheKey,previousKey=cacheKey?.call(material)||'';
    const uniforms=this.uniforms,macro=hash(macroId);
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
    material.onBeforeCompile=hook;material.customProgramCacheKey=()=>`${previousKey}|candidate-city-clip-v1|${featureIds?1:0}`;
    material.needsUpdate=true;this.bindings.set(material,{previous,cacheKey,hook});
  }
  bindObject(group,record){
    if(this.objects.has(group))return;
    const materials=new Set(),created=[];
    group.traverse(mesh=>{
      if(!mesh.isMesh)return;
      const config={featureIds:Boolean(mesh.geometry?.getAttribute('_feature_id_0')),macroId:record.parent?.id||record.id};
      for(const material of Array.isArray(mesh.material)?mesh.material:[mesh.material]){this.bindMaterial(material,config);materials.add(material);}
      for(const [property,make] of [['customDepthMaterial',()=>new this.THREE.MeshDepthMaterial({depthPacking:this.THREE.RGBADepthPacking})],['customDistanceMaterial',()=>new this.THREE.MeshDistanceMaterial()]]){
        if(!mesh[property]){mesh[property]=make();created.push({mesh,property,material:mesh[property]});}
        this.bindMaterial(mesh[property],config);materials.add(mesh[property]);
      }
    });
    this.objects.set(group,{materials,created});
  }
  releaseObject(group){
    const binding=this.objects.get(group);if(!binding)return;
    for(const material of binding.materials){const b=this.bindings.get(material);if(!b)continue;
      if(material.onBeforeCompile===b.hook){material.onBeforeCompile=b.previous;material.customProgramCacheKey=b.cacheKey;material.needsUpdate=true;}
      this.bindings.delete(material);
    }
    for(const {mesh,property,material} of binding.created){if(mesh[property]===material)mesh[property]=undefined;material.dispose();}
    this.objects.delete(group);
  }
  getState(){return {triangles:this.triangleCount,sourceObjects:this.objects.size,boundMaterials:this.bindings.size,revision:this.revision};}
  dispose(){for(const object of [...this.objects.keys()])this.releaseObject(object);this.texture.dispose();}
}
