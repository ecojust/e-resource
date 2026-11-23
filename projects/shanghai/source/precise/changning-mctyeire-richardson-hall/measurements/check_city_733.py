"""Register the baked north-hall meshes to the mapped lawn frontage, with independent east-hall protection."""
import argparse, hashlib, json, math, struct
from pathlib import Path
w=Path(__file__).absolute().parent
review=json.loads((w/'north-and-east-boundaries.json').read_bytes())
ring=review['current_north_hall']['footprint'];a,c=ring[4:6];lon,lat=(a[0]+c[0])/2,(a[1]+c[1])/2
az=math.radians((review['source_edges'][4]['azimuth_true']+180)%360);unit=111319.490793*math.cos(math.radians(lat));dy=110861.0
def local(p):
 E=(p[0]-lon)*unit;N=(p[1]-lat)*dy
 return [E*math.sin(az)+N*math.cos(az),-E*math.cos(az)+N*math.sin(az)]
def world(q):
 x,y=q;return [lon+(x*math.sin(az)-y*math.cos(az))/unit,lat+(x*math.cos(az)+y*math.sin(az))/dy]
def h(b):return hashlib.sha256(b).hexdigest()
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('full',type=Path);parser.add_argument('lod',type=Path)
parser.add_argument('--reference-full',type=Path);parser.add_argument('--reference-lod',type=Path)
parser.add_argument('--version', action='append', nargs=3, metavar=('LABEL', 'FULL', 'LOD'), default=[], help='Include the hashes of another authored version in the report.')
parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
if bool(args.reference_full)!=bool(args.reference_lod):parser.error('Both reference LODs are required together.')
source=json.loads((w/'city-733-local-features.json').read_bytes());rows=source['features'];ids={733,2885}
from shapely.geometry import Polygon, MultiPoint
from PIL import Image,ImageDraw,ImageChops
import numpy as np
geoms={}
for r in rows:
 rr=r['geometry']['coordinates'][0];rr=rr if r['geometry']['type']=='Polygon' else max(rr,key=len);p=rr[0]
 if abs(p[0]-lon)>.0015 or abs(p[1]-lat)>.0015:continue
 coords=[local(v)for v in rr];geoms[r['localId']]=[Polygon(coords),r]
assert ids<=geoms.keys()
res=.025; xmin,ymin,xmax,ymax=-38,-4,38,56;sz=(round((xmax-xmin)/res)+1,round((ymax-ymin)/res)+1)
def pixel(x,y):return [round((x-xmin)/res),round((ymax-y)/res)]
def area(i):return sum(i.histogram()[1:])*res**2
def image_of(ring):
 i=Image.new('1',sz);ImageDraw.Draw(i).polygon([tuple(pixel(x,y))for x,y in ring],fill=1);return i
