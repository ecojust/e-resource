#!/usr/bin/env python3
"""Rebuild the approximate Chongming city placements and node-only corridor assembly.

Needs Python 3 + shapely, the committed global integration inventory, and original
Git objects at the pinned asset baseline. No reference photo pixels are required,
embedded, sampled or redistributed. Geometry is original MIT; source map metadata
retains OpenStreetMap ODbL attribution. Author-selected offsets are not a survey.
"""
from pathlib import Path
import json,math,struct,hashlib,subprocess,copy,gzip
from shapely.geometry import Polygon,shape,mapping,Point,MultiPolygon
from shapely.ops import transform
ROOT=Path(__file__).resolve().parents[3];PR=ROOT/'projects/shanghai';OUT=PR/'data/global-models';AUD=PR/'data/audit/global-model-integration-v1';OUT.mkdir(parents=True,exist_ok=True);AUD.mkdir(parents=True,exist_ok=True);(PR/'assets/models/global/chongming-stele-corridors').mkdir(parents=True,exist_ok=True)
COMMIT='65af6bea52780f274d2ee005bbbd513317b559fc';H=5.0;R=6378137;C=math.cos(math.radians(H));S=math.sin(math.radians(H))
# Approximate ground anchor from north-up satellite roof image (2026 retrieval, unknown imagery epoch).
pixel=[314,353];N=256*2**19;gx=438940*256+pixel[0];gy=213558*256+pixel[1];LON=gx/N*360-180;LAT=math.degrees(math.atan(math.sinh(math.pi*(1-2*gy/N))));COS=math.cos(math.radians(LAT))
def ll(e,n):return [LON+math.degrees(e/(R*COS)),LAT+math.degrees(n/R)]
def en(lon,lat):return [(lon-LON)*math.pi/180*R*COS,(lat-LAT)*math.pi/180*R]
def orient(e,n,h=H):c=math.cos(math.radians(h));s=math.sin(math.radians(h));return [e*c+n*s,-e*s+n*c]
def at(e,n):return ll(*orient(e,n))
def rect(e,n,b,h):
 p=[]
 for x,y in [(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])]:
  dx,dy=orient(x,y,h);ae,an=orient(e,n);p.append(ll(ae+dx,an+dy))
 return Polygon(p)
def sha(b):return hashlib.sha256(b).hexdigest()
def loadgit(p):return subprocess.check_output(['git','show',COMMIT+':'+p],cwd=ROOT)
table_path='projects/shanghai/assets/city-detail/macros/14-13716-6673/feature-table.json.gz';table_raw=gzip.decompress(loadgit(table_path));table=json.loads(table_raw);site=next(f for f in table['features'] if f['localId']==192);assert site['properties']['id']=='128f4cb0-fcdf-4948-8729-d812245dc745';sg=shape(site['geometry']);inv=json.load(open(AUD/'inventory.json'));by={r['id']:r for r in inv['records']};metadata=[]
# Keep original compressed geometry/indices/materials. Modify just two scene-node rigid transforms.
for role in ['web','lod']:
 src=f'projects/shanghai/assets/models/candidates/chongming-stele-corridors/chongming-stele-corridors-{role}.glb';raw=loadgit(src);jl=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+jl]);original=copy.deepcopy(j);tail=raw[20+jl:]
 assert len(j['nodes'])==2 and [n['name'] for n in j['nodes']]==['East_long_component','West_long_component']
 for i,(east,angle) in enumerate([(9,-math.pi/2),(-9,math.pi/2)]):
  j['nodes'][i]['translation']=[east,0,0];j['nodes'][i]['rotation']=[0,math.sin(angle/2),0,math.cos(angle/2)];j['nodes'][i]['extras']={**j['nodes'][i].get('extras',{}),'display_placement_only':False,'global_approximate_courtyard_placement':True,'spacing_status':'18 m author placement estimate, not a survey','original_model_geometry_unchanged':True}
 data=json.dumps(j,ensure_ascii=False,separators=(',',':')).encode();data+=b' '*(-len(data)%4);out=struct.pack('<4sII',b'glTF',2,20+len(data)+len(tail))+struct.pack('<II',len(data),0x4e4f534a)+data+tail
 dst=PR/f'assets/models/global/chongming-stele-corridors/chongming-stele-corridors-{role}.glb';dst.write_bytes(out)
 rec={'role':role,'file':str(dst.relative_to(PR)),'bytes':len(out),'sha256':sha(out),'triangles':232696 if role=='web' else 42200,'source_file':src,'source_bytes':len(raw),'source_sha256':sha(raw),'source_commit':COMMIT,'source_bin_chunk_sha256':sha(tail),'derived_bin_chunk_sha256':sha(out[20+len(data):]),'binary_chunks_identical':tail==out[20+len(data):],'non_node_json_identical':{k:v for k,v in j.items() if k!='nodes'}=={k:v for k,v in original.items() if k!='nodes'},'node_transforms':j['nodes']};assert rec['binary_chunks_identical'] and rec['non_node_json_identical'];metadata.append(rec)
