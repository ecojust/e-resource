#!/usr/bin/env python3
"""Compose a model-only registration draft from actual independent evidence.
No installation, accepted catalog, navigation mutation, renderer or upload.
"""
from pathlib import Path
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent
KEYS=('source_photos','identity_footprint','height_evidence','visible_facade_opening_grid','roof','texture_mapping_qa','geometry_proof','size_proof','uncertainty')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def descriptor(p):
 p=Path(p).resolve();assert p.is_file() and not p.is_symlink();return {'source':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def load(p):return json.loads(Path(p).read_text())
def write_new(p,data):
 with Path(p).open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--run',type=Path,required=True);a.add_argument('--native-review',type=Path,required=True);a.add_argument('--contact-review',type=Path,required=True);a.add_argument('--navigation',type=Path,required=True);args=a.parse_args()
 run=args.run.resolve();package_path=run/'package/packaging-record.json';package=load(package_path);decoded_path=run/'decoded-package-check.json';decoded=load(decoded_path);visual=load(args.native_review)
 assert package['building_id']=='songjiang-fangta-pagoda' and package['packaging_passed'] is True and package['registered'] is False
 assert decoded['passed'] is True and decoded['package_record_sha256']==sha(package_path)
 for role in ('raw','web','lod'):
  checks=decoded['assets'][role];assert len(checks['aperture_samples'])==36 and all(x['type']=='through-cusped-door' and x['hits']==0 for x in checks['aperture_samples'])
  assert len(checks['open_finial_ring_samples'])==9
  assert all(len(x['samples'])==4 and all(y['void_hits']==0 and y['annulus_hits']>0 for y in x['samples']) for x in checks['open_finial_ring_samples'])
 assert visual['passed'] is True and visual['actually_viewed'] is True and visual.get('browser_passed') is False
 assert visual['raw']['sha256']==package['assets']['raw']['sha256'] and visual['native']['sha256']==package['assets']['native']['sha256']
 for role,item in package['registration_assets'].items():
  p=Path(item['source']);assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256'] and item['bytes']<100_000_000
  if role!='native':assert decoded['assets'][role]['sha256']==item['sha256'] and decoded['assets'][role]['embedded_images']==0
 structure_path=HERE/'independent-review/actual-raw-structure.json';structure=load(structure_path)
 roof_path=HERE/'independent-review/actual-raw-roof-pairs.json';roof=load(roof_path)
 assert structure['structure_passed'] and structure['raw']['sha256']==package['assets']['raw']['sha256']
 assert roof['finite_sample_passed'] and roof['actual_raw_sha256']==package['assets']['raw']['sha256']
 contacts_path=HERE/'independent-review/actual-roles-contacts.json';contacts=load(contacts_path);contact_review=load(args.contact_review)
 assert contacts['schema']=='fangta-actual-roles-finite-contacts-v1'
 assert contacts['raw']['sha256']==package['assets']['raw']['sha256']
 assert all(contacts[key] is True for key in ('central_openings_passed','porch_support_chains_passed','open_finial_hoops_passed','hip_centerline_contact_passed'))
 assert contact_review['schema']=='fangta-root-finite-contact-review-v1' and contact_review['passed'] is True and contact_review['actually_reviewed'] is True
 assert contact_review['raw']['sha256']==package['assets']['raw']['sha256']
 assert contact_review['actual_contacts']['sha256']==sha(contacts_path)
 assert contact_review['support_criterion'] and contact_review['rationale']
 assert isinstance(contact_review['limitations'],list)
 geometry=load(HERE/'geometry-input.json');cal=load(HERE/'calibration.json');assert sha(HERE/'geometry-input.json')==cal['source_geometry_sha256']
 photos=load(HERE/'references/photo-register.json')['photos'];source_photos=[]
 for photo in photos:
  image=HERE/'references'/photo['local_file'];assert image.stat().st_size==photo['bytes'] and sha(image)==photo['sha256'] and photo['actual_viewed'] is True
  source_photos.append({'id':str(photo['pageid']),'author':photo['author'],'license':photo['license'],'license_url':photo['license_url'],'source_url':photo['description_page'],'date':photo['photography_date'],'embedded_as_texture':False,'reference_form':photo['reference_form'],'original_url':photo['original_url'],'image':{**descriptor(image),'file':f"assets/references/precise/songjiang-fangta-pagoda/{photo['local_file']}"}})
 nav=load(args.navigation);assert nav['id']==geometry['id'];assert nav['geometry_input']['sha256']==sha(HERE/'geometry-input.json')
 frozen_navigation=load(HERE/'navigation-proposal.json');assert nav['navigation']==frozen_navigation['navigation'], 'Navigation values differ from model delivery proposal; review a new immutable revision.'
 evidence={'photo_register':descriptor(HERE/'references/photo-register.json'),'official_height_and_history':descriptor(HERE/'references/official-review.json'),'source_geometry':descriptor(HERE/'geometry-input.json'),'calibration':descriptor(HERE/'calibration.json'),'source_lock':descriptor(HERE/'build-source-files.json'),'provisional_navigation':descriptor(HERE/'navigation-proposal.json'),'actual_raw_structure':descriptor(structure_path),'finite_actual_raw_roof_samples':descriptor(roof_path),'actual_roles_contacts':descriptor(contacts_path),'root_finite_contact_review':descriptor(args.contact_review),'actual_decoded_package':descriptor(decoded_path),'native_visual':descriptor(args.native_review),'package':descriptor(package_path)}
 notes={
 'source_photos':'Five actually viewed licensed Commons reference files retained at exact bytes, with four separate authors; individual BY-SA3/4 licenses and source-native/preview forms are preserved. No photograph pixels embedded.',
 'identity_footprint':'Unique OSM w461743815@7 / GERS22db76bc owner and original quadrilateral retained. The model has an independent 6m square lower core and an estimated source-derived orthogonal orientation; owner quad is not asserted as a wall or eave line.',
 'height_evidence':'42.65m total and 6m lower brick face follow one official nominal description; 7.85m finial follows two other chapters. The derived34.80m roof split does not prove a shared datum. Official42.5/48.5m alternatives and separate13/8.20m heartwood values remain recorded.',
 'visible_facade_opening_grid':'Nine levels/four faces have36 actual central through 壸门 in three-bay framing. Decoded wall rays and limited actual native review passed; hidden face symmetry and absolute facade orientation are estimates.',
 'roof':'Nine curved four-slope roofs, eight upper galleries, continuous hip seats, separate physical tiles/rafters/brackets,12 porch columns and nine open annular finial hoops. Actual finite geometry samples and native image review are limited evidence, not a full collision-free proof or measured roof reconstruction.',
 'texture_mapping_qa':'Intentional zero images/textures in raw/web/LOD; color materials and geometric details represent2017 exterior appearance without baked photo lighting.',
 'geometry_proof':'Actual Float32 exported part closure/normals/volume, exact decoded web oriented position/material triangle multiset and <=0.05deg normal policy; finite doorway, roof, porch and finial-hole checks. No hidden interior accuracy claim.',
 'size_proof':'All four actual package assets individually strictly less than100,000,000 bytes; native size checked after generation.',
 'uncertainty':'Nominal height conflicts, estimated layer heights/taper/overhang/construction depths, repeated hidden faces,12-column symmetric porch scenario,2017 material state and geometric exterior-navigation scope remain explicit.'}
 summary={'schema':'fangta-prebrowser-acceptance-summary-v10','id':geometry['id'],'prebrowser_scope_passed':True,'browser_passed':False,'raw_sha256':package['assets']['raw']['sha256'],'native_sha256':package['assets']['native']['sha256'],'evidence':evidence,'finite_contact_scope':{'support_criterion':contact_review['support_criterion'],'rationale':contact_review['rationale'],'independent_report_original_passed':contacts.get('passed'),'root_review_passed':True},'limitations':cal['uncertainty']+visual.get('limitations',[])+contact_review['limitations'],'statement':'Passed sections mean evidence and limited checks are complete for independent model delivery, not measured architectural accuracy or HTML acceptance. Original finite-contact findings are retained; any difference between full-width contact and a narrower support criterion must be explained by the root review.'}
 for key in KEYS:
  summary[key]={'building_id':geometry['id'],'geometry_input_sha256':sha(HERE/'geometry-input.json'),'passed':True,'scope':notes[key]}
 summary['source_photos']['photo_sha256']=[photo['sha256'] for photo in photos]
 summary['geometry_proof']['raw_sha256']=package['assets']['raw']['sha256']
 summary['texture_mapping_qa'].update(mode='none',raw_sha256=package['assets']['raw']['sha256'],web_sha256=package['assets']['web']['sha256'])
 summary_path=run/'prebrowser-acceptance-summary.json';registration_path=run/'registration.draft.json';metadata_path=run/'model-metadata.json'
 assert all(not p.exists() for p in (summary_path,registration_path,metadata_path))
 write_new(summary_path,summary);proof=descriptor(summary_path)
 prov=package['provenance'];entry={k:prov[k] for k in ('id','name','district','source_provider','source_url','source_license','asset_license','appearance_epoch')}
 entry.update(geometry_input=descriptor(HERE/'geometry-input.json'),assets=package['registration_assets'],source_photos=source_photos,primary_photo='62446245',source_package='source/precise/songjiang-fangta-pagoda',height={'metres':42.65,'estimated':True,'note':notes['height_evidence']},uncertainty=summary['limitations'],navigation=nav['navigation'],navigation_evidence=descriptor(args.navigation),navigation_scope=nav['navigation_semantics'],architecture_style='九级四面砖木方塔；白抹灰、朱框、灰柱与水平栏杆、四坡曲檐',detail_note='三间正中真实壸门、十二柱围廊、八层回廊与九相轮镂空塔刹；比例、背面及方位仍含估计。',browser_accepted=False,geographic_opening_alignment=None)
 entry['acceptance']={key:{'status':'passed','evidence':proof,'section':key} for key in KEYS};entry['acceptance']['browser_proof']={'status':'pending','reason':'Independent model delivery; browser/owner/LOD/navigation acceptance belongs to the subsequent integration workflow.'}
 write_new(registration_path,{'schema':'precise-registration-input-v1','buildings':[entry]})
 metadata=load(run/'raw/asset-metadata.json');metadata['native_visual_passed']=True;metadata['native_visual_evidence']=descriptor(args.native_review);metadata['package_evidence']=descriptor(package_path);metadata['browser_passed']=False;metadata['stage']='independent model delivery; original raw metadata remains unchanged';write_new(metadata_path,metadata)
 print(json.dumps({'summary':descriptor(summary_path),'registration':descriptor(registration_path),'model_metadata':descriptor(metadata_path)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
