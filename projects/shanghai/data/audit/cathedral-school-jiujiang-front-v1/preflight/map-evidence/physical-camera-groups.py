"""Find every native feature that the nominated eye-to-surface sight lines approach."""
from pathlib import Path
import json,gzip,math,hashlib
import numpy as np,shapely
from shapely.geometry import shape,LineString,Point
from shapely.strtree import STRtree
w=Path(__file__).parent;read=lambda p:json.loads(p.read_bytes());ref=read(w/'original-review.json');contract=read(w/'final-placement-contract.json');cam=read(w/'map-camera-proof.json')['winner'];table=json.loads(gzip.decompress((w/'inputs/feature-table.json.gz').read_bytes()))['features'];ready=read(w/'inputs/READY.json');lon,lat=contract['lng'],contract['lat'];k=6371008.8*math.cos(math.radians(lat));north0=math.asinh(math.tan(math.radians(lat)));angle=math.radians(contract['heading']);c,s=math.cos(angle),math.sin(angle)
def local(q):
 east=np.radians(q[:,0]-lon)*k;north=(np.arcsinh(np.tan(np.radians(q[:,1])))-north0)*k;return np.column_stack((east*c-north*s,east*s+north*c))
fids=[];polys=[]
for r in table:
 g=shape(r['geometry'])
 if g.distance(Point(lon,lat))<.0026:
  fids.append(r['localId']);polys.append(shapely.transform(g,local))
ix=STRtree(np.array(polys,dtype=object));rows={};ids=set()
for v in cam['scores']:
 eye=v['camera_local'];obs=[]
 for sample in v['probes']:
  target=sample['point_local'];line=LineString([eye[:2],target[:2]]);close=ix.query(line.buffer(1.20),predicate='intersects');near=sorted({fids[i]for i in close});ids.update(near);obs.append({'feature':sample['feature'],'target':target,'owner_ids_to_inspect':near})
 rows[v['screen']]=dict(eye=eye,sightlines=obs)
gr=[{'id':t['id'],'file':t['file'],'signed_sha256':t['sha256'],'members':t['featureLocalIds'],'relevant':sorted(ids.intersection(t['featureLocalIds']))} for t in ready['tiles'] if ids.intersection(t['featureLocalIds'])]
out={'contract_sha256':hashlib.sha256((w/'final-placement-contract.json').read_bytes()).hexdigest(),'camera_sha256':hashlib.sha256((w/'map-camera-proof.json').read_bytes()).hexdigest(),'groups':gr,'all_ids':sorted(ids),'views':rows};(w/'camera-sightline-sources.json').write_text(json.dumps(out,indent=1)+'\n');print(len(gr),len(ids),[(q['id'],len(q['relevant']))for q in gr])
