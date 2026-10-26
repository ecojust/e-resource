"""Strict additional library raw proofs and explicit decoded carryforward.

This is evidence validation, never geometry generation or visual acceptance.
The three proof types are distinct; a structure PASS cannot replace any of them.
"""
import json,math,re
from pathlib import Path
from contracts import need,identity,text
from report_adapters import engine_descriptor

LIBRARY='minhang-baoyugang-library'
NAMES={'bounded_revision_preservation','horizontal_pane_seating','colonnade_cap_clearance'}

def finite_number(value):
    return type(value) in (int,float) and math.isfinite(value)

def bound_engine(row,inputs):
    return inputs.file(engine_descriptor(row))

def matching_input(row,expected,inputs,message):
    need(identity(row)==identity(expected),message);bound_engine(row,inputs)

def check_checker_files(report,expected,inputs):
    files=report.get('checker_files')
    need(isinstance(files,list) and len(files)==len(expected) and
         {Path(x.get('file','')).name for x in files}==set(expected),'Supplement checker set differs')
    return [dict(source=str(bound_engine(x,inputs)),**identity(x)) for x in files]

def validate_raw_supplements(request,target,package,structure,inputs):
    chosen=target.get('actual',{}).get('geometry_supplements')
    if target['id']!=LIBRARY:
        need(chosen in (None,{}),'Unsupported building supplemental proof suite')
        return None
    need(isinstance(chosen,dict) and set(chosen)==NAMES,'All three distinct library supplemental proofs are required')
    current=package['assets']['raw'];structure_desc=target['actual']['source_structure_report']
    baseline={p['key']:p for p in structure['part_results']}
    need(len(baseline)==3253 and structure['model_id']==LIBRARY and structure['structure_passed'] is True,
         'Library supplements require current independent actual structure')
    matching_input(structure['asset_identity']['raw'],current,inputs,'Supplement current raw differs')
    matching_input(structure['frozen_source_manifest'],request['source_freeze'],inputs,'Supplement source freeze differs')
    need(structure['source_geometry_sha256']==request['source_geometry']['sha256'] and
         structure['calibration_sha256']==request['source_roles']['calibration']['sha256'],
         'Supplement geometry/calibration source differs')
    proofs={name:inputs.json(chosen[name]) for name in sorted(NAMES)}
    tools=[];protected=set()
    # Bounded revision proof: only exact authorized keys may change.
    revision=proofs['bounded_revision_preservation']
    need(revision.get('schema')=='library-actual-geometry-revision-preservation-v1' and
         revision.get('preservation_passed') is True and revision.get('new_geometry_accepted') is False,
         'Failed/wrong-domain bounded revision proof')
    matching_input(revision['current_asset_identity']['raw'],current,inputs,'Revision belongs to stale raw')
    matching_input(revision['current_structure_report'],structure_desc,inputs,'Revision structure differs')
    old_structure=inputs.json(engine_descriptor(revision['old_structure_report']))
    need(old_structure.get('schema')=='modern-actual-raw-structure-v1' and old_structure.get('structure_passed') is True
         and old_structure.get('model_id')==LIBRARY,'Revision historical structure missing')
    matching_input(revision['old_asset_identity']['raw'],old_structure['asset_identity']['raw'],inputs,'Revision old raw differs')
    need(revision['old_asset_identity']['raw']['sha256']!=current['sha256'],'Revision cannot compare current raw to itself')
    allow=inputs.json(engine_descriptor(revision['repair_allowlist']))
    need(allow.get('schema')=='library-actual-part-repair-allowlist-v1' and
         allow.get('old_raw_sha256')==revision['old_asset_identity']['raw']['sha256'],'Wrong repair allowlist')
    matching_input(allow['new_source_freeze'],request['source_freeze'],inputs,'Repair source revision differs')
    matching_input(allow['independently_selected_from_actual_structure'],revision['old_structure_report'],inputs,'Repair old structure differs')
    change=inputs.json(engine_descriptor(allow['author_change_scope']))
    source_path=inputs.file(request['source_freeze']);source_doc=inputs.json(request['source_freeze'])
    change_path=bound_engine(allow['author_change_scope'],inputs)
    need(change_path==source_path.parent/'change-scope.json' and any(
         x.get('path',x.get('file'))=='change-scope.json' and identity(x)==identity(allow['author_change_scope'])
         for x in source_doc['files']),'Repair change scope absent from exact source freeze')
    need(identity(change.get('baseline_raw'))==identity(revision['old_asset_identity']['raw']) and
         source_doc.get('baseline_rejected_raw_sha256')==revision['old_asset_identity']['raw']['sha256'],
         'Revision historical raw differs from the unique baseline in frozen author source')
    permitted=allow.get('allowed_changed_part_keys');need(isinstance(permitted,list) and len(permitted)==len(set(permitted))==265,
         'Repair exact265-key allowlist required')
    declared={json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in change.get('allowed_changed_part_keys',[])}
    need(set(permitted)==declared and change.get('allowed_count')==265,'Independent/authored repair scope differs')
    rows=revision.get('part_comparisons');need(isinstance(rows,list) and len(rows)==3253 and
         {x.get('key') for x in rows}==set(baseline),'Revision part coverage differs')
    modified=set();old_by_key={x['key']:x for x in old_structure['part_results']}
    for row in rows:
        key=row['key'];same=row.get('actual_identical_oriented_positions_and_attached_normals')
        need(type(same) is bool and row.get('allowed_to_change') is (key in set(permitted)), 'Invalid revision truth domain')
        need(row.get('new_triangles')==baseline[key]['triangles'] and row.get('old_triangles')==old_by_key[key]['triangles'],
             'Revision actual triangle coverage differs')
        hashes=[row.get(k,'') for k in ('old_attribute_sha256','new_attribute_sha256')]
        need(all(re.fullmatch('[0-9a-f]{64}',h) for h in hashes) and same==(hashes[0]==hashes[1]),'Revision attributes/boolean conflict')
        if not same:modified.add(key)
    need(modified==set(permitted) and revision.get('actual_changed_parts')==265 and revision.get('actual_unchanged_parts')==2988
         and revision.get('actual_part_count')==3253 and revision.get('all_actual_material_json_unchanged') is True
         and revision.get('unexpected_changed_part_keys')==[] and revision.get('expected_but_not_changed_keys')==[],
         'Revision allows undeclared changes or incomplete preservation')
    protected.update(permitted)
    tools+=check_checker_files(revision,{'audit_library_revision_preservation_v2.py','modern_mesh.py'},inputs)
    # All actual pane/frame seats, not a substitute generic structure proof.
    seating=proofs['horizontal_pane_seating']
    need(seating.get('schema')=='modern-actual-horizontal-pane-seating-v1' and seating.get('horizontal_seating_passed') is True
         and seating.get('model_appearance_accepted') is False,'Failed/wrong-domain pane seating proof')
    matching_input(seating['asset_identity']['raw'],current,inputs,'Pane seating belongs to stale raw')
    matching_input(seating['source_structure_report'],structure_desc,inputs,'Pane seating structure differs')
    questions=inputs.json(engine_descriptor(seating['requests_file']))
    need(questions.get('schema')=='modern-finite-requests-v1' and questions.get('state')=='READY_FOR_ACTUAL_AUDIT'
         and questions.get('model_id')==LIBRARY and questions.get('source_binding',{}).get('raw_sha256')==current['sha256']
         and questions['source_binding'].get('source_freeze_sha256')==request['source_freeze']['sha256']
         and questions['source_binding'].get('structure_report_sha256')==structure_desc['sha256']
         and questions['source_binding'].get('geometry_input_sha256')==request['source_geometry']['sha256']
         and questions['source_binding'].get('calibration_sha256')==request['source_roles']['calibration']['sha256'], 'Pane question source differs')
    need(seating.get('minimum_actual_cell_area_m2')==1e-5 and seating.get('maximum_opposite_plane_separation_m')==1e-9,
         'Pane seat threshold changed')
    rows=seating.get('pane_results');pane_keys={k for k,p in baseline.items() if '/glass-pane-' in p['label']}
    need(isinstance(rows,list) and len(rows)==len(pane_keys)==788 and {x.get('pane_key') for x in rows}==pane_keys
         and seating.get('pane_count')==788 and seating.get('window_question_count')==271 and len(questions.get('checks',[]))==271,
         'Pane seating inventory incomplete/duplicate')
    for row in rows:
        pane_key,frame_key=row['pane_key'],row['frame_key'];pane=baseline[pane_key];frame=baseline.get(frame_key)
        need(frame is not None and frame['label']==pane['label'].rsplit('/glass-pane-',1)[0]+'/continuous-frame-grid'
             and row.get('passed') is True,'Pane seat/frame pairing failed')
        witness=row.get('largest_actual_joint_witness') or {};g=witness.get('pane_actual_interval_m');f=witness.get('frame_actual_interval_m')
        need(type(row.get('qualifying_cell_count')) is int and row['qualifying_cell_count']>0 and
             type(witness.get('pane_triangle_index')) is int and 0<=witness['pane_triangle_index']<pane['triangles'] and
             type(witness.get('frame_triangle_index')) is int and 0<=witness['frame_triangle_index']<frame['triangles'],
             'Pane seat facet references invalid')
        need(finite_number(witness.get('joint_area_m2')) and witness['joint_area_m2']>=1e-5
             and all(isinstance(x,list) and len(x)==2 and all(finite_number(y) for y in x) and x[1]>x[0] for x in [g,f])
             and abs(g[0]-f[1])<=1e-9 and finite_number(witness.get('actual_endpoint_separation_m'))
             and abs(witness['actual_endpoint_separation_m'])<=1e-9 and finite_number(witness.get('cell_vertex_plane_separation_m'))
             and abs(witness['cell_vertex_plane_separation_m'])<=1e-9,'Pane actual positive-area seat missing')
        protected.update([pane_key,frame_key])
    tools+=check_checker_files(seating,{'audit_glass_horizontal_seating.py','modern_mesh.py','finite_checks.py'},inputs)
    # Six visible cap fixes: real footprint containment + height + deck joint.
    caps=proofs['colonnade_cap_clearance']
    need(caps.get('schema')=='library-actual-colonnade-cap-clearance-v1' and caps.get('cap_clearance_passed') is True,
         'Failed/wrong-domain column cap proof')
    matching_input(caps['asset_identity']['raw'],current,inputs,'Column cap proof belongs to stale raw')
    matching_input(caps['source_structure_report'],structure_desc,inputs,'Column cap structure differs')
    need(caps.get('minimum_required_vertical_clearance_m')==.02 and caps.get('maximum_uncovered_cap_plan_area_m2')==1e-9,
         'Column cap clearance policy changed')
    expected={k for k,p in baseline.items() if p['label'].startswith('colonnade/F5/round-column-')}
    rows=caps.get('actual_columns');need(len(expected)==6 and isinstance(rows,list) and len(rows)==6 and
         {x.get('key') for x in rows}==expected and caps.get('column_count')==6,'Column cap coverage incomplete')
    deck=next(k for k,p in baseline.items() if p['label']=='terrace/F6/colonnade-roof-deck')
    surface=next(k for k,p in baseline.items() if p['label']=='terrace/F6/colonnade-walking-surface')
    protected.update([deck,surface])
    for row in rows:
        for key in ('actual_column_top_m','actual_walking_surface_top_m','actual_vertical_clearance_m','actual_top_cap_area_m2','actual_cap_outside_surface_plan_area_m2'):
            need(finite_number(row.get(key)),'Nonfinite column cap evidence')
        contact=row.get('actual_column_deck_contact') or {}
        need(row.get('passed') is True and row['actual_vertical_clearance_m']>.02 and
             abs(row['actual_walking_surface_top_m']-row['actual_column_top_m']-row['actual_vertical_clearance_m'])<1e-9 and
             row['actual_top_cap_area_m2']>0 and 0<=row['actual_cap_outside_surface_plan_area_m2']<1e-9 and
             contact.get('left_key')==row['key'] and contact.get('right_key')==deck and
             contact.get('positive_volume_contact_found') is True and contact.get('contact_found') is True and
             contact.get('state')=='LOCAL_POSITIVE_VOLUME_WITNESS' and finite_number(contact.get('witness_overlap_m')) and
             contact['witness_overlap_m']>=1e-6 and finite_number(contact.get('witness_cell_area_m2')) and
             contact['witness_cell_area_m2']>0,'Column cap is exposed/unseated or evidence domain differs')
    tools+=check_checker_files(caps,{'audit_library_colonnade_caps.py','modern_mesh.py','finite_checks.py'},inputs)
    return {'schema':'modern-validated-library-raw-supplements-v11','current_raw':dict(current),
            'source_freeze':request['source_freeze'],'source_structure_report':structure_desc,
            'proofs':chosen,'required_retained_part_keys':sorted(protected),'checker_dependencies':tools,
            'raw_supplemental_geometry_passed':True,'native_accepted':False,'browser_accepted':False}

