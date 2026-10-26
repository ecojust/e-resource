// A shader can sample only its own parent's local feature namespace.
const materialOwners = new WeakMap();
// Three caches a material's compiled uniforms by program key. Keep these
// containers alive for the material, not the shorter-lived macro mask: a cache
// hit skips onBeforeCompile when an ordinary catalog rebinds the same far mesh.
const materialUniforms = new WeakMap();

/** Replace individual far buildings only after their physical near model is ready. */
export class CityFeatureMask {
  constructor(THREE, featureCount) {
    if (!Number.isInteger(featureCount) || featureCount < 1 || featureCount > 16777215) throw new Error('Invalid city feature count');
    this.THREE=THREE; this.count=featureCount;
    this.width=2**Math.ceil(Math.log2(Math.ceil(Math.sqrt(featureCount+1))));
    this.data=new Uint8Array(this.width*this.width);
    this.references=new Uint32Array(featureCount+1); this.owners=new Map(); this.bindings=new Map(); this.shadowBindings=[];this.boundMeshes=new Set();
    this.texture=new THREE.DataTexture(this.data,this.width,this.width,THREE.RedFormat,THREE.UnsignedByteType);
    this.texture.magFilter=this.texture.minFilter=THREE.NearestFilter;
    this.texture.generateMipmaps=false; this.texture.flipY=false; this.texture.needsUpdate=true;
    this.disposed=false;
  }
  setOwner(owner, ids=[]) {
    if(this.disposed)throw new Error('City feature mask was disposed');
    // Validate the whole transaction before changing any existing ownership.
    const next=new Set(ids);
    for(const id of next)if(!Number.isInteger(id)||id<1||id>this.count)throw new Error(`Invalid local city feature ID: ${id}`);
    const previous=this.owners.get(owner)||new Set(); let changed=false;
    for(const id of previous)if(!next.has(id)) {if(--this.references[id]===0)this.data[id]=0;changed=true;}
    for(const id of next)if(!previous.has(id)) {this.references[id]++;this.data[id]=255;changed=true;}
    if(next.size)this.owners.set(owner,next);else this.owners.delete(owner);
    if(changed)this.texture.needsUpdate=true;
  }
  removeOwner(owner){this.setOwner(owner,[]);}
  bindMaterial(material) {
    if(this.disposed)throw new Error('City feature mask was disposed');
    if(this.bindings.has(material))return;
    if(materialOwners.has(material)&&materialOwners.get(material)!==this)throw new Error('Far city material is shared across feature masks');
    const previous=material.onBeforeCompile, cacheKey=material.customProgramCacheKey;
    // Three's default key reads this.onBeforeCompile. Capture before wrapping.
    const previousKey=cacheKey?.call(material)||'';
    let uniforms=materialUniforms.get(material);
    if(!uniforms) {
      uniforms={texture:{value:null},width:{value:1}};
      materialUniforms.set(material,uniforms);
    }
    uniforms.texture.value=this.texture;uniforms.width.value=this.width;
    const hook=(shader,renderer)=>{
      previous?.call(material,shader,renderer);
      for(const [source,anchor] of [[shader.vertexShader,'#include <common>'],[shader.vertexShader,'#include <begin_vertex>'],
        [shader.fragmentShader,'#include <common>']]) {
        if(!source.includes(anchor))throw new Error(`Unsupported city mask shader: ${anchor}`);
      }
      const main=/void\s+main\s*\(\s*\)\s*\{/;
      if(!main.test(shader.fragmentShader))throw new Error('Unsupported city mask shader: fragment main');
      shader.uniforms.cityFeatureMask=uniforms.texture;shader.uniforms.cityFeatureMaskWidth=uniforms.width;
      shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nattribute float _feature_id_0;\nvarying float vCityFeatureId;')
        .replace('#include <begin_vertex>','#include <begin_vertex>\nvCityFeatureId = _feature_id_0;');
      shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nuniform sampler2D cityFeatureMask;\nuniform float cityFeatureMaskWidth;\nvarying float vCityFeatureId;')
        .replace(main,'void main() {\nfloat cityId=floor(vCityFeatureId+0.5);\nvec2 maskUV=(vec2(mod(cityId,cityFeatureMaskWidth),floor(cityId/cityFeatureMaskWidth))+0.5)/cityFeatureMaskWidth;\nif(texture2D(cityFeatureMask,maskUV).r>0.5) discard;');
    };
    const key=()=>`${previousKey}|city-feature-mask-v2`;
    this.bindings.set(material,{previous,cacheKey,hook,key,uniforms});materialOwners.set(material,this);
    material.onBeforeCompile=hook;material.customProgramCacheKey=key;
    material.needsUpdate=true;
  }
  bindObject(group) {
    if(this.disposed)throw new Error('City feature mask was disposed');
    const meshes=[];
    group.traverse(mesh=>{if(mesh.isMesh&&!this.boundMeshes.has(mesh))meshes.push(mesh);});
    // Fail closed: an untagged roof or wall would keep occluding the new model.
    for(const mesh of meshes) {
      const ids=mesh.geometry.getAttribute('_feature_id_0');
      if(!ids || ids.itemSize!==1 || ids.count!==mesh.geometry.getAttribute('position')?.count)throw new Error('Far city geometry is missing feature IDs');
      for(let i=0;i<ids.count;i++)if(!Number.isInteger(ids.getX(i))||ids.getX(i)<1||ids.getX(i)>this.count)throw new Error('Far city geometry has an invalid feature ID');
      const index=mesh.geometry.index,count=index?.count??ids.count;
      if(count%3)throw new Error('Far city geometry has incomplete triangles');
      for(let i=0;i<count;i+=3) {
        const a=ids.getX(index?index.getX(i):i),b=ids.getX(index?index.getX(i+1):i+1),c=ids.getX(index?index.getX(i+2):i+2);
        if(!Number.isInteger(a)||a!==b||a!==c)throw new Error('Far city triangle mixes feature IDs');
      }
      for(const material of Array.isArray(mesh.material)?mesh.material:[mesh.material]) {
        if(!material)throw new Error('Far city geometry is missing a material');
        if(materialOwners.has(material)&&materialOwners.get(material)!==this)throw new Error('Far city material is shared across feature masks');
      }
    }
    for(const mesh of meshes) {
      for(const material of Array.isArray(mesh.material)?mesh.material:[mesh.material])this.bindMaterial(material);
      // Install even while castShadow is false: a lighting owner may enable it
      // later. The same feature must disappear from visible/depth/distance passes.
      {
        const oldDepth=mesh.customDepthMaterial, oldDistance=mesh.customDistanceMaterial;
        const shadowMaterial=(old,make)=>{
          const result=old?old.clone():make();
          if(old){result.onBeforeCompile=old.onBeforeCompile;result.customProgramCacheKey=old.customProgramCacheKey;}
          return result;
        };
        mesh.customDepthMaterial=shadowMaterial(oldDepth,()=>new this.THREE.MeshDepthMaterial({depthPacking:this.THREE.RGBADepthPacking}));
        mesh.customDistanceMaterial=shadowMaterial(oldDistance,()=>new this.THREE.MeshDistanceMaterial());
        this.bindMaterial(mesh.customDepthMaterial);this.bindMaterial(mesh.customDistanceMaterial);
        this.shadowBindings.push({mesh,oldDepth,oldDistance,depth:mesh.customDepthMaterial,distance:mesh.customDistanceMaterial});
      }
      this.boundMeshes.add(mesh);
    }
  }
  dispose() {
    if(this.disposed)return;this.disposed=true;
    this.data.fill(0);this.references.fill(0);
    const releasedMaterials=new Set();
    for(const [material,{previous,cacheKey,hook,key,uniforms}] of this.bindings) {
      if(materialOwners.get(material)!==this)continue;
      // Release the GPU texture without leaving a live material holder pointing
      // at a disposed mask. A later owner updates these same two containers.
      if(uniforms.texture.value===this.texture){uniforms.texture.value=null;uniforms.width.value=1;}
      if(material.onBeforeCompile===hook)material.onBeforeCompile=previous;
      if(material.customProgramCacheKey===key)material.customProgramCacheKey=cacheKey;
      if(materialOwners.get(material)===this)materialOwners.delete(material);
      material.needsUpdate=true;
      // Unmasked rendering may compile a different program before the next
      // macro binds. Three stores one uniforms object per material, so stable
      // holders alone cannot repair a subsequent cached masked-program hit.
      // Material.dispose releases renderer program references only; the far
      // material object, its maps and geometry remain reusable and untouched.
      material.dispose();releasedMaterials.add(material);
    }
    for(const item of this.shadowBindings) {
      if(item.mesh.customDepthMaterial===item.depth)item.mesh.customDepthMaterial=item.oldDepth;
      if(item.mesh.customDistanceMaterial===item.distance)item.mesh.customDistanceMaterial=item.oldDistance;
      if(!releasedMaterials.has(item.depth))item.depth.dispose();
      if(!releasedMaterials.has(item.distance))item.distance.dispose();
    }
    this.texture.dispose();this.owners.clear();this.bindings.clear();this.shadowBindings=[];this.boundMeshes.clear();
  }
}
