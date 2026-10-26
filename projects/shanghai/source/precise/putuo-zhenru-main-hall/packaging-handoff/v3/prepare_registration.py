#!/usr/bin/env python3
"""Compose an immutable Zhenru model-delivery draft from actual bound evidence.

No installation, rendering, accepted catalog mutation, browser proof or upload.
Historical full-raw reports keep their original hashes. Only explicit serialized roof/tile identity carries their tile scope to the current raw. All arguments are concrete files; failed checks leave no acceptance outputs.
"""
from pathlib import Path
import argparse,hashlib,json
KEYS=('source_photos','identity_footprint','height_evidence','visible_facade_opening_grid','roof','texture_mapping_qa','geometry_proof','size_proof','uncertainty')
ID='putuo-zhenru-main-hall'
AUTHOR_FREEZE='02929a28105be0fa9765a9d0e3105279c6e41f67d6aa7667c570cd405ea25056'
BASELINE_AUTHOR_FREEZE='78e935b7c3158bc5c4eb89d721ca24954fefc309480ae4186425940887578ed8'
BASELINE_RAW='b9d4c8981740c19a22ced43d825e643b04fb42960cb113b13ae605e02e3106f9'
HISTORICAL_HASHES={
 'historical_structure_proof':'874014a62b9652a7f500b1ac1d0e54d77c894c94e0e1522cf592e78044d53c65',
 'historical_contact_proof':'3d92f68f5ef05584df73ab122fb26e72220075c4d0376722b08097b87a4707d8',
 'historical_pca_contact_proof':'82f42f7c2d4019643f3db03ff285a703ed6a5c8b54e4d0654f0261abf2bcc481',
 'historical_lip_contact_proof':'ca8a5910b7e9e614742b4caa5ac43ecbb34dfe3287d4a7623d6f8dda98c34a0b',
 'historical_contact_review':'17114bf8cc4cf416e630cfe4e1c3f95093d9bea3b0f2391990d79a0b3852f1b5',
 'historical_native_report':'1de7244e5edd3a4e98d61ced8fb8b70048739d9169a3298d197ea1dba1191d12',
}
EXPECTED_RIDGES={f'ridge/descending-gable-{sx}-{sy}' for sx in [-1,1] for sy in [-1,1]}
NAVIGATION_FREEZE='79024eb60138b349164b3545226cf8225dafe6461085a9bde3f6ee96176cf84e'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(Path(p).read_text())
def descriptor(p):
 p=Path(p).resolve();assert p.is_file() and not p.is_symlink();return {'source':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def check_bound(p,record):
 assert p.is_file() and not p.is_symlink() and p.stat().st_size==record['bytes'] and sha(p)==record['sha256']
def write_new(p,data):
 with Path(p).open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 for key in ('run','model-source','native-report','native-review','structure-proof','preservation-proof','ridge-proof','historical-structure-proof','historical-contact-proof','historical-pca-contact-proof','historical-lip-contact-proof','historical-contact-review','historical-native-report','navigation'):parser.add_argument('--'+key,type=Path,required=True)
 a=parser.parse_args();run=a.run.resolve();model=a.model_source.resolve()
 source_lock=model/'source-freeze.json';source_manifest=load(source_lock)
 assert source_manifest['id']==ID and sha(source_lock)==AUTHOR_FREEZE and AUTHOR_FREEZE!=BASELINE_AUTHOR_FREEZE
 assert source_manifest['files']
 for item in source_manifest['files']:check_bound(model/item.get('path',item.get('file')),item)
 for argument,expected in HISTORICAL_HASHES.items():assert sha(getattr(a,argument))==expected, 'Historical proof changed: '+argument
 package_path=run/'package/packaging-record.json';package=load(package_path)
 assert package['schema']=='precise-building-packaging-v1' and package['building_id']==ID
 assert package['packaging_passed'] is True and package['registered'] is False
 raw_sha=package['assets']['raw']['sha256'];native_sha=package['assets']['native']['sha256']
 assert raw_sha!=BASELINE_RAW,'Geometry-v2 must not silently reuse rejected geometry-v1 raw.'
 assert package['provenance']['model_revision'].startswith('geometry-v2'), 'Package provenance must identify the actual new geometry revision.'
 decoded_path=run/'decoded-package-check.json';decoded=load(decoded_path)
 assert decoded['schema']=='zhenru-actual-decoded-package-check-v10' and decoded['passed'] is True
 assert decoded['package_record_sha256']==sha(package_path)
 for role,item in package['registration_assets'].items():
  check_bound(Path(item['source']),item);assert item['bytes']<100_000_000
  if role!='native':
   r=decoded['assets'][role];assert r['sha256']==item['sha256'] and r['embedded_images']==0
   leaves=[x for x in r['aperture_samples'] if x['type']=='door-leaf-lattice'];windows=[x for x in r['aperture_samples'] if x['type']=='through-flame-window']
   assert len(leaves)==12 and all(x['rays']==9 and x['hits']==0 and x['solid_stile_negative_hits']>0 for x in leaves)
   assert len(windows)==2 and all(x['rays']==9 and x['hits']==0 and x['lattice_void_hits']==0 and x['bar_negative_hits']>0 and x['solid_wall_negative_hits']>0 for x in windows)
   assert len(r['central_wall_aperture_samples'])==2 and all(x['rays']==9 and x['hits']==0 and x['solid_wall_negative_hits']>0 for x in r['central_wall_aperture_samples'])
 structure=load(a.structure_proof);previous_structure=load(a.historical_structure_proof)
 assert structure['schema']=='zhenru-independent-actual-raw-structure-v1' and structure['structure_passed'] is True and structure['raw']['sha256']==raw_sha
 assert structure['frozen_source_manifest']['sha256']==sha(source_lock)
 assert previous_structure['structure_passed'] is True and previous_structure['raw']['sha256']==BASELINE_RAW
 assert previous_structure['frozen_source_manifest']['sha256']==BASELINE_AUTHOR_FREEZE
 contacts=load(a.historical_contact_proof);pca=load(a.historical_pca_contact_proof);lip=load(a.historical_lip_contact_proof)
 assert contacts['schema']=='zhenru-independent-actual-roles-contacts-v1' and contacts['raw']['sha256']==BASELINE_RAW
 assert contacts['structure_report']['sha256']==sha(a.historical_structure_proof) and contacts['finite_checks_passed'] is False
 assert pca['schema']=='zhenru-actual-cover-pan-piecewise-intersection-v1' and pca['raw']['sha256']==BASELINE_RAW
 assert pca['strict_edge_band_contact_passed'] is False and pca['pair_count']==8500 and pca['failed_pair_count']==96
 assert pca['first_failing_roles_report']['sha256']==sha(a.historical_contact_proof) and pca['structure_report']['sha256']==sha(a.historical_structure_proof)
 assert lip['schema']=='zhenru-actual-cover-pan-piecewise-intersection-v2' and lip['raw']['sha256']==BASELINE_RAW
 assert lip['strict_edge_band_contact_passed'] is True and lip['pair_count']==8500 and lip['failed_pair_count']==0
 assert lip['first_failing_roles_report']['sha256']==sha(a.historical_contact_proof)
 assert lip['previous_pca_section_report']['sha256']==sha(a.historical_pca_contact_proof) and lip['structure_report']['sha256']==sha(a.historical_structure_proof)
 historical_review=load(a.historical_contact_review)
 assert historical_review['passed'] is True and historical_review['actually_reviewed'] is True and historical_review['raw']['sha256']==BASELINE_RAW
 assert historical_review['actual_contacts']['sha256']==sha(a.historical_contact_proof)
 assert historical_review['cover_lip_intersection']['sha256']==sha(a.historical_lip_contact_proof)
 assert historical_review['previous_pca_contacts']['sha256']==sha(a.historical_pca_contact_proof)
 assert historical_review['support_criterion'] and historical_review['rationale'] and isinstance(historical_review['limitations'],list)
 preservation=load(a.preservation_proof)
 assert preservation['schema']=='zhenru-actual-geometry-v2-bracket-preservation-v1'
 assert preservation['geometry_revision_passed'] is True and preservation['raw']['sha256']==raw_sha
 assert preservation['previous_raw']['sha256']==BASELINE_RAW
 assert preservation['structure_report']['sha256']==sha(a.structure_proof)
 assert preservation['previous_structure_report']['sha256']==sha(a.historical_structure_proof)
 assert preservation['changed_part_allowlist_count']==144 and preservation['bracket_part_count']==140
 assert preservation['non_allowlisted_parts_byte_identical'] is True
 assert preservation['bracket_no_protrusion_passed'] is True and preservation['bracket_support_chains_passed'] is True
 carry=preservation['tile_proof_carryforward']
 assert carry['previous_raw']['sha256']==BASELINE_RAW and carry['current_raw']['sha256']==raw_sha
 assert carry['historical_report']['sha256']==sha(a.historical_lip_contact_proof)
 assert carry['actual_all_roof_tile_triangle_normals_materials_unchanged'] is True and carry['original_report_not_modified'] is True
 ridges=load(a.ridge_proof)
 assert ridges['schema']=='zhenru-v2-actual-descending-ridge-gable-review-v1'
 assert ridges['passed'] is True and ridges['raw']['sha256']==raw_sha and ridges['baseline_raw']['sha256']==BASELINE_RAW
 assert ridges['source_geometry']['sha256']==sha(model/'geometry-input.json') and ridges['calibration']['sha256']==sha(model/'calibration.json')
 assert ridges['actual_structure_report']['sha256']==sha(a.structure_proof)
 assert ridges['v1_native_report']['sha256']==sha(a.historical_native_report)
 assert len(ridges['four_ridge_labels'])==4 and set(ridges['four_ridge_labels'])==EXPECTED_RIDGES
 for key,count in [('high_pitch_contact_checks',4),('ridge_connection_checks',8),('gable_fill_preservation_checks',2),('ridge_curtain_projection_checks',4)]:
  checks=ridges[key];assert isinstance(checks,list) and len(checks)==count and all(item['passed'] is True for item in checks), 'Actual ridge/gable checks failed or incomplete: '+key
 cameras=ridges['actual_camera_gable_visibility_checks']
 assert isinstance(cameras,list) and len(cameras)>=2 and all(item['passed'] is True for item in cameras)
 assert {'full','rear'}<={item['camera_role'] for item in cameras}, 'Both actual full and rear camera gable views are required.'
 visual=load(a.native_review);native=load(a.native_report)
 assert visual['passed'] is True and visual['actually_viewed'] is True and visual.get('browser_passed') is False
 assert visual['raw']['sha256']==raw_sha and visual['native']['sha256']==native_sha
 assert native['schema']=='zhenru-native-render-v10' and native['source_glb_sha256']==raw_sha and native['native']['sha256']==native_sha
 assert native['builder_sha256']==sha(model/'build_model.py') and native['calibration_sha256']==sha(model/'calibration.json')
 assert native['renderer_sha256']==sha(model/'render_previews.py') and native['model_images']==0
 assert len(native['renders'])==3
 for role in ('full','detail','rear'):
  image=next(x for x in native['renders'] if x['file']==f'{ID}-{role}.png');check_bound(a.native_report.parent/image['file'],image)
 geometry=load(model/'geometry-input.json');cal=load(model/'calibration.json')
 assert geometry['id']==ID and sha(model/'geometry-input.json')==cal['source_geometry_sha256']
 nav=load(a.navigation);assert sha(a.navigation)==NAVIGATION_FREEZE
 assert nav['id']==ID and nav['geometry_input']['sha256']==sha(model/'geometry-input.json') and nav['browser_passed'] is False
 raw_metadata=load(run/'raw/asset-metadata.json');raw_geometry=load(run/'raw/geometry-report.json')
 assert raw_metadata['raw']['sha256']==raw_sha and raw_metadata['id']==ID and raw_metadata['ground_base_m']==0
 assert raw_geometry['passed'] is True and raw_geometry['source_geometry_sha256']==sha(model/'geometry-input.json') and raw_geometry['calibration_sha256']==sha(model/'calibration.json')
 height=raw_metadata['height_estimate_m'];assert abs(height-raw_geometry['bbox_enu_m'][1][2])<1e-7
 assert abs(height-native['bounds_enu_m'][1][2])<1e-4 and abs(height-package['provenance']['height_estimate_m'])<1e-7
 photos=load(model/'references/photo-register.json')['photos'];assert len(photos)==4;source_photos=[]
 for photo in photos:
  image=model/'references'/photo['local_file'];check_bound(image,photo);assert photo['actual_viewed'] is True and photo['embedded_as_texture'] is False
  source_photos.append({'id':str(photo['pageid']),'author':photo['author'],'license':photo['license'],'license_url':photo['license_url'],'source_url':photo['description_page'],'date':photo['photography_date'],'embedded_as_texture':False,'reference_form':photo['download_kind'],'original_url':photo['original_url'],'image':{**descriptor(image),'file':f"assets/references/precise/{ID}/{photo['local_file']}"}})
 evidence={'photo_register':descriptor(model/'references/photo-register.json'),'official_structural_facts':descriptor(model/'references/review.json'),'source_geometry':descriptor(model/'geometry-input.json'),'calibration':descriptor(model/'calibration.json'),'source_lock':descriptor(source_lock),'provisional_navigation':descriptor(a.navigation),'actual_raw_structure':descriptor(a.structure_proof),'actual_geometry_revision_preservation':descriptor(a.preservation_proof),'actual_descending_ridges':descriptor(a.ridge_proof),'actual_decoded_package':descriptor(decoded_path),'native_render':descriptor(a.native_report),'native_visual':descriptor(a.native_review),'package':descriptor(package_path)}
 for key in HISTORICAL_HASHES:evidence[key]=descriptor(getattr(a,key))
 notes={
 'source_photos':'Four actually viewed Commons references, CC0 and CC BY-SA3/4, retain exact bytes and individual attributions. 2025 front is primary;2013/2019 are comparisons; historical rear capture date/current state are uncertain. No photo pixels are embedded.',
 'identity_footprint':'Unique OSMw489505048@5/GERS e68a1152 owner and original427.676m² quadrilateral retained. It identifies the hall, not a measured wall or eave line. The independent squarecore derives from sqrt158 as an explicit area-definition-limited estimate.',
 'height_evidence':'Published16 columns with6.45/.40m inner shafts and4.28/.32m eave shafts constrain the reconstruction. Their datum is unspecified. The actual exported model bound is about10.24m, an estimate, not a published overall height. Neighbor TianwangHall9.96/13.9/9.5m values are excluded.',
 'visible_facade_opening_grid':'South and north each have six separate lattice leaves; south has two flame-headed straight-lattice windows and real wall openings. Actual decoded checks cover12 leaf lattices,2 windows and2 central wall openings. Door angles, sizes and current rear details remain estimates.',
 'roof':'Historical geometry-v1 actual8500 cover/pan positive-volume lateral lip-band results are carried to geometry-v2 only through the bound actual byte identity of every roof/tile POSITION,NORMAL and material. Those8500 tests are not claimed to have run on the new fullraw. Original interior-grid/PCA failures and the oldraw root criterion remain historical records. New140 bracket support-chain/no-protrusion and4 descending-ridge contact/gable-visibility checks are separately bound. Distinct single-eave hip-gable assembly with4 closed substrate fields, actual tile shells, continuous ridge seats, rafters/brackets,2chiwen and small hip ornaments. No central finial or separate background pagoda. Actual finite contact evidence and native review remain bounded checks, not whole-assembly collision freedom.',
 'texture_mapping_qa':'Intentional zero images/textures in raw/web/LOD. Color materials and geometric details represent visible2025 south appearance without baked photograph pixels or lighting. Exact modern plaque lettering is unresolved and omitted.',
 'geometry_proof':'Current serialized Float32 closure/normals/volume/placement checks and current decoded apertures. Exactly144 parts are allowed to change (140 brackets and4 descendingridges); actual evidence must show every other part byte-identical to the fixed baseline, including tiles,columns,doors andgables. Current bracket andridge checks plus explicitly carried historical tile evidence; exact decoded web oriented-position/material triangle multiset and≤.05° normal policy. Raw/web/LOD retain sampled open lattice cells and solid negative controls.',
 'size_proof':'All4 actual package assets are individually strictly below100,000,000bytes; actual native size is checked after generation.',
 'uncertainty':'Owner boundary versus core, undefined158m² area, roof profile/total height/overhang, basal datum, central-bay lean interpretation, historic rear and estimated details remain explicit. No interior statuary, surveyed reconstruction, access permission or HTML/browser acceptance.'}
 limitations=cal['uncertainty']+visual.get('limitations',[])+historical_review['limitations']
 limitations+=['Historical cover/pan reports target geometry-v1 raw '+BASELINE_RAW+'; their byte-identical roof/tile result is carried only by the current bound preservation proof, not by treating old and new fullraw hashes as equal.','144 allowed changed parts are140 bracket components and4 descending-gable ridges; the two independent reports cover different subsets and do not certify whole-building collision freedom.','Current native and decoded checks are required independently; historical native camera descriptions do not substitute for current rendered-image review.']
 summary={'schema':'zhenru-prebrowser-acceptance-summary-v10','id':ID,'geometry_revision':'geometry-v2','prebrowser_scope_passed':True,'browser_passed':False,'raw_sha256':raw_sha,'native_sha256':native_sha,'evidence':evidence,'limitations':limitations,'statement':'Passed sections bind current independent model evidence within its stated scope. Historical geometry-v1 roof/tile evidence is explicitly carried through byte-identical geometry/material proof; original raw hashes and failed findings remain unchanged. No measurement accuracy, current rear survey, whole-building collision freedom or HTML acceptance is certified.'}
 summary['geometry_revision_scope']={'current_raw_sha256':raw_sha,'baseline_raw_sha256':BASELINE_RAW,'allowed_changed_part_count':144,'bracket_part_count':140,'descending_ridge_part_count':4,'non_allowlisted_parts_byte_identical':True,'current_structure_evidence':descriptor(a.structure_proof),'current_bracket_preservation_evidence':descriptor(a.preservation_proof),'current_ridge_evidence':descriptor(a.ridge_proof)}
 summary['tile_contact_carryforward']={'historical_raw_sha256':BASELINE_RAW,'current_raw_sha256':raw_sha,'historical_edge_band_report':descriptor(a.historical_lip_contact_proof),'preservation_evidence':descriptor(a.preservation_proof),'historical_edge_band_contact_passed':lip['strict_edge_band_contact_passed'],'historical_edge_pairs_checked':lip['pair_count'],'historical_pca_report_passed':pca['strict_edge_band_contact_passed'],'historical_pca_failed_pair_count':pca['failed_pair_count'],'historical_initial_finite_checks_passed':contacts['finite_checks_passed'],'historical_root_review':descriptor(a.historical_contact_review),'current_roof_tile_position_normal_materials_byte_identical':True,'historical_reports_modified':False,'8500_pair_test_reexecuted_on_current_fullraw':False,'historical_support_criterion':historical_review['support_criterion'],'current_brackets_and_ridges_use_separate_actual_reports':True}
 for key in KEYS:summary[key]={'building_id':ID,'geometry_input_sha256':sha(model/'geometry-input.json'),'passed':True,'scope':notes[key]}
 summary['source_photos']['photo_sha256']=[p['sha256'] for p in photos];summary['geometry_proof']['raw_sha256']=raw_sha
 summary['texture_mapping_qa'].update(mode='none',raw_sha256=raw_sha,web_sha256=package['assets']['web']['sha256'])
 summary_path=run/'prebrowser-acceptance-summary.json';registration_path=run/'registration.draft.json';metadata_path=run/'model-metadata.json'
 assert all(not p.exists() for p in (summary_path,registration_path,metadata_path))
 write_new(summary_path,summary);proof=descriptor(summary_path);prov=package['provenance']
 entry={k:prov[k] for k in ('id','name','district','source_provider','source_url','source_license','asset_license','appearance_epoch')}
 entry.update(geometry_input=descriptor(model/'geometry-input.json'),assets=package['registration_assets'],source_photos=source_photos,primary_photo='179591117',source_package=f'source/precise/{ID}',height={'metres':height,'estimated':True,'note':notes['height_evidence']},uncertainty=limitations,navigation=nav['navigation'],navigation_evidence=descriptor(a.navigation),navigation_scope=nav['navigation_semantics'],architecture_style='元代单檐歇山式木构正殿；三间三进深、深色木构、灰瓦与侧面白墙',detail_note='六扇格子门、火焰形直棂窗、十六柱、歇山瓦面及鸱吻；尺寸与当前背面仍有明确估计。',browser_accepted=False,geographic_opening_alignment=None)
 entry['acceptance']={key:{'status':'passed','evidence':proof,'section':key} for key in KEYS}
 entry['acceptance']['browser_proof']={'status':'pending','reason':'Independent model delivery. Owner/LOD/navigation and actual browser acceptance belong to later integration.'}
 write_new(registration_path,{'schema':'precise-registration-input-v1','buildings':[entry]})
 metadata=dict(raw_metadata);metadata.update(native_visual_passed=True,native_visual_evidence=descriptor(a.native_review),package_evidence=descriptor(package_path),geometry_revision='geometry-v2',geometry_revision_preservation_evidence=descriptor(a.preservation_proof),descending_ridge_evidence=descriptor(a.ridge_proof),historical_tile_raw_sha256=BASELINE_RAW,tile_contact_carryforward_evidence=descriptor(a.preservation_proof),browser_passed=False,stage='independent geometry-v2 model delivery; original raw metadata and historical geometry-v1 reports remain unchanged')
 write_new(metadata_path,metadata)
 print(json.dumps({'summary':descriptor(summary_path),'registration':descriptor(registration_path),'model_metadata':descriptor(metadata_path)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
