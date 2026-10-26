"""Museum-specific actual proof gates; no geometry generation or new mathematics.

Generic master6114 and decoder retain the original one-suite protocol. These
four proofs cannot be replaced by structure/native/finite summary booleans.
"""
import copy,importlib.util,json,math,re
from pathlib import Path
from contracts import need,identity
from report_adapters import engine_descriptor,validate_finite
from geometry_supplements import material_equal

MODEL='jiading-shanghai-auto-museum'
NAMES={'bounded_revision_preservation','repair_envelope','finite_area_pane_seating','all_opaque_slot_rays'}
AUTHOR_SHA='5acf7f82a27d7ccfb4b7d4ca0c6e13d98cb381c8409cc3fa0a5697c01fe0a45a'
OLD_RAW_SHA='5c2f93f9b66f75771587ed532928d02dbc3d6960fc1c0804d37e498faa9a969d'
OLD_SOURCE_SHA='82e0bb92df2d7ff09bc0554fc5c421546b865a7b8849b6cbbdb131133169db2c'
ADAPTATION_FREEZE_SHA='2e324ecd6a88945549335eb2f48263dda74b9e1ad024d2def42902371c1084a8'

def number(v):return type(v)in(int,float)and math.isfinite(v)
def bind(row,expected,inputs,label):
    need(identity(row)==identity(expected),label)
    return inputs.file(engine_descriptor(row))
def checkers(report,names,inputs):
    rows=report.get('checker_files')
    need(isinstance(rows,list)and len(rows)==len(names)and {Path(r.get('file','')).name for r in rows}==set(names),'Museum checker inventory differs')
    for row in rows:inputs.file(engine_descriptor(row))
    return [engine_descriptor(r)for r in rows]
def hash64(v):return isinstance(v,str)and re.fullmatch('[0-9a-f]{64}',v)is not None
def keyset(values):
    need(isinstance(values,list)and len(values)==len(set(values)),'Duplicate/missing part keys')
    return set(values)

def current_bindings(documents,current,request,target):
    expected={'raw_sha256':current['sha256'],'source_freeze_sha256':request['source_freeze']['sha256'],
              'geometry_input_sha256':request['source_geometry']['sha256'],
              'calibration_sha256':request['source_roles']['calibration']['sha256'],
              'structure_report_sha256':target['actual']['source_structure_report']['sha256']}
    need(documents and all(doc==expected for doc in documents),'Museum supplemental source binding differs from actual current master inputs')
    return expected

def checked_request_generator(rebinding,inputs):
    """Only the exact independently reviewed source-only rebinder may load."""
    root=Path(__file__).resolve().parents[2]/'request-adaptation'
    from contracts import descriptor
    frozen=descriptor(root/'source-freeze.json')
    need(frozen['sha256']==ADAPTATION_FREEZE_SHA,'Unknown Museum question adaptation revision')
    document=inputs.json(frozen)
    for row in document['files']:inputs.file(engine_descriptor(row))
    generator=descriptor(root/'rebind_requests.py')
    bind(rebinding['generator'],generator,inputs,'Unreviewed question generator')
    bind(rebinding['old_request_lock'],descriptor(root/'adaptation-input-lock.json'),inputs,'Question input lock differs')
    spec=importlib.util.spec_from_file_location('_frozen_museum_question_rebinder',generator['source'])
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module,[frozen,generator,descriptor(root/'adaptation-input-lock.json')]

