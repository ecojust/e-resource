"""Find the registered southern block among the individual polygons of the real fallback tile."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import numpy as np
from shapely.geometry import shape,Point,mapping
import shapely as g
import mapbox_vector_tile
def main():
 ap=argparse.ArgumentParser();ap.add_argument('tile',type=Path);ap.add_argument('footprint',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
 b=a.tile.read_bytes();dig=hashlib.sha256(b).hexdigest();assert dig=='36448c327185ab13a8d07e723bda4d00dec0c1d36c6831a4c6aa50de13a07893'
 r=json.loads(a.footprint.read_bytes());o=r['author_frame']['anchor'];owner=next(v for v in r['owners']if v['local_id']==4093);poly=shape(owner['geometry_wgs84']);sx=111195.08*math.cos(math.radians(o['lat']));sy=111195.08
 def metres(xy):return (xy-[o['lng'],o['lat']])*[sx,sy]
 source=g.transform(poly,metres);total=0;near=[];best=None
 layer=mapbox_vector_tile.decode(b,default_options={'y_coord_down':True})['building']
 def wgs(uv):
  x=13719+uv[:,0]/layer['extent'];y=6695+uv[:,1]/layer['extent'];return np.c_[x/16384*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*y/16384))))]
 for f in layer['features']:
  parts=g.get_parts(shape(f['geometry']));total+=len(parts)
  for i,raw in enumerate(parts):
   outline=g.transform(raw,wgs);m=g.transform(outline,metres)
   if m.distance(Point(0,0))>60:continue
   iou=m.intersection(source).area/m.union(source).area
   arow=dict(type='Feature',id=f['id'],component=i,properties=f['properties'],geometry=mapping(outline))
   near.append(arow)
   if best is None or iou>best['iou']:best=dict(native_id=4093,mvt_feature_id=f['id'],component=i,iou=iou)
 assert len(near)>10 and total>1000 and best['iou']>.50,(len(near),total,best)
 stats=dict(passed=True,tile_source='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13719/6695.pbf',sha256=dig,original_parts=total,nearby=near,native_to_vector=[best],ground_replacement=None)
 a.output.write_text(json.dumps(stats,ensure_ascii=False,indent=1)+'\n');print(total,len(near),best)
if __name__=='__main__':main()
