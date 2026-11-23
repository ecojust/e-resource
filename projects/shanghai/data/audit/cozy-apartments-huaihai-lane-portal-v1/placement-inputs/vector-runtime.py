"""Run all components from the original vector tile through its signed ordinary renderer."""
import os
from model import *
import gzip,subprocess
sys.path.insert(0,os.environ['SHANGHAI_VECTOR_TOOLS'])
import mapbox_vector_tile
pg=ri(w/'vector-scope.json');base=ri(w/'runtime-baseline.json');raw=gzip.decompress((w/'vector.pbf.gz').read_bytes());assert sha(raw)==pg['sha256']
layer=mapbox_vector_tile.decode(raw,default_options={'y_coord_down':True})['building']
def geographic(v):
    x,y=v.T/layer['extent'];return np.column_stack(((13720+x)/16384*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*(6694+y)/16384))))))
def components(geo):return list(geo.geoms) if geo.geom_type=='MultiPolygon' else [geo]
features=[dict(type='Feature',id=r['id'],properties=r['properties'],geometry=G.mapping(g.transform(G.shape(r['geometry']),geographic)))for r in layer['features']]
filename=w/f"signed-runtime-{base['order']}/src/candidate-vector-clipping.js";assert sha(filename.read_bytes())==base['inputs']['src/candidate-vector-clipping.js']
js="""import fs from 'node:fs';import {pathToFileURL}from'node:url';const {planCandidateVectorClipping:plan}=await import(pathToFileURL(process.argv[1]));const {features,clip}=JSON.parse(fs.readFileSync(0));const ctx={source:'openmaptiles',sourceLayer:'building'},a=plan(features,{candidateClips:[]},ctx),b=plan(features,{candidateClips:[clip]},ctx);console.log(JSON.stringify({before:a.stats,after:b.stats,changed:[...b.desired.values()],residual:b.residualData}));"""
clip=ri(w/'final-placement-contract.json')['site_replacement'];out=json.loads(subprocess.check_output(['node','--input-type=module','-e',js,filename],input=json.dumps(dict(features=features,clip=clip)).encode()))
fid,index=pg['affected'][0]['feature'],pg['affected'][0]['component'];assert out['changed']==[{'id':fid,'residual':True}] and out['before']['partialIDs']==0 and out['after']['clippingErrors']==0
remaining=components(g.transform(G.shape(out['residual']['features'][0]['geometry']),loc));spatial=g.STRtree(remaining);mask=g.transform(G.shape(clip['geometry']),loc);losses=[];hit=None
for f in features:
 for i,poly in enumerate(components(G.shape(f['geometry']))):
    p=g.transform(poly,loc);expected=p.intersection(mask).area
    if f['id']==fid:
        residual=g.union_all([remaining[k]for k in spatial.query(p,predicate='intersects')]);lost=p.difference(residual).area
    else:lost=0
    assert abs(lost-expected)<.003,(f['id'],i,lost,expected)
    if (f['id'],i)==(fid,index):hit=dict(component=i,area_m2=p.area,removed_m2=lost,retained_m2=p.area-lost)
    else:losses.append(lost)
assert hit and hit['removed_m2']>12 and len(losses)==pg['all_components']-1
save(w/'vector-renderer.json',dict(passed=True,source=pg['url'],tile_sha256=pg['sha256'],runtime_sha256=base['inputs']['src/candidate-vector-clipping.js'],owner=2172,feature_id=fid,actual_component=hit,checked_neighbor_components=len(losses),largest_other_area_change_m2=max(losses),total_other_area_change_m2=sum(losses),before=out['before'],after=out['after']))
print('vector',fid,hit,len(losses))
