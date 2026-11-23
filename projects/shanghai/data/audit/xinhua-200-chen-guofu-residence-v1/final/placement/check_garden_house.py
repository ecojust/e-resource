"""Read the actual released meshes and compare the registered garden facade and glazed eaves with the city parcel."""
from pathlib import Path as P
from math import *
import json,hashlib,gzip,subprocess,tempfile,sys
import numpy as np
from shapely.geometry import MultiPoint,Polygon,Point,shape
from shapely.ops import transform
import argparse
from urllib.request import urlopen
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('models',type=P,help='Directory containing full-source.glb and lod-source.glb')
parser.add_argument('output',type=P,help='Directory for the resulting JSON and downloaded cache')
parser.add_argument('meshopt_decoder',type=P,help='The project vendor/meshopt_decoder.module.js')
args=parser.parse_args();base=P(__file__).parent;w=base;out=args.output;out.mkdir(parents=True,exist_ok=True)
cache=out/'cache';cache.mkdir(exist_ok=True)
import triangles
from authored import read_mesh
rawurl='https://raw.githubusercontent.com/ecojust/e-resource/ae55637ce1d7cbc4d21fd94934c8309aca1dcd09/projects/shanghai/assets/city-detail/macros/14-13718-6695/'
def fixed_file(name):
    p=cache/name.replace('/','-')
    if not p.is_file():p.write_bytes(urlopen(rawurl+name,timeout=30).read())
    return p
H=lambda b:hashlib.sha256(b).hexdigest()
survey=json.loads((base/'two-roofs.json').read_bytes());v=survey['feature'];assert v['id']==1241
points=np.asarray(v['geometry']['coordinates'][0]);a,b=points[3],points[2];mid=(a+b)*.5
metres=np.array([111320*cos(radians(mid[1])),110860.]);d=(b-a)*metres;length=float(np.linalg.norm(d));ax=d/length;inward=np.array([-ax[1],ax[0]]);yaw=degrees(atan2(*ax));org=mid+.5*inward/metres
registrations={'south-roof-and-garden-axis':dict(origin_wgs84=org.tolist(),positive_x_bearing_deg=yaw,metres_per_degree=metres.tolist(),source_south_edge_wgs84=[a.tolist(),b.tolist()],source_edge_length_m=length,origin_offset_inward_m=.5,method='South eave aligned to the southern 1241 roof edge. The two aerial seasons resolve the tiled roof and garden axis; absolute registration is conditional to about 1–2 m.')}
models={};body={}
for n in ('full','lod'):
 f=args.models/(n+'-source.glb');v=np.concatenate([r for _,r in read_mesh(f)]);models[n]=v;body[n]=dict(sha256=H(f.read_bytes()),triangles=len(v),local_bounds_m=[v.min((0,1)).tolist(),v.max((0,1)).tolist()]);
# On the original tile keep each indexed object and all anonymous decorations in the search rectangle.
readtr=(base/'triangles.py').read_text();start=readtr.index('    for fid in (owner_id,):');end=readtr.index('   else:yield mat,local(tri)',start);readtr=readtr[:start]+'''    orig=local(tri);lo=orig.min(1);hi=orig.max(1);keep=(lo[:,0]<=xmax)&(hi[:,0]>=xmin)&(lo[:,1]<=ymax)&(hi[:,1]>=ymin)
    for fid in np.unique(F[keep]):yield mat+' owner '+str(fid),orig[keep&(F==fid)]
'''+readtr[end:];scope={};exec(readtr,scope);finfo={};tiles=json.loads(fixed_file('READY.json').read_bytes());rawurl='https://raw.githubusercontent.com/ecojust/e-resource/ae55637ce1d7cbc4d21fd94934c8309aca1dcd09/projects/shanghai/assets/city-detail/macros/14-13718-6695/';from urllib.request import urlopen
originals=json.loads(gzip.decompress(fixed_file('feature-table.json.gz').read_bytes()))['features'];stats={};projections={};allgeo=[]
for d,reg in registrations.items():
 o=np.array(reg['origin_wgs84']);XY=models['full'].reshape(-1,3)[:,:2];h=MultiPoint(XY).convex_hull;geo=Polygon([o+(x*ax+y*inward)/metres for x,y in h.exterior.coords]);allgeo.append(geo);owners={}
 for r in originals:
  p=shape(r['geometry']);
  if p.distance(geo)>.00045:continue
  p=transform(lambda lon,lat:((lon-o[0])*metres[0]*ax[0]+(lat-o[1])*metres[1]*ax[1],(lon-o[0])*metres[0]*inward[0]+(lat-o[1])*metres[1]*inward[1]),p);owners[r['localId']]=[p.distance(h),p.intersection(h).area]
 projections[d]={'footprint_wgs84':list(geo.exterior.coords),'nearest_original_polygon_distance_m_and_hull_intersection_m2':sorted([(i,v)for i,v in owners.items()],key=lambda a:a[1][0])[:9]};stats[d]={}