def validate_preservation(p,current,structure,request,target,inputs):
    need(p.get('schema')=='museum-actual-geometry-v2-preservation-v1','Wrong Museum preservation schema')
    for flag in ['geometry_preservation_passed','all_non_allowlisted_parts_position_normals_materials_identical',
                 'exact_changed_and_added_key_sets','changed_panel_bounded_bottom_only','original_materials_unchanged',
                 'global_bounds_unchanged','current_counts_match_approved_plan']:
        need(p.get(flag)is True,'Museum actual preservation failed: '+flag)
    bind(p['raw'],current,inputs,'Preservation current raw differs')
    bind(p['structure_report'],target['actual']['source_structure_report'],inputs,'Preservation structure differs')
    bind(p['source_freeze'],request['source_freeze'],inputs,'Preservation source differs')
    need(p['previous_raw']['sha256']==OLD_RAW_SHA and p['previous_source_freeze']['sha256']==OLD_SOURCE_SHA,'Wrong historical Museum baseline')
    for name in ['previous_raw','previous_structure_report','previous_source_freeze']:inputs.file(engine_descriptor(p[name]))
    old=inputs.json(engine_descriptor(p['previous_structure_report']))
    need(old['schema']=='modern-actual-raw-structure-v1'and old['structure_passed']is True and old['model_id']==MODEL and old['parts']==12373,'Historical actual structure missing')
    bind(old['asset_identity']['raw'],p['previous_raw'],inputs,'Historical structure/raw mismatch')
    source=inputs.json(request['source_freeze']);root=Path(request['source_freeze']['source']).parent
    plan=inputs.json(engine_descriptor(p['approved_change_plan']))
    need(plan['schema']=='museum-geometry-v2-approved-independent-change-plan-v1','Wrong independent change plan')
    change_path=inputs.file(engine_descriptor(plan['source_change_scope']))
    need(change_path==root/'change-scope.json'and any(r.get('file',r.get('path'))=='change-scope.json'and identity(r)==identity(plan['source_change_scope'])for r in source['files']),
         'Independent change scope is not frozen author dependency')
    change=inputs.json(engine_descriptor(plan['source_change_scope']))
    need(source['baseline_rejected_raw_sha256']==OLD_RAW_SHA and change['baseline_raw']['sha256']==OLD_RAW_SHA,'Author historical baseline differs')
    for k,e in [('source_freeze',request['source_freeze']),('baseline_raw',p['previous_raw']),('baseline_structure',p['previous_structure_report']),('baseline_source_freeze',p['previous_source_freeze'])]:
        bind(plan[k],e,inputs,'Independent change plan binding differs: '+k)
    compact=lambda key:json.dumps(key,ensure_ascii=False,separators=(',',':'))
    changed={compact(k)for k in change['planned_allowed_changed_part_keys']};added={compact(k)for k in change['planned_allowed_added_part_keys']}
    need(len(changed)==1 and len(added)==5 and keyset(plan['allowed_changed_old_part_keys'])==keyset(p['modified_old_part_keys'])==changed and
         keyset(plan['allowed_added_part_keys'])==keyset(p['added_part_keys'])==added and p['removed_part_keys']==p['unexpected_part_keys']==[],
         'Actual/independent/authored repair sets differ')
    current_by={r['key']:r for r in structure['part_results']};old_by={r['key']:r for r in old['part_results']}
    need(len(current_by)==12378 and set(current_by)==set(old_by)|added,'Actual part coverage changed')
    rows=p.get('actual_old_part_comparisons');need(isinstance(rows,list)and len(rows)==12373 and {r['key']for r in rows}==set(old_by),'Incomplete historical comparison')
    for row in rows:
        key=row['key'];same=row.get('positions_corner_normals_materials_identical')
        need(type(same)is bool and row.get('allowed_changed')is(key in changed)and row.get('passed')is True,'Repair truth domain differs')
        need(row['old_triangles']==old_by[key]['triangles'] and row['new_triangles']==current_by[key]['triangles'] and
             row['old_oriented_positions_sha256']==old_by[key]['oriented_position_triangles_sha256'] and
             row['new_oriented_positions_sha256']==current_by[key]['oriented_position_triangles_sha256'],'Repair position coverage differs')
        a,b=row['old_oriented_corner_attributes_sha256'],row['new_oriented_corner_attributes_sha256']
        need(hash64(a)and hash64(b)and same==(a==b and row['old_oriented_positions_sha256']==row['new_oriented_positions_sha256'])and same is(key not in changed),'Unauthorized old part change')
    need(p['unchanged_part_count']==12372 and p['changed_part_count']==1 and p['added_part_count']==5 and
         p['current_part_count']==12378 and p['current_triangle_count']==structure['triangles']==528396 and
         p['current_material_count']==p['original_material_count']==23 and
         p['previous_bounds_enu_m']==p['current_bounds_enu_m']==old['bounds_enu_m']==structure['bounds_enu_m'],'Preservation actual counts/bounds differ')
    panel=p['changed_panel_actual_comparison'];columns=panel.get('columns')
    need(panel.get('passed')is True and panel.get('state')=='ACTUAL_BOTTOM_ONLY_COMPARISON'and panel['old_key']==panel['new_key']==next(iter(changed)) and
         panel['triangle_count']==12 and panel['same_oriented_upper_lower_vertex_role_topology']is True and
         panel['top_actual_positions_and_corner_normals_identical']is True and panel['material_unchanged']is True and
         panel['old_top_triangle_count']==panel['new_top_triangle_count']==2 and isinstance(columns,list)and len(columns)==panel['xy_column_count']==4,'Panel bounded repair missing')
    for c in columns:
        need(c.get('passed')is True and all(number(c.get(k))for k in ['old_bottom_m','new_bottom_m','old_top_m','new_top_m','actual_downward_extension_m'])and
             c['old_top_m']==c['new_top_m']and .001498<=c['actual_downward_extension_m']<=.001502 and
             abs(c['old_bottom_m']-c['new_bottom_m']-c['actual_downward_extension_m'])<1e-12,'Panel repair exceeds actual Float32 bound')
    need(p['historical_facts_relabelled_to_new_raw']is False and p['repair_contacts_accepted_by_this_report']is False and
         p['appearance_accepted']is False and p['complete_collision_checked']is False,'Preservation scope expanded')
    return plan,changed,added

