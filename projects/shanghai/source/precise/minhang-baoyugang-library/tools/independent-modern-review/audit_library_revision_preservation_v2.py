#!/usr/bin/env python3
"""Independent actual old/new raw comparison for bounded library repair.

Reads actual triangles and attached normals. A source allowlist identifies
permitted changes; it does not prove their geometry is correct.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from modern_mesh import load_raw,filemeta,require,oriented_position_hash

def attribute_hash(part):
 q=np.concatenate([part.triangles_enu,part.normals_enu],axis=2).astype('<f8');q[q==0]=0
 first=np.zeros(len(q),int);rows=np.arange(len(q))
 for vertex in [1,2]:
  a,b=q[:,vertex,:3],q[rows,first,:3]
  less=(a[:,0]<b[:,0])|((a[:,0]==b[:,0])&(a[:,1]<b[:,1]))|((a[:,0]==b[:,0])&(a[:,1]==b[:,1])&(a[:,2]<b[:,2]))
  first[less]=vertex
 q=q[rows[:,None],(first[:,None]+np.arange(3))%3].reshape(-1,18)
 q=q[np.lexsort(tuple(q[:,i] for i in range(17,-1,-1)))]
 return hashlib.sha256(q.tobytes()).hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--old-raw',type=Path,required=True);ap.add_argument('--new-raw',type=Path,required=True);ap.add_argument('--old-structure',type=Path,required=True);ap.add_argument('--new-structure',type=Path,required=True);ap.add_argument('--allowlist',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 require(not a.output.exists(),'Do not replace historical proof');old,new=load_raw(a.old_raw),load_raw(a.new_raw)
 proofs=[json.loads(p.read_bytes()) for p in [a.old_structure,a.new_structure]]
 for asset,proof in zip([old,new],proofs):
  require(proof['structure_passed'] is True and proof['asset_identity']['raw']['sha256']==asset.identity['raw']['sha256'],'No matching actual structure prerequisite')
  baseline={r['key']:r for r in proof['part_results']}
  require(all(oriented_position_hash(p.triangles_enu)==baseline[p.key]['oriented_position_triangles_sha256'] for p in asset.parts),'Actual structure per-part proof differs')
 allow=json.loads(a.allowlist.read_bytes())
 # This reviewer owns the simple canonical allowlist wrapper; any author
 # manifest is independently converted to exact ACTUAL raw keys beforehand.
 require(allow['schema']=='library-actual-part-repair-allowlist-v1' and allow['old_raw_sha256']==old.identity['raw']['sha256'],'Repair allowlist identity differs')
 expected=set(allow['allowed_changed_part_keys']);require(len(expected)==len(allow['allowed_changed_part_keys'])==265,'Unexpected repair scope')
 before={p.key:p for p in old.parts};after={p.key:p for p in new.parts}
 require(set(before)==set(after),'Actual parts added/deleted/reidentified')
 rows=[];changed=set();failures=[]
 for key,p in before.items():
  q=after[key];ph,qh=attribute_hash(p),attribute_hash(q)
  same=(ph==qh and p.material==q.material and p.label==q.label)
  if not same:changed.add(key)
  if not same and key not in expected:failures.append(key)
  rows.append({'key':key,'allowed_to_change':key in expected,'actual_identical_oriented_positions_and_attached_normals':same,
               'old_triangles':len(p.triangles_enu),'new_triangles':len(q.triangles_enu),'old_attribute_sha256':ph,'new_attribute_sha256':qh})
 materials_same=old.materials==new.materials
 passed=not failures and changed==expected and materials_same and len(rows)==3253
 report={'schema':'library-actual-geometry-revision-preservation-v1','preservation_passed':passed,
   'old_asset_identity':old.identity,'current_asset_identity':new.identity,'old_structure_report':filemeta(a.old_structure),
   'current_structure_report':filemeta(a.new_structure),'repair_allowlist':filemeta(a.allowlist),
   'actual_changed_parts':len(changed),'actual_unchanged_parts':len(rows)-len(changed),'actual_part_count':len(rows),
   'all_actual_material_json_unchanged':materials_same,'unexpected_changed_part_keys':failures,
   'expected_but_not_changed_keys':sorted(expected-changed),'part_comparisons':rows,
   'checker_files':[filemeta(__file__),filemeta(Path(__file__).parent/'modern_mesh.py')],
   'scope':'Exact actual oriented position+attached-normal multisets and actual material JSON preservation outside a bounded265-part repair. Changed-part correctness, new-frame contacts, appearance and delivery remain independent gates.',
   'new_geometry_accepted':False}
 a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'report':filemeta(a.output),'passed':passed,'changed':len(changed),'unchanged':len(rows)-len(changed)}));raise SystemExit(0 if passed else 1)

if __name__=='__main__':main()
