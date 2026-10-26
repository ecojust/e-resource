"""Resumable frozen-input city builder. Never writes into the input project.
Pilot: --macros 14-13708-6688,14-13719-6695,14-13720-6694
Full build requires explicit --all; a pilot never marks city complete.
"""
import sys;sys.dont_write_bytecode=True
from pathlib import Path
import argparse,atexit,collections,copy,gzip,hashlib,json,math,os,struct,subprocess,time,traceback
from pack_client import GltfpackService
import numpy as np
import shapely,mapbox_earcut
from shapely.validation import explain_validity
from shapely.geometry import Polygon,MultiPolygon,shape
from shapely.strtree import STRtree
from geometry_engine import Encoder,Batch,write_near,feature_estimate
VERSION='shanghai-v5-adaptive-physical-v3-constrained-wall'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def atomic(path,obj,gz=False):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);b=canonical(obj)+b'\n';b=gzip.compress(b,compresslevel=6,mtime=0) if gz else b
 if len(b)>=100_000_000:raise RuntimeError('Published JSON exceeds100MB: '+str(path))
 tmp=path.with_name('.'+path.name+'.tmp-'+str(os.getpid()));tmp.write_bytes(b);os.replace(tmp,path)
def read(p):return json.loads(gzip.decompress(Path(p).read_bytes()) if str(p).endswith('.gz') else Path(p).read_bytes())
def polygons(g):return g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
def bounds(fs):
 ps=[p for f in fs for poly in polygons(f['geometry']) for ring in poly for p in ring]
 return [min(p[0] for p in ps),min(p[1] for p in ps),max(p[0] for p in ps),max(p[1] for p in ps)]
def family(props,H,area):
 cls=str(props.get('class','')).lower();sub=str(props.get('subtype','')).lower()
 if cls in ['house','detached','terrace','semidetached_house']:return 'house'
 if any(x in cls for x in ['warehouse','industrial','factory','manufactur']):return 'industrial'
 if any(x in cls for x in ['office','commercial','retail']):return 'office'
 if cls in ['apartments','dormitory']:return 'apartment'
 if sub=='residential' or cls=='residential':return 'house' if H<=10 and area<150 else 'apartment'
 if H<=10 and area<150:return 'house'
 if H<15 and area>800:return 'industrial'
 if 10<H<40 and area<1500:return 'apartment'
 if H>=40:return 'office'
 return 'unknown'

def glb_json(path):
 b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
