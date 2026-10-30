import {getVerifiedOrdinaryAsset} from './ordinary-asset-verification.js';

const SHA=/^[a-f0-9]{64}$/;
const finitePoint=p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite)&&Math.abs(p[0])<=180&&Math.abs(p[1])<=85;
const polygons=g=>g?.type==='Polygon'?[g.coordinates]:g?.type==='MultiPolygon'?g.coordinates:[];
export function validCandidateGeometry(g) {
  const parts=polygons(g);
  return parts.length>0&&parts.length<=32&&parts.every(p=>p.length>0&&p.length<=8&&p.every(r=>r.length>=4&&r.length<=65
    &&r.every(finitePoint)&&r[0].every((v,i)=>v===r.at(-1)[i])));
}
export function mergeCandidateCityModels(existing,manifest) {
  if(manifest?.schema!=='candidate-city-integrations-v1'||!Array.isArray(manifest.models))throw Error('候选模型全局目录格式无效');
  const ids=new Set(existing.map(row=>row.id));
  const models=manifest.models.map(row=>{
    if(!row.id||ids.has(row.id)||row.kind!=='building'||!finitePoint([row.lng,row.lat])
      ||!Number.isFinite(row.heading)||!Number.isFinite(row.height_m)||row.height_m<=0
      ||(row.scale!==undefined&&(!Number.isFinite(row.scale)||row.scale<=0))
      ||!row.placement||!['estimated','map-aligned'].includes(row.placement.status)
      ||!row.navigation||typeof row.navigation.listed!=='boolean')throw Error(`候选模型定位无效：${row.id}`);
    ids.add(row.id);
    for(const key of ['web','lod']) {
      const asset=row.assets?.[key];
      if(!asset||typeof asset.file!=='string'||!asset.file.startsWith('assets/')||asset.file.includes('..')
        ||!Number.isInteger(asset.bytes)||asset.bytes<=0||asset.bytes>=100000000||!SHA.test(asset.sha256))throw Error(`候选模型资产无效：${row.id}/${key}`);
    }
    for(const key of ['collision_geometry','replacement_geometry'])if(row[key]&&!validCandidateGeometry(row[key]))throw Error(`候选模型边界无效：${row.id}/${key}`);
    if(row.site_replacement&&(!row.site_replacement.id||!validCandidateGeometry(row.site_replacement.geometry)))throw Error(`候选模型场址修正无效：${row.id}`);
    if(row.navigation.listed&&(!finitePoint(row.navigation.walkStart)||!Number.isFinite(row.navigation.bearing)))throw Error(`候选模型漫游起点无效：${row.id}`);
    return {...row,candidate_id:row.id,city_integration:true,accepted:false,candidate_only:true,
      model:row.assets.web.file,lod_model:row.assets.lod.file,maxDistance:row.maxDistance??450,
      lod_switch_in_m:row.lod_switch_in_m??75,lod_switch_out_m:row.lod_switch_out_m??115,
      overviewZoom:row.overviewZoom??18.4,detail_level:'architectural'};
  });
  return [...existing,...models];
}

export function candidateAssetVisible(record,scene) {
  if(!record?.city_integration||record.status!=='loaded'||!record.object?.visible||record.catalogDisposed)return false;
  let inScene=false;
  for(let n=record.object;n;n=n.parent){if(n.visible===false)return false;if(n===scene){inScene=true;break;}}
  const variant=record.activeVariant==='full'?'web':record.activeVariant==='distant'?'lod':null;
  const receipt=getVerifiedOrdinaryAsset(record.object),asset=record.assets?.[variant];
  return Boolean(inScene&&variant&&asset&&receipt&&receipt.modelId===record.id&&receipt.variant===variant
    &&receipt.sha256===asset.sha256&&receipt.bytes===asset.bytes&&receipt.file===asset.file);
}
function ringContains(r,p) {
  let inside=false;
  for(let i=0,j=r.length-1;i<r.length;j=i++)if((r[i][1]>p[1])!==(r[j][1]>p[1])
    &&p[0]<(r[j][0]-r[i][0])*(p[1]-r[i][1])/(r[j][1]-r[i][1])+r[i][0])inside=!inside;
  return inside;
}
export function candidateGeometryContains(g,p) {
  return polygons(g).some(rings=>ringContains(rings[0],p)&&!rings.slice(1).some(r=>ringContains(r,p)));
}

/** Display corrections are deliberately separate from the accepted precise registry.
 * Every correction is conditional on a currently visible, SHA-verified asset.
 */
export class CandidateCityState {
  constructor({getRecords,getScene,onChange=()=>{}}){Object.assign(this,{getRecords,getScene,onChange});this.active=[];this.clips=[];this.signature='';this.revision=0;}
  sync(){
    const active=[...this.getRecords().values()].filter(r=>candidateAssetVisible(r,this.getScene()));
    const clips=new Map();
    for(const r of active){
      if(r.replacement_geometry)clips.set(r.id,{id:r.id,geometry:r.replacement_geometry,source_feature_ids:r.source_feature_ids||{},owner:r.owner,owners:r.owners});
      const site=r.site_replacement;
      if(site)clips.set(site.id,{...site,source_feature_ids:site.source_feature_ids||{}});
    }
    const signature=JSON.stringify([active.map(r=>[r.id,r.activeVariant,r.assets[r.activeVariant==='full'?'web':'lod'].sha256]),[...clips.values()]]);
    this.active=active;this.clips=[...clips.values()];
    if(signature===this.signature)return false;
    this.signature=signature;this.revision++;this.onChange(this);return true;
  }
  getState(){return {revision:this.revision,active:this.active.map(r=>({id:r.id,variant:r.activeVariant,assetSha256:r.assets[r.activeVariant==='full'?'web':'lod'].sha256})),clips:this.clips.map(c=>({id:c.id,geometry:c.geometry,source_feature_ids:c.source_feature_ids,owner:c.owner,owners:c.owners}))};}
  clipsPoint(lng,lat,source){
    if(!source)return false;
    return this.clips.some(c=>{
      const ids=c.source_feature_ids?.[source.layer];
      const matches=source.name!=='overture-buildings'||Boolean(ids?.includes(String(source.id))||ids?.includes(String(source.propertyId)));
      return matches&&candidateGeometryContains(c.geometry,[lng,lat]);
    });
  }
  collisions(){return this.active.filter(r=>r.collision_geometry).map(r=>({id:r.id,geometry:r.collision_geometry}));}
}
