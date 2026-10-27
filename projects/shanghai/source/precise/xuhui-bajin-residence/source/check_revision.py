"""Read actual v2 parts/raw and compare with frozen v1; never modifies v1."""
from pathlib import Path
import json,gzip,hashlib,collections,struct
import numpy as np
ROOT=Path(__file__).resolve().parent.parent
OLD=ROOT.parent/'bajin-detailed-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parts(root):return json.loads(gzip.decompress((root/'construction-parts.json.gz').read_bytes()))['parts']
def sign(p):return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()
a=parts(OLD);b=parts(ROOT);assert len(a)==len(b)
allowed={'north-entry-bay/arch-surround','north-entry-bay/portal-low-side-coping','north-entry-single-stepped-solid','north-entry-bay/portal-low-side-wall'}
changed=[]
for p,q in zip(a,b):
 assert (p['label'],p['material'])==(q['label'],q['material'])
 if sign(p)!=sign(q):
  assert q['label'] in allowed;changed.append(q['label'])
assert len(changed)==6
same_paths=['source/geometry-input.json','source/roof_planar.py','source/build_palette.py','source/facade_details.py','source/common/photo_architecture.py','source/generate_material.py','roof-planar-contract.json','uv-contract.json']+[p.relative_to(ROOT).as_posix() for p in (ROOT/'textures').glob('*')]
for name in same_paths:assert sha(OLD/name)==sha(ROOT/name),name
oldD=json.loads((OLD/'source/design-input.json').read_text());D=json.loads((ROOT/'source/design-input.json').read_text());assert oldD['frame']==D['frame'] and oldD['dimensions_C']==D['dimensions_C']
f=D['frame'];R=np.array([[*f['architecture_X_EN'],0],[*f['architecture_Y_EN'],0],[0,0,1]]).T
p=next(p for p in b if p['label']=='north-entry-single-stepped-solid');v=np.asarray(p['vertices']);tri=np.array(p['triangles']);vv=v@R
edges=collections.Counter(tuple(sorted((int(i),int(j)))) for t in tri for i,j in zip(t,np.roll(t,-1)))
assert set(edges.values())=={2},collections.Counter(edges.values())
vol=float(np.einsum('ij,ij->i',v[tri[:,0]],np.cross(v[tri[:,1]],v[tri[:,2]])).sum()/6)
expect=sum(w*f*.1 for w,f in zip([2.25,2.04,1.84],[.91,.68,.45]));assert abs(vol-expect)<1e-9
nf=D['frame']['depth_m']/2+.18
stair_faces=[]
for zi,yf,width in zip([.1,.2,.3],[.91,.68,.45],[2.25,2.04,1.84]):
 tris=[]
 for t in tri:
  q=vv[t]
  if np.max(np.abs(q[:,1]-nf-yf))<1e-9 and q[:,2].min()>=zi-.1-1e-9 and q[:,2].max()<=zi+1e-9:
   n=np.cross(q[1]-q[0],q[2]-q[0]);
   if n[1]>1e-9:tris.extend(q.tolist())
 q=np.asarray(tris);assert len(q)>0
 got=float(q[:,0].max()-q[:,0].min());assert abs(got-width)<1e-9
 stair_faces.append({'riser_top_m':zi,'front_from_facade_m':yf,'actual_riser_width_m':got})
arch=next(p for p in b if p['label']=='north-entry-bay/arch-surround');archv=np.asarray(arch['vertices'])@R
assert abs(archv[:,2].min()-1.34)<1e-9
copings=[p for p in b if p['label']=='north-entry-bay/portal-low-side-coping'];cb=[]
for p in copings:
 q=np.asarray(p['vertices'])@R;outer=float(np.abs(q[:,0]).max());inner=float(np.abs(q[:,0]).min());assert abs(inner-.885)<1e-9 and abs(outer-2.345)<1e-9;assert abs(q[:,2].min()-1.2)<1e-9 and abs(q[:,2].max()-1.34)<1e-9;cb.append({'inner_abs_x_m':inner,'outer_abs_x_m':outer,'z_min_max_m':[float(q[:,2].min()),float(q[:,2].max())]})
