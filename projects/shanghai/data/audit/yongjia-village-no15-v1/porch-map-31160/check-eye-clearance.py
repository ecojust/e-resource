"""Check actual projected eyes and segment clearance from retained neighboring footprints."""
import json,hashlib
from pathlib import Path
MOD='xuhui-yongjia-village-no15'
def read(path):return json.loads(path.read_bytes())
def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,data):path.write_bytes(data)
def canon(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
from shapely.geometry import Point,Polygon,LineString
from math import radians,cos,sin
import argparse
co=argparse.ArgumentParser();co.add_argument('locations',type=Path,nargs='+');co.add_argument('--out',type=Path,required=True);a=co.parse_args()
p=Path(__file__).resolve().parents[4];rfile=p/'source/precise'/MOD/'footprint-review.json';r=read(rfile)
an=r['author_frame']['anchor'];rad=r['author_frame']['earth_radius_m'];h=radians(r['author_frame']['runtime_heading_deg'])
def xy(lng,lat):
 e=radians(lng-an['lng'])*rad*cos(radians(an['lat']));n=radians(lat-an['lat'])*rad
 return (e*cos(h)-n*sin(h),e*sin(h)+n*cos(h))
neighbors=[(o['local_id'],Polygon([xy(*c)for c in o['geometry']['coordinates'][0]])) for o in r['owners'] if o['local_id']!=4151]
features=[('left garden-side arch',(-4.02,-1.38)),('right garden-side arch',(-3.06,-1.38)),('green enamel 15',(-2.41,-1.21)),('central pier',(-3.54,-1.38))]
out=[]
for f in a.locations:
 q=read(f);assert q['passed']and q['closed']
 for s in q['views']:
  if s['name']!='signed':continue
  eye=s['eye'];pt=xy(eye['lng'],eye['lat']);p2=Point(pt);ds=sorted((v.distance(p2),i)for i,v in neighbors)
  rays=[]
  for k,t in features:
   line=LineString([pt,t]);clear=sorted((line.distance(poly),i)for i,poly in neighbors);occ=[i for i,poly in neighbors if line.intersection(poly).length>.001]
   assert not occ,(k,occ)
   rays.append({'target':k,'author_xy':t,'nearest_neighbor':clear[0][1],'ray_plan_clearance_m':round(clear[0][0],4)})
  assert ds[0][0]>.25 and not any(s['control']for s in s['samples'])
  out.append({'receipt':str(f),'receipt_sha256':sha(f.read_bytes()),'image_sha256':s['sha256'],'camera_eye_wgs84_and_height':eye,'camera_eye_author_xy':pt,'nearest_neighbor':ds[0][1],'eye_plan_clearance_m':ds[0][0],'rays':rays,'actual_dom_samples':s['samples']})
save(a.out,canon({'passed':True,'footprint_review_sha256':sha(rfile.read_bytes()),'neighbor_count':len(neighbors),'source':'Metre-space 2D segments against unchanged native neighbor ground polygons. Visibility of detailed geometry comes from each actual PNG.','devices':out}))
