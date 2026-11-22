"""Run the full published 2,426-component fallback feature through the actual renderer clipping function."""
from pathlib import Path
from urllib.request import urlopen
import json,sys,hashlib,os,subprocess
import numpy as np,shapely as g
from shapely import geometry as G
from model import w,project,ri,save,sha,loc
import mapbox_vector_tile
r=ri(w/'proposed-source-cut.json');pg=r['vector']
import requests
cache=os.environ.get('CHANGSHU_VECTOR_FILE');source=Path(cache).read_bytes() if cache else None
if cache and cache.endswith('.gz'):
 import gzip
 source=gzip.decompress(source)
if source is None:
 rep=requests.get(pg['url'],timeout=30);rep.raise_for_status();source=rep.content
assert sha(source)==pg['sha256'];layer=mapbox_vector_tile.decode(source,default_options={'y_coord_down':True})['building'];entry=next(row for row in layer['features']if row['id']==147898520);ext=layer['extent']
def wgs(v):
 c,y=v.T/ext;return np.column_stack(((13718+c)/16384*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*(6695+y)/16384))))))
geom=g.transform(G.shape(entry['geometry']),wgs);assert len(geom.geoms)==2426
feature={'type':'Feature','id':entry['id'],'geometry':G.mapping(geom),'properties':entry['properties']}
source_js=w/f"signed-runtime-{ri(w/'runtime-baseline.json')['order']}"/'src/candidate-vector-clipping.js'
expected=ri(w/'runtime-baseline.json')['inputs']['src/candidate-vector-clipping.js'];assert sha(source_js.read_bytes())==expected
code="""import fs from 'node:fs';import {pathToFileURL} from 'node:url';
const {planCandidateVectorClipping}=await import(pathToFileURL(process.argv[1]).href);
const {feature,clip}=JSON.parse(fs.readFileSync(0,'utf8'));const context={source:'openmaptiles',sourceLayer:'building'};
const off=planCandidateVectorClipping([feature],{candidateClips:[]},context);
const on=planCandidateVectorClipping([feature],{candidateClips:[{...clip,geometry:clip.replacement_geometry}]},context);
process.stdout.write(JSON.stringify({prior:off.stats,stats:on.stats,residual:on.residualData}));"""
ret=json.loads(subprocess.check_output(['node','--input-type=module','-e',code,source_js],input=json.dumps(dict(feature=feature,clip=ri(w/'final-placement-contract.json'))).encode()))
assert ret['stats']['clippingErrors']==0 and ret['prior']['partialIDs']==0 and ret['stats']['partialIDs']==1
residual=g.transform(G.shape(ret['residual']['features'][0]['geometry']),loc);mask=G.shape(r['cut_local']);nearbox=mask.buffer(1);index=g.STRtree(residual.geoms);neg=[];hitrow=None
# Touching source components may be merged by a union. Measure actual area still covered for each input feature.
for i,p in enumerate(geom.geoms):
 native=g.transform(p,loc);candidates=index.query(native,predicate='intersects');back=g.union_all([residual.geoms[k]for k in candidates]);retained=native.intersection(back).area;loss=max(0.,native.area-retained);expected=native.intersection(mask).area
 assert abs(loss-expected)<.003,(i,loss,expected)
 if i==2277:hitrow=dict(component=i,area_m2=native.area,removed_m2=loss,retained_m2=retained)
 else:neg.append(loss)
assert hitrow and hitrow['removed_m2']>80 and max(neg)<.003
save(w/'vector-renderer.json',dict(passed=True,source=pg['url'],tile_sha256=pg['sha256'],runtime_sha256=expected,owner=3343,feature_id=entry['id'],actual_component=hitrow,checked_neighbor_components=len(neg),largest_other_area_change_m2=max(neg),total_other_area_change_m2=sum(neg),whole_feature_response=ret['stats'],before=ret['prior']))
print('runtime',hitrow,len(neg),max(neg))