# Same coherent estimated site frame; orientation and offsets are not surveyed.
layout=[('dacheng-hall',0,0,0),('zunjing-pavilion',-4.5,29,0),('chongsheng-shrine',13.5,29,0),('ji-gate',0,-43,0),('east-wing',17,-25,90),('west-wing',-17,-25,-90),('minghuan-shrine',15,-43,0),('xiangxian-shrine',-15,-43,0),('pan-pool-bridge',0,-57,0),('east-guanting',16.5,-57,90),('west-guanting',-16.5,-57,-90),('lingxing-gate',0,-69,0),('lingxing-photo-left-gate',-6.3,-69,0),('lingxing-photo-right-gate',6.3,-69,0),('xuehai-paifang',-16.5,-77,90),('chaozong-paifang',16.5,-77,90),('minglun-hall',36,0,0),('yimen',36,-45,0),('ruxue-gate',36,-64,0),('stele-corridors',36,-24.4,0)]
clear_local=[[-23,-84],[53,-84],[53,10],[27,10],[27,40],[-17,40],[-17,14],[-23,14]]
clearance=Polygon([at(e,n) for e,n in clear_local]).intersection(sg);residual=sg.difference(clearance)
site_replacement={'id':'chongming-confucian-temple-main-east-courtyards','geometry':mapping(clearance),'source_feature_ids':{'building':[site['properties']['id']],'building_part':[]},'note':'有界纠正整园误拉高15.3米板块，仅主轴与东轴已建单体及其庭院；西轴、东北两合院及其余园址源几何保留。场址范围与建筑位置是影像/文字引导的近似配准，非测绘。','source_macro':'14-13716-6673','source_local_id':192,'residual_geometry':mapping(residual)}
records=[];geoms={}
for short,e,n,rel in layout:
 id='chongming-'+short;r=by[id];bounds=r['geometry']['bounds_enu_m'];a=bounds['min'];b=bounds['max'];heading=H+rel;anchor=at(e,n)
 if short=='stele-corridors':
  g=MultiPolygon([rect(e+9,n,[-1.545,-15.55,1.545,15.55],H),rect(e-9,n,[-1.545,-15.55,1.545,15.55],H)]);bg={'min':[-10.545,0,-15.55],'max':[10.545,4.6,15.55]}
 else:g=rect(e,n,[a[0],a[1],b[0],b[1]],heading);bg=r['geometry']['bounds_glb']
 geoms[id]=g
 p={'id':id,'lng':anchor[0],'lat':anchor[1],'heading':heading,'scale':1,'height_m':b[2],'districtId':'310151','overviewZoom':19.0 if short not in ['lingxing-gate','lingxing-photo-left-gate','lingxing-photo-right-gate'] else 20.0,'maxDistance':450,'lod_switch_out_m':115,'lod_switch_in_m':75,'collision_geometry':mapping(g),'replacement_geometry':None,'source_feature_ids':{'building':[site['properties']['id']],'building_part':[]},'navigation':{'listed':False,'walkStart':anchor,'bearing':H,'note':'本轮只提供全局俯瞰直达；院内出生点、桥面、门洞、台阶通行未验收，不开放自动漫游。'},'placement':{'status':'estimated','note':'基于场址地图、北向上卫星参考与建筑相对次序的近似配准；位置、5°轴向、院落间距非测绘，原单体尺寸与形态估计继续适用。','local_site_east_north_m':[e,n],'heading_relative_to_site_deg':rel,'references':['satellite-reference-v1','sohu-2023-aerial-and-layout','archived-museum-text','frozen-source-14-13716-6673-192']},'site_replacement':site_replacement,'bounds_glb':bg}
 if short=='pan-pool-bridge':
  p['altitude']=0.85;p['placement']['note']+=' 为零高程底图显示采用0.85米抬升，非实测高程；原模型未改，池底仍低于地面，上桥通行未验收。'
 if short=='stele-corridors':
  p['assets']={x['role']:{k:x[k] for k in ['file','bytes','sha256','triangles']} for x in metadata};p['derived_asset_note']='原近/远景GLB压缩几何、索引和材质完全不变，仅两个scene节点分别旋转±90°并移到中心东西±9米，形成朝院的两条长廊。18米间距及场址位置为近似配准；不补造未建南北短段。原Blender仍是独立展示布局。'
 records.append(p)