def validate_envelope(e,p,chosen,current,structure,request,target,inputs,added):
    need(e.get('schema')=='museum-actual-geometry-v2-repair-envelope-v1','Wrong Museum envelope schema')
    for flag in ['repair_envelope_passed','all_five_new_parts_match_frozen_plans','all_five_new_parts_inside_source_owner',
                 'new_parts_retained_neighbor_overlap_absent','new_parts_do_not_intersect_any_of_five_slot_glass_slab_hulls']:
        need(e.get(flag)is True,'Actual repair envelope failed: '+flag)
    for key,expected in [('raw',current),('source_structure_report',target['actual']['source_structure_report']),
                         ('preservation_report',chosen['bounded_revision_preservation']),('approved_change_plan',p['approved_change_plan']),('source_geometry',request['source_geometry'])]:
        bind(e[key],expected,inputs,'Repair envelope binding differs: '+key)
    need(e['actual_added_part_count']==5 and e['actual_added_slot_slab_checks']==25 and e['retained_neighbor_ids']==[735,797]and
         e['actual_added_coordinate_comparison_precision_m']==1e-5 and e['geometry_buffering_applied']is False and e['contact_or_gap_tolerance_changed']is False,'Envelope scope/precision differs')
    rows=e['added_part_results'];need(len(rows)==5 and {r['key']for r in rows}==added,'Added envelope inventory incomplete')
    parts={r['key']:r for r in structure['part_results']}
    for r in rows:
        part=parts[r['key']]
        need(r['actual_structure_position_sha256']==part['oriented_position_triangles_sha256']and r['actual_triangles']==part['triangles']and
             r['actual_bounds_enu_m']==part['bounds_enu_m']and r['matches_frozen_local_plan']is True and r['inside_source_owner']is True and
             r['outside_source_owner_area_m2']==0 and number(r['actual_footprint_area_m2'])and r['actual_footprint_area_m2']>0 and
             r['actual_height_levels_m']==r['expected_float32_height_levels_m']and
             number(r['boundary_hausdorff_m'])and 0<=r['boundary_hausdorff_m']<=1e-5 and
             number(r['plan_symmetric_difference_m2'])and number(r['float32_plan_area_difference_budget_m2'])and
             0<=r['plan_symmetric_difference_m2']<=r['float32_plan_area_difference_budget_m2'],'Actual new part shape/owner proof incomplete')
        ns=r['retained_neighbors'];need(len(ns)==2 and {n['local_id']for n in ns}=={735,797}and all(n['overlap_absent']is True and n['actual_new_part_overlap_m2']==0 for n in ns),'Incremental neighbor overlap')
    slots={r['key']for r in structure['part_results']if re.fullmatch(r'north-spine/glazed-wrap-slot-[1-5]',r['label'])}
    tests=e['slot_slab_clearance_results'];need(len(slots)==5 and len(tests)==25 and {(r['new_part_key'],r['actual_glazed_slot_key'])for r in tests}=={(a,s)for a in added for s in slots},'Slot clearance inventory incomplete')
    for r in tests:
        need(r['passed']is True and r['state']in ['ACTUAL_VERTICAL_INTERVAL_DISJOINT','CONSERVATIVE_ACTUAL_SLAB_HULL_DISJOINT']and
             r['actual_new_footprint_enclosure_overlap_m2']==0,'New repair overlaps conservative actual slot slab')
        if r['state']=='CONSERVATIVE_ACTUAL_SLAB_HULL_DISJOINT':need(number(r['positive_separation_m'])and r['positive_separation_m']>0,'Missing positive slot separation')
    need(e['repair_support_contacts_proven_by_this_report']is False and e['appearance_accepted']is False and
         e['whole_model_collision_checked']is False and e['dynamic_navigation_checked']is False,'Envelope scope expanded')