owner_img=image_of(geoms[733][0].exterior.coords);old_area=area(owner_img)
outputs={}
for label,path in [("full",args.full),("lod",args.lod)]+([("reference_full",args.reference_full),("reference_lod",args.reference_lod)]if args.reference_full else []):
 p=Path(path);raw=p.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jl]);binary=memoryview(raw)[28+jl:];img=Image.new('1',sz);draw=ImageDraw.Draw(img);cloud=[];zlo,zhi=1e6,-1e6;nt=0
 def accessor(i):
  a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];dt={5126:'<f4',5123:'<u2',5125:'<u4'}[a['componentType']];n={'VEC3':3,'SCALAR':1}[a['type']];s=np.dtype(dt).itemsize
  return np.ndarray((a['count'],n),dt,buffer=binary,offset=a.get('byteOffset',0)+v.get('byteOffset',0),strides=(v.get('byteStride',s*n),s))
 for node in doc['nodes']:
  assert set(node)<={'name','mesh'}
  for prim in doc['meshes'][node['mesh']]['primitives']:
   v=accessor(prim['attributes']['POSITION']);xy=v[:,[0,2]].copy();xy[:,1]*=-1;hull=MultiPoint(xy).convex_hull
   if hull.geom_type=='Polygon':cloud+=list(hull.exterior.coords)
   zlo=min(zlo,float(v[:,1].min()));zhi=max(zhi,float(v[:,1].max()));ind=accessor(prim['indices']).reshape(-1,3);nt+=len(ind)
   at=np.rint(np.column_stack([(xy[:,0]-xmin)/res,(ymax-xy[:,1])/res])).astype(int)
   for q in at[ind].tolist():draw.polygon([tuple(k)for k in q],fill=1)
 hull=MultiPoint(cloud).convex_hull;assert hull.bounds[0]>xmin and hull.bounds[1]>ymin and hull.bounds[2]<xmax and hull.bounds[3]<ymax
 A=area(img);over=area(ImageChops.logical_and(img,owner_img));neighbors=sorted([{'id':i,'distance_to_conservative_actual_vertex_hull_m':hull.distance(g),'source_height_m':r['height']} for i,(g,r) in geoms.items()if i!=733], key=lambda q:q['distance_to_conservative_actual_vertex_hull_m'])
 for q in neighbors:
  if q['distance_to_conservative_actual_vertex_hull_m']<3:
   poly=geoms[q['id']][0]; other=image_of(poly.exterior.coords); inter=ImageChops.logical_and(img,other)
   q['sampled_overlap_m2']=area(inter);q['neighbor_ring_local_m']=list(poly.exterior.coords)
   if not inter.getbbox():
    low,high=0.,20.
    for _ in range(10):
     m=(low+high)/2
     if ImageChops.logical_and(img,image_of(poly.buffer(m).exterior.coords)).getbbox():high=m
     else:low=m
    q['sampled_minimum_clearance_bracket_m']=[max(0,low-2*res),high+2*res]
   if inter.getbbox():
    q['sample_transition_bounds_xy']=[xmin+inter.getbbox()[0]*res,ymax-inter.getbbox()[3]*res,xmin+inter.getbbox()[2]*res,ymax-inter.getbbox()[1]*res]
 outputs[label]={'asset_name':p.name,'footprint_raster_sha256':h(img.tobytes()),'sha256':h(raw),'triangles':nt,'bounds_xy':hull.bounds,'bounds_z':[zlo,zhi],'actual_orthographic_triangle_area_m2':A,'source_733_area_same_sampling_m2':old_area,'common_area_m2':over,'source_covered_ratio':over/old_area,'projected_mesh_in_source_ratio':over/A,'iou':over/(A+old_area-over),'neighbors':neighbors[:10],'separate_east_2885_clearance_lower_bound_m':hull.distance(geoms[2885][0])}
out={'macro':'14-13718-6694','source_feature_table':source['source_url'],'source_sha256':source['source_sha256'],'frame':{'origin_wgs84': [lon,lat],'positive_x_true_bearing_deg':math.degrees(az),'positive_y':'inward, perpendicular to the lawn-facing edge','anchor':'midpoint of OSM way 494669990, zero-based vertices 4 and 5','x_unit_m':1.0,'y_unit_m':1.0},'sample_cell_m':res,'source_733':{'key':geoms[733][1]['key'],'height':geoms[733][1]['height'],'area_m2':geoms[733][0].area,'local_ring':list(geoms[733][0].exterior.coords)},'results':outputs,'limits':'Plan overlap comes from every baked triangle at 2.5 cm sampling; a sloping roof and entrance steps can overhang the ground-source polygon. The cadastral height is a city model input, not a surveyed cornice. Plan distance to surrounding buildings uses the conservative full convex envelope.'}
if args.reference_full:
 out['reference_comparison']={role:{'source_identical':outputs[role]['sha256']==outputs['reference_'+role]['sha256'],'projected_footprint_identical_at_2_5_cm':outputs[role]['footprint_raster_sha256']==outputs['reference_'+role]['footprint_raster_sha256'],'net_projected_area_change_m2':outputs[role]['actual_orthographic_triangle_area_m2']-outputs['reference_'+role]['actual_orthographic_triangle_area_m2']}for role in ('full','lod')}
if args.version:
 out['geometry_versions'] = {}
 for label, full, lod in args.version:
  hashes = {}
  for role, mesh_path in [('full', full), ('lod', lod)]:
   with Path(mesh_path).open('rb') as mesh:
    hashes[role] = hashlib.file_digest(mesh, 'sha256').hexdigest()
  out['geometry_versions'][label] = hashes
args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
for k,v in outputs.items():print(k,v['iou'],v['bounds_z'],v['neighbors'][:3],v['separate_east_2885_clearance_lower_bound_m'])
