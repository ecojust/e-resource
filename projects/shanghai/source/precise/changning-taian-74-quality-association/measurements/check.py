from pathlib import Path
import argparse,hashlib,json,math
from photo_ray_mesh import ProjectedMesh
here=Path(__file__).absolute().parent
c=argparse.ArgumentParser();c.add_argument('mesh',type=Path);c.add_argument('cameras',type=Path);c.add_argument('output',type=Path);c.add_argument('--window-only',action='store_true');c.add_argument('--points',type=Path,default=here/'independent-source-pixels.json');args=c.parse_args()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
data=args.points;original=load(data);stations=load(args.cameras);g=args.mesh.with_suffix('.geometry.json')
mesh=ProjectedMesh(args.mesh,load(g))
spread=sorted((math.hypot(x,y),x,y)for x in range(-15,16)for y in range(-15,16)if x*x+y*y<=225)
def expects(f,h):
 if not h:return False
 p=h['part'].lower();m=h['material'].lower()
 if f.startswith(('upper-','lower-')):return p.startswith(f+'/glazing')
 if f.startswith('coffer-'):return p.startswith(f.split('-')[1]+' spandrel/')
 if f=='plaque-face':return 'seven-character nameplate' in p or 'pier name/' in p
 if f=='inscription':return 'pier name/' in p
 if f=='apron':return 'apron' in p
 if f=='pediment':return 'attic pediment' in p
 if f=='corner':return 'corner' in p or 'scored pale render'==m
 if f in ('west-door','east-door'):return p.startswith(f.split('-')[0]+' door/leaf') and 'glazing' in p
 if f in ('west-fanlight','east-fanlight'):return p.startswith(f.split('-')[0]+' door/') and 'fanlight' in p
 if f=='74':return p.startswith('number 74/')
 if f=='canopy':return p.startswith('canopy/')
 if f=='relief':return 'relief' in m
 if f=='step':return 'entrance tile' in m
 raise ValueError(f)
out={'mesh':mesh.asset,'cameras_sha256':sha(args.cameras),'original_pixels_sha256':sha(data),'part_geometry_sha256':sha(g),'stations':{}}
for key,record in original['photographs'].items():
 mesh.station(stations[key]);rows=[]
 for a in record['points']:
  f=a['feature'];u,v=a['uv']
  if args.window_only and not f.startswith(('upper-','lower-')):continue
  center=mesh.hit(u,v);nearest=None
  for dist,x,y in spread:
   h=center if not dist else mesh.hit(u+x,v+y)
   if expects(f,h):
    nearest={'distance':dist,'delta':[x,y],'part':h['part'],'material':h['material']};break
  rows.append(dict(a,center=center,direct=expects(f,center),nearby=nearest))
 out['stations'][key]=rows
result=[v for group in out['stations'].values()for v in group]
out['counts']={str(limit):sum(bool(p['nearby'] and p['nearby']['distance']<=limit)for p in result)for limit in [0,4,8,15]}
args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(args.mesh.parent.name,args.mesh.name,len(result),out['counts'])