def restore_glb_provenance(path,source):
 g,blob=glb_json(path);g['asset']['copyright']=source['asset'].get('copyright','© Overture Maps Foundation; © OpenStreetMap contributors ODbL-1.0; Qian Shi et al. CC BY4.0; CMAB/CNBH/GHSL CC BY4.0; inferred facade geometry MIT.')
 g['extras']={**source.get('extras',{}),**source.get('nodes',[{}])[0].get('extras',{})}
 js=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();js+=b' '*((-len(js))%4);path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(js)+len(blob))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(blob),0x004e4942)+blob)
 expanded=0
 for node in g['nodes']:
  if 'mesh' not in node:continue
  attrs=node.get('extensions',{}).get('EXT_mesh_gpu_instancing',{}).get('attributes',{});count=g['accessors'][next(iter(attrs.values()))]['count'] if attrs else 1
  expanded+=count*sum(g['accessors'][pr['indices']]['count']//3 for pr in g['meshes'][node['mesh']]['primitives'])
 return expanded

def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--output',type=Path,required=True);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--macros');g.add_argument('--all',action='store_true');p.add_argument('--gltfpack',required=True);p.add_argument('--gltfpack-library',type=Path);p.add_argument('--target-triangles',type=int,default=180000);p.add_argument('--microcell-m',type=float,default=250.0);p.add_argument('--enrichment',type=Path);p.add_argument('--plan-only',action='store_true');p.add_argument('--workers',type=int,choices=[1,2],default=1);p.add_argument('--worker-only',action='store_true',help=argparse.SUPPRESS);p.add_argument('--finalize-only',action='store_true');a=p.parse_args();P=a.project.resolve();O=a.output.resolve();HERE=Path(__file__).resolve().parent
 if O.is_relative_to(P) or P.is_relative_to(O):raise RuntimeError('Output must be separate from input project')
 O.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(P/'source/city'))
 from build_district_models import Mesh,cleaned_ring,building_height,write_glb
 from building_height_sampler import BuildingHeightSampler
 from roof_geometry import append_roof_shell
 baseline=read(P/'assets/city/manifest.json');raw_manifest=read(P/'data/fullcity-raw/manifest.json');base_config=read(P/'assets/city/build-configuration.json');exclude=read(P/'data/landmark-exclusions.json');residual=read(P/'data/parent-residual-overrides.json');roofs=read(P/'data/roofs/qualified-roofs.json');heightlock=read(P/'data/heights/height_sources_lock.json')
 selected=sorted(t['id'] for t in baseline['tiles']) if a.all else a.macros.split(',');base_rows={t['id']:t for t in baseline['tiles']};unknown=set(selected)-set(base_rows)
 if unknown:raise RuntimeError('Unknown macro: '+str(unknown))
 excluded={k:set(exclude[k+'_ids']) for k in ['building','building_part']};roofmap={x['key']:x for x in roofs['roofs']};enrichment=read(a.enrichment).get('features',{}) if a.enrichment else {}
 expected={'feature_count':baseline['feature_count'],'macro_count':baseline['model_count'],'renderable_exclusions':baseline['landmark_replacement_count'],'residuals':baseline['residual_parent_features'],'qualified_roofs':len(roofmap),'protected_keys':sum(map(len,excluded.values()))}
 assert expected=={'feature_count':1796419,'macro_count':1708,'renderable_exclusions':98,'residuals':401,'qualified_roofs':126,'protected_keys':103},expected
 hashes={n:sha(P/n) for n in ['assets/city/manifest.json','assets/city/build-configuration.json','data/fullcity-raw/manifest.json','data/landmark-exclusions.json','data/parent-residual-overrides.json','data/roofs/qualified-roofs.json','data/heights/height_sources_lock.json']}
 if hashes['data/heights/height_sources_lock.json']!=base_config['height_lock_sha256']:raise RuntimeError('Frozen height lock differs from current baseline')
 lock_verified=[]
 for f in heightlock['files']:
  path=P/'source/city'/f['path'] if f['path'].endswith('.py') else P/'data/heights'/f['path']
  if path.stat().st_size!=f['bytes'] or sha(path)!=f['sha256']:raise RuntimeError('Height dependency changed: '+f['path'])
  lock_verified.append(f)
 config={'version':VERSION,'input_hashes':hashes,'geometry_engine_sha256':sha(HERE/'geometry_engine.py'),'geometry_dependencies':{'numpy':np.__version__,'shapely':shapely.__version__,'geos':shapely.geos_version_string,'mapbox_earcut':mapbox_earcut.__version__},'builder_schema_version':VERSION,'roof_engine_sha256':sha(P/'source/city/roof_geometry.py'),'mesh_engine_sha256':sha(P/'source/city/build_district_models.py'),'near_transport':'deterministic gzip level6 mtime0; Meshopt noq', 'structural_wall':'GEOS constrained Delaunay of whole facade polygon with genuine openings; shared float32 world-space vertices', 'target_triangles':a.target_triangles,'microcell_m':float(a.microcell_m),'enrichment_sha256':sha(a.enrichment) if a.enrichment else None,'expected_city':expected,'dimension_policy':'No height/footprint enrichment accepted. Existing source/estimated values frozen; residual and landmark changes exactly follow current baseline.'}
 config_sha=hashlib.sha256(canonical(config)).hexdigest();cp=O/'build-configuration.json'
 if cp.exists() and read(cp)!=config:raise RuntimeError('Output configuration differs; choose a new output directory')
 atomic(cp,config);atomic(O/'source-provenance.json',{'builder_version':VERSION,'scripts':{n:sha(HERE/n) for n in ['build_city_v5.py','geometry_engine.py','pack_client.py','gltfpack_server.mjs']},'compression_execution':'persistent unmodified gltfpack library; identical arguments and output validation','immutable_snapshot_required':True});atomic(O/'height-inputs-verified.json',{'lock_sha256':hashes['data/heights/height_sources_lock.json'],'verified_files':len(lock_verified),'total_bytes':sum(x['bytes'] for x in lock_verified),'all_hashes_match':True})
 if a.plan_only:atomic(O/'plan.json',{'selected_macros':selected,'full_build_requested':a.all,'expected_city':expected});print('PLAN',len(selected));return
 worker_reports=[];process_macros=selected
 if a.finalize_only:process_macros=[]
 elif a.workers==2 and len(selected)>1:
  jobs=[]
  for group in [selected[::2],selected[1::2]]:
   command=[sys.executable,str(HERE/'build_city_v5.py'),'--project',str(P),'--output',str(O),'--macros',','.join(group),'--gltfpack',a.gltfpack,'--target-triangles',str(a.target_triangles),'--microcell-m',str(a.microcell_m),'--workers','1','--worker-only']
   if a.enrichment:command+=['--enrichment',str(a.enrichment)]
   if a.gltfpack_library:command+=['--gltfpack-library',str(a.gltfpack_library)]
   jobs.append(subprocess.Popen(command))
  for job in jobs:
   code=job.wait();report_file=O/'.work'/('worker-'+str(job.pid)+'.json')
   worker_reports.append(read(report_file) if report_file.exists() else {'errors':[{'error':'Worker did not publish completion report','pid':job.pid,'exit_code':code}],'built':[],'resumed':[]})
  process_macros=[]
 sampler=BuildingHeightSampler(P/'data/heights/alternatives/cnbh_2020_shanghai_core_dm.tif',P/'data/heights/shanghai_ghsl_anbh_2018_3arcsec.tif',P/'data/heights/cmab/shards')
 def roof_shell(rings,f):
  rm,wm=Mesh(),Mesh();r=f['roof'];append_roof_shell(rm,wm,rings,base=f['base'],height=f['height'],roof_height=r['roof_height'],roof_shape=r['roof_shape'],ridge_unit=r.get('ridge_unit'),down_slope_unit=r.get('down_slope_unit'));return rm,wm
 library=a.gltfpack_library or Path(a.gltfpack).resolve().parent/'library.js'
 if not library.exists():raise RuntimeError('Persistent gltfpack library not found; provide --gltfpack-library')
 packer=GltfpackService(library,server=HERE/'gltfpack_server.mjs') if process_macros else None
 if packer:atexit.register(packer.close)
 pack_stats={'calls':0,'pack_ms':0.0,'peak_rss_bytes':0}
 def pack(arguments):
  result=packer.pack(arguments);pack_stats['calls']+=1;pack_stats['pack_ms']+=result['packMs'];pack_stats['peak_rss_bytes']=max(pack_stats['peak_rss_bytes'],result['maxRssBytes']);return result
 atomic(O/'.work'/('compressor-'+str(os.getpid())+'.json'),{'library_sha256':sha(library),'version':packer.ready['version'] if packer else None,'server_sha256':sha(HERE/'gltfpack_server.mjs'),'calls_at_start':0})
 errors=[];run_start=time.perf_counter();resumed=[];built=[]
 for macro in process_macros:
  mdir=O/'macros'/macro;ready=mdir/'READY.json'
  try:
   if ready.exists():
    old=read(ready)
    if old['configuration_sha256']!=config_sha:raise RuntimeError('Ready configuration mismatch')
    if all((mdir/n).exists() and (mdir/n).stat().st_size==v['bytes'] and sha(mdir/n)==v['sha256'] for n,v in old['published_files'].items()):resumed.append(macro);print('RESUME',macro,flush=True);continue
    raise RuntimeError('READY file checksum mismatch; refusing silent reuse')
   started=time.perf_counter();mdir.mkdir(parents=True,exist_ok=True);z,x,y=macro.split('-');raw=P/f'data/fullcity-raw/tiles/{z}/{x}/{y}.geojson.gz';collection=read(raw);row=base_rows[macro];record=read(P/'assets/city/records'/f'{macro}.json');state=read(P/'assets/city/state'/f'{macro}.json')
   if sha(raw)!=row['source_sha256'] or state['source_sha256']!=row['source_sha256']:raise RuntimeError('Raw hash not current baseline')
   origin=[row['origin_longitude'],row['origin_latitude']];features=[];changes=[];excluded_renderable=[];nonrenderable=[];degenerate=[]
   for original in collection['features']:
    original_props=original['properties'];props=copy.deepcopy(original_props);identity=str(props['id']);layer=props['source_layer'];key=layer+':'+identity;geometry=copy.deepcopy(original['geometry']);is_residual=False
    if identity in excluded[layer]:
     if props.get('renderable') is not False:excluded_renderable.append(key)
     continue
    if props.get('renderable') is False:
     if identity in residual['parent_geometry_overrides']:
      geometry=copy.deepcopy(residual['parent_geometry_overrides'][identity]);is_residual=True;changes.append({'key':key,'kind':'footprint','reason':'Retain existing baseline exact parent-minus-parts residual; no new geometry interpretation','original_sha256':hashlib.sha256(canonical(original['geometry'])).hexdigest(),'effective_sha256':hashlib.sha256(canonical(geometry)).hexdigest()})
     else:nonrenderable.append(key);continue
    if key in exclude.get('geometry_overrides',{}):geometry=copy.deepcopy(exclude['geometry_overrides'][key]);changes.append({'key':key,'kind':'footprint','reason':'Preserve current landmark geometry override'})
    if key in enrichment:
     e=enrichment[key]
     if not e.get('source') or not e.get('reason'):raise RuntimeError('Enrichment requires source and reason: '+key)
     if any(k in e for k in ['geometry','height','height_m','base','min_height']):raise RuntimeError('Dimension enrichment is disabled; new approved height/geometry baseline required')
     allowed={'facade_color','facade_material','class','subtype','num_floors'}
     if set(e.get('properties',{}))-allowed:raise RuntimeError('Unrecognized enrichment properties')
     # Module floors can be enriched, but frozen geometry height remains derived
     # from original source props below, not enriched num_floors.
     props.update(e.get('properties',{}));changes.append({'key':key,'kind':'appearance_parameters','source':e['source'],'reason':e['reason'],'properties':e.get('properties',{})})
    hp={k:v for k,v in original_props.items() if not(is_residual and k in ['height','num_floors'])};base,H,quality=building_height(hp);provenance={}
    if quality=='fallback_12m':
     sampled=sampler.sample_geometry(geometry)
     if sampled and sampled['height_m']>base+.1:H=sampled['height_m'];quality=sampled['height_quality'];provenance=sampled
    rr=[]
    for component,poly in enumerate(polygons(geometry)):
     rings=[cleaned_ring(r,origin,j==0) for j,r in enumerate(poly)]
     if not rings or not rings[0]:degenerate.append({'key':key,'component':component,'reason':'Existing mesh threshold: degenerate exterior <0.01m2 or <3 vertices'});continue
     rr.append([r for r in rings if r])
    if not rr:raise RuntimeError('No renderable geometry: '+key)
    geoms=[Polygon(r[0],r[1:]) for r in rr];localg=geoms[0] if len(geoms)==1 else MultiPolygon(geoms);roof=roofmap.get(key)
    if not localg.is_valid:changes.append({'key':key,'kind':'local_projection_numeric_warning','reason':explain_validity(localg),'source_footprint_unchanged':True,'policy':'Retain original rings; no make_valid/buffer0 alteration. Separate decorative buffer operations must succeed.'})
    if roof:
     assert roof['geometry']==original['geometry'] and roof['original_properties']==original_props and roof['source_sha256']==row['source_sha256']
     assert abs(base-roof['base'])<1e-6 and abs(H-roof['height'])<1e-6 and not is_residual
    f={'key':key,'properties':props,'original_properties':original_props,'geometry':geometry,'rings':rr,'base':base,'height':H,'eave':H-roof['roof_height'] if roof else H,'height_quality':quality,'height_provenance':provenance,'roof':roof,'residual':is_residual,'local_geometry':localg,'family':family(props,H-base,localg.area)};features.append(f)
   features.sort(key=lambda f:f['key'])
   for i,f in enumerate(features,1):f['local_id']=i;pt=f['local_geometry'].representative_point();f['center']=[pt.x,pt.y];f['estimated_triangles']=feature_estimate(f)
   quality=dict(collections.Counter(f['height_quality'] for f in features));expected_quality={k:v for k,v in row['height_quality'].items() if v}
   if len(features)!=row['building_count'] or quality!=expected_quality:raise RuntimeError('Baseline feature/height quality mismatch: '+str((len(features),row['building_count'],quality,expected_quality)))
   actual_bounds=bounds(features)
   if max(abs(a-b) for a,b in zip(actual_bounds,row['geometry_bbox']))>1e-7:raise RuntimeError('Source geographic bounds changed')
   if sum(f['residual'] for f in features)!=record.get('residual_parent_features',0):raise RuntimeError('Residual count changed')
   expected_roofs=set(record.get('source_roof_enhancement',{}).get('keys',[]));actual_roofs={f['key'] for f in features if f['roof']}
   if expected_roofs!=actual_roofs:raise RuntimeError('Roof override coverage mismatch')
   # Far meshes reproduce the existing mesh/roof engines, plus local IDs.
   meshes=[Mesh() for _ in range(4)];ids=[[] for _ in meshes];online={'building':set(),'building_part':set()}
   for f in features:
    before=[len(m.positions) for m in meshes];roof_index=1 if f['height']<18 else 2 if f['height']<60 else 3
    for rings in f['rings']:
     if f['roof']:
      rm,wm=roof_shell(rings,f)
      for dest,src in [(meshes[roof_index],rm),(meshes[0],wm)]:
       off=len(dest.positions);dest.positions.extend(src.positions);dest.normals.extend(src.normals);dest.indices.extend(i+off for i in src.indices)
     else:meshes[roof_index].polygon(rings,f['base'],f['height'],meshes[0])
    for j,m in enumerate(meshes):ids[j].extend([f['local_id']]*(len(m.positions)-before[j]))
    p0=f['properties'];online[p0['source_layer']].add(p0['id'])
    if p0.get('building_id'):online['building'].add(p0['building_id'])
   extras={'district_name':'Shanghai v5 frozen baseline macro','origin_longitude':origin[0],'origin_latitude':origin[1],'macro_id':macro,'source_sha256':row['source_sha256'],'configuration_sha256':config_sha,'feature_count':len(features),'feature_table_file':'feature-table.json.gz','feature_id_base':1,'source_roof_keys':sorted(actual_roofs)}
   far_raw=mdir/'far.raw.glb';far_tri=write_glb(far_raw,meshes,extras)
   if far_tri!=row['triangles']:raise RuntimeError('Original far triangles changed: '+str((far_tri,row['triangles'])))
   b=far_raw.read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);blob=bytearray(b[28+n:])
   for m in g['meshes']:
    for prim in m['primitives']:
     v=np.asarray(ids[prim['material']],dtype='<u4');assert len(v)==g['accessors'][prim['attributes']['POSITION']]['count'];off=len(blob);blob.extend(v.tobytes());g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':v.nbytes,'target':34962});g['accessors'].append({'bufferView':len(g['bufferViews'])-1,'componentType':5125,'count':len(v),'type':'SCALAR'});prim['attributes']['_FEATURE_ID_0']=len(g['accessors'])-1
   g['buffers'][0]['byteLength']=len(blob);js=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();js+=b' '*((-len(js))%4);far_raw.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(js)+len(blob))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(blob),0x004e4942)+blob)
   far_source,_=glb_json(far_raw)
   far=mdir/'far.glb';pack(['-i',str(far_raw),'-o',str(far),'-cc','-noq','-kv','-km','-ke'])
   if restore_glb_provenance(far,far_source)!=far_tri:raise RuntimeError('Far compressed triangle count changed')
   far_raw_bytes=far_raw.stat().st_size;far_raw_sha256=sha(far_raw);far_raw.unlink()
   # Open generic inputs differ from old quantized bytes, not from resolved
   # heights/footprint geometry. Keep full precision for ID validation in pilot.
   feature_table={'schema':'city-v5-feature-table-v1','feature_id_base':1,'origin':origin,'keys':[None]+[f['key'] for f in features],'features':[{'localId':f['local_id'],'key':f['key'],'properties':f['properties'],'geometry':f['geometry'],'base':f['base'],'height':f['height'],'height_quality':f['height_quality'],'height_provenance':f['height_provenance'],'residual':f['residual'],'roof':f['roof'],'family':f['family'],'family_is_inferred':True,'family_basis':'source class/subtype where available, otherwise explicit height/footprint-scale inference','appearance_accuracy':'inferred module layout; no individual facade photograph'} for f in features]}
   atomic(mdir/'feature-table.json.gz',feature_table,True);atomic(mdir/'online-ids.json.gz',{k:sorted(v) for k,v in online.items()},True);atomic(mdir/'changes.json',{'changes':changes,'height_changes':[],'source_geometry_changes_only_existing_baseline_overrides':True,'physical_detail_changes':['Whole-facade perforated wall skin and shared true-opening returns replace independent bay structural instances; no internal opposing faces or bay TRS gaps','Retain instanced frames, glazing, sills and inset doors','Close courtyard-facing cornice thickness with correctly oriented interior-ring fascia'], 'near_cornice_projection_m':.07,'cornice_reason':'Inferred superficial near detail, does not change original far footprint or height'})
   tree=STRtree([f['local_geometry'] for f in features]);groups=collections.defaultdict(list)
   for f in features:groups[(math.floor(f['center'][0]/a.microcell_m),math.floor(f['center'][1]/a.microcell_m))].append(f)
   def split(fs,label):
    if len(fs)>1 and sum(f['estimated_triangles'] for f in fs)>a.target_triangles:
     span=[max(f['center'][i] for f in fs)-min(f['center'][i] for f in fs) for i in [0,1]];axis=span.index(max(span));ordered=sorted(fs,key=lambda f:(f['center'][axis],f['key']));mid=len(fs)//2
     return split(ordered[:mid],label+'-s0')+split(ordered[mid:],label+'-s1')
    return [(fs,label)]
   leaves=[leaf for (gx,gy),fs in sorted(groups.items()) for leaf in split(fs,f'{gx}_{gy}')];near=[];owners={}
   def export_near(fs,label):
    path=mdir/'near'/(label+'.glb');meta={'macro_id':macro,'origin_longitude':origin[0],'origin_latitude':origin[1],'featureLocalIds':[f['local_id'] for f in fs],'feature_id_base':1,'source_roof_keys':[f['key'] for f in fs if f['roof']]};stats=write_near(path,fs,features,tree,roof_shell,meta)
    if stats['expandedTriangles']>a.target_triangles and len(fs)>1:
     path.unlink();span=[max(f['center'][i] for f in fs)-min(f['center'][i] for f in fs) for i in [0,1]];axis=span.index(max(span));ordered=sorted(fs,key=lambda f:(f['center'][axis],f['key']));mid=len(fs)//2;export_near(ordered[:mid],label+'-a0');export_near(ordered[mid:],label+'-a1');return
    raw_source,_=glb_json(path);raw_bytes=path.stat().st_size;packed=path.with_suffix('.packed.glb')
    pack(['-i',str(path),'-o',str(packed),'-cc','-noq','-mi','-kv','-km','-ke'])
    expanded=restore_glb_provenance(packed,raw_source)
    if expanded!=stats['expandedTriangles']:raise RuntimeError('Near compressed expanded triangle count changed')
    decoded=packed.read_bytes()
    if len(decoded)>=100_000_000:raise RuntimeError('Decoded near GLB exceeds100MB')
    published=path.with_suffix('.glb.gz');payload=gzip.compress(decoded,compresslevel=6,mtime=0)
    if len(payload)>=100_000_000:raise RuntimeError('Published near gzip exceeds100MB')
    published.write_bytes(payload);packed.unlink();path.unlink();path=published
    stats['raw_bytes_before_compression']=raw_bytes;stats['bytes']=path.stat().st_size;stats['content_encoding']='gzip';stats['decoded_size_bytes']=len(decoded);stats['decoded_sha256']=hashlib.sha256(decoded).hexdigest();stats['compression']={'type':'EXT_meshopt_compression','quantization':False,'gpu_instancing':True,'transport':'gzip','gzip_level':6,'gzip_mtime':0}
    bbox=bounds(fs);pad=.40;lat_pad=pad/111000;lon_pad=lat_pad/math.cos(math.radians(origin[1]));geometry_bbox=[bbox[0]-lon_pad,bbox[1]-lat_pad,bbox[2]+lon_pad,bbox[3]+lat_pad]
    info={'id':macro+'-'+label,'file':'near/'+path.name,'featureLocalIds':meta['featureLocalIds'],'feature_id_base':1,'feature_count':len(fs),'origin_longitude':origin[0],'origin_latitude':origin[1],'geographic_bbox':bbox,'geometry_bbox':geometry_bbox,'triangles':stats['expandedTriangles'],'size_bytes':stats['bytes'],'sha256':sha(path),**stats,'budgetException':stats['expandedTriangles']>a.target_triangles,'budgetExceptionReason':'Single indivisible feature; retain full geometry, runtime may defer near under budget' if stats['expandedTriangles']>a.target_triangles else None}
    for f in fs:
     if f['key'] in owners:raise RuntimeError('Duplicate near ownership')
     owners[f['key']]=info['id']
    near.append(info)
   for fs,label in leaves:export_near(fs,label)
   if set(owners)!={f['key'] for f in features}:raise RuntimeError('Missing near ownership')
   atomic(mdir/'ownership.json.gz',{'feature_id_base':1,'owners':[[f['local_id'],owners[f['key']]] for f in features]},True)
   files={str(q.relative_to(mdir)):{'bytes':q.stat().st_size,'sha256':sha(q)} for q in mdir.rglob('*') if q.is_file() and q.name!='READY.json'}
   if any(v['bytes']>=100_000_000 for v in files.values()):raise RuntimeError('Published asset exceeds100MB')
   result={'schema':'city-v5-macro-ready-v1','id':macro,'complete':True,'configuration_sha256':config_sha,'source_sha256':row['source_sha256'],'baseline_far_sha256':row['sha256'],'feature_count':len(features),'feature_id_base':1,'far':{'file':'far.glb','raw_size_bytes':far_raw_bytes,'raw_sha256':far_raw_sha256,'triangles':far_tri,'size_bytes':far.stat().st_size,'sha256':sha(far)},'feature_table_file':'feature-table.json.gz','feature_ids_file':'online-ids.json.gz','ownership_file':'ownership.json.gz','origin_longitude':origin[0],'origin_latitude':origin[1],'geographic_bbox':row['geographic_bbox'],'geometry_bbox':actual_bounds,'height_quality':quality,'source_roof_keys':sorted(actual_roofs),'residual_count':sum(f['residual'] for f in features),'excluded_renderable_keys':excluded_renderable,'nonrenderable_keys':nonrenderable,'degenerate_components':degenerate,'district_counts':dict(collections.Counter(f['properties']['district_id'] for f in features)),'near':near,'tiles':near,'published_files':files,'build_seconds':time.perf_counter()-started,'near_total_bytes':sum(t['size_bytes'] for t in near),'near_total_triangles':sum(t['triangles'] for t in near),'families':dict(collections.Counter(f['family'] for f in features)),'source_height_and_footprint_preserved':True,'all_features_own_exactly_one_near_tile':True,'near_content_encoding':'gzip','near_decoded_bytes':sum(t['decoded_size_bytes'] for t in near)}
   atomic(ready,result);built.append(macro);print('READY',macro,len(features),len(near),result['near_total_bytes'],round(result['build_seconds'],2),flush=True)
  except Exception as exc:errors.append({'macro':macro,'error':str(exc),'traceback':traceback.format_exc()});atomic(O/'errors.json',errors);print('FAILED',macro,str(exc),flush=True)
 if a.worker_only:
  atomic(O/'.work'/('worker-'+str(os.getpid())+'.json'),{'errors':errors,'built':built,'resumed':resumed,'compressor_stats':pack_stats})
  if errors:raise SystemExit(1)
  return
 for wr in worker_reports:errors.extend(wr['errors']);built.extend(wr['built']);resumed.extend(wr['resumed'])
 # Every invocation rebuilds the recoverable index from verified READY records.
 records=[read(q) for q in sorted((O/'macros').glob('*/READY.json'))];keys=set();duplicates=[];tiles=[]
 for r in records:
  if r['configuration_sha256']!=config_sha:raise RuntimeError('Mixed build configurations')
  table=read(O/'macros'/r['id']/r['feature_table_file'])
  for key in table['keys'][1:]:
   if key in keys:duplicates.append(key)
   keys.add(key)
  prefix='macros/'+r['id']+'/'
  tiles.append({'id':r['id'],'file':prefix+r['far']['file'],'origin_longitude':r['origin_longitude'],'origin_latitude':r['origin_latitude'],'geographic_bbox':r['geographic_bbox'],'geometry_bbox':r['geometry_bbox'],'triangles':r['far']['triangles'],'size_bytes':r['far']['size_bytes'],'sha256':r['far']['sha256'],'feature_ids_file':prefix+r['feature_ids_file'],'feature_table_file':prefix+r['feature_table_file'],'near_manifest_file':prefix+'READY.json','feature_count':r['feature_count'],'building_count':r['feature_count']})
 district_counts=collections.Counter()
 for r in records:district_counts.update(r.get('district_counts',{}))
 districts=[{'id':d['id'],'name':d['name'],'features':district_counts.get(d['id'],0)} for d in baseline['districts']]
 totals={'features':sum(r['feature_count'] for r in records),'macro_count':len(records),'residuals':sum(r['residual_count'] for r in records),'renderable_exclusions':sum(len(r['excluded_renderable_keys']) for r in records),'qualified_roofs':sum(len(r['source_roof_keys']) for r in records),'near_tiles':sum(len(r['near']) for r in records),'near_bytes':sum(r['near_total_bytes'] for r in records),'far_bytes':sum(r['far']['size_bytes'] for r in records),'published_asset_bytes':sum(v['bytes'] for r in records for v in r['published_files'].values()),'published_asset_files':sum(len(r['published_files']) for r in records),'build_seconds_sum':sum(r['build_seconds'] for r in records),'near_expanded_triangles':sum(r['near_total_triangles'] for r in records),'budget_exception_tiles':sum(t['budgetException'] for r in records for t in r['near'])}
 complete=not errors and not duplicates and len(records)==expected['macro_count'] and totals['features']==expected['feature_count'] and totals['residuals']==401 and totals['renderable_exclusions']==98 and totals['qualified_roofs']==126
 if a.all and len(records)==expected['macro_count'] and not complete:errors.append({'error':'Full-city conservation failed; complete blocked','totals':totals,'duplicates':duplicates[:10]})
 manifest={'schema':'shanghai-city-v5-v1','complete':complete,'pilot_complete':not errors and all(x in {r['id'] for r in records} for x in selected),'model_count':len(tiles),'feature_count':totals['features'],'tile_size_m':2000,'districts':districts,'scope':'All16 Shanghai districts; this index currently contains only READY macros, never claims pilot equals full city','configuration_sha256':config_sha,'expected_city':expected,'totals':totals,'tiles':tiles,'errors':errors,'duplicate_keys':duplicates[:20],'this_run':{'selected':selected,'built':built,'resumed':resumed,'seconds':time.perf_counter()-run_start,'compressor_stats':pack_stats,'worker_reports':worker_reports},'attribution':baseline.get('attribution','© Overture Maps Foundation; © OpenStreetMap contributors ODbL-1.0; Qian Shi et al. CC BY4.0; height datasets CMAB/CNBH/GHSL CC BY4.0')}
 atomic(O/'manifest.json',manifest);atomic(O/'errors.json',errors);print('MANIFEST',json.dumps({'complete':complete,'pilot_complete':manifest['pilot_complete'],'totals':totals,'errors':len(errors)},ensure_ascii=False),flush=True)
 if errors or duplicates:raise SystemExit(1)
if __name__=='__main__':main()
