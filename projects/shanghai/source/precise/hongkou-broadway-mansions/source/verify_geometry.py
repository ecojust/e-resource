"""Actual exported geometry and closed author solids; no claim of surveyed accuracy. MIT."""
import argparse,hashlib,json,struct,subprocess,tempfile
from pathlib import Path
import numpy as np
import trimesh
from build_model import build,ID
p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--gltfpack',type=Path);a=p.parse_args();report={}
manifest=json.loads((a.assets/'manifest.json').read_text()) if (a.assets/'manifest.json').exists() else None
with tempfile.TemporaryDirectory(prefix='broadway-decode-') as tmp:
 for role in ['raw','full','lod'] if manifest else ['raw','lod']:
  entry=manifest['assets'][role] if manifest else None
  path=a.assets/entry['file'] if entry else a.assets/f'{ID}-{role}.glb'
  data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);assert doc['extras']['id']==ID
  assert not doc.get('images') and not doc['extras']['map_replacement'] and not doc['extras']['floor_conflict_resolved']
  if entry:assert entry['bytes']==len(data) and entry['sha256']==hashlib.sha256(data).hexdigest()
  decoded=path
  if 'EXT_meshopt_compression' in doc.get('extensionsRequired',[]):
   assert a.gltfpack
   decoded=Path(tmp)/(role+'.glb');subprocess.run([str(a.gltfpack.resolve()),'-i',str(path),'-o',str(decoded),'-noq','-vnf','-km','-kn','-ke'],check=True)
  scene=trimesh.load(decoded,force='scene',process=False);meshes=list(scene.dump());assert meshes
  for m in meshes:assert np.isfinite(m.vertices).all() and (m.area_faces>1e-12).all() and m.is_winding_consistent
  count=sum(len(m.faces) for m in meshes);assert 0<count and abs(scene.bounds[1,1]-76.7)<1e-4 and abs(scene.bounds[0,1])<1e-6
  if entry:assert count==entry['triangles']
  if role in ['raw','lod']:
   authored,_,features=build(role=='lod')
   for part in authored.parts:
    m=trimesh.Trimesh(part['vertices'],part['triangles'],process=True)
    assert m.is_watertight and m.is_winding_consistent and m.volume>0,part['label']
   assert count==sum(len(q['triangles']) for q in authored.parts)
   assert len(features['floors'])==22 and features['estimated_window_openings']>500
   assert all(x['plan_area_m2']>=y['plan_area_m2'] for x,y in zip(features['floors'],features['floors'][1:]))
  report[role]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'triangles':count,'bounds_glb':scene.bounds.tolist(),'finite_vertices':True,'nondegenerate_faces':True,'consistent_winding':True,'authored_closed_positive_solids_checked':role in ['raw','lod'],'photos_embedded':False}
 assert report['lod']['triangles']<report['raw']['triangles']
 if manifest:
  assert report['full']['triangles']==report['raw']['triangles']
  for r in report:assert np.allclose(report[r]['bounds_glb'],report['raw']['bounds_glb'],atol=1e-5)
  native=manifest['assets']['native'];d=(a.assets/native['file']).read_bytes();assert len(d)==native['bytes'] and hashlib.sha256(d).hexdigest()==native['sha256']
 assert all(x['bytes']<100_000_000 for x in report.values())
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
