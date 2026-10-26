#!/usr/bin/env python3
"""Freeze exact Museum v2 authorized scope, without reading new raw triangles."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOURCE_SHA = '5acf7f82a27d7ccfb4b7d4ca0c6e13d98cb381c8409cc3fa0a5697c01fe0a45a'
REPAIR_SHA = '25af6662e85898d7d464231a0a11f8647900087e589ffd73ade89851ce62d550'


def desc(path):
    path = Path(path).resolve(); data = path.read_bytes()
    return {'file': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def read(path): return json.loads(Path(path).read_bytes())


def key(label, material): return json.dumps([label,material,0], ensure_ascii=False, separators=(',',':'))


def project_geometry(geometry, anchor):
    rad=math.pi/180.; radius=6378137.; cosine=math.cos(anchor[1]*rad)
    x0=radius*anchor[0]*rad; y0=radius*math.log(math.tan(math.pi/4+anchor[1]*rad/2))
    def convert(value):
        if isinstance(value[0], (int,float)):
            return [(radius*value[0]*rad-x0)*cosine,
                    (radius*math.log(math.tan(math.pi/4+value[1]*rad/2))-y0)*cosine]
        return [convert(item) for item in value]
    assert geometry['type'] in ['Polygon','MultiPolygon']
    return {'type':geometry['type'],'coordinates':convert(geometry['coordinates'])}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--baseline-structure',type=Path,required=True)
    ap.add_argument('--baseline-sidecar',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); out=a.output.resolve()
    assert out.is_relative_to(ROOT) and not out.exists()
    assert desc(a.source/'source-freeze.json')['sha256']==SOURCE_SHA
    assert desc(a.source/'repair-inputs.json')['sha256']==REPAIR_SHA
    freeze=read(a.source/'source-freeze.json'); assert len(freeze['files'])==59
    for row in freeze['files']:
        path=(a.source/row.get('file',row.get('path'))).resolve()
        assert path.is_relative_to(a.source.resolve())
        actual=desc(path); assert actual['bytes']==row['bytes'] and actual['sha256']==row['sha256']
    repair=read(a.source/'repair-inputs.json'); scope=read(a.source/'change-scope.json')
    old=read(a.baseline_structure); side=read(a.baseline_sidecar)
    assert old['structure_passed'] is True and old['parts']==12373
    assert old['asset_identity']['raw']['sha256']==repair['baseline_raw']['sha256']==side['sha256']
    assert desc(a.baseline_sidecar)['sha256']==repair['baseline_sidecar']['sha256']
    geometry=read(a.source/'geometry-input.json')
    assert desc(a.source/'geometry-input.json')['sha256']==old['source_geometry_sha256']
    assert geometry['replacement']['retained_same_near_feature_local_ids']==[735,797]
    expected=[
        ('repair/entry-small-pane-bottom-seat','Museum brushed rail metal'),
        ('repair/fifth-floor-west-pane-seat','Museum interior floor'),
        ('repair/fifth-floor-east-pane-seat','Museum interior floor'),
        ('repair/north-roof-concealed-tie-west','Museum recessed panel joint'),
        ('repair/north-roof-concealed-tie-east','Museum recessed panel joint')]
    assert [(r['label'],r['material'])for r in repair['added_parts']]==expected
    changed=key('roof/lower-silver-top/panel--1--12-0','Museum silver honeycomb aluminium')
    assert scope['planned_allowed_changed_part_keys']==[json.loads(changed)]
    assert scope['planned_allowed_added_part_keys']==[[label,material,0]for label,material in expected]
    assert repair['changed_part']['bottom_extension_m']==.0015
    bylabel={r['label']:r for r in old['part_results']}
    old_ranges={r['label']:r for r in side['actual_serialized_part_ranges']}
    critical=['curtain/layer-1/bay-161/glass-pane-1','curtain/layer-5/bay-002/glass-pane-0',
              'curtain/layer-5/bay-028/glass-pane-0','roof/lower-curved-continuous-underlayer',
              'roof/lower-silver-top/panel--1--12-0']
    assert all(label in bylabel and label in old_ranges for label in critical)
    anchor=geometry['anchor']; assert anchor==[121.16569392318252,31.28056444400137]
    neighbors=[]
    for row in geometry['current_city_detail']['same_near_neighbors_to_retain']:
        assert row['local_id'] in [735,797]
        neighbors.append({'local_id':row['local_id'],'geometry_wgs84':row['geometry'],
            'geometry_enu_m':project_geometry(row['geometry'],anchor)})
    assert sorted(r['local_id']for r in neighbors)==[735,797]
    added=[]
    for row in repair['added_parts']:
        points=row['plan']['coordinates'][0]
        added.append({**row,'key':key(row['label'],row['material']),
            'planned_bounds_enu_m':[[min(p[0]for p in points),min(p[1]for p in points),row['bottom_m']],
                                  [max(p[0]for p in points),max(p[1]for p in points),row['top_m']]]})
    plan={'schema':'museum-geometry-v2-approved-independent-change-plan-v1',
        'state':'PREPARED_REQUIRES_ACTUAL_NEW_STRUCTURE_AND_PRESERVATION',
        'building_id':'jiading-shanghai-auto-museum',
        'source_freeze':desc(a.source/'source-freeze.json'),'repair_inputs':desc(a.source/'repair-inputs.json'),
        'source_change_scope':desc(a.source/'change-scope.json'),
        'source_geometry':desc(a.source/'geometry-input.json'),'calibration':desc(a.source/'calibration.json'),
        'baseline_raw':old['asset_identity']['raw'],'baseline_sidecar':desc(a.baseline_sidecar),
        'baseline_structure':desc(a.baseline_structure),'baseline_source_freeze':old['frozen_source_manifest'],
        'baseline_part_count':12373,'required_unchanged_old_part_count':12372,
        'expected_changed_old_part_count':1,'expected_added_part_count':5,'expected_current_part_count':12378,
        'expected_material_count':23,'expected_current_triangle_count':528396,
        'allowed_changed_old_part_keys':[changed],'allowed_added_part_keys':[r['key']for r in added],
        'removed_old_part_keys_allowed':[],
        'changed_panel':{'key':changed,'old_record':bylabel['roof/lower-silver-top/panel--1--12-0'],
            'old_serialized_range':old_ranges['roof/lower-silver-top/panel--1--12-0'],
            'same_triangle_count_required':12,'same_xy_and_top_required':True,'same_oriented_vertex_role_topology_required':True,
            'same_top_corner_normals_required':True,'planned_bottom_extension_m':.0015,
            'actual_bottom_extension_bounds_m':[.001498,.001502],
            'bound_scope':'Only Float32 representation of the authorized1.5mm underside edit; not a contact/air-gap allowance.'},
        'added_parts':added,'planned_new_part_coordinate_precision_m':1e-5,
        'new_part_coordinate_precision_scope':'Conservative Float32 plan quantization budget; never a contact or collision tolerance.',
        'require_exact_global_bounds':old['bounds_enu_m'],
        'old_failed_target_records':[{'part':bylabel[label],'serialized_range':old_ranges[label]}for label in critical],
        'anchor_wgs84':anchor,'source_owner_enu_m':geometry['model_geometry_local_east_north_m'],
        'retained_neighbors':neighbors,
        'coordinate_contract':'R6378137; Mercator coordinate differences times cos(anchor latitude); glTF[E,U,-N].',
        'historical_first_pass':desc(ROOT/'actual-first-pass-review-v1.json'),
        'historical_actual_failures_unchanged':True,'historical_reports_relabelled_to_new_raw':False,
        'current_raw_examined_by_this_preparation':False,'geometry_preservation_passed':None,
        'repair_contact_passed':None,'appearance_accepted':False,'generator':desc(__file__)}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({'plan':desc(out),'files_individually_verified':59,'actual_new_geometry_examined':False}))


if __name__=='__main__':main()
