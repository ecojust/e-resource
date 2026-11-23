"""Recompute two dates of visible garden-house roof overlap in a local WGS84 metric frame."""
import json,math,sys
from pathlib import Path
from shapely.geometry import Polygon,shape
from shapely.ops import transform
root=Path(__file__).parent
epochs=json.loads((root/'two-period-visible-roof.json').read_bytes())['records']
owners=json.loads((root/'236-and-248-candidates.json').read_bytes())
def collect(obj):
 if isinstance(obj,dict):
  if 'wgs84' in obj and 'id' in obj:yield obj
  for value in obj.values():yield from collect(value)
 if isinstance(obj,list):
  for value in obj:yield from collect(value)
lon,lat=121.42321,31.20486
rad=math.pi/180;e=.00669437999014;k=math.sqrt(1-e*math.sin(lat*rad)**2)
sx=6378137*math.cos(lat*rad)*rad/k;sy=6378137*(1-e)*rad/k**3
def planar(x,y,z=None):return ((x-lon)*sx,(y-lat)*sy)
city={str(r['id']):transform(planar,shape(r['wgs84'])) for r in collect(owners)}
result={};roofs=[]
for data in epochs:
 x0,y0=data['original_origin'];x1,y1,*_=data['crop_native'];n=256*2**19
 def model(x,y):
  x=x/data['display_scale']+x0+x1;y=y/data['display_scale']+y0+y1
  return planar(360*x/n-180,math.atan(math.sinh(math.pi*(1-2*y/n)))/rad)
 footprint=Polygon([model(*pair)for pair in data['visible_outline']]);assert footprint.is_valid
 roofs.append(footprint);result[data['imagery']['layerIdentifier']]={'visible_area_m2':footprint.area,'overlaps':{id:footprint.intersection(g).area for id,g in city.items()}}
out={'address':'新华路236号','epochs':result,'mutual_overlap_m2':roofs[0].intersection(roofs[1]).area,'centres_apart_m':roofs[0].centroid.distance(roofs[1].centroid)}
Path(sys.argv[1]).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(result)
