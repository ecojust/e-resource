#!/usr/bin/env python3
"""Actual GLB array proof: v3 changes only the two roof tile materials."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from check_glass_inset import read
HERE=Path(__file__).resolve().parent
BASE='7e38b487a82f626e9a43ef7bbf0ba8b33903798dec63c06de7f4bb319b962815'
ALLOWED={'gray roof tile','gray roof tile light'}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def check(before,after):
    br,bd,ba,bp,bi=read(before);ar,ad,aa,ap,ai=read(after)
    assert hashlib.sha256(br).hexdigest()==BASE
    assert len(ar)<100000000 and bd['materials']==ad['materials'] and set(bp)==set(ap)
    assert bi==ai
    rows=[]
    for name,p0 in bp.items():
        p1=ap[name];i0=ba(p0['indices']);i1=aa(p1['indices'])
        r={'material':name,'before_triangles':len(i0)//3,'after_triangles':len(i1)//3,'authorized_roof_change':name in ALLOWED}
        if name not in ALLOWED:
            assert np.array_equal(i0,i1),name+' indices changed'
            assert set(p0['attributes'])==set(p1['attributes'])
            for attr in p0['attributes']:assert np.array_equal(ba(p0['attributes'][attr]),aa(p1['attributes'][attr])),name+' '+attr+' changed'
            r['all_serialized_attribute_and_index_values_identical']=True
        rows.append(r)
    oldroot=before.parent.parent
    for rel in ['geometry-input.json','model-calibration-input.json','calibration-independent.json','calibration-independent-controls.json','photo-glass-controls.json','photo_glazing.py']:
        assert sha(oldroot/rel)==sha(HERE/rel),rel+' changed'
    for rel in ['glass-frame-depth-check.json','photo-uv-evidence.json']:
        assert json.loads((before.parent/rel).read_text())==json.loads((after.parent/rel).read_text())
    a=json.loads((oldroot/'calibration.json').read_text());b=json.loads((HERE/'calibration.json').read_text())
    for key in ['estimated_dimensions_m','opening_records','bounds_glb','source_polygon_area_m2','entrance_sign']:
        assert a[key]==b[key],key+' changed'
    roof=json.loads((after.parent/'roof-continuity-v3-check.json').read_text());assert roof['passed']
    assert roof['tiles_plan_uncovered_m2']<1e-7 and roof['domain_pairwise_overlap_m2']<1e-8
    assert roof['conservative_lap_clearance_after_surface_interpolation_m']>0
    qa=json.loads((after.parent/'photo-uv-check.json').read_text());assert qa['passed'] and qa['raw_sha256']==sha(after)
    r={'schema':'bund09-roof-v3-preservation-v1','passed':True,'before_raw_sha256':BASE,'after_raw_sha256':sha(after),'after_bytes':len(ar),'authorized_materials':sorted(ALLOWED),'unchanged_material_batches':len(bp)-len(ALLOWED),'per_material':rows,'original_embedded_images_byte_identical':True,'image_sha256':[hashlib.sha256(x).hexdigest() for x in ai],'all_glass_positions_normals_indices_and_uvs_identical':True,'all_non_roof_attributes_and_indices_identical':True,'stone_radial_joints_and_balcony_posts_identical':True,'balcony_baluster_count_unchanged':9,'broad_inferred_roof_zinc_cap_identical':True,'bounds_and_opening_records_identical':True,'geometry_source_and_calibration_controls_identical':True,'roof_proof':'roof-continuity-v3-check.json','limitation':'Numerical coverage, per-part topology and unchanged-data checks do not certify exact historical roof shape or replace actual native/photo visual review.'}
    (after.parent/'roof-revision-preservation.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='per_material'},ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,default=HERE/'output/bund09-raw.glb');a=p.parse_args();check(a.before,a.after)
