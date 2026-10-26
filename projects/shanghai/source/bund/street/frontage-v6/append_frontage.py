#!/usr/bin/env python3
"""Append bounded facade-to-road paving to a frozen street GLB; never edit the project.

All existing raw buffer bytes, primitives, accessors and materials are retained.
Only selected frozen primary front edges generate surface. Other buildings are
negative masks, including courtyard interiors; they never generate new paving.
"""
import argparse,copy,gzip,hashlib,importlib.util,json,math,struct,subprocess,sys
from pathlib import Path
import numpy as np
from shapely.geometry import shape,Polygon,LineString,Point,box,mapping
from shapely.geometry.polygon import orient
from shapely.ops import transform,unary_union

ORIGIN=(121.4862,31.2385)
BASE,TOP=.003,.075
LIMIT=24

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
 b=Path(path).read_bytes();return json.loads(gzip.decompress(b) if str(path).endswith('.gz') else b)
def write(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def polygons(g):
 if g.is_empty:return []
 return [g] if g.geom_type=='Polygon' else [p for item in getattr(g,'geoms',[]) for p in polygons(item)]
def closed_outer(g):return unary_union([Polygon(p.exterior) for p in polygons(g)])
def forward_road_point(road,point,direction):
 """Project only towards the confirmed public front, not a nearer side street."""
 assert not road.contains(point),'Facade endpoint unexpectedly lies inside asphalt'
 ray=LineString([point.coords[0],(point.x+direction[0]*LIMIT,point.y+direction[1]*LIMIT)])
 boundary=unary_union([LineString(p.exterior.coords) for p in polygons(road)])
 hit=ray.intersection(boundary)
 def points(g):
  if g.is_empty:return []
  if g.geom_type=='Point':return [g]
  if g.geom_type=='LineString':return [Point(g.coords[0]),Point(g.coords[-1])]
  return [p for item in getattr(g,'geoms',[]) for p in points(item)]
 found=[p for p in points(hit) if p.distance(point)>1e-7]
 assert found,'No actual road boundary within forward width limit'
 return min(found,key=lambda p:p.distance(point))
def metric(g):
 scale=math.cos(math.radians(ORIGIN[1]));y0=math.asinh(math.tan(math.radians(ORIGIN[1])))
 return transform(lambda x,y,z=None:(6378137*math.radians(x-ORIGIN[0])*scale,-6378137*(math.asinh(math.tan(math.radians(y)))-y0)*scale),g)
def geographic(g):
 scale=math.cos(math.radians(ORIGIN[1]));y0=math.asinh(math.tan(math.radians(ORIGIN[1])))
 return transform(lambda x,z:(ORIGIN[0]+math.degrees(x/(6378137*scale)),math.degrees(math.atan(math.sinh(y0-z/(6378137*scale))))),g)
def glb(path):
 b=Path(path).read_bytes();magic,version,size=struct.unpack_from('<III',b);assert magic==0x46546c67 and version==2 and size==len(b)
 n,kind=struct.unpack_from('<II',b,12);assert kind==0x4e4f534a
 count,kind=struct.unpack_from('<II',b,20+n);assert kind==0x004e4942
 return json.loads(b[20:20+n]),b[28+n:28+n+count]
def save_glb(path,doc,blob):
 data=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();data+=b' '*((-len(data))%4)
 blob=bytes(blob);blob+=b'\0'*((-len(blob))%4)
 Path(path).write_bytes(struct.pack('<III',0x46546c67,2,28+len(data)+len(blob))+struct.pack('<II',len(data),0x4e4f534a)+data+struct.pack('<II',len(blob),0x004e4942)+blob)
def accessor(doc,blob,index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];assert v['buffer']==0 and not v.get('byteStride')
 typ={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']];size={'SCALAR':1,'VEC3':3}[a['type']]
 return np.frombuffer(blob,dtype=typ,count=a['count']*size,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],size)
def top_geometry(doc,blob,names):
 parts=[];triangles=0
 for prim in doc['meshes'][0]['primitives']:
  if doc['materials'][prim['material']]['name'] not in names:continue
  p=accessor(doc,blob,prim['attributes']['POSITION']);indices=accessor(doc,blob,prim['indices']).reshape(-1,3);t=p[indices].astype(float)
  n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);keep=(n[:,1]>1e-10)&(np.ptp(t[:,:,1],axis=1)<1e-6)
  for tri in t[keep]:parts.append(Polygon(tri[:,[0,2]]));triangles+=1
 return unary_union(parts),triangles

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--inputs',type=Path,default=Path(__file__).parent/'inputs');ap.add_argument('--output',type=Path,required=True);ap.add_argument('--ids',nargs='+',default=['bund05','bund06','bund14']);ap.add_argument('--gltfpack',required=True);args=ap.parse_args()
 I=args.inputs.resolve();O=args.output.resolve();assert O!=I and not O.is_relative_to(I)
 assert not (O/'street-frontage-audit.json').exists(),'Use a fresh output directory'
 O.mkdir(parents=True,exist_ok=True)
 source=read(I/'source-manifest.json')
 for f in source['files']:
  p=(I/f['file']).resolve();assert p.is_relative_to(I) and sha(p)==f['sha256'] and p.stat().st_size==f['bytes'],'Frozen source differs: '+f['file']
 assert len(set(args.ids))==len(args.ids)
 sys.path.insert(0,str(I/'source/city'));from build_district_models import Mesh
 sys.path.insert(0,str(I/'source/bund/street'));from connector_paving import shortest_outer_chain
 raw_before=I/'assets/models/bund/bund-streets.glb';doc,blob=glb(raw_before);old=copy.deepcopy(doc)
 assert len(doc['buffers'])==1 and len(doc['meshes'])==1 and doc['nodes']==[{'name':'Bund mapped public streetscape','mesh':0}]
 sidecar=read(I/'data/bund/street-interaction-v5.json');assert sidecar['owner']=='bund-streets' and sidecar['origin']==list(ORIGIN)
 assert sidecar['raw_model_sha256']==sha(raw_before) and sidecar['web_model_sha256']==sha(I/'assets/models/bund/web/bund-streets.glb')
 baseline_feature_count=len(sidecar['features']);baseline_obstacles=copy.deepcopy(sidecar['local_obstacles'])
 road,road_tris=top_geometry(doc,blob,{'BundRoadSurface'})
 old_paving,paving_tris=top_geometry(doc,blob,{'BundStonePaving','BundFrontagePaving','BundGraniteCurb','BundPlantingGranite','BundRoadGutter'})
 supporting=unary_union([metric(shape(f['geometry'])) for f in sidecar['features'] if f['properties']['role']=='walk-surface'])
 protected=unary_union([metric(shape(f['geometry'])) for f in sidecar['features'] if f['properties']['role']=='obstacle'])
 map_features=read(I/'source/bund/street/bund-map.geojson')['features']
 water=unary_union([metric(shape(f['geometry'])) for f in map_features if f['properties'].get('layer')=='water' and f['geometry']['type'] in ('Polygon','MultiPolygon')])
 old_candidates=read(I/'source/bund/bund-candidates.json')['candidates']
 frozen={p.parent.name:read(p) for p in sorted((I/'geometry').glob('*/geometry-input.json'))}
 assert set(args.ids).issubset(frozen),'Missing frozen target input'
 table=read(I/'assets/city-detail/macros/14-13720-6694/feature-table.json.gz')
 building_shapes=[metric(shape(x['geometry'])) for x in old_candidates]+[metric(shape(x['geometry'])) for x in frozen.values()]+[metric(shape(x['geometry'])) for x in table['features']]
 # A courtyard is not public pavement evidence. Preserve the entire outer
 # building envelope as unavailable here, even where its source has holes.
 buildings=unary_union([closed_outer(g) for g in building_shapes]).buffer(.08)
 road_sources=read(I/'source/bund/street/bund-streets-road-check.geojson')['features']
 road_source=unary_union([metric(shape(f['geometry'])) for f in road_sources if f['properties'].get('role')=='asphalt_surface'])
 assert road.hausdorff_distance(road_source)<.00015,'Frozen road audit is inconsistent with rendered asphalt'
 crop=metric(box(121.4842,31.23545,121.4892,31.2419))
 exclusions={'existing_rendered_paving_curbs_gutters':old_paving,'existing_supported_surfaces':supporting,
  'actual_asphalt_road':road,'water':water,'all_known_building_outer_envelopes_with_08m_clearance':buildings,
  'protected_source_openings_and_planting_beds':protected}
 records=[];features=[];patches=[];mesh=Mesh();new_features=[]
 for ident in args.ids:
  g=frozen[ident];edge=metric(LineString(g['front_edge']['endpoints_wgs84']));ends=[Point(p) for p in edge.coords]
  outward=g['front_edge']['outward_normal_east_north'];direction=(outward[0],-outward[1])
  projected=[forward_road_point(road,p,direction) for p in ends]
  road_edge=shortest_outer_chain(road,projected);envelope=Polygon(list(edge.coords)+list(road_edge.coords)[::-1])
  assert envelope.is_valid and envelope.area>0,(ident,'invalid facade-road envelope')
  assert road_edge.length<edge.length+30,(ident,'road boundary wrapped a side road')
  width=max(Point(p).distance(edge) for p in road_edge.coords);assert width<LIMIT,(ident,width)
  patch=envelope.intersection(crop)
  for geom in exclusions.values():patch=patch.difference(geom)
  if patches:patch=patch.difference(unary_union(patches))
  allparts=polygons(patch);discarded=sum(p.area for p in allparts if p.area<=1e-6)
  patch=unary_union([orient(p,sign=1) for p in allparts if p.area>1e-6]);assert not patch.is_empty and patch.is_valid,(ident,'no valid bounded gap')
  overlaps={name:patch.intersection(geom).area for name,geom in exclusions.items()};assert max(overlaps.values())<1e-6
  assert patch.difference(envelope).area<1e-6
  for p in polygons(patch):
   rings=[list(p.exterior.coords)[:-1]]+[list(r.coords)[:-1] for r in p.interiors]
   mesh.polygon(rings,BASE,TOP,mesh)
  patches.append(patch)
  record={'id':ident,'front_edge_index':g['front_edge']['edge_index'],'front_edge_length_m':edge.length,'maximum_width_m':width,
   'road_selection':'First actual road outer edge hit in positive confirmed facade-normal direction; avoids nearer side-street boundaries',
   'forward_projection_distances_m':[a.distance(b) for a,b in zip(ends,projected)],
   'envelope_area_m2':envelope.area,'new_paving_area_m2':patch.area,'discarded_under_1e_minus6_m2':discarded,
   'overlap_m2':overlaps,'outside_envelope_m2':patch.difference(envelope).area,'base_m':BASE,'top_m':TOP,
   'geometry_input_sha256':sha(I/'geometry'/ident/'geometry-input.json'),'footprint_source':g['osm'],
   'scope':'Only primary frozen public street front; no side alley, inter-building gap, internal courtyard or inferred platform.'}
  records.append(record)
  for role,geom in [('confirmed_primary_front',edge),('actual_road_outer_edge',road_edge),('bounded_estimated_envelope',envelope),('new_paving',patch)]:
   features.append({'type':'Feature','properties':{'id':ident,'role':role,'height_world_m':TOP},'geometry':mapping(geographic(geom))})
  new_features.append({'type':'Feature','properties':{'id':'v6-frontage-'+ident,'role':'walk-surface','base_world_m':BASE,'top_world_m':TOP,'height_world_m':TOP,
    'blocks_walk':False,'blocks_camera':False,'source':'street-frontage-audit.json / frozen '+ident+' primary front edge and existing rendered road outer edge',
    'evidence_class':'source-bounded estimated public sidewalk; photograph-corroborated continuity, construction datum inferred'},'geometry':mapping(geographic(patch))})
 new=unary_union(patches);v=np.asarray(mesh.positions,dtype='<f4');normals=np.asarray(mesh.normals,dtype='<f4');indices=np.asarray(mesh.indices,dtype='<u4').reshape(-1,3)
 t=v[indices].astype(float);n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);keep=np.linalg.norm(n,axis=1)>0
 zero_removed=int((~keep).sum());indices=indices[keep].reshape(-1);assert np.isfinite(v).all() and np.isfinite(normals).all()
 binary=bytearray(blob)
 def append(array,component,kind,target):
  while len(binary)%4:binary.append(0)
  offset=len(binary);binary.extend(array.tobytes());view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':array.nbytes,'target':target})
  a={'bufferView':view,'componentType':component,'count':len(array),'type':kind}
  if kind=='VEC3':a.update(min=array.min(axis=0).tolist(),max=array.max(axis=0).tolist())
  result=len(doc['accessors']);doc['accessors'].append(a);return result
 pos=append(v,5126,'VEC3',34962);normal=append(normals,5126,'VEC3',34962);index=append(indices,5125,'SCALAR',34963)
 mat=next(i for i,m in enumerate(doc['materials']) if m['name']=='BundFrontagePaving')
 doc['meshes'][0]['primitives'].append({'attributes':{'POSITION':pos,'NORMAL':normal},'indices':index,'material':mat})
 doc['buffers'][0]['byteLength']=len(binary);doc['asset']['generator']='Shanghai Bund street v5.0 + source-bounded primary frontages v6'
 raw=O/'bund-streets.glb';save_glb(raw,doc,binary)
 # These checks cover every original material and triangle, not a sample.
 assert bytes(binary[:len(blob)])==blob
 assert doc['materials']==old['materials'] and doc['nodes']==old['nodes'] and doc['scenes']==old['scenes']
 assert doc['accessors'][:len(old['accessors'])]==old['accessors'] and doc['bufferViews'][:len(old['bufferViews'])]==old['bufferViews']
 assert doc['meshes'][0]['primitives'][:len(old['meshes'][0]['primitives'])]==old['meshes'][0]['primitives']
 added_doc=copy.deepcopy(doc);added_doc['meshes'][0]['primitives']=[doc['meshes'][0]['primitives'][-1]]
 top,top_triangles=top_geometry(added_doc,bytes(binary),{'BundFrontagePaving'})
 delta=new.symmetric_difference(top).area;distance=new.hausdorff_distance(top)
 assert distance<.00015 and delta<.02,(delta,distance,'float32 added support surface differs')
 actual_overlaps={name:top.intersection(geom).area for name,geom in exclusions.items()}
 # At most float32 boundary rounding, never a guessed enlargement/buffer fill.
 assert top.difference(new.buffer(.00015)).area<1e-6
 web=O/'bund-streets-web.glb';subprocess.run([args.gltfpack,'-i',str(raw),'-o',str(web),'-cc','-noq','-kn','-km','-ke'],check=True)
 webdoc,webblob=glb(web);webdoc['asset']['copyright']=doc['asset']['copyright'];webdoc['asset']['generator']='Shanghai Bund streets v6 frontage append; Meshopt, no quantization';save_glb(web,webdoc,webblob)
 sidecar['features'].extend(new_features);sidecar['raw_model_sha256']=sha(raw);sidecar['web_model_sha256']=sha(web)
 sidecar['frontage_append']={'version':6,'targets':args.ids,'audit':'street-frontage-audit.json','base_world_m':BASE,'top_world_m':TOP,'estimated_not_surveyed':True}
 sidecar_path=O/'street-interaction-v5.json';write(sidecar_path,sidecar)
 original_sidecar=read(I/'data/bund/street-interaction-v5.json')
 assert sidecar['features'][:baseline_feature_count]==original_sidecar['features'] and sidecar['local_obstacles']==baseline_obstacles
 for path in [raw,web,sidecar_path]:assert path.stat().st_size<100000000
 baseline_triangles=sum(old['accessors'][p['indices']]['count']//3 for p in old['meshes'][0]['primitives'])
 audit={'schema':'bund-bounded-frontage-append-v6','passed':True,'targets':args.ids,'origin':list(ORIGIN),'single_existing_prop':'bund-streets',
  'raw_before_sha256':sha(raw_before),'raw_after_sha256':sha(raw),'web_before_sha256':sha(I/'assets/models/bund/web/bund-streets.glb'),'web_after_sha256':sha(web),
  'raw_bytes':raw.stat().st_size,'web_bytes':web.stat().st_size,'baseline_triangles':baseline_triangles,'added_triangles':len(indices)//3,'total_triangles':baseline_triangles+len(indices)//3,
  'existing_raw_binary_prefix_unchanged':True,'existing_materials_primitives_accessors_unchanged':True,'existing_material_count':len(old['materials']),
  'existing_primitive_count':len(old['meshes'][0]['primitives']),'existing_nodes_unchanged':True,
  'sidecar_original_features_unchanged':baseline_feature_count,'sidecar_original_obstacles_unchanged':len(baseline_obstacles),'sidecar_added_support_features':len(new_features),'sidecar_sha256':sha(sidecar_path),
  'new_paving_area_m2':new.area,'parts':records,'float32_surface_check':{'hausdorff_m':distance,'symmetric_difference_m2':delta,'upward_triangles':top_triangles,'exact_zero_area_triangles_removed':zero_removed,'boundary_tolerance_m':.00015,'rendered_overlap_m2':actual_overlaps},
  'building_exclusion_scope':{'old_detailed_candidates':len(old_candidates),'frozen_current_and_next':list(frozen),'generic_macro':table.get('macro_id','14-13720-6694'),'generic_features':len(table['features']),'courtyard_interiors_reserved':True,'building_clearance_m':.08,'clearance_policy':'Same conservative clearance as original v5 street generation'},
  'road_boundary_comes_from_actual_raw_triangles':road_tris,'old_paving_upward_triangles':paving_tris,'web_compression_flags':['-cc','-noq','-kn','-km','-ke'],
  'limits':['Plan envelopes are inferred only between frozen primary public facade and existing road edge; not surveyed sidewalk polygons.',
   'Top .075m is inherited modeled sidewalk datum; no actual Shanghai elevation or new stair claim.',
   'No new side alley, internal courtyard, garden, tree, railing, furniture or road geometry.',
   'Known buildings, reserved source openings, beds, water, road and old paving are excluded; geographic coverage is this bounded crop and frozen local source only.']}
 probes=[{'id':f['properties']['id'],'point':list(shape(f['geometry']).representative_point().coords)[0],
          'method':'Shapely interior representative_point of actual sidecar support polygon'} for f in new_features]
 write(O/'support-probes.json',probes)
 write(O/'street-frontage-audit.json',audit);write(O/'street-frontage-check.geojson',{'type':'FeatureCollection','features':features})
 exclusions_geo=[{'type':'Feature','properties':{'role':name},'geometry':mapping(geographic(geom.intersection(crop)))} for name,geom in exclusions.items()]
 write(O/'exclusions.geojson',{'type':'FeatureCollection','features':exclusions_geo})
 props=copy.deepcopy(read(I/'data/scene-props.json'));assert len(props)==1 and props[0]['id']=='bund-streets'
 props[0].update(raw_sha256=sha(raw),raw_bytes=raw.stat().st_size,web_sha256=sha(web),sha256=sha(web),web_bytes=web.stat().st_size,bytes=web.stat().st_size,
  triangles=audit['total_triangles'],interaction_sha256=sha(sidecar_path),interaction_bytes=sidecar_path.stat().st_size)
 props[0]['frontage_append']={'targets':args.ids,'estimated':True,'audit':'data/bund/validation/street-frontage-v6.json'}
 props[0]['version']=6.0;props[0]['validation']='data/bund/validation/street-frontage-v6.json'
 write(O/'scene-props.candidate.json',props)
 metadata=copy.deepcopy(read(I/'data/bund/models/bund-streets.json'))
 metadata.update(version=6.0,sha256=sha(raw),bytes=raw.stat().st_size,triangles=audit['total_triangles'],web_sha256=sha(web),web_bytes=web.stat().st_size,interaction_sha256=sha(sidecar_path))
 metadata['frontage_append']={**props[0]['frontage_append'],'new_paving_area_m2':new.area,'base_m':BASE,'top_m':TOP,'existing_geometry_unchanged':True}
 write(O/'bund-streets-metadata.candidate.json',metadata);write(O/'bund-streets-web-metadata.candidate.json',props[0])
 print(json.dumps({k:audit[k] for k in ['passed','new_paving_area_m2','added_triangles','total_triangles','raw_bytes','web_bytes']},ensure_ascii=False))

if __name__=='__main__':main()