payload={'schema':'shanghai-global-chongming-placement-v1','baseline_commit':COMMIT,'scope':'20既有独立候选接入全局场景；文字/影像引导近似配准，不是整个学宫或某一历史日期的测绘复原。','coordinate_frame':{'anchor_wgs84':[LON,LAT],'origin_role':'大成殿近似中心','origin_imagery_pixel':{'z':19,'tile_top_left':[438940,213558],'mosaic_pixel':[314,353]},'heading_clockwise_from_north_deg':H,'local_axes':'x east,y north,z up; heading h: e=x cos h+y sin h,n=-x sin h+y cos h','meters_conversion':'spherical local tangent plane R=6378137,longitude scaled cos(origin latitude)','uncertainty':'影像年代/地面控制点和屋顶视差未知；整体位置、旋转及相对偏移约米级至十余米不确定，不声称测量精度'},'records':records}
(OUT/'chongming-placement.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
# all-source metric neighbor review around exact site, not just candidate index.
rows=table['features'];local_site=transform(en,sg);neighbors=[]
for f in rows:
 if f['key']==site['key']:continue
 g=transform(en,shape(f['geometry']));dist=g.distance(local_site)
 if dist<=65:
  neighbors.append({'id':f['properties']['id'],'key':f['key'],'macro':'14-13716-6673','localId':f['localId'],'name':f['properties'].get('@name'),'distance_to_site_m':dist,'intersection_with_site_m2':g.intersection(local_site).area,'intersection_with_clearance_m2':g.intersection(transform(en,clearance)).area,'preserved':True})
overlap=[]
for i,r in enumerate(records):
 for s in records[i+1:]:
  area=transform(en,geoms[r['id']].intersection(geoms[s['id']])).area
  if area>1e-5:overlap.append({'a':r['id'],'b':s['id'],'conservative_projection_intersection_m2':area})
report={'schema':'chongming-global-placement-audit-v1','baseline_commit':COMMIT,'status':'approximate-overview-placement','candidate_count':20,'models_scale':1,'source_feature':site,'source_source_path':'projects/shanghai/assets/city-detail/macros/14-13716-6673/feature-table.json.gz','source_feature_table_uncompressed_sha256':sha(table_raw),'source_scope':'整园单块，名崇明区博物馆，OSM w413345693@3；15.3米为统计高度估计，不是整座庭院统一建筑高度','clearance':{'geometry':mapping(clearance),'local_proposed_polygon_m':clear_local,'source_area_m2':local_site.area,'clearance_area_m2':transform(en,clearance).area,'retained_source_area_m2':transform(en,residual).area,'retained_geometry':mapping(residual),'scope':'保留西轴小殿范围及东北两排合院范围；只开放现有20候选主轴/东轴范围和其相邻庭院。边界近似，不提供庭院漫游验收。'},'neighbor_review':{'radius_m':65,'macro_features_scanned':len(rows),'neighbors':neighbors,'positive_overlap_with_source':[r for r in neighbors if r['intersection_with_site_m2']>1e-5],'positive_overlap_with_clearance':[r for r in neighbors if r['intersection_with_clearance_m2']>1e-5],'all_other_feature_ids_preserved':True},'candidate_pairwise_aabb_footprint_overlaps':overlap,'candidate_ground_height_m':0,'pan_pool_display_altitude_m':0.85,'candidate_height_range_m':[min(r['height_m'] for r in records),max(r['height_m'] for r in records)],'pan_pool_limit':'原池体局部最低-2.16米、水面-0.8米；城市显示抬0.85米，使水面0.05米高于零高程底图，无地形开挖。抬升非实测高程，上桥和水下未开放。','stele_derivation':{'schema':'node-only-rigid-assembly-v1','original_scene_retained_in_standalone_assets':True,'original_blender_unchanged':True,'new_blender_created':False,'geometry_edit':False,'components_separation_m':18,'spacing_status':'author estimate from east-axis court context; not documentary measured','full_and_lod':metadata},'navigation':'20overview deep links; no new walkStart accepted','photo_pixels_redistributed':False}
(AUD/'chongming-placement.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'anchor':[LON,LAT],'records':len(records),'neighbors':len(neighbors),'overlaps':overlap,'source_area':local_site.area,'clearance_area':transform(en,clearance).area,'residual_area':transform(en,residual).area,'neighbors_positive_clearance':report['neighbor_review']['positive_overlap_with_clearance'],'derived':[{'role':r['role'],'bytes':r['bytes'],'sha256':r['sha256']} for r in metadata]},ensure_ascii=False,indent=2))
