#!/usr/bin/env python3
"""Small method controls only; no actual Museum mesh is loaded."""
import argparse,json
from pathlib import Path
import numpy as np
from audit_preservation import panel_test,corner_attribute_hash
from modern_mesh import Part,filemeta


def box(key,zbottom,ztop,dx=0.):
    v=np.array([[0,0,zbottom],[1,0,zbottom],[1,1,zbottom],[0,1,zbottom],
                [0,0,ztop],[1,0,ztop],[1,1,ztop],[0,1,ztop]],dtype=np.float32).astype(float)
    v[:,0]+=dx
    faces=np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],
                    [1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]])
    t=v[faces];cross=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);norm=cross/np.linalg.norm(cross,axis=1)[:,None]
    return Part(key,key,'synthetic',t,np.repeat(norm[:,None,:],3,axis=1),0,0)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists()
    old=box('panel',23.,23.055);good=box('panel',23.-.0015,23.055)
    spec={'same_triangle_count_required':12,'actual_bottom_extension_bounds_m':[.001498,.001502]}
    rows=[]
    for name,new,expected in [('exact_allowed_bottom_only',good,True),
        ('top_move_rejected',box('panel',23.-.0015,23.056),False),
        ('plan_move_rejected',box('panel',23.-.0015,23.055,.00001),False),
        ('excess_bottom_move_rejected',box('panel',23.-.002,23.055),False),
        ('missing_bottom_move_rejected',box('panel',23.,23.055),False)]:
        result=panel_test(old,new,spec);rows.append({'case':name,'expected':expected,'actual':result['passed'],'passed':result['passed']is expected})
    changed=box('panel',23.-.0015,23.055);changed.normals_enu[2,0,0]=1e-5
    result=panel_test(old,changed,spec);rows.append({'case':'top_corner_normal_change_rejected','expected':False,'actual':result['passed'],'passed':not result['passed']})
    original_hash=corner_attribute_hash(old.triangles_enu,old.normals_enu)
    rotated_hash=corner_attribute_hash(np.roll(old.triangles_enu,1,axis=1)[::-1],np.roll(old.normals_enu,1,axis=1)[::-1])
    rows.append({'case':'cyclic_rotation_and_triangle_order_preserve_hash','passed':original_hash==rotated_hash})
    flipped_hash=corner_attribute_hash(old.triangles_enu[:,::-1],old.normals_enu[:,::-1])
    rows.append({'case':'reversed_orientation_changes_hash','passed':original_hash!=flipped_hash})
    passed=all(r['passed']for r in rows)
    report={'schema':'museum-geometry-v2-preservation-synthetic-tests-v1','synthetic_tests_passed':passed,
        'test_count':len(rows),'tests':rows,'actual_museum_geometry_loaded':False,
        'checker_files':[filemeta(__file__),filemeta(Path(__file__).parent/'audit_preservation.py')]}
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':filemeta(a.output),'passed':passed}))
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':main()
