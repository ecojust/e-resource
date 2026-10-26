#!/usr/bin/env python3
"""Actual old/new triangles, corner normals and exact authorized change set."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
sys.path.insert(0,str(HERE.parent))
from modern_mesh import load_raw,filemeta,require,oriented_position_hash


def read(path):return json.loads(Path(path).read_bytes())


def corner_attribute_hash(positions,normals):
    """Exact cyclic oriented position/normal pairs; no rounding or welding."""
    p=np.asarray(positions,dtype='<f8').copy();n=np.asarray(normals,dtype='<f8').copy()
    require(p.shape==n.shape and p.ndim==3 and p.shape[1:]==(3,3),'Bad corner array')
    p[p==0]=0.;n[n==0]=0.
    first=np.zeros(len(p),dtype=int);rows=np.arange(len(p))
    for i in [1,2]:
        a,b=p[:,i],p[rows,first]
        less=(a[:,0]<b[:,0])|((a[:,0]==b[:,0])&(a[:,1]<b[:,1]))|((a[:,0]==b[:,0])&(a[:,1]==b[:,1])&(a[:,2]<b[:,2]))
        first[less]=i
    ids=(first[:,None]+np.arange(3))%3
    q=np.concatenate([p[rows[:,None],ids],n[rows[:,None],ids]],axis=2).reshape(-1,18)
    q=q[np.lexsort(tuple(q[:,i]for i in range(17,-1,-1)))]
    return hashlib.sha256(q.astype('<f8',copy=False).tobytes()).hexdigest()


def panel_test(old,new,spec):
    ot,nt=old.triangles_enu,new.triangles_enu
    result={'old_key':old.key,'new_key':new.key,'passed':False}
    if len(ot)!=spec['same_triangle_count_required'] or len(nt)!=len(ot):
        return {**result,'state':'TRIANGLE_COUNT_CHANGED'}
    def columns(t):
        result={}
        for x,y,z in np.unique(t.reshape(-1,3),axis=0):result.setdefault((float(x),float(y)),[]).append(float(z))
        return {key:sorted(values)for key,values in result.items()}
    a,b=columns(ot),columns(nt)
    if set(a)!=set(b) or any(len(a[k])!=2 or len(b[k])!=2 for k in a):
        return {**result,'state':'PLAN_VERTEX_COLUMNS_OR_TWO_LAYER_TOPOLOGY_CHANGED'}
    rows=[];valid=True
    for xy in sorted(a):
        delta=a[xy][0]-b[xy][0]
        passed=(a[xy][1]==b[xy][1] and spec['actual_bottom_extension_bounds_m'][0]<=delta<=spec['actual_bottom_extension_bounds_m'][1])
        valid=valid and passed
        rows.append({'xy_m':list(xy),'old_bottom_m':a[xy][0],'new_bottom_m':b[xy][0],
            'old_top_m':a[xy][1],'new_top_m':b[xy][1],'actual_downward_extension_m':delta,'passed':bool(passed)})
    def roles(t,cols):
        r=t.copy()
        for triangle in r:
            for corner in triangle:
                values=cols[(float(corner[0]),float(corner[1]))]
                require(float(corner[2])in values,'Unknown panel corner')
                corner[2]=values.index(float(corner[2]))
        return r
    oroles,nroles=roles(ot,a),roles(nt,b)
    same_topology=oriented_position_hash(oroles)==oriented_position_hash(nroles)
    omask=np.all(oroles[:,:,2]==1,axis=1);nmask=np.all(nroles[:,:,2]==1,axis=1)
    same_top=(int(omask.sum())==int(nmask.sum())==2 and
        corner_attribute_hash(ot[omask],old.normals_enu[omask])==corner_attribute_hash(nt[nmask],new.normals_enu[nmask]))
    passed=valid and same_topology and same_top and old.material==new.material
    return {**result,'passed':bool(passed),'state':'ACTUAL_BOTTOM_ONLY_COMPARISON',
        'triangle_count':len(nt),'xy_column_count':len(a),'columns':rows,
        'same_oriented_upper_lower_vertex_role_topology':bool(same_topology),
        'top_actual_positions_and_corner_normals_identical':bool(same_top),'material_unchanged':old.material==new.material,
        'old_top_triangle_count':int(omask.sum()),'new_top_triangle_count':int(nmask.sum())}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raw',type=Path,required=True)
    ap.add_argument('--structure',type=Path,required=True)
    ap.add_argument('--plan',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();out=a.output.resolve()
    require(out.is_relative_to(ROOT)and not out.exists(),'Expected new immutable output')
    plan=read(a.plan);require(plan['schema']=='museum-geometry-v2-approved-independent-change-plan-v1','Wrong plan')
    oldproof=read(plan['baseline_structure']['file']);newproof=read(a.structure)
    require(filemeta(plan['baseline_structure']['file'])==plan['baseline_structure'],'Previous structure proof changed')
    require(oldproof['structure_passed']is True and newproof['structure_passed']is True,'Both actual structure proofs must pass')
    require(newproof['frozen_source_manifest']==plan['source_freeze'],'New actual source freeze differs from approved scope')
    require(newproof['source_geometry_sha256']==plan['source_geometry']['sha256'],'New source geometry differs')
    require(newproof['calibration_sha256']==plan['calibration']['sha256'],'New calibration differs')
    require(filemeta(a.raw)==newproof['asset_identity']['raw'],'New actual raw differs from structure')
    previous=load_raw(plan['baseline_raw']['file']);current=load_raw(a.raw)
    require(previous.identity['raw']==plan['baseline_raw'],'Historical raw changed')
    require(previous.identity['raw']==oldproof['asset_identity']['raw'],'Historical raw structure differs')
    old={p.key:p for p in previous.parts};new={p.key:p for p in current.parts}
    require(len(old)==len(previous.parts)and len(new)==len(current.parts),'Duplicate actual part keys')
    oldrecords={r['key']:r for r in oldproof['part_results']};newrecords={r['key']:r for r in newproof['part_results']}
    allow=set(plan['allowed_changed_old_part_keys']);added=set(new)-set(old);removed=set(old)-set(new)
    expected_added=set(plan['allowed_added_part_keys'])
    original_materials_unchanged=(previous.materials==current.materials and len(previous.materials)==plan['expected_material_count'])
    comparisons=[];changed=[]
    for key in sorted(old):
        op=old[key];old_position=oriented_position_hash(op.triangles_enu)
        require(old_position==oldrecords[key]['oriented_position_triangles_sha256'],'Actual previous part differs from its proof')
        if key not in new:
            comparisons.append({'key':key,'passed':False,'state':'MISSING_OLD_PART'});continue
        npart=new[key];new_position=oriented_position_hash(npart.triangles_enu)
        require(new_position==newrecords[key]['oriented_position_triangles_sha256'],'Current actual part differs from its proof')
        oh=corner_attribute_hash(op.triangles_enu,op.normals_enu);nh=corner_attribute_hash(npart.triangles_enu,npart.normals_enu)
        same=(old_position==new_position and oh==nh and op.label==npart.label and op.material==npart.material)
        if not same:changed.append(key)
        comparisons.append({'key':key,'allowed_changed':key in allow,'old_triangles':len(op.triangles_enu),
            'new_triangles':len(npart.triangles_enu),'old_oriented_positions_sha256':old_position,
            'new_oriented_positions_sha256':new_position,'old_oriented_corner_attributes_sha256':oh,
            'new_oriented_corner_attributes_sha256':nh,'positions_corner_normals_materials_identical':same,
            'passed':bool(same or key in allow)})
    for key in added:
        require(oriented_position_hash(new[key].triangles_enu)==newrecords[key]['oriented_position_triangles_sha256'],'New added actual part differs from proof')
    unchanged=[r for r in comparisons if r.get('allowed_changed')is False]
    all_unchanged=(len(unchanged)==plan['required_unchanged_old_part_count'] and all(r.get('positions_corner_normals_materials_identical')is True for r in unchanged))
    panel_key=plan['changed_panel']['key']
    panel=panel_test(old[panel_key],new[panel_key],plan['changed_panel']) if panel_key in new else {'passed':False,'state':'MISSING_CHANGED_PANEL'}
    exact_sets=(set(changed)==allow and added==expected_added and not removed and
        len(old)==plan['baseline_part_count'] and len(new)==plan['expected_current_part_count'])
    bounds_unchanged=(oldproof['bounds_enu_m']==newproof['bounds_enu_m']==plan['require_exact_global_bounds'])
    counts=(newproof['parts']==plan['expected_current_part_count'] and newproof['triangles']==plan['expected_current_triangle_count'])
    passed=all_unchanged and exact_sets and panel['passed'] and original_materials_unchanged and bounds_unchanged and counts
    report={'schema':'museum-actual-geometry-v2-preservation-v1','geometry_preservation_passed':bool(passed),
        'raw':current.identity['raw'],'previous_raw':previous.identity['raw'],
        'structure_report':filemeta(a.structure),'previous_structure_report':plan['baseline_structure'],
        'source_freeze':newproof['frozen_source_manifest'],'previous_source_freeze':oldproof['frozen_source_manifest'],
        'approved_change_plan':filemeta(a.plan),
        'all_non_allowlisted_parts_position_normals_materials_identical':bool(all_unchanged),
        'unchanged_part_count':sum(r.get('positions_corner_normals_materials_identical')is True and r.get('allowed_changed')is False for r in comparisons),
        'changed_part_count':len(changed),'added_part_count':len(added),'exact_changed_and_added_key_sets':bool(exact_sets),
        'changed_panel_bounded_bottom_only':panel['passed'],'changed_panel_actual_comparison':panel,
        'original_materials_unchanged':bool(original_materials_unchanged),'original_material_count':len(previous.materials),
        'current_material_count':len(current.materials),'global_bounds_unchanged':bool(bounds_unchanged),
        'previous_bounds_enu_m':oldproof['bounds_enu_m'],'current_bounds_enu_m':newproof['bounds_enu_m'],
        'current_counts_match_approved_plan':bool(counts),'current_part_count':len(new),'current_triangle_count':newproof['triangles'],
        'modified_old_part_keys':sorted(changed),'added_part_keys':sorted(added),'removed_part_keys':sorted(removed),
        'unexpected_part_keys':sorted(added-expected_added),'actual_old_part_comparisons':comparisons,
        'checker_files':[filemeta(__file__),filemeta(HERE.parent/'modern_mesh.py')],
        'historical_facts_relabelled_to_new_raw':False,'repair_contacts_accepted_by_this_report':False,
        'appearance_accepted':False,'complete_collision_checked':False,
        'scope':'Exact cyclic-oriented Float32-derived positions and paired corner normals, with signed zero normalized only. Existing material JSON values remain exact. The one authorized panel changes only its lower vertex heights within the declared Float321.5mm range; its top and topology remain exact. This does not prove attachment of new parts, no slot obstruction, full collision freedom, or appearance.'}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'report':filemeta(out),'passed':bool(passed),'unchanged':report['unchanged_part_count'],
        'modified':len(changed),'added':len(added)}))
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':main()
