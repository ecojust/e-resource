/** Geographic display clipping for inferred candidate placement. Authored models
 * are never clipped. Source geometry is retained unchanged in its GLB assets.
 */
// A page holds 320 triangle records. WebGL2 guarantees at least 2048 texels per axis.
const MAX_TRIANGLES=320;
const MAX_PAGES=512;
const materialUniforms=new WeakMap();
const hash=value=>{let n=2166136261;for(const c of value||''){n^=c.charCodeAt(0);n=Math.imul(n,16777619);}return (n>>>0)%16777215;};
const polygons=g=>g?.type==='Polygon'?[g.coordinates]:g?.type==='MultiPolygon'?g.coordinates:[];

export class CandidateCityClipper {
  constructor({THREE,geographicPosition}){
    Object.assign(this,{THREE,geographicPosition});this.bindings=new Map();this.objects=new Map();this.triangleCount=0;this.triangleOwners=[];
    this.macroTables=new Map();
    this.defaultTable=this.newTable();
    this.texture=this.defaultTable.texture;
    this.data=this.defaultTable.data;
    this.uniforms={texture:{value:this.texture},count:{value:0}};this.revision=0;
  }
  newTable(){
    const {THREE}=this;
    const data=new Float32Array(16*MAX_TRIANGLES);
    const texture=new THREE.DataTexture(data,4,MAX_TRIANGLES,THREE.RGBAFormat,THREE.FloatType);
    texture.magFilter=texture.minFilter=THREE.NearestFilter;
    texture.generateMipmaps=false;texture.needsUpdate=true;
    return {data,texture,triangles:0,pages:1,wildcards:0,maxFeatureSpan:0};
  }
  allocatePages(table,pages){
    if(table.pages===pages)return;
    // Three requires a new texture for a dimension change. Existing materials
    // retain their uniform holders; update() rebinds their texture below.
    const previous=table.texture;
    table.pages=pages;
    table.data=new Float32Array(16*MAX_TRIANGLES*pages);
    table.texture=new this.THREE.DataTexture(table.data,4*pages,MAX_TRIANGLES,this.THREE.RGBAFormat,this.THREE.FloatType);
    table.texture.magFilter=table.texture.minFilter=this.THREE.NearestFilter;
    table.texture.generateMipmaps=false;
    previous.dispose();
  }
  writeTable(table,rows){
    const pages=Math.max(1,Math.ceil(rows.length/MAX_TRIANGLES));
    this.allocatePages(table,pages);
    table.data.fill(0);
    table.wildcards=0;table.maxFeatureSpan=0;
    // In a multipage macro, group all triangles of each local feature together.
    // The last two channels in the owner texel give the first row and its count.
    const sorted=pages===1?rows:[...rows].sort((a,b)=>a.localId-b.localId);
    let start=0;
    while(start<sorted.length){
      const id=sorted[start].localId;
      let end=start+1;
      while(end<sorted.length&&sorted[end].localId===id)end++;
      if(id===0)table.wildcards+=end-start;
      else table.maxFeatureSpan=Math.max(table.maxFeatureSpan,end-start);
      for(let i=start;i<end;i++){
        const {p:[a,b,c],localId,macro,minHeight,maxHeight}=sorted[i];
        table.data.set([a.x,a.y,b.x,b.y,c.x,c.y,minHeight,maxHeight,
          Math.min(a.x,b.x,c.x),Math.min(a.y,b.y,c.y),Math.max(a.x,b.x,c.x),Math.max(a.y,b.y,c.y),
          localId,macro,start,end-start],i*16);
      }
      start=end;
    }
    table.maxFeatureSpan=pages===1?rows.length:table.maxFeatureSpan+table.wildcards;
    table.triangles=rows.length;
    table.texture.needsUpdate=true;
  }
  tableFor(macro){
    return this.macroTables.get(macro)||this.defaultTable;
  }
  update(clips){
    const {THREE,geographicPosition}=this,triangles=[];
    for(const clip of clips){
      let minHeight=-100,maxHeight=1000;
      if('min_height' in clip||'max_height' in clip||'height_reference' in clip){
        const ref=clip.height_reference;
        if(!Number.isFinite(clip.min_height)||!Number.isFinite(clip.max_height)||clip.min_height>=clip.max_height
          ||!Array.isArray(ref)||ref.length!==2||!ref.every(Number.isFinite)||Math.abs(ref[0])>180||Math.abs(ref[1])>85)
          throw Error('候选模型高度裁剪范围无效');
        // Heights are native source metres at its macro anchor. Near groups
        // inherit that macro's latitude scale; the shader compares world Y.
        minHeight=Math.fround(geographicPosition(...ref,clip.min_height).y);
        maxHeight=Math.fround(geographicPosition(...ref,clip.max_height).y);
        if(!Number.isFinite(minHeight)||!Number.isFinite(maxHeight)||minHeight>=maxHeight)throw Error('候选模型高度裁剪范围无效');
      }
      for(const rings of polygons(clip.geometry)){
        const contour=rings.map(r=>r.slice(0,-1).map(p=>{const v=geographicPosition(...p);return new THREE.Vector2(v.x,v.z);}));
        const points=contour.flat(),faces=THREE.ShapeUtils.triangulateShape(contour[0],contour.slice(1));
        for(const owner of clip.owners?.length?clip.owners:[clip.owner||{}]){
          const localId=owner.feature_local_id??owner.local_id??clip.source_local_id??0;
          const macroId=owner.macro_id||clip.source_macro,macro=macroId?hash(macroId):0;
          for(const face of faces)triangles.push({p:face.map(i=>points[i]),localId,macro,minHeight,maxHeight});
        }
      }
    }
    // Prefer the original shared texture for small sets. Beyond one texture,
    // an owner in another macro can never match this draw. Wildcards can.
    let common=triangles;
    const groups=new Map();
    if(triangles.length>MAX_TRIANGLES){
      common=[];
      for(const triangle of triangles){
        if(!triangle.macro){ common.push(triangle); continue; }
        if(!groups.has(triangle.macro))groups.set(triangle.macro,[]);
        groups.get(triangle.macro).push(triangle);
      }
      // Allocate all tables only after validating every individual owner span.
      // A scoped fragment evaluates its feature plus matching wildcard triangles.
      for(const rows of [common,...[...groups.values()].map(group=>[...common,...group])]){
        if(rows.length<=MAX_TRIANGLES)continue;
        const counts=new Map();
        for(const row of rows)counts.set(row.localId,(counts.get(row.localId)||0)+1);
        const wild=counts.get(0)||0;counts.delete(0);
        const overlong=[...counts.values()].some(count=>count+wild>MAX_TRIANGLES);
        if(rows.length>MAX_TRIANGLES*MAX_PAGES||wild>MAX_TRIANGLES||overlong)
          throw Error('候选模型局部边界过于复杂');
      }
    }
    this.writeTable(this.defaultTable,common);
    this.texture=this.defaultTable.texture;this.data=this.defaultTable.data;this.uniforms.texture.value=this.texture;
    for(const [macro,rows] of groups){
      if(!this.macroTables.has(macro))this.macroTables.set(macro,this.newTable());
      this.writeTable(this.macroTables.get(macro),[...common,...rows]);
    }
    for(const [macro,table] of this.macroTables)if(!groups.has(macro)){
      this.macroTables.delete(macro);
      table.texture.dispose();
    }
    this.triangleOwners=triangles.map(({localId,macro})=>({localId,macro}));
    this.uniforms.count.value=common.length;this.triangleCount=triangles.length;this.revision++;
    for(const {scope} of this.objects.values())if(scope)this.updateOwnerScope(scope);
    for(const {uniforms,scope,macro} of this.bindings.values()){
      const table=scope||this.tableFor(macro);
      this.useTable(uniforms,table);
    }
  }
  updateOwnerScope(scope){
    const table=this.tableFor(scope.macro);
    const selected=[];scope.clipIds.clear();
    for(let i=0;i<table.triangles;i++){
      const offset=i*16,localId=table.data[offset+12],macro=table.data[offset+13];
      if((macro===0||macro===scope.macro)&&(localId===0||scope.ids.has(localId))){
        selected.push(offset);scope.clipIds.add(localId);
      }
    }
    this.allocatePages(scope,Math.max(1,Math.ceil(selected.length/MAX_TRIANGLES)));
    scope.data.fill(0);
    selected.forEach((offset,index)=>scope.data.set(table.data.subarray(offset,offset+16),index*16));
    scope.triangles=selected.length;scope.wildcards=0;
    scope.texture.needsUpdate=true;
  }
  useTable(uniforms,table){
    uniforms.texture.value=table.texture;uniforms.count.value=table.triangles;
    uniforms.pages.value=table.pages;uniforms.wildcards.value=table.wildcards;
  }
  bindMaterial(material,{featureIds,macroId,scope=null}){
    if(!material||this.bindings.has(material))return;
    const previous=material.onBeforeCompile,cacheKey=material.customProgramCacheKey,previousKey=cacheKey?.call(material)||'';
    // Cached Three programs keep these holders when a near object is rebound.
    let uniforms=materialUniforms.get(material);
    if(!uniforms){uniforms={texture:{value:null},count:{value:0},pages:{value:1},wildcards:{value:0},macro:{value:0}};materialUniforms.set(material,uniforms);}
    const macro=hash(macroId),table=scope||this.tableFor(macro);
    uniforms.macro.value=macro;this.useTable(uniforms,table);
    const hook=(shader,renderer)=>{
      previous?.call(material,shader,renderer);
      if(!shader.vertexShader.includes('#include <project_vertex>')||!shader.fragmentShader.includes('#include <common>'))throw Error('Unsupported candidate clipping shader');
      Object.assign(shader.uniforms,{candidateClipTexture:uniforms.texture,candidateClipCount:uniforms.count,
        candidateMacro:uniforms.macro,candidateHasFeatureIds:{value:featureIds?1:0},
        candidateClipPages:uniforms.pages,candidateWildcardCount:uniforms.wildcards});
      // Interpolate source-relative coordinates. Large world X/Z values on
      // thin triangles lost centimetres in the real fragment interpolator.
      // Three uploads modelMatrix for every object, including cached programs.
      const attribute=featureIds&&!shader.vertexShader.includes('attribute float _feature_id_0;')?'attribute float _feature_id_0;':'';
      shader.vertexShader=shader.vertexShader.replace('#include <common>',`#include <common>\n${attribute}\nvarying vec3 vCandidatePosition;\nvarying float vCandidateFeatureId;`)
        .replace('#include <project_vertex>',`#include <project_vertex>\nvec4 candidatePosition=vec4(transformed,1.0);\n#ifdef USE_BATCHING\ncandidatePosition=batchingMatrix*candidatePosition;\n#endif\n#ifdef USE_INSTANCING\ncandidatePosition=instanceMatrix*candidatePosition;\n#endif\nvCandidatePosition=mat3(modelMatrix)*candidatePosition.xyz;\nvCandidateFeatureId=${featureIds?'_feature_id_0':'0.0'};`);
      shader.fragmentShader=shader.fragmentShader.replace('#include <common>',`#include <common>
// Transmission shaders declare this later in their own pars chunk.
#ifndef USE_TRANSMISSION
uniform mat4 modelMatrix;
#endif
uniform sampler2D candidateClipTexture;
uniform float candidateClipCount;
uniform float candidateClipPages;
uniform float candidateWildcardCount;
uniform float candidateMacro;
uniform float candidateHasFeatureIds;
varying vec3 vCandidatePosition;
varying float vCandidateFeatureId;
float candidateCross(vec2 a,vec2 b){return a.x*b.y-a.y*b.x;}
vec4 candidateCell(int index,float column){
  float entry=float(index);
  return texture2D(candidateClipTexture,vec2((mod(entry,candidateClipPages)+column)/candidateClipPages,
    (floor(entry/candidateClipPages)+0.5)/${MAX_TRIANGLES}.0));
}
bool candidateRange(vec3 candidateWorldPosition,int start,int count){
  vec2 p=candidateWorldPosition.xz;
  for(int step=0;step<${MAX_TRIANGLES};step++){
    if(step>=count)break;
    int i=start+step;
    vec4 box=candidateCell(i,0.625);
    if(p.x<box.x||p.y<box.y||p.x>box.z||p.y>box.w)continue;
    vec4 owner=candidateCell(i,0.875);
    if(owner.y>0.0&&abs(owner.y-candidateMacro)>0.5)continue;
    if(candidateHasFeatureIds>0.5&&owner.x>0.0&&abs(owner.x-vCandidateFeatureId)>0.5)continue;
    vec4 ab=candidateCell(i,0.125);
    vec4 cy=candidateCell(i,0.375);
    if(candidateWorldPosition.y<cy.z||candidateWorldPosition.y>cy.w)continue;
    float a=candidateCross(ab.zw-ab.xy,p-ab.xy),b=candidateCross(cy.xy-ab.zw,p-ab.zw),c=candidateCross(ab.xy-cy.xy,p-cy.xy);
    if((a>=-0.001&&b>=-0.001&&c>=-0.001)||(a<=0.001&&b<=0.001&&c<=0.001))return true;
  }
  return false;
}
bool candidateInside(vec3 candidateWorldPosition){
  int count=int(candidateClipCount);
  if(count==0)return false;
  if(candidateClipPages<=1.0)return candidateRange(candidateWorldPosition,0,count);
  if(candidateHasFeatureIds>0.5){
    int wildcard=int(candidateWildcardCount);
    if(candidateRange(candidateWorldPosition,0,wildcard))return true;
    if(vCandidateFeatureId<0.5)return false;
    int low=wildcard,high=count;
    // The largest representable table has 163840 records, so 18 comparisons suffice.
    for(int step=0;step<18;step++){
      if(low>=high)break;
      int mid=(low+high)/2;
      vec4 owner=candidateCell(mid,0.875);
      if(abs(owner.x-vCandidateFeatureId)<0.5)
        return candidateRange(candidateWorldPosition,int(owner.z),int(owner.w));
      if(owner.x<vCandidateFeatureId)low=mid+1;
      else high=mid;
    }
    return false;
  }
  // Untagged near meshes already have their source tile's membership-filtered table.
  // Also preserve the original spatial fallback for untagged, unscoped source meshes.
  for(int start=0;start<count;start+=${MAX_TRIANGLES})
    if(candidateRange(candidateWorldPosition,start,min(${MAX_TRIANGLES},count-start)))return true;
  return false;
}`).replace(/void\s+main\s*\(\s*\)\s*\{/,'void main(){\nif(candidateInside(vCandidatePosition+modelMatrix[3].xyz))discard;');
    };
    material.onBeforeCompile=hook;material.customProgramCacheKey=()=>`${previousKey}|candidate-city-clip-v4|${MAX_TRIANGLES}|${featureIds?1:0}|${scope?1:0}`;
    material.needsUpdate=true;this.bindings.set(material,{previous,cacheKey,hook,uniforms,scope,macro});
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
        scope={...this.newTable(),id:record.id,macroId,macro:hash(macroId),ids:new Set(record.ids),clipIds:new Set()};
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
  getState(){return {triangles:this.triangleCount,triangleLimit:MAX_TRIANGLES,macroTextures:this.macroTables.size,denseMacroTables:[...this.macroTables].filter(([,t])=>t.pages>1).map(([macro,t])=>({macro,triangles:t.triangles,pages:t.pages,maxFeatureSpan:t.maxFeatureSpan})),clippingTexture:{width:this.texture.image.width,height:this.texture.image.height,bytes:this.data.byteLength,
    type:this.texture.type===this.THREE.FloatType?'FloatType':this.texture.type,format:this.texture.format===this.THREE.RGBAFormat?'RGBAFormat':this.texture.format,
    minFilter:this.texture.minFilter===this.THREE.NearestFilter?'NearestFilter':this.texture.minFilter,
    magFilter:this.texture.magFilter===this.THREE.NearestFilter?'NearestFilter':this.texture.magFilter,generateMipmaps:this.texture.generateMipmaps},sourceObjects:this.objects.size,boundMaterials:this.bindings.size,revision:this.revision,
    ownerScopedSources:[...this.objects.values()].filter(({scope})=>scope).map(({scope})=>({id:scope.id,macro_id:scope.macroId,
      feature_local_ids:[...scope.ids],triangles:scope.triangles,clip_feature_local_ids:[...scope.clipIds]}))};}
  dispose(){for(const object of [...this.objects.keys()])this.releaseObject(object);for(const table of this.macroTables.values())table.texture.dispose();this.macroTables.clear();this.texture.dispose();}
}
