"""Prove the bounded right-door-only visible-v3 correction against an explicit prior source.

No mutation of the baseline. Rebuild it in a temporary directory to bind the
comparison to its actual recorded GLB SHA, then compare original solid parts.
"""
import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import numpy as np
from build_model import Residence222, HERE, PALETTE


def digest(data):
    return hashlib.sha256(data).hexdigest()


def part_fingerprint(part):
    h=hashlib.sha256(part['material'].encode())
    for key,kind in [('vertices','<f4'),('triangles','<u4'),('texcoords','<f4')]:
        h.update(np.asarray(part.get(key,[]),dtype=kind).tobytes())
    return h.hexdigest()


def allowed(label):
    return ('/right-closed-glass-door-pane-' in label or '/right-door-leaf-' in label)


def groups(model):
    out=defaultdict(list)
    for part in model.b.parts:
        out[part['label']].append(part_fingerprint(part))
    return dict(out)


def physical_laps(model):
    parts={p['label']:p for p in model.b.parts}
    left=model.local_plan[0]+[-.04,.42];right=model.local_plan[3]+[.04,.42]
    rearleft=model.local_plan[1]+[-.04,-.18];rearright=model.local_plan[2]+[.04,-.18]
    def uv(t,s):return (1-s)*((1-t)*left+t*right)+s*((1-t)*rearleft+t*rearright)
    laps=[]
    for half in [0,1]:
        for col in range(60):
            t=(col+.5)/60;a=uv(t,0 if half==0 else 1);b=uv(t,.5)
            A=model.point(*a,model.h['upper_eave']);B=model.point(*b,model.h['ridge'])
            S=B-A;S/=np.linalg.norm(S)
            N=np.cross(model.T,S)
            if N[2]<0:N=-N
            N/=np.linalg.norm(N)
            previous=None
            for row in range(15):
                part=parts[f'roof-overlapping-clay-cap-{half}-{col}-{row}']
                xyz=np.asarray(part['vertices'],dtype=np.float32).astype(float)
                local=np.asarray([model.local(p) for p in xyz])
                expected_u=a[0]+(local[:,1]-a[1])*(b[0]-a[0])/(b[1]-a[1])
                # Actual center-ridge vertices of each curved cap; inner/outer
                # skins at both ends survive actual FLOAT32 serialization.
                centers=xyz[np.abs(local[:,0]-expected_u)<.004]
                assert len(centers)==4,(half,col,row,len(centers))
                s=centers@S;n=centers@N;mid=(s.min()+s.max())/2
                ends=[]
                for selected in [s<mid,s>=mid]:
                    ids=np.flatnonzero(selected);ii=ids[np.argmax(n[ids])]
                    ends.append((float(s[ii]),float(n[ii])))
                if previous:
                    (s0,n0),(s1,n1)=previous;s2,n2=ends[0]
                    overlap=s1-s2
                    lower=n0+(s2-s0)*(n1-n0)/(s1-s0)
                    lip=n2-lower
                    assert overlap>.025 and .010<lip<.027,(half,col,row,overlap,lip)
                    laps.append({'half':half,'column':col,'uphill_course':row,
                                 'actual_slope_overlap_m':overlap,'actual_outer_lip_clearance_m':lip})
                previous=ends
    return {'course_junctions':len(laps),
            'minimum_actual_overlap_m':min(v['actual_slope_overlap_m'] for v in laps),
            'maximum_actual_overlap_m':max(v['actual_slope_overlap_m'] for v in laps),
            'minimum_actual_outer_lip_clearance_m':min(v['actual_outer_lip_clearance_m'] for v in laps),
            'maximum_actual_outer_lip_clearance_m':max(v['actual_outer_lip_clearance_m'] for v in laps),
            'actual_float32_geometry':True,'not_coplanar_continuous_ribs':True}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--original',type=Path,help='Optional original aaf7 source for direct 349-part preservation proof')
    args=parser.parse_args();baseline=args.baseline.resolve()
    spec=importlib.util.spec_from_file_location('qingpu222_prior_candidate',baseline/'build_model.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    old=mod.Residence222()
    old_sha=digest((baseline/'output/qingpu-beidajie-222.glb').read_bytes())
    with tempfile.TemporaryDirectory(prefix='qingpu222-baseline-proof-') as tmp:
        report=old.build(Path(tmp))
        assert report['sha256']==old_sha,'Current baseline source no longer reproduces recorded raw GLB'
    new=Residence222();new.construct()
    before=groups(old);after=groups(new);unchanged={};changed=[]
    for name in sorted(set(before)|set(after)):
        if before.get(name)!=after.get(name):
            assert allowed(name),'Unapproved change outside visible correction scope: '+name
            changed.append(name)
        else:unchanged[name]=before[name]
    # Strong independent baseline inputs are byte-identical, not reserialized.
    locked=['geometry-input.json','calibration-independent.json','photos/commons-121178626.jpg',
            'metric-source/2016-fayhoo-original.jpg','fonts/Qingpu222SignSubset.otf']
    for rel in locked:assert (baseline/rel).read_bytes()==(HERE/rel).read_bytes()
    assert old.c['heights_m']==new.c['heights_m']
    assert old.c['front_bay_boundaries_normalized']==new.c['front_bay_boundaries_normalized']
    assert old.c['gallery_setback_m']==new.c['gallery_setback_m']
    assert mod.PALETTE==PALETTE,'Any pre-existing material value change is outside right-door scope'
    assert new.b.palette['right door estimated glass']=={k:new.c['glazing']['right_door_material'][k] for k in ['color','roughness','metallic']}
    palette_changed=[];palette_added=['right door estimated glass']
    preserved=['guardian','balcony-key-pattern','central-cursive','carved-frieze',
               'frieze-','open-leaf','left-open-portal','2022-upper-left-aircon','ridge-overlap-cap',
               'pitched-roof-shell','upturned-end-wall','unobserved-source-side']
    proof={prefix:sum(len(items) for label,items in unchanged.items() if prefix in label) for prefix in preserved}
    assert all(proof.values()),proof
    original_proof=None
    if args.original:
        original=args.original.resolve()
        spec0=importlib.util.spec_from_file_location('qingpu222_original_candidate',original/'build_model.py')
        mod0=importlib.util.module_from_spec(spec0);spec0.loader.exec_module(mod0)
        first=mod0.Residence222();first.construct();first_groups=groups(first)
        preserved_original={k:v for k,v in sorted(first_groups.items()) if after.get(k)==v}
        canonical=digest(json.dumps(preserved_original,sort_keys=True,separators=(',',':')).encode())
        earlier=json.loads((baseline/'checks/unchanged-regions-and-roof-proof.json').read_text())
        assert canonical==earlier['unchanged_parts_canonical_sha256']
        assert sum(map(len,preserved_original.values()))==349
        original_proof={'raw_sha256':digest((original/'output/qingpu-beidajie-222.glb').read_bytes()),
                        'actual_original_parts_still_identical':349,
                        'unchanged_parts_canonical_sha256':canonical,
                        'matches_original_to_v2_preservation_set':True}
    output={'status':'PASS','prior_raw_sha256':old_sha,'prior_source_rebuild_byte_exact':True,
            'current_raw_sha256':digest((HERE/'output/qingpu-beidajie-222.glb').read_bytes()),
            'unchanged_parts':sum(map(len,unchanged.values())),
            'unchanged_label_groups':len(unchanged),'changed_label_groups':len(changed),
            'unchanged_parts_canonical_sha256':digest(json.dumps(unchanged,sort_keys=True,separators=(',',':')).encode()),
            'protected_components':proof,'locked_inputs_unchanged':locked,
            'original_aaf7_preservation':original_proof,
            'global_heights_bays_gallery_depth_unchanged':True,
            'unchanged_part_comparison_includes':'FLOAT32 positions, triangle indices, material names, UVs; material values separately audited below',
            'changed_preexisting_palette_values':palette_changed,'added_right_door_material':palette_added,
            'allowed_changes_only':True,'changed_labels':changed,
            'roof_actual_course_laps':physical_laps(new),
            'baseline_files_mutated':False,'main_project_browser_blender_used':False}
    (HERE/'checks').mkdir(exist_ok=True)
    path=HERE/'checks/unchanged-regions-v3-proof.json'
    path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k!='changed_labels'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
