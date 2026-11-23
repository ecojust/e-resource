import json,hashlib
from pathlib import Path
import numpy as np,shapely
from read_vector import building
from shapely.geometry import shape,mapping
w=Path(__file__).parent;rev=json.loads((w/'original-review.json').read_bytes());f=w/'inputs/original-vector.pbf';data=f.read_bytes();layer=building(data);scale=layer['extent']
def to_ll(q):
 u,v=q.T/scale;return np.stack(((13720+u)/16384*360-180,np.rad2deg(np.arctan(np.sinh(np.pi*(1-2*(6694+v)/16384))))),axis=1)
pieces=[];own=shape(next(o['geometry_wgs84'] for o in rev['owners'] if o['local_id']==1810));zone=own.buffer(.0015)
for feat in layer['features']:
 raw=shapely.transform(shape(feat['geometry']),to_ll)
 for i,p in enumerate(raw.geoms if raw.geom_type=='MultiPolygon'else [raw]):
  if zone.intersects(p):pieces.append((int(feat['id']),i,p,feat['properties']))
rows=[];unmatched=[]
for g in rev['owners']:
 near=shape(g['geometry_wgs84']);candidates=[(p.intersection(near).area/p.union(near).area,k,i,pr)for k,i,p,pr in pieces if p.intersects(near)]
 if not candidates:unmatched.append(g['local_id']);continue
 score,fid,idx,prop=max(candidates,key=lambda v:v[0]);rows.append(dict(native_id=g['local_id'],mvt_feature_id=fid,component=idx,iou=score,properties=prop))
target=next(v for v in rows if v['native_id']==1810);assert target['iou']>.96 and not any(v['native_id']!=1810 and v['mvt_feature_id']==target['mvt_feature_id']and v['component']==target['component'] for v in rows)
(w/'map-visible-components.json').write_text(json.dumps([dict(type='Feature',id=k,component=i,properties=pr,geometry=mapping(p))for k,i,p,pr in pieces],separators=(',',':'))+'\n')
(w/'vector-and-osm-owners.json').write_text(json.dumps({'source_url':'https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13720/6694.pbf','mvt_sha256':hashlib.sha256(data).hexdigest(),'building_feature_count':len(layer['features']),'local_component_count':len(pieces),'native_to_vector':rows,'native_without_local_osm_component':unmatched,'osm_way':292718777},ensure_ascii=False,indent=1)+'\n');print(target,len(pieces))
