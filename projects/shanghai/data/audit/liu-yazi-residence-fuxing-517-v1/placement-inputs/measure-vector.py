"""Resolve the public vector-grid component of the one old main house, retaining the rest of the tile."""
import os as _author_os
from pathlib import Path as _AuthorPath
_author_project = next(p for p in _AuthorPath(__file__).resolve().parents if p.name == 'shanghai')
_author_data = _AuthorPath(_author_os.environ.get('LIUYAZI_EVIDENCE_ROOT', _author_project / 'data' / 'surveys'))
from pathlib import Path
import gzip, json, sys, os, hashlib, math
import numpy as np
import shapely as g
from shapely.geometry import shape,mapping
sys.path.insert(0,str(_author_data / 'qianguild301-vector'))
import mapbox_vector_tile
w=Path(__file__).parent
read=lambda p:json.loads(p.read_bytes());cfg=read(w/'portal-frame.json');ref=read(w/'footprint-review.json');uri='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13719/6695.pbf'
archive=w/'vector.pbf.gz'
if not archive.exists():os.link(str(_author_data / 'schiller336-gis/vector.pbf.gz'),archive)
raw=gzip.decompress(archive.read_bytes());prior=read(Path(str(_author_data / 'schiller336-gis/vector-scope.json')));assert prior['url']==uri and hashlib.sha256(raw).hexdigest()==prior['sha256']
b=mapbox_vector_tile.decode(raw,default_options=dict(y_coord_down=True))['building'];E=b['extent'];C=cfg['anchor'];k=6371008.8*math.cos(math.radians(C[1]));b0=math.asinh(math.tan(math.radians(C[1])));t=math.radians(cfg['runtime_heading_degrees']);axes=np.array([[math.cos(t),-math.sin(t)],[math.sin(t),math.cos(t)]])
def local(v):return np.column_stack([np.radians(v[:,0]-C[0])*k,(np.arcsinh(np.tan(np.radians(v[:,1])))-b0)*k])@axes.T
def wgs(v):return np.column_stack(((13719+v[:,0]/E)/16384*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*(6695+v[:,1]/E)/16384))))))
def geog(v):
 east,north=(v@axes).T;return np.column_stack((C[0]+np.degrees(east/k),np.degrees(np.arctan(np.sinh(b0+north/k)))))
owner=g.transform(shape(ref['owners'][0]['geometry']),local);allparts=[]
for f in b['features']:
 geo=shape(f['geometry']);sub=list(geo.geoms)if geo.geom_type=='MultiPolygon'else[geo]
 for i,part in enumerate(sub):
  geo=g.transform(part,wgs);obj=g.transform(geo,local);allparts.append((f['id'],i,len(sub),obj))
candidates=[]
for fid,i,n,part in allparts:
 overlap=part.intersection(owner).area
 if overlap>.002:candidates.append((overlap/owner.union(part).area,fid,i,n,part))
assert len(candidates)>=1 and max(x[0]for x in candidates)>.88
iou,fid,i,n,part=max(candidates,key=lambda x:x[0]);restore=part.buffer(.04,quad_segs=1,join_style='mitre');impacts=[(f,num,size,obj.intersection(restore).area)for f,num,size,obj in allparts if obj.intersects(restore)]
assert len(impacts)==1 and impacts[0][0]==fid and impacts[0][1]==i,impacts
out=dict(id=cfg['original_owner'],url=uri,tile_sha256=prior['sha256'],size=len(raw),original_parts=len(allparts),feature_count=len(b['features']),source_owner=2849,feature=fid,component=i,sibling_count=n-1,area=part.area,source_iou=iou,touching_source=[(ii,ff,ix,ct)for ii,ff,ix,ct,_ in candidates],selected_ground_wgs=mapping(g.transform(restore,geog)),all_changed_components=impacts,unchanged_parts=len(allparts)-1,selected_source_id=ref['owners'][0]['key'].split(':',1)[1])
(w/'vector-scope.json').write_text(json.dumps(out,indent=2)+'\n')
print(fid,i,n,iou,len(allparts),impacts)
