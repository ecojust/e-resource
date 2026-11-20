from pathlib import Path
import json,math,gzip,collections
import numpy as np, shapely as sg
from shapely.geometry import Point,LineString,shape
w=Path('/tmp/saintjoseph137');p=Path('/workspace/e-resource/projects/shanghai/source/precise/huangpu-st-joseph-church-east-front');par=json.loads((p/'source/parameters.json').read_bytes());lat=par['author_frame']['anchor']['lat'];lon=par['author_frame']['anchor']['lng'];rad=math.pi/180;k=6371008.8*math.cos(lat*rad);ref=math.asinh(math.tan(lat*rad));h=math.radians(par['author_frame']['runtime_heading_deg'])
def enu(q):return np.column_stack(((q[:,0]-lon)*rad*k,(np.arcsinh(np.tan(q[:,1]*rad))-ref)*k))
geoms=[];ids=[];heights=[]
for r in json.loads(gzip.decompress((w/'feature-table.json.gz').read_bytes()))['features']:
 if r['localId']!=2923 and r['key'].startswith('building:')and shape(r['geometry']).distance(Point(lon,lat))<.0036:
  g=sg.transform(shape(r['geometry']),enu);geoms.append(g);ids.append(r['localId']);heights.append(r['height'])
angle=np.array([[math.cos(h),-math.sin(h)],[math.sin(h),math.cos(h)]])
parts=[('south portal',-7.36,.74,2.15),('central door',0,.25,2.15),('north portal',7.36,.74,2.15),('south saint niche',-7.36,.74,6.75),('north saint niche',7.36,.74,6.75),('rose',0,.25,17.13),('spire',0,3.0,31.6),('central door threshold',0,.25,.55),('south door threshold',-7.36,.74,.75),('north door threshold',7.36,.74,.75),('south wall edge',-10.21,.74,2.7),('north wall edge',10.21,.74,2.7)]
positions=np.array([np.array([x,y])@angle for _,x,y,z in parts])
gs=np.array(geoms,dtype=object);index=sg.STRtree(gs);group=collections.defaultdict(list)

cases=[('street',0,.10,10,27,-11.9,18.89),('roof',0,2.12,15,21,-19.9,18.94),('door-and-rose',0,.30,11.4,30,-11.9,19.85),('bell-tower',0,2.8,27.7,26,-11.9,19.78)]
cameras=[]
for name,x,y,e,pitch,bearing,zoom in cases:
 east=x*math.cos(h)+y*math.sin(h);north=-x*math.sin(h)+y*math.cos(h)
 cameras.append(dict(name=name,view=dict(height=660,width=870),center=[lon+east/k/rad,math.atan(math.sinh(ref+north/k))/rad],elevation=e,pitch=pitch,bearing=math.degrees(h)+bearing,zoom=zoom))
for v in cameras:
 z=v['zoom'];b=v['bearing'];pit=v['pitch']
 d=v['view']['height']/(2*math.tan(36.87*rad/2))*2*math.pi*k/(512*2**z)
 cam=enu(np.array([v['center']]))[0]-d*math.sin(pit*rad)*np.array([math.sin(b*rad),math.cos(b*rad)]);alt=v['elevation']+d*math.cos(pit*rad)
 rays=np.array([LineString([t,cam])for t in positions],dtype=object);minima=[(None,None)]*len(rays)
 for i,j in zip(*index.query(rays,predicate='intersects')):
  hit=rays[i].intersection(gs[j]);s=parts[i][3];distance=Point(positions[i]).distance(hit);clear=s+(alt-s)*distance/rays[i].length-heights[j]
  if minima[i][0] is None or clear<minima[i][0]:minima[i]=(clear,ids[j])
 group[(b,pit)].append({'camera':v,'worst_m':round(min([k[0]for k in minima if k[0] is not None]or[1000]),2),'tests':[{'witness':q[0],'local_xyz':list(q[1:]),'minimum_m':round(t[0],2)if t[0]is not None else None,'owner':t[1]}for q,t in zip(parts,minima)]})

out=Path('/tmp/saintjoseph137/city-24137/camera-line-clearance.json')
records=[r for grouprecords in group.values()for r in grouprecords]
out.write_text(json.dumps(dict(scope='City-roof line clearance for four QA-only desktop positions, computed before formal Chromium captures',source_sha256=__import__('hashlib').sha256((w/'feature-table.json.gz').read_bytes()).hexdigest(),cameras=records),indent=2)+'\n')
print([(r['camera']['name'],r['worst_m'])for r in records])
