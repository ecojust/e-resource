"""Inventory final curtain assets without rewriting upstream wall-stage claims."""
import argparse,json,struct,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--directory',type=Path,required=True);a=ap.parse_args();d=a.directory;files={};copyright=None;extras=None
for name in ['bund15-curtain-raw.glb','bund15-curtain-web.glb','bund15-curtain-lod.glb']:
 p=d/name;b=p.read_bytes();magic,version,size=struct.unpack_from('<III',b);assert magic==0x46546c67 and version==2 and size==len(b) and size<100_000_000
 n,t=struct.unpack_from('<II',b,12);assert t==0x4e4f534a;doc=json.loads(b[20:20+n]);assert not doc.get('images') and not doc.get('textures')
 cp=doc['asset']['copyright'];ex=doc['asset']['extras'];assert 'Suicasmo' in cp and 'OpenStreetMap' in cp and 'CC0' in cp
 if copyright is None:copyright,extras=cp,ex
 assert cp==copyright and ex==extras
 assert ex['wall_cleanup_stage']=='classical-bank-wall-v4.4';assert ex['curtain_repair']['input_wall_raw_sha256']=='0b6ec1409ca5230da74b63b977a08420e493e75670fdb5047322d97ec001eb29'
 tris=0;bounds=[]
 for me in doc['meshes']:
  for pr in me['primitives']:
   ac=doc['accessors'][pr['attributes']['POSITION']];bounds.append((ac['min'],ac['max']));tris+=doc['accessors'][pr['indices']]['count']//3
 files[name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'triangles':tris,'images':[],'textures':0,'copyright':cp,'asset_extras':ex,'bounds_glb':{'min':[min(v[0][k] for v in bounds) for k in range(3)],'max':[max(v[1][k] for v in bounds) for k in range(3)]}}
p=d/'bund15-curtain.blend';files[p.name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};assert p.stat().st_size<100_000_000
raw,web,lod=[files[n] for n in ['bund15-curtain-raw.glb','bund15-curtain-web.glb','bund15-curtain-lod.glb']];assert raw['triangles']==web['triangles']==92848 and lod['triangles']<92848
for b in [web,lod]:
 for k in ['min','max']:assert max(abs(x-y) for x,y in zip(b['bounds_glb'][k],raw['bounds_glb'][k]))<1e-6
record=json.loads((ROOT/'asset-template.json').read_text());wall_before=json.dumps(record['wall_topology_cleanup'],sort_keys=True)
repair={'version':'bund15-curtain-v4.4','upstream_source_package':'source/bund/classical_bank/wall-v4.4/README.md','input_wall_stage_sha256':{r:record[r+'_sha256'] for r in ['raw','web','lod','native']},'prisms_reoriented':10,'native_faces_reoriented':425,'triangles_reoriented':580,'remaining_vertex_positions_unchanged':True,'interpenetrating_fold_boxes_removed':120,'interpenetrating_fold_triangles_removed':1440,'wall_and_opening_geometry_unchanged':True,'current_native_validation':'data/bund/validation/bund15-curtain-native-v4.4.json','current_preservation':'data/bund/validation/bund15-curtain-preservation-v4.4.json','prior_report_scope':'wall_topology_cleanup and its preservation report retain their original pre-wall→wall-stage output hashes. This later stage reverses ten curtain prisms and deletes 120 interpenetrating internal fold boxes; it does not extend the old full-preservation claim across these explicit changes.'}
for role,name in [('raw','bund15-curtain-raw.glb'),('web','bund15-curtain-web.glb'),('lod','bund15-curtain-lod.glb'),('native','bund15-curtain.blend')]:record[role+'_sha256']=files[name]['sha256'];record[role+'_bytes']=files[name]['bytes']
record['triangles']=raw['triangles'];record['lod_triangles']=lod['triangles'];record['bounds_glb']=raw['bounds_glb'];record['source_package']='source/bund/classical_bank/curtain-v4.4/README.md';record['curtain_repair']=repair
record['detail_note']='先修复结构墙内部重合面与T接缝，保留96洞、拱曲线、中央退进、柱和窗框；随后纠正10个反向窗帘体的580三角朝向，删除120个内部穿插褶皱盒的1440三角，剩余位置与其他几何保持不变。参考照片不作为纹理；高度及未见细节含推定，不是测绘或摄影测量。'
assert json.dumps(record['wall_topology_cleanup'],sort_keys=True)==wall_before
meta=json.loads((ROOT/'raw-metadata-template.json').read_text());assert meta['wall_topology_cleanup']==record['wall_topology_cleanup']
meta.update({'version':'bund15-curtain-v4.4','raw_bytes':raw['bytes'],'glb_bytes':raw['bytes'],'raw_sha256':raw['sha256'],'native_bytes':files['bund15-curtain.blend']['bytes'],'native_sha256':files['bund15-curtain.blend']['sha256'],'triangles':raw['triangles'],'bounds_glb':raw['bounds_glb'],'source_package':record['source_package'],'curtain_repair':repair,'current_detail_note':record['detail_note']})
(d/'asset-files.json').write_text(json.dumps(files,ensure_ascii=False,indent=2));(d/'asset-metadata.json').write_text(json.dumps(record,ensure_ascii=False,indent=2));(d/'raw-metadata-proposal.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print(json.dumps({k:{'bytes':v['bytes'],'sha256':v['sha256'],'triangles':v.get('triangles')} for k,v in files.items()},indent=2))
