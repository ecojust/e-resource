"""Verify the final repair changes only the two previously buried side panels.

Compare actual oriented FLOAT32 serialized surface multisets, not author counts.
"""
from pathlib import Path
import argparse,collections,hashlib,importlib.util,json
import numpy as np
HELPER=Path(__file__).with_name('independent-glb-review-helpers.py')
SPEC=importlib.util.spec_from_file_location('independent_glb_review',HELPER);MOD=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MOD)

def canonical_counter(tris):
    tris=tris.astype('<f4');n=len(tris)
    flattened=np.stack([np.roll(tris,k,axis=1).reshape(n,9) for k in range(3)],axis=1)
    first=np.lexsort(tuple(flattened[:,:,j] for j in range(8,-1,-1)),axis=1)[:,0]
    canonical=flattened[np.arange(n),first]
    return collections.Counter(row.tobytes() for row in canonical)

def change_bounds(counter):
    points=np.array([np.frombuffer(k,dtype='<f4').reshape(3,3) for k,n in counter.items() for _ in range(n)])
    center=np.array([43.0151853324771,-6.141230763948351]);t=np.array([.4819097604926674,.8762208527203059]);normal=np.array([t[1],-t[0]])
    uv=np.stack([(points[:,:,:2]-center)@t,(points[:,:,:2]-center)@normal,points[:,:,2]],axis=-1)
    sides=[]
    for side in [-1,1]:
        part=uv[(uv[:,:,0].mean(axis=1)*side)>0]
        sides.append({'side':side,'triangles':len(part),'tower_local_bounds_m':[part.min((0,1)).tolist(),part.max((0,1)).tolist()] if len(part) else None})
    contained=bool(np.all((abs(uv[:,:,0])>6.37)&(abs(uv[:,:,0])<6.56)&(uv[:,:,1]>.5499)&(uv[:,:,1]<1.0501)&(uv[:,:,2]>24.5249)&(uv[:,:,2]<25.4751)))
    return {'triangle_count':sum(counter.values()),'two_panel_neighborhoods_only':contained,'sides':sides}

def compare(old,new):
    a,b=MOD.SerialScene(old),MOD.SerialScene(new)
    da,db=a.surface_digest(),b.surface_digest();unchanged=[m for m in da if da[m]==db.get(m)];changed=[m for m in set(da)|set(db) if da.get(m)!=db.get(m)]
    rows={}
    for name in changed:
        ca=canonical_counter(a.tri[a.mi==a.materials.index(name)]);cb=canonical_counter(b.tri[b.mi==b.materials.index(name)])
        rows[name]={'removed':change_bounds(ca-cb),'added':change_bounds(cb-ca)}
    checks={'exactly_dark_bronze_surface_changed':changed==['dark bronze'],'all_other_materials_exactly_identical':len(unchanged)==len(da)-1,'material_appearance_unchanged':MOD.material_appearance(old)==MOD.material_appearance(new),'triangle_count_unchanged':len(a.tri)==len(b.tri)}
    if 'dark bronze' in rows:
        d=rows['dark bronze'];checks['only_two_twelve_triangle_panels_changed']=all(r['triangle_count']==24 and r['two_panel_neighborhoods_only'] and all(s['triangles']==12 for s in r['sides']) for r in d.values())
    return {'old_asset':a.asset,'new_asset':b.asset,'checks':checks,'passed':all(checks.values()),'unchanged_materials':unchanged,'old_surface_digests':da,'new_surface_digests':db,'changes':rows}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--old-raw',type=Path,required=True);ap.add_argument('--new-raw',type=Path,required=True);ap.add_argument('--old-lod',type=Path,required=True);ap.add_argument('--new-lod',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    variants={k:compare(old,new) for k,old,new in [('raw',a.old_raw,a.new_raw),('lod',a.old_lod,a.new_lod)]}
    r={'schema':'postal-independent-side-panel-delta-v1','passed':all(v['passed'] for v in variants.values()),'method':'Exact orientation-preserving cyclic triangle canonicalization and FLOAT32 multisets grouped by actual material; removed/added surface bounds in independent tower frame. No author feature or delta helper imported.','variants':variants,'bindings':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [Path(__file__),HELPER]]}
    a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'variants':{k:v['checks'] for k,v in variants.items()}}));raise SystemExit(0 if r['passed'] else 1)
if __name__=='__main__':main()