def valid_seat(w,boundary):
    if w.get('passed')is not True or w.get('state')!='ACTUAL_FINITE_AREA_SEAT':return False
    keys=['actual_joint_cell_xy_area_m2','actual_interval_overlap_m','actual_facing_endpoint_separation_m','pane_facing_vertical_cosine','support_facing_vertical_cosine']
    if not all(number(w.get(k))for k in keys):return False
    point=w.get('witness_xy_m');vertices=w.get('actual_joint_cell_xy_vertices_m');planes=w.get('actual_four_facet_planes')
    if not isinstance(point,list)or len(point)!=2 or not all(number(x)for x in point):return False
    if not isinstance(vertices,list)or len(vertices)<3 or not all(isinstance(p,list)and len(p)==2 and all(number(x)for x in p)for p in vertices):return False
    if not isinstance(planes,dict)or set(planes)!={'pane_down','pane_up','support_down','support_up'}or not all(isinstance(p,list)and len(p)==3 and all(number(x)for x in p)for p in planes.values()):return False
    if w['actual_joint_cell_xy_area_m2']<1e-5 or min(w['pane_facing_vertical_cosine'],w['support_facing_vertical_cosine'])<.5:return False
    g,f=w.get('pane_actual_interval_m'),w.get('support_actual_interval_m');extensions=w.get('actual_ordered_end_extensions_m')
    if not all(isinstance(x,list)and len(x)==2 and all(number(v)for v in x)for x in [g,f,extensions]):return False
    if g[1]<=g[0]or f[1]<=f[0]or min(extensions)<1e-6:return False
    wanted=[g[0]-f[0],g[1]-f[1]]if boundary=='bottom'else[f[0]-g[0],f[1]-g[1]]
    overlap=min(g[1],f[1])-max(g[0],f[0]);gap=g[0]-f[1]if boundary=='bottom'else f[0]-g[1]
    if max(abs(a-b)for a,b in zip(wanted,extensions))>1e-7 or abs(overlap-w['actual_interval_overlap_m'])>1e-7 or abs(gap-w['actual_facing_endpoint_separation_m'])>1e-7:return False
    if w.get('contact_mode')=='positive_volume':return overlap>=1e-6-1e-8
    if w.get('contact_mode')=='opposite_facet_area':
        values=w.get('opposite_facet_cell_vertex_separations_m')
        return abs(gap)<=1e-9 and isinstance(values,list)and len(values)>=3 and all(number(x)and abs(x)<=1e-9 for x in values)
    return False

