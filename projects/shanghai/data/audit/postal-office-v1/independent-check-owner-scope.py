"""Independently check local source protection from frozen serialized projections.

The mapping agent decoded the scene/instance transforms; this review verifies
input hashes, raw cached triangle arrays, source identities and mask geometry.
No claim of independently decoding the entire city or authoring the model.
"""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
import shapely
from shapely.geometry import shape,Point


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mapping',type=Path,default=Path('/workspace/shanghai-postal-mapping'));ap.add_argument('--contract',type=Path,default=Path('/workspace/e-resource/projects/shanghai/source/precise/hongkou-general-post-office/footprint-contract.json'));ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    d=a.mapping;contract=json.loads(a.contract.read_text());ctx=json.loads((d/'context-features.json').read_text());polys={r['localId']:shape(r['geometry_local_enu']) for r in ctx}
    mask=shape(contract['provisional_display_clip']['geometry_local_enu']);source=shape(contract['source_geometry_local_enu']);protect=polys[3148].buffer(.12,join_style=2)
    expected=source.buffer(.12,join_style=2).difference(protect)
    if expected.geom_type=='MultiPolygon':expected=max(expected.geoms,key=lambda p:p.area)
    checks={'target_identity_matches_frozen_source':contract['source_record']=='w11629370@10' and contract['owner']=={'macro_id':'14-13720-6693','feature_local_id':1959},'mask_is_valid':mask.is_valid and mask.area>0,'mask_matches_protected_source_buffer':mask.equals_exact(expected,1e-8),'neighbor_protection_is_geometrically_independent_of_owner_classification':mask.intersection(protect).area<1e-9}
    detail={};bindings=[]
    for row in contract['source_bindings']:
        p=Path(row['private_path']);actual=hashlib.sha256(p.read_bytes()).hexdigest()
        checks['source_binding:'+p.name]=actual==row['sha256'] and p.stat().st_size==row['bytes']
    for variant in ['near','far']:
        tp=d/f'baseline-{variant}-triangles.f64';op=d/('baseline-near-classified-owners.u32' if variant=='near' else 'baseline-far-owners.u32')
        tris=np.fromfile(tp,dtype='f8').reshape(-1,3,3);owners=np.fromfile(op,dtype='u4');assert len(tris)==len(owners)
        bindings += [{'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [tp,op]]
        if variant=='near':
            classes=np.array([1780,814,3148,1959]);centers=shapely.points(tris[:,:,:2].mean(axis=1));dist=np.column_stack([shapely.distance(centers,polys[int(k)]) for k in classes]);sort=np.sort(dist,axis=1)
            checks['near_classification_recomputed_from_geometry']=bool(np.array_equal(owners,classes[dist.argmin(axis=1)]))
            detail['near_classification']={'min_nearest_margin_m':float((sort[:,1]-sort[:,0]).min()),'triangle_centroids_with_margin_below_015m':int(((sort[:,1]-sort[:,0])<.15).sum()),'scope':'Near shared group lacks vertex IDs; classification near the common seam has tiny margins. The mask excludes the whole buffered neighbor polygon irrespective of that classification; no unambiguous-owner claim.'}
        projections=shapely.polygons(tris[:,:,:2]);foreign=projections[owners!=1959];mine=projections[owners==1959]
        intersection=shapely.area(shapely.intersection(foreign,mask));max_foreign=float(intersection.max(initial=0))
        checks[variant+'_all_foreign_triangles_no_clip_area']=max_foreign<1e-9
        mine_union=shapely.union_all(mine);residual=mine_union.difference(mask)
        actual=float(residual.area);field='target_native_'+variant+'_residual_m2'
        checks[variant+'_source_residual_matches_explicit_retention']=abs(actual-contract['provisional_display_clip'][field])<1e-7
        checks[variant+'_residual_confined_to_protected_shared_joint']=residual.difference(polys[3148].buffer(.16,join_style=2)).area<1e-5
        detail[variant]={'triangles':len(tris),'target_triangles':int((owners==1959).sum()),'foreign_triangles':int((owners!=1959).sum()),'foreign_max_intersection_m2':max_foreign,'target_residual_m2':actual,'residual_outside_016m_neighbor_joint_m2':float(residual.difference(polys[3148].buffer(.16,join_style=2)).area)}
    checks['17_neighbor_source_polygons_preserved']=len(polys)==18 and all(poly.intersection(mask).area<1e-9 for owner,poly in polys.items() if owner!=1959)
    body=shape(contract['main_u_footprint_local_enu']);canopy=shape(contract['courtyard_canopy_plan_local_enu']);envelope=shape(contract['author_envelope_local_enu'])
    checks['body_and_canopy_plans_valid']=body.is_valid and canopy.is_valid
    checks['body_has_no_near_zero_width_boundary_spur']=body.minimum_clearance>1e-5
    checks['body_canopy_tile_author_envelope']=body.union(canopy).symmetric_difference(envelope).area<1e-7 and body.intersection(canopy).area<1e-7
    detail['authoring_plan']={'body_minimum_clearance_m':body.minimum_clearance,'body_area_m2':body.area,'canopy_area_m2':canopy.area,'union_envelope_difference_m2':body.union(canopy).symmetric_difference(envelope).area}
    bindings.append({'file':a.contract.name,'bytes':a.contract.stat().st_size,'sha256':hashlib.sha256(a.contract.read_bytes()).hexdigest()})
    result={'schema':'postal-independent-owner-scope-v1','model_id':'hongkou-general-post-office','checks':checks,'passed':all(checks.values()),'detail':detail,'bindings':bindings,'review_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Frozen local near/far arrays, retained-neighbor mask geometry, and authoring footprint contract. Final authored GLB/collision and actual production shader behavior are verified separately.'}
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':len(checks),'failed':[k for k,v in checks.items() if not v]},ensure_ascii=False));raise SystemExit(0 if result['passed'] else 1)
if __name__=='__main__':main()