low_wall_bounds=[]
for p in [p for p in b if p['label']=='north-entry-bay/portal-low-side-wall']:
 q=np.asarray(p['vertices'])@R;inner=float(np.abs(q[:,0]).min());outer=float(np.abs(q[:,0]).max());front=float(q[:,1].max()-nf)
 assert abs(inner-.92)<1e-9 and abs(outer-2.125)<1e-9 and abs(front-.03)<1e-9
 low_wall_bounds.append({'inner_abs_x_m':inner,'outer_abs_x_m':outer,'front_projection_m':front})
canonical=json.loads((ROOT/'source/asset-metadata.json').read_text())['copyright']
raw_copyright=[]
for fn in ['bajin-main-detailed.glb','bajin-main-lod.glb']:
 data=(ROOT/'exports'/fn).read_bytes();n=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+n]);assert g['asset']['copyright']==g['extras']['copyright']==canonical
 blob=data[28+n:]
 def ac(i):
  aa=g['accessors'][i];bv=g['bufferViews'][aa['bufferView']];dt={5126:'<f4',5125:'<u4'}[aa['componentType']];k={'VEC3':3,'SCALAR':1}[aa['type']]
  return np.frombuffer(blob,dtype=dt,count=aa['count']*k,offset=bv.get('byteOffset',0)+aa.get('byteOffset',0)).reshape(-1,k)
 def tk(t):
  pp=tuple(tuple(float(x) for x in v) for v in t);return min(pp,pp[1:]+pp[:1],pp[2:]+pp[:2])
 actual=collections.Counter()
 for prim in g['meshes'][0]['primitives']:
  pos=ac(prim['attributes']['POSITION']);ix=ac(prim['indices']).reshape(-1,3);mat=g['materials'][prim['material']]['name']
  actual.update((mat,tk(pos[t])) for t in ix)
 matched=0
 for part in b:
  if part['label'] not in allowed:continue
  xyz=(np.asarray(part['vertices'])[:,[0,2,1]]*np.array([1,1,-1])).astype('<f4')
  for t in part['triangles']:
   key=(part['material'],tk(xyz[t]));assert actual[key]>0;actual[key]-=1;matched+=1
 raw_copyright.append({'file':fn,'sha256':sha(ROOT/'exports'/fn),'copyright_matches_canonical':True,'changed_part_triangles_bound_to_actual_raw':matched})
# Verify the full frozen v1 index, including artifacts that were never copied.
idx=json.loads((OLD/'FILES.json').read_text());checked=0
for item in idx['files']:
 p=OLD/item['file'];assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256'];checked+=1
assert sha(OLD/'HANDOFF.json')==json.loads((ROOT/'source/parent-binding.json').read_text())['parent_handoff_sha256']
report={'schema':'bajin-v2-author-revision-check','independent_QA':False,'changed_part_count':len(changed),'changed_labels':changed,'unchanged_part_count':len(a)-len(changed),'frame_and_main_dimensions_exactly_preserved':True,'byte_identical_invariants':same_paths,'stair_closed_manifold_edge_uses':dict(collections.Counter(edges.values())),'stair_volume_m3':vol,'stair_expected_nested_volume_m3':expect,'actual_risers':stair_faces,'arch_trim_min_z_m':float(archv[:,2].min()),'coping_bounds':cb,'low_wall_closed_join_bounds':low_wall_bounds,'central_coping_clear_gap_m':1.77,'raw_copyright_checks':raw_copyright,'frozen_v1_index_entries_checked_unchanged':checked,'native_metadata_readback_report':'review/native-metadata-check.json'}
(ROOT/'review/author-revision-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