def validate_raw_supplements(request,target,package,structure,inputs):
    chosen=target['actual'].get('geometry_supplements')
    need(target['id']==MODEL and request['source_freeze']['sha256']==AUTHOR_SHA and isinstance(chosen,dict)and set(chosen)==NAMES,'All four current Museum supplemental proofs required')
    need(target['lod_policy']['mode']=='compression-only'and target['actual'].get('authored_lod')is None,'Museum requires exact compression-only delivery')
    need(structure['parts']==12378 and structure['structure_passed']is True,'Current complete actual Museum structure required')
    current=package['assets']['raw'];proofs={name:inputs.json(chosen[name])for name in sorted(NAMES)}
    p=proofs['bounded_revision_preservation'];plan,changed,added=validate_preservation(p,current,structure,request,target,inputs)
    e=proofs['repair_envelope'];validate_envelope(e,p,chosen,current,structure,request,target,inputs,added)
    area=proofs['finite_area_pane_seating']
    need(area.get('schema')=='museum-actual-finite-area-pane-seating-v3'and area.get('finite_area_seating_passed')is True,'Actual current Museum area seating missing/failed')
    bind(area['asset_identity']['raw'],current,inputs,'Area seating current raw differs')
    bind(area['source_structure_report'],target['actual']['source_structure_report'],inputs,'Area structure differs')
    bind(area['actual_preservation_prerequisite'],chosen['bounded_revision_preservation'],inputs,'Area preservation differs')
    questions=inputs.json(engine_descriptor(area['requests_file']));rebinding=inputs.json(engine_descriptor(area['actual_rebinding_manifest']))
    bind(rebinding['requests']['02-curtain-local-seating'],area['requests_file'],inputs,'Area rebinding requests differ')
    bind(rebinding['requests']['complete-6114'],target['actual']['probe_set'],inputs,'Master6114 differs from bound rebinding')
    need(rebinding['schema']=='museum-v2-request-rebinding-manifest-v1'and rebinding['questions_prepared']is True and rebinding['actual_checks_executed']is False and
         rebinding['old_question_count']==6102 and rebinding['new_question_count']==6114 and rebinding['pane_boundary_questions']==5114 and rebinding['all_opaque_finite_rays']==20,'Wrong Museum question mapping scope')
    for k,v in [('raw',current),('structure',target['actual']['source_structure_report']),('preservation',chosen['bounded_revision_preservation']),('source_freeze',request['source_freeze'])]:bind(rebinding['context'][k],v,inputs,'Rebinding context differs: '+k)
    generator,generator_dependencies=checked_request_generator(rebinding,inputs)
    originals=[generator.read(generator.OLD/(name+'.requests.json'))for name in generator.GROUPS]
    expected_groups,expected_mapping=generator.transform(originals,structure['part_results'])
    master=inputs.json(target['actual']['probe_set']);mapping=inputs.json(engine_descriptor(rebinding['mapping']))
    current_bindings([master['source_binding'],area['source_binding'],questions['source_binding'],rebinding['source_binding']],current,request,target)
    need(master['checks']==[q for group in expected_groups for q in group]and questions['checks']==expected_groups[1]and
         mapping['old_question_mappings']==expected_mapping and mapping['old_question_count']==6102 and mapping['new_question_count']==6114,
         'Actual master/area suite does not equal complete approved source-role mapping')
    need(area['source_binding']==questions['source_binding']==rebinding['source_binding']and questions['schema']=='modern-finite-requests-v1'and questions['state']=='READY_FOR_ACTUAL_AUDIT'and questions['model_id']==MODEL,'Area question bindings differ')
    policies={'minimum_actual_cell_xy_area_m2':1e-5,'minimum_volume_embed_m':1e-6,'minimum_opposed_facing_vertical_cosine':.5,
              'minimum_actual_end_extension_m':1e-6,'maximum_opposite_plane_separation_m':1e-9,'maximum_endpoint_arithmetic_error_m':1e-7,'maximum_cells_per_pair':20000}
    need(all(area.get(k)==v for k,v in policies.items())and area['fixed_original_request_sha256']=='610a076ddd48afb77be52cdbeb0bb2074fcb74864718d4bedf5374ba95553803','Area mathematics policy changed')
    rows=area['boundary_results'];qs=questions['checks'];need(len(rows)==len(qs)==5114 and len({q['id']for q in qs})==5114 and [r['id']for r in rows]==[q['id']for q in qs],'Area boundary inventory incomplete')
    panes=set();boundaries={}
    for row,q in zip(rows,qs):
        boundary='bottom'if q['id'].endswith('/bottom-frame-or-floor-local-joint')else'top'if q['id'].endswith('/top-transom-local-joint')else None
        need(boundary and row['passed']is True and row['boundary']==boundary and len(q['left_selectors'])==1 and row['pane_key']==q['left_selectors'][0]['key'],'Area pane/boundary identity differs')
        candidates=row['actual_candidates'];supports={s['key']for s in q['right_selectors']}
        need(candidates and all(w['pane_key']==row['pane_key']and w['support_key']in supports and w['boundary']==boundary for w in candidates)and any(valid_seat(w,boundary)for w in candidates),'Actual finite-area support witness missing')
        panes.add(row['pane_key']);boundaries.setdefault(row['pane_key'],set()).add(boundary)
    expected_panes={r['key']for r in structure['part_results']if r['label'].startswith('curtain/')and '/glass-pane-'in r['label']}
    need(panes==expected_panes and len(panes)==area['pane_count']==2557 and area['boundary_question_count']==5114 and area['all_actual_parts_position_hash_verified']is True and area['verified_actual_part_count']==12378 and all(b=={'bottom','top'}for b in boundaries.values()),'Area pane/actual-part completeness differs')
    need(area['model_appearance_accepted']is False and area['complete_collision_checked']is False and area['physical_structural_safety_verified']is False,'Area scope expanded')
    rays=proofs['all_opaque_slot_rays'];ray_requests=rebinding['requests']['all-opaque-slots'];temp=copy.deepcopy(target);temp['actual']['probe_set']=engine_descriptor(ray_requests)
    validate_finite(rays,current,request,temp,structure,inputs)
    bind(rays['requests_file'],ray_requests,inputs,'Twenty-ray exact questions differ')
    qr=inputs.json(engine_descriptor(ray_requests));need(len(qr['checks'])==len(rays['check_results'])==5,'Five actual slot groups required')
    expected_rays,expected_broad=generator.all_opaque(inputs.file(package['registration_assets']['raw']),structure['part_results'],expected_groups[0])
    need(qr['checks']==expected_rays and all(qr.get(k)==v for k,v in expected_broad.items()),'Actual20-ray selection omits current potentially intersecting opaque parts')
    for i,(q,row)in enumerate(zip(qr['checks'],rays['check_results']),1):
        need(q['id']==row['id']==f'north-slot-{i}/all-opaque-finite-false-backing-probes'and q['points_uv_m']==[[0.,24.],[0.,26.],[0.,28.],[0.,30.]]and q['expect']=='clear'and len(row['rays'])==4,'Twenty actual finite rays changed')
        need(all(r['passed']is True and r['actual_hits']==[]and r['ambiguous_parts']==[]and r['uv_m']==uv for r,uv in zip(row['rays'],q['points_uv_m'])),'Actual opaque obstruction/ambiguity remains')
    tools=generator_dependencies
    tools+=checkers(p,{'audit_preservation.py','modern_mesh.py'},inputs)
    tools+=checkers(e,{'audit_repair_envelope.py','modern_mesh.py'},inputs)
    tools+=checkers(area,{'run_area_seating_v3.py','rebind_requests.py','audit_pane_area_seating_v2.py','modern_mesh.py','finite_checks.py'},inputs)
    tools+=checkers(rays,{'run_finite_checks.py','modern_mesh.py','finite_checks.py'},inputs)
    tools+=[engine_descriptor(rebinding[k])for k in ['generator','old_request_lock']]
    for t in tools:inputs.file(t)
    return {'schema':'modern-validated-museum-raw-supplements-v11','current_raw':current,'source_freeze':request['source_freeze'],
            'source_structure_report':target['actual']['source_structure_report'],'proofs':chosen,'checker_dependencies':tools,
            'required_retained_part_keys':sorted(r['key']for r in structure['part_results']),
            'raw_supplemental_geometry_passed':True,'native_accepted':False,'browser_accepted':False}

