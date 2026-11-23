"""Re-run the source lookup and measured cut through the signed original ordinary renderer."""
import os as _author_os
from pathlib import Path as _AuthorPath
_author_project = next(p for p in _AuthorPath(__file__).resolve().parents if p.name == 'shanghai')
_author_data = _AuthorPath(_author_os.environ.get('LIUYAZI_EVIDENCE_ROOT', _author_project / 'data' / 'surveys'))
from pathlib import Path
from urllib.request import urlopen
from tempfile import TemporaryDirectory
import hashlib,subprocess,gzip,time,os,sys,json
import numpy as np,shapely
from shapely.geometry import shape,mapping
sys.path.insert(0,str(_author_data / 'qianguild301-vector'))
import mapbox_vector_tile
w=Path(os.environ.get('LIUYAZI_WORK',Path(__file__).parent));order=int(sys.argv[1]) if len(sys.argv)>1 else 277
read=lambda p:json.loads(p.read_bytes());h=lambda b:hashlib.sha256(b).hexdigest()
v=read(w/'vector-scope.json');r=read(w/'footprint-review.json');orig=read(w/'source-owner-selection.json');pbf=gzip.decompress((w/'vector.pbf.gz').read_bytes());assert h(pbf)==v['tile_sha256']
lay=mapbox_vector_tile.decode(pbf,default_options=dict(y_coord_down=True))['building'];E=lay['extent']
def geo(q):return np.column_stack(((13719+q[:,0]/E)/16384*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*(6695+q[:,1]/E)/16384))))))
f=[dict(type='Feature',id=g['id'],properties=g['properties'],geometry=mapping(shapely.transform(shape(g['geometry']),geo)))for g in lay['features']]
owner=[dict(type='Feature',id=e['key'].split(':',1)[1],properties={'id':e['key'].split(':',1)[1]},geometry=e['geometry']) for e in r['owners']]
rule=dict(id=r['id'],owner=dict(macro_id=r['frozen_macro'],feature_local_id=2849),geometry=orig['proposed_cut_wgs84'],osm_replacement_geometry=v['selected_ground_wgs'],source_feature_ids=dict(building=[v['selected_source_id']],building_part=[]))
args=dict(features=f,originals=owner,srcRule=rule,target=v['feature'],index=v['component'],m2PerDegree2=(np.pi*6371008.8/180)**2*np.cos(np.radians(r['author_frame']['anchor']['lat'])))
inputs={};baseline=read(Path(_author_data / 'shanghai-yongjia-porch' / 'scenes' / f'{order}-comparison.json'));assert baseline['passed']
sys.path.insert(0,str(_author_data / 'shanghai-yongjia-porch'))
from common import canon,full
signed=full(order)
assert h(canon(signed))==baseline['production_receipt_sha256']
with TemporaryDirectory(dir='/dev/shm') as tmp:
 t=Path(tmp)
 for k in ['src/candidate-vector-clipping.js','src/candidate-vector-geometry.js','vendor/polygon-clipping.umd.min.js']:
  with urlopen(f'http://127.0.0.1:{31000+order}/'+k,timeout=15)as response:
   assert response.status==200;data=response.read()
  local=Path(str(_author_project))/k;assert h(data)==h(local.read_bytes());assert k not in signed['files'] or signed['files'][k]==h(data);dest=t/k;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);inputs[k]=h(data)
 (t/'package.json').write_text('{"type":"module"}')
 result=json.loads(subprocess.check_output(['nice','-n','15','node','--max-old-space-size=300',Path(__file__).with_name('check-vector.mjs'),t],input=json.dumps(args).encode()))
result.update(order=order,production_receipt_sha256=baseline['production_receipt_sha256'],renderer_inputs=inputs,real_tile_sha256=h(pbf),gis_scope_sha256=h((w/'source-owner-selection.json').read_bytes()),rollback_source_clear=True)
file=w/f'vector-renderer-{order}.json';file.write_text(json.dumps(result,indent=2)+'\n');print(file,h(file.read_bytes()),result['other_component_union_xor_m2'])