from shapely.geometry import box
rows=[tiles['far']]+[r for r in tiles['near'] if any(box(*r['geometry_bbox']).intersects(g)for g in allgeo)];print('rows',[(r['file'])for r in rows],flush=True)
for row in rows:
 name=row['file'];old=fixed_file(name)
 b=old.read_bytes();assert H(b)==row['sha256'];finfo[name]={'url':rawurl+name,'sha256':H(b),'bytes':len(b)}
 with tempfile.TemporaryDirectory(dir=cache) as tmp:
  pre=json.loads((base/'decoded-control.json').read_bytes()).get(name,{});dst=cache/pre.get('decoded_file','none')
  if not (dst.is_file() and H(dst.read_bytes())==pre.get('decoded_sha256') and pre.get('input')==H(b)):
   g=P(tmp)/'original.glb';dst=P(tmp)/'decoded.glb';g.write_bytes(gzip.decompress(b) if b[:2]==b'\x1f\x8b' else b);subprocess.run(['node','--input-type=module','-',g,dst,args.meshopt_decoder],input=(base/'decode.mjs').read_bytes(),check=True)
  finfo[name]['decoded_sha256']=H(dst.read_bytes())
  for d,reg in registrations.items():
   scope['configure'](tiles,reg['origin_wgs84'],yaw,0);lo=np.min([v.min((0,1))for v in models.values()],0);hi=np.max([v.max((0,1))for v in models.values()],0);scope.update(xmin=lo[0]-20,ymin=lo[1]-20,xmax=hi[0]+20,ymax=hi[1]+20);groups=[]
   for mat,tr in scope['city_tri'](dst):
    sel=np.all(tr.max(1)[:,:2]>=lo[:2]-1e-6,1)&np.all(tr.min(1)[:,:2]<=hi[:2]+1e-6,1)
    if sel.any():groups.append((mat,tr[sel]))
   stats[d][name]={}
   for n,v in models.items():
    v0=v.min(1);v1=v.max(1);tags={};bb=0;count=0
    for mat,tr in groups:
     for T in tr:
      ix=np.where(np.all(v0<=T.max(0)+2e-6,1)&np.all(v1>=T.min(0)-2e-6,1))[0];bb+=len(ix)
      if len(ix):
       hits=int(scope['sat'](T,v[ix]).sum());count+=hits
       if hits:tags[mat]=tags.get(mat,0)+hits
    stats[d][name][n]=dict(original_faces_in_model_xy_bounds=sum(len(t) for _,t in groups),three_dimensional_bbox_pairs=bb,separating_axis_true_contacts=count,materials_with_contact=tags)
r=dict(candidate='新华路200号陈果夫住宅的重檐与南花园外廊，3M011',conditional_station=registrations,source_meshes=body,original_mesh_files=finfo,plan=projections,triangle_intersections=stats,interpretation='两期实照与两期俯拍校准的新南立面、重檐和双廊未提供整栋背面及内部测绘；原1241及周边保持完整，以独立展示提供细部。')
p=out/'actual-1241-surfaces.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(H(p.read_bytes()),{d:{k:{n:m['separating_axis_true_contacts']for n,m in v.items()}for k,v in x.items()}for d,x in stats.items()})