def validate_decoded_supplement_transfer(validated,decoded,request,target,package,structure,inputs):
    need(validated['raw_supplemental_geometry_passed']is True and decoded['passed']is True and
         decoded['web_exact_oriented_position_material_triangle_multiset']is True and decoded['modern_material_properties_preserved']is True,'Actual Museum decoded preservation absent')
    need(target['lod_policy']['mode']=='compression-only'and decoded['authored_lod']is None,'Unexpected Museum LOD mode')
    for key in ['raw_web','authored_to_compressed_lod']:
        c=decoded[key];need(c['triangle_copies']==structure['triangles']==528396 and c['normal_angle_tolerance_degrees']==.05 and
              number(c['maximum_normal_angle_degrees'])and 0<=c['maximum_normal_angle_degrees']<=.05,'Museum actual normals/triangle count changed')
    suite=inputs.json(decoded['finite_actual_decoded_report']);need(suite['passed']is True and set(suite['roles'])=={'raw','web','lod'},'Every actual Museum delivery role required')
    baseline={r['key']:r for r in structure['part_results']};transfers={};raw_materials=decoded['assets']['raw']['materials']
    for role,row in suite['roles'].items():
        current=package['assets'][role];actual=inputs.json(row['finite_report']);finite=actual['actual_finite_result'];carry=finite['actual_structure_carryforward']
        need(row['passed']is True and actual['passed']is True and finite['finite_checks_passed']is True and identity(row['current_asset'])==identity(current)and
             carry['all_present_parts_position_identical']is True,'Current role finite proof failed')
        need(carry['source_raw_sha256']==package['assets']['raw']['sha256']and identity(carry['actual_current_asset'])==identity(current)and carry['omitted_source_part_keys']==[],'Museum compression lost source parts')
        comparisons=carry['actual_part_comparisons'];need(len(comparisons)==12378 and {r['key']for r in comparisons}==set(baseline),'Current Museum part coverage incomplete')
        for r in comparisons:
            need(r['triangles']==baseline[r['key']]['triangles']and r['actual_oriented_position_sha256']==baseline[r['key']]['oriented_position_triangles_sha256'],'Current Museum protected geometry differs')
        asset=decoded['assets'][role];need(identity(asset)==identity(current)and material_equal(raw_materials,asset['materials']),'Current Museum actual materials changed')
        transfers[role]={'current_asset':current,'actual_decoded_finite_report':row['finite_report'],'actual_decoded_array_manifest':row['array_manifest'],
                         'required_retained_part_count':12378,'exact_oriented_positions_preserved':True,'actual_loaded_materials_preserved':True,
                         'normal_policy_degrees':.05,'omitted_source_part_keys':[],'raw_supplement_proofs':validated['proofs']}
    return {'schema':'modern-museum-supplement-delivery-transfer-v11','source_raw':validated['current_raw'],'source_freeze':validated['source_freeze'],
            'source_structure_report':validated['source_structure_report'],'raw_proofs':validated['proofs'],
            'actual_decoded_package_report':request['decoded_report'],'actual_decoded_finite_suite':decoded['finite_actual_decoded_report'],
            'roles':transfers,'bounded_revision_proof_bound_as_raw_history':True,'finite_area_pane_seating_preserved':True,
            'repair_envelope_and_slot_clearance_preserved':True,'all_current_parts_preserved':True,'native_accepted':False,'browser_accepted':False,
            'scope':'All four Museum raw supplemental properties transfer through actual exact current part positions/materials and bounded normals in each of raw/web/lod. Counts12372+1+5 describe old/current RAW history; no whole-model collision, visual or browser acceptance is inferred.'}
