#!/usr/bin/env python3
"""Actual five added solids: frozen extent, incremental footprint and slot clearance.

Slot clearance uses a conservative convex hull of all actual triangle vertices
after clipping to the added solid's full vertical interval. It includes cap
interiors even for vertical faces and cannot falsely clear an enclosed solid.
An overlap is unresolved by this conservative test, not automatically collision.
"""
import argparse,json
from pathlib import Path
import sys
import numpy as np
from shapely.geometry import Polygon,MultiPoint,shape
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
sys.path.insert(0,str(HERE.parent))
from modern_mesh import load_raw,filemeta,require,oriented_position_hash


def read(path):return json.loads(Path(path).read_bytes())


def projected_footprint(triangles):
    polygons=[]
    for t in triangles:
        polygon=Polygon(t[:,:2])
        if polygon.area>0:polygons.append(polygon)
    require(polygons,'Closed nonzero-volume added part has no XY footprint')
    result=unary_union(polygons)
    require(result.is_valid and result.area>0,'Invalid actual projected footprint')
    return result


def clip_z(vertices,level,keep_above):
    if not vertices:return []
    result=[]
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):
        da=(a[2]-level)*(1 if keep_above else -1)
        db=(b[2]-level)*(1 if keep_above else -1)
        if da>=0:result.append(a)
        if (da<0)!=(db<0):
            fraction=da/(da-db)
            result.append((np.asarray(a)+fraction*(np.asarray(b)-a)).tolist())
    return result


