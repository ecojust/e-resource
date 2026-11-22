"""Test the garden portico's preliminary cut against every OSM fallback tile component."""
from pathlib import Path
import gzip,hashlib,json,sys,math,requests
import numpy as np
import shapely as g
from shapely.geometry import shape,box,mapping
import mapbox_vector_tile
w=Path(__file__).parent
frame=json.loads((w/'garden-face.json').read_bytes());src=Path(__file__).resolve().parents[4]/'source/precise/jingan-ho-tung-residence-garden-portico/footprint-review.json';review=json.loads(src.read_bytes())
lon,lat=frame['anchor'];h=math.radians(frame['runtime_heading_degrees']);axes=np.array([[math.cos(h),-math.sin(h)],[math.sin(h),math.cos(h)]])
k=6371008.8*math.cos(math.radians(lat));base=math.asinh(math.tan(math.radians(lat)))
def local(coords):return np.column_stack((np.radians(coords[:,0]-lon)*k,(np.arcsinh(np.tan(np.radians(coords[:,1])))-base)*k))@axes.T
def wgs(v):
 xs,ys=v.T/extent
 return np.column_stack(((13719+xs)/16384*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*(6694+ys)/16384))))))
def unproject(v):
 east,north=(v@axes).T
 return np.column_stack((lon+np.degrees(east/k),np.degrees(np.arctan(np.sinh(base+north/k)))))
owner=g.transform(shape(next(r['geometry'] for r in review['owners']if r['local_id']==1292)),local);cut=box(-5.15,-.40,5.15,4.30)
url='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13719/6694.pbf'
archive=w/'vector.pbf.gz'
if archive.is_file():payload=gzip.decompress(archive.read_bytes())
else:
 response=requests.get(url,timeout=(10,40));response.raise_for_status();payload=response.content;archive.write_bytes(gzip.compress(payload,6,mtime=0))
layer=mapbox_vector_tile.decode(payload,default_options={'y_coord_down':True})['building'];extent=layer['extent'];seen=0;around=[];cover=[]
for f in layer['features']:
 geo=shape(f['geometry']);parts=list(geo.geoms) if geo.geom_type=='MultiPolygon'else[geo]
 for idx,obj in enumerate(parts):
  seen+=1;q=g.transform(g.transform(obj,wgs),local);distance=q.distance(cut)
  if distance>55:continue
  overlap=q.intersection(owner).area;removed=q.intersection(cut).area
  r=dict(feature=f['id'],component=idx,feature_components=len(parts),area=q.area,source_iou=overlap/q.union(owner).area,overlap_m2=overlap,cut_overlap_m2=removed,distance_m=distance,properties=f['properties'])
  around.append(r)
  if removed>1e-7:cover.append(r)
assert len(cover)<=1,cover
if cover:assert cover[0]['source_iou']>.80 and cover[0]['cut_overlap_m2']>30
info=dict(provisional=True,owner=1292,source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),url=url,bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),tile=[14,13719,6694],extent=extent,feature_count=len(layer['features']),all_components=seen,affected=cover,nearby=sorted(around,key=lambda r:r['distance_m']),other_component_count=seen-len(cover),cut_local=list(cut.exterior.coords),cut_wgs=mapping(g.transform(cut,unproject)))
(w/'vector-scope.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
print(seen,len(cover),[(v['feature'],v['component'],v['source_iou'],v['cut_overlap_m2'])for v in cover])
