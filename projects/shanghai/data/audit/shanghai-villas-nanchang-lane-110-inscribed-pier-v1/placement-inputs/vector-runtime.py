import os
"""Run all components from the original vector tile through its signed ordinary renderer."""
from model import *
import gzip,subprocess
sys.path.insert(0,os.environ['VILLA_VECTOR_TOOLS'])
import mapbox_vector_tile
pg=ri(w/'vector-scope.json');base=ri(w/'runtime-baseline.json');raw=gzip.decompress((w/'vector.pbf.gz').read_bytes());assert sha(raw)==pg['sha256']
layer=mapbox_vector_tile.decode(raw,default_options={'y_coord_down':True})['building']
def geographic(v):
    x,y=v.T/layer['extent'];return np.column_stack(((13719+x)/16384*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*(6695+y)/16384))))))
def components(geo):return list(geo.geoms) if geo.geom_type=='MultiPolygon' else [geo]
features=[dict(type='Feature',id=r['id'],properties=r['properties'],geometry=G.mapping(g.transform(G.shape(r['geometry']),geographic)))for r in layer['features']]
filename=w/f"signed-runtime-{base['order']}/src/candidate-vector-clipping.js";assert sha(filename.read_bytes())==base['inputs']['src/candidate-vector-clipping.js']
js="""import fs from 'node:fs';import{pathToFileURL}from'node:url';const{planCandidateVectorClipping:plan}=await import(pathToFileURL(process.argv[1]));const{features}=JSON.parse(fs.readFileSync(0));const ctx={source:'openmaptiles',sourceLayer:'building'},a=plan(features,{candidateClips:[]},ctx);console.log(JSON.stringify({stats:a.stats,changed:[...a.desired.values()],residual:a.residualData}));"""
raw=json.loads(subprocess.check_output(['node','--input-type=module','-e',js,filename],input=json.dumps(dict(features=features)).encode()))
assert not raw['changed'] and raw['stats']['partialIDs']==0 and raw['stats']['clippingErrors']==0
assert len(features)==pg['feature_count']and not pg['affected']
identity=sorted(pg['nearby'],key=lambda x:-x['source_iou'])[0];assert identity['source_iou']>.85
save(w/'vector-renderer.json',dict(passed=True,source=pg['url'],tile_sha256=pg['sha256'],runtime_sha256=base['inputs']['src/candidate-vector-clipping.js'],owner=3695,identity=identity,all_components=pg['all_components'],all_direct_changes=raw['changed'],all_max_area_change_m2=0,model_intersects_no_identity=True,stats=raw['stats']))
print('vector',pg['all_components'],identity['feature'],identity['component'],identity['source_iou'])