def material_equal(a,b):
    if type(a) in (int,float) and type(b) in (int,float):
        return finite_number(a) and finite_number(b) and abs(a-b)<1e-6
    if isinstance(a,dict) and isinstance(b,dict):return set(a)==set(b) and all(material_equal(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(material_equal(x,y) for x,y in zip(a,b))
    return type(a) is type(b) and a==b

def validate_decoded_supplement_transfer(validated,decoded,request,target,package,structure,inputs):
    """Called only AFTER the existing strict decoded/finite gates succeed."""
    if validated is None:return None
    need(validated.get('raw_supplemental_geometry_passed') is True,'Raw supplemental proofs not validated')
    need(decoded.get('passed') is True and decoded.get('web_exact_oriented_position_material_triangle_multiset') is True
         and decoded.get('modern_material_properties_preserved') is True,'No actual exact decoded position/material evidence')
    for name,count in [('raw_web',structure['triangles']),('authored_to_compressed_lod',decoded['assets']['lod']['triangles'])]:
        comparison=decoded.get(name) or {}
        need(comparison.get('triangle_copies')==count and comparison.get('normal_angle_tolerance_degrees')==.05 and
             finite_number(comparison.get('maximum_normal_angle_degrees')) and 0<=comparison['maximum_normal_angle_degrees']<=.05,
             'Actual decoded normal/triangle comparison missing or failed')
    suite=inputs.json(decoded['finite_actual_decoded_report']);need(suite.get('passed') is True,'Decoded finite suite did not pass')
    roles={'raw','web','lod'}|({'authored_lod'} if target['actual'].get('authored_lod') else set())
    need(set(suite.get('roles',{}))==roles,'Missing delivery role for supplement transfer')
    baseline={p['key']:p for p in structure['part_results']};required=set(validated['required_retained_part_keys']);transfers={}
    raw_materials=decoded['assets']['raw']['materials'];materials={baseline[k]['material'] for k in required}
    for role in sorted(roles):
        row=suite['roles'][role];actual=inputs.json(row['finite_report']);finite=actual.get('actual_finite_result') or {}
        current=target['actual']['authored_lod'] if role=='authored_lod' else package['assets'][role]
        need(actual.get('passed') is True and finite.get('finite_checks_passed') is True and
             identity(row['current_asset'])==identity(current),'Current decoded finite role differs')
        carry=finite.get('actual_structure_carryforward') or {}
        need(carry.get('all_present_parts_position_identical') is True and carry.get('source_raw_sha256')==package['assets']['raw']['sha256']
             and identity(carry['actual_current_asset'])==identity(current),'Actual decoded position proof differs')
        comparisons={p['key']:p for p in carry.get('actual_part_comparisons',[])}
        need(required<=set(comparisons) and not required.intersection(carry.get('omitted_source_part_keys',[])),
             'Supplement-dependent pane/frame/column/deck omitted in delivery')
        for key in required:
            need(comparisons[key]['triangles']==baseline[key]['triangles'] and comparisons[key]['actual_oriented_position_sha256']==baseline[key]['oriented_position_triangles_sha256'],
                 'Supplement-dependent current geometry changed')
        asset=decoded['authored_lod'] if role=='authored_lod' else decoded['assets'][role]
        need(identity(asset)==identity(current) and all(name in asset['materials'] and
             material_equal(raw_materials[name],asset['materials'][name]) for name in materials),
             'Supplement-dependent actual loaded material changed')
        transfers[role]={'current_asset':current,'actual_decoded_finite_report':row['finite_report'],
                         'actual_decoded_array_manifest':row['array_manifest'],'required_retained_part_count':len(required),
                         'exact_oriented_positions_preserved':True,'actual_loaded_materials_preserved':True,
                         'normal_policy_degrees':.05,'raw_supplement_proofs':validated['proofs']}
        transfers[role]['omitted_source_part_keys']=carry.get('omitted_source_part_keys',[])
        transfers[role]['revision_count_scope']='265/2988 counts describe the historical old-to-current RAW comparison only; authored-subtraction delivery may omit separately approved fine tile seams. Every retained current part is checked by the independent finite carryforward.'
    return {'schema':'modern-library-supplement-delivery-transfer-v11','source_raw':validated['current_raw'],
            'source_freeze':validated['source_freeze'],'source_structure_report':validated['source_structure_report'],
            'raw_proofs':validated['proofs'],'actual_decoded_package_report':request['decoded_report'],
            'actual_decoded_finite_suite':decoded['finite_actual_decoded_report'],'roles':transfers,
            'pane_seating_and_cap_clearance_preserved':True,'bounded_revision_proof_bound_as_raw_history':True,
            'native_accepted':False,'browser_accepted':False,
            'authored_lod_normal_evidence':'When authored LOD is present, the bound frozen decoder compareProtectedGroups invokes compareTriangles at0.05 degrees for every retained group before reporting passed. This first segment has no separate numeric maximum field; no such value is invented here.',
            'scope':'Current raw supplemental geometry properties transfer only through actual exact retained triangle positions/materials and separately bounded normals; every delivery role passed the same finite questions. No visual or browser acceptance is inferred.'}
