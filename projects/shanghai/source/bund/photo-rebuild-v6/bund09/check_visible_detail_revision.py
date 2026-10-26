#!/usr/bin/env python3
"""Bound the v2 changes using actual uncompressed GLB arrays and frozen inputs."""
from pathlib import Path
from collections import Counter
import argparse, hashlib, json
import numpy as np
from check_glass_inset import read

HERE=Path(__file__).resolve().parent
PRIOR_SHA='de7fdbd4bb3f4b66e0f506aed39b4412a05481c610bea8607d352ebe4971dce6'
CHANGED={'pale stone','stone joints','gray roof tile','gray roof tile light'}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def triangle_records(accessor,primitive):
    ids=accessor(primitive['indices']).reshape(-1,3)
    xyz=accessor(primitive['attributes']['POSITION'])[ids]
    normals=accessor(primitive['attributes']['NORMAL'])[ids]
    records=np.concatenate([xyz,normals],axis=2).astype('<f4').reshape(len(ids),18)
    return xyz,records


def check(before,after):
    br,bd,ba,bp,bi=read(before);ar,ad,aa,ap,ai=read(after)
    assert hashlib.sha256(br).hexdigest()==PRIOR_SHA,'Wrong comparison baseline'
    assert len(ar)<100_000_000 and set(bp)==set(ap)
    assert bd['materials']==ad['materials'],'Material definitions changed'
    assert bi==ai,'Source JPEG bytes changed'
    rows=[]
    for name,p0 in bp.items():
        p1=ap[name];i0=ba(p0['indices']);i1=aa(p1['indices'])
        row={'material':name,'before_triangles':len(i0)//3,'after_triangles':len(i1)//3}
        if name not in CHANGED:
            assert np.array_equal(i0,i1),name+' indices changed'
            assert set(p0['attributes'])==set(p1['attributes'])
            for attr in p0['attributes']:
                assert np.array_equal(ba(p0['attributes'][attr]),aa(p1['attributes'][attr])),name+' '+attr+' changed'
            row['all_serialized_attributes_and_indices_identical']=True
        else:row['authorized_changed_material']=True
        if 'TEXCOORD_0' in p0['attributes']:
            uv0=ba(p0['attributes']['TEXCOORD_0']);uv1=aa(p1['attributes']['TEXCOORD_0'])
            assert np.array_equal(uv0,uv1) and np.array_equal(uv0[i0],uv1[i1])
            row['all_raw_and_indexed_uv_values_identical']=True
        rows.append(row)

    # Pale stone is shared by ornaments, wall, columns and the edited balcony.
    # Require every old triangle outside an explicit balcony box to survive
    # verbatim (positions + flat normals + multiplicity) in the new mesh.
    coords=json.loads((HERE/'geometry-input.json').read_text())['polygon_local_east_north']
    a,c=np.array(coords[17]),np.array(coords[18]);t=(c-a)/np.linalg.norm(c-a);n=np.array([t[1],-t[0]]);center=(a+c)/2
    x0,r0=triangle_records(ba,bp['pale stone']);_,r1=triangle_records(aa,ap['pale stone'])
    en=x0[:,:,[0,2]]*np.array([1.,-1.]);u=(en-center)@t;d=(en-center)@n;z=x0[:,:,1]
    in_box=((np.abs(u)<=2.1)&(d>=-.50)&(d<=1.90)&(z>=4.55)&(z<=5.65)).all(axis=1)
    wanted=Counter(row.tobytes() for row in r0[~in_box]);actual=Counter(row.tobytes() for row in r1)
    missing=wanted-actual
    assert not missing,{'missing_old_pale_stone_triangles_outside_balcony':sum(missing.values())}

    old_source=before.parent.parent
    same_files=['geometry-input.json','footprint.geojson','footprint-dimensions.json',
        'calibration-independent.json','calibration-independent-controls.json','calibration-depth-check.json',
        'model-calibration-input.json','photo-glass-controls.json','photo_glazing.py',
        'references/bund09-20250501-suicasmo-original.jpg']
    frozen=[]
    for rel in same_files:
        h=sha(HERE/rel);assert h==sha(old_source/rel),rel+' changed'
        frozen.append({'path':rel,'sha256':h})
    oldcal=json.loads((old_source/'calibration.json').read_text());newcal=json.loads((HERE/'calibration.json').read_text())
    for key in ['estimated_dimensions_m','opening_records','bounds_glb','source_polygon_area_m2',
                'front_upper_shaft_positions_per_level','column_orders_by_level',
                'front_rear_openings_per_upper_floor','front_pediments','north_roof_structures','entrance_sign']:
        assert oldcal[key]==newcal[key],key+' changed'
    for rel in ['glass-frame-depth-check.json','photo-uv-evidence.json']:
        assert json.loads((before.parent/rel).read_text())==json.loads((after.parent/rel).read_text()),rel+' changed'
    qa=json.loads((after.parent/'photo-uv-check.json').read_text());assert qa['passed'] and qa['raw_sha256']==sha(after)
    detail=json.loads((after.parent/'visible-detail-v2-check.json').read_text())
    assert len(detail['voussoir_partitions'])==4
    assert all(r['partition_area_residual_m2']<1e-8 and r['stone_joint_overlap_m2']<1e-10 for r in detail['voussoir_partitions'])
    report={'schema':'bund09-visible-detail-v2-preservation-v1','passed':True,
        'before':{'file':str(before),'sha256':hashlib.sha256(br).hexdigest(),'bytes':len(br)},
        'after':{'file':str(after),'sha256':sha(after),'bytes':len(ar)},
        'authorized_changed_materials':sorted(CHANGED),'per_material':rows,
        'pale_stone_preservation':{'old_triangles_preserved_verbatim_outside_balcony':int((~in_box).sum()),
            'old_triangles_inside_declared_exception_box':int(in_box.sum()),'missing_outside':0,
            'box_local_front_u_z_d_m':{'u':[-2.1,2.1],'z':[4.55,5.65],'d':[-.50,1.90]},
            'scope':'Every old pale-stone triangle outside this small central-balcony box retains exact FLOAT32 positions, normals and multiplicity. New voussoir stones may add triangles. No claim that all geometry inside the exception box changed.'},
        'exactly_preserved':['All unchanged-material index and attribute arrays, including all glass, frames, brick, lettering, inferred inner roof cap',
            'Every photo UV accessor and indexed corner; original embedded JPEG bytes',
            'All 672 measured glass/frame depth rows; all registered photo-pane evidence',
            'Source polygon, metric inputs, configuration heights, opening records, orders/shaft counts, model bounds'],
        'image_sha256':[hashlib.sha256(x).hexdigest() for x in ai],'frozen_inputs':frozen,
        'voussoir_partition_count':4,'geometry_qa':'photo-uv-check.json; bund09-all-parts-check.json',
        'limitations':'Mortar is re-clipped around the four stone arch zones and the changed roof materials are deliberately rebuilt. Per-part closure is not whole-building Boolean union. Numerical checks do not imply photographic or native/browser acceptance.'}
    (after.parent/'visible-detail-preservation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['per_material','frozen_inputs']},ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,default=HERE/'output/bund09-raw.glb');a=p.parse_args();check(a.before,a.after)