def slab_projection_hull(triangles,low,high):
    require(high>low,'Positive actual vertical slab required')
    points=[]
    for t in triangles:
        if float(t[:,2].max())<low or float(t[:,2].min())>high:continue
        clipped=clip_z(clip_z(t.tolist(),low,True),high,False)
        points.extend(v[:2]for v in clipped)
    if not points:return None
    # A convex outer enclosure is intentional. Boundary-only projection may
    # be empty for vertical faces and must never stand in for a solid cap.
    return MultiPoint(points).convex_hull


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raw',type=Path,required=True)
    ap.add_argument('--structure',type=Path,required=True)
    ap.add_argument('--preservation',type=Path,required=True)
    ap.add_argument('--plan',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();out=a.output.resolve()
    require(out.is_relative_to(ROOT)and not out.exists(),'New immutable report required')
    plan=read(a.plan);proof=read(a.structure);preservation=read(a.preservation)
    require(plan['schema']=='museum-geometry-v2-approved-independent-change-plan-v1','Invalid plan')
    require(preservation['schema']=='museum-actual-geometry-v2-preservation-v1'and preservation['geometry_preservation_passed']is True,'Actual preservation prerequisite absent')
    require(preservation['approved_change_plan']==filemeta(a.plan),'Plan differs from actual preservation')
    require(preservation['structure_report']==filemeta(a.structure),'Structure proof differs from actual preservation')
    require(proof['structure_passed']is True and proof['frozen_source_manifest']==plan['source_freeze'],'Current closed structure not bound to planned source')
    asset=load_raw(a.raw)
    require(asset.identity['raw']==proof['asset_identity']['raw']==preservation['raw'],'Current actual raw binding differs')
    bykey={p.key:p for p in asset.parts};records={r['key']:r for r in proof['part_results']}
    require(len(bykey)==12378,'Unexpected current actual inventory')
    bylabel={p.label:p for p in asset.parts}
    require(len(bylabel)==len(bykey),'Ambiguous actual labels')
    owner=shape(plan['source_owner_enu_m']);require(owner.is_valid and owner.area>0,'Invalid frozen owner polygon')
    neighbors=[(r['local_id'],shape(r['geometry_enu_m']))for r in plan['retained_neighbors']]
    require(sorted(key for key,polygon in neighbors)==[735,797]and all(g.is_valid for key,g in neighbors),'Wrong retained neighbors')
    slots=[bylabel[f'north-spine/glazed-wrap-slot-{n}']for n in range(1,6)]
    for part in slots:
        require(oriented_position_hash(part.triangles_enu)==records[part.key]['oriented_position_triangles_sha256'],'Actual slot differs from current structure')
    rows=[];slot_rows=[];precision=plan['planned_new_part_coordinate_precision_m']
    for specification in plan['added_parts']:
        part=bykey[specification['key']]
        require(part.label==specification['label']and part.material==specification['material'],'Wrong actual added identity')
        require(oriented_position_hash(part.triangles_enu)==records[part.key]['oriented_position_triangles_sha256'],'Actual added solid differs from structure')
        footprint=projected_footprint(part.triangles_enu);expected=shape(specification['plan'])
        require(expected.is_valid and expected.area>0,'Invalid frozen added plan')
        low=float(part.triangles_enu[:,:,2].min());high=float(part.triangles_enu[:,:,2].max())
        expected_heights=[float(np.float32(specification['bottom_m'])),float(np.float32(specification['top_m']))]
        actual_heights=np.unique(part.triangles_enu[:,:,2]).tolist()
        heights_match=actual_heights==expected_heights
        hausdorff=float(footprint.boundary.hausdorff_distance(expected.boundary))
        difference=float(footprint.symmetric_difference(expected).area)
        area_budget=precision*(footprint.length+expected.length)+precision*precision*4
        matches=bool(heights_match and hausdorff<=precision and difference<=area_budget and records[part.key]['edge_component_count']==1)
        outside=float(footprint.difference(owner).area)
        nearby=[]
        for local_id,polygon in neighbors:
            overlap=float(footprint.intersection(polygon).area)
            nearby.append({'local_id':local_id,'actual_new_part_overlap_m2':overlap,
                'actual_new_part_distance_m':float(footprint.distance(polygon)), 'overlap_absent':overlap==0.})
        rows.append({'key':part.key,'actual_structure_position_sha256':records[part.key]['oriented_position_triangles_sha256'],
            'actual_bounds_enu_m':records[part.key]['bounds_enu_m'],'actual_triangles':len(part.triangles_enu),
            'actual_footprint_area_m2':float(footprint.area),'frozen_plan_area_m2':float(expected.area),
            'actual_height_levels_m':actual_heights,'expected_float32_height_levels_m':expected_heights,
            'boundary_hausdorff_m':hausdorff,'plan_symmetric_difference_m2':difference,
            'float32_plan_area_difference_budget_m2':area_budget,'matches_frozen_local_plan':matches,
            'outside_source_owner_area_m2':outside,'inside_source_owner':outside==0.,'retained_neighbors':nearby})
        for slot in slots:
            hull=slab_projection_hull(slot.triangles_enu,low,high)
            if hull is None:
                clear=True;overlap=0.;distance=None;state='ACTUAL_VERTICAL_INTERVAL_DISJOINT'
            else:
                clear=footprint.disjoint(hull)
                overlap=float(footprint.intersection(hull).area)
                distance=float(footprint.distance(hull))
                state='CONSERVATIVE_ACTUAL_SLAB_HULL_DISJOINT'if clear else'CONSERVATIVE_PROJECTION_OVERLAP_REQUIRES_DIAGNOSIS'
            slot_rows.append({'new_part_key':part.key,'actual_glazed_slot_key':slot.key,
                'complete_actual_new_part_z_interval_m':[low,high],'passed':bool(clear),'state':state,
                'actual_clipped_slot_convex_enclosure_area_m2':float(hull.area)if hull is not None else 0.,
                'actual_new_footprint_enclosure_overlap_m2':overlap,'positive_separation_m':distance,
                'method':'Convex hull of every actual slot triangle clipped to the complete added-part z slab, including closure-interior enclosure; no geometry buffering or gap allowance.'})
    require(len(rows)==5 and len(slot_rows)==25,'Incomplete actual added/slot comparison')
    plans=all(r['matches_frozen_local_plan']for r in rows)
    inside=all(r['inside_source_owner']for r in rows)
    neighbors_clear=all(n['overlap_absent']for r in rows for n in r['retained_neighbors'])
    slots_clear=all(r['passed']for r in slot_rows)
    passed=plans and inside and neighbors_clear and slots_clear
    report={'schema':'museum-actual-geometry-v2-repair-envelope-v1','repair_envelope_passed':bool(passed),
        'raw':asset.identity['raw'],'source_structure_report':filemeta(a.structure),
        'preservation_report':filemeta(a.preservation),'approved_change_plan':filemeta(a.plan),
        'source_geometry':plan['source_geometry'],'all_five_new_parts_match_frozen_plans':bool(plans),
        'all_five_new_parts_inside_source_owner':bool(inside),'new_parts_retained_neighbor_overlap_absent':bool(neighbors_clear),
        'new_parts_do_not_intersect_any_of_five_slot_glass_slab_hulls':bool(slots_clear),
        'actual_added_part_count':5,'actual_added_slot_slab_checks':25,
        'added_part_results':rows,'slot_slab_clearance_results':slot_rows,
        'retained_neighbor_ids':[735,797],'actual_added_coordinate_comparison_precision_m':precision,
        'geometry_buffering_applied':False,'contact_or_gap_tolerance_changed':False,
        'checker_files':[filemeta(__file__),filemeta(HERE.parent/'modern_mesh.py')],
        'repair_support_contacts_proven_by_this_report':False,'appearance_accepted':False,
        'whole_model_collision_checked':False,'dynamic_navigation_checked':False,
        'scope':'Only the five actual added solids: bounded frozen-plan agreement, containment in the source owner and no incremental positive-area overlap with retained735/797, plus conservative full-height no-contact with all five actual glass slots. Together with preservation, this prevents new neighbor overlap from these edits; it does not establish absence of any preexisting model collision, structural adequacy, attachment or appearance.'}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'report':filemeta(out),'passed':bool(passed),'plan_matches':plans,'inside_owner':inside,'retained_neighbors_clear':neighbors_clear,'slot_hulls_clear':slots_clear}))
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':main()
