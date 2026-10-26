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
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--run',type=Path,required=True);a.add_argument('--native-review',type=Path,required=True);a.add_argument('--navigation',type=Path,required=True);args=a.parse_args()
 run=args.run.resolve();package_path=run/'package/packaging-record.json';package=load(package_path);decoded_path=run/'decoded-package-check.json';decoded=load(decoded_path);visual=load(args.native_review)
 assert package['building_id']=='xuhui-longhua-pagoda' and package['packaging_passed'] is True and package['registered'] is False
 assert decoded['passed'] is True and decoded['package_record_sha256']==sha(package_path)
 assert visual['passed'] is True and visual['actually_viewed'] is True and visual.get('browser_passed') is False
 assert visual['raw']['sha256']==package['assets']['raw']['sha256'] and visual['native']['sha256']==package['assets']['native']['sha256']
 for role,item in package['registration_assets'].items():
  p=Path(item['source']);assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256'] and item['bytes']<100_000_000
  if role!='native':assert decoded['assets'][role]['sha256']==item['sha256'] and decoded['assets'][role]['embedded_images']==0
 structure_path=HERE/'independent-review/actual-raw-structure.json';structure=load(structure_path)
 roof_path=HERE/'independent-review/actual-raw-roof-pairs.json';roof=load(roof_path)
 assert structure['structure_passed'] and structure['raw']['sha256']==package['assets']['raw']['sha256']
 assert roof['finite_sample_passed'] and roof['actual_raw_sha256']==package['assets']['raw']['sha256']
 geometry=load(HERE/'geometry-input.json');cal=load(HERE/'calibration.json');assert sha(HERE/'geometry-input.json')==cal['source_geometry_sha256']
 photos=load(HERE/'references/photo-register.json')['photos'];source_photos=[]
 for photo in photos:
  image=HERE/'references'/photo['local_file'];assert image.stat().st_size==photo['bytes'] and sha(image)==photo['sha256'] and photo['actual_viewed'] is True
  source_photos.append({'id':str(photo['pageid']),'author':photo['author'],'license':photo['license'],'license_url':photo['license_url'],'source_url':photo['description_page'],'date':photo['photography_date'],'embedded_as_texture':False,'reference_form':'unchanged licensed Commons 960px preview, not the full-resolution original','original_url':photo['original_url'],'image':{**descriptor(image),'file':f"assets/references/precise/xuhui-longhua-pagoda/{photo['local_file']}"}})
 nav=load(args.navigation);assert nav['id']==geometry['id'];assert nav['geometry_input']['sha256']==sha(HERE/'geometry-input.json')
 evidence={'photo_register':descriptor(HERE/'references/photo-register.json'),'official_height_and_history':descriptor(HERE/'references/official-independent/review.json'),'source_geometry':descriptor(HERE/'geometry-input.json'),'calibration':descriptor(HERE/'calibration.json'),'source_lock':descriptor(HERE/'build-source-files.json'),'actual_raw_structure':descriptor(structure_path),'finite_actual_raw_roof_samples':descriptor(roof_path),'actual_decoded_package':descriptor(decoded_path),'native_visual':descriptor(args.native_review),'package':descriptor(package_path)}
 notes={
 'source_photos':'Four actually viewed licensed Commons previews retained at exact bytes, with four separate authors/licenses; none embedded as texture.',
 'identity_footprint':'Single named OSM w47011877@11 / GERS66c3a80d owner, original source octagon and anchor retained. This does not prove owner boundary is the visible wall/eave line.',
 'height_evidence':'40.64m total/32.3m body follows the cited official nominal convention. No survey, common ground datum, measured storey height or verified photo metric claim.',
 'visible_facade_opening_grid':'Real seven-level shell openings and alternating blind panels; decoded wall rays and limited actual native review passed. First-level cardinal opening phase remains unverified scenario0.',
 'roof':'Seven continuous curved eaves and distinct gallery brackets, tiles/rafters/finial; actual exported finite tile samples plus native visual review. Not whole-assembly intersection freedom or measured roof curvature.',
 'texture_mapping_qa':'Intentional zero images/textures in raw/web/LOD; color materials and geometric details, without baked photograph lighting.',
 'geometry_proof':'Actual exported Float32 part closure/normals/volume, exact decoded web oriented position/material triangle multiset and <=0.05deg normal rule; finite door/roof checks. Does not certify unseen interiors.',
 'size_proof':'All four actual package assets individually strictly less than100,000,000 bytes; no native size inferred before generation.',
 'uncertainty':'Nominal height, estimated widths/taper/depths/roof curve, unknown absolute door phase, hidden faces, repair epochs and viewing-navigation scope remain explicit.'}
 summary={'schema':'longhua-prebrowser-acceptance-summary-v9','id':geometry['id'],'prebrowser_scope_passed':True,'browser_passed':False,'raw_sha256':package['assets']['raw']['sha256'],'native_sha256':package['assets']['native']['sha256'],'evidence':evidence,'limitations':cal['uncertainty']+visual.get('limitations',[]),'statement':'Passed sections mean evidence and limited checks are complete for independent model delivery, not measured architectural accuracy or HTML acceptance.'}
 for key in KEYS:
  summary[key]={'building_id':geometry['id'],'geometry_input_sha256':sha(HERE/'geometry-input.json'),'passed':True,'scope':notes[key]}
 summary['source_photos']['photo_sha256']=[photo['sha256'] for photo in photos]
 summary['geometry_proof']['raw_sha256']=package['assets']['raw']['sha256']
 summary['texture_mapping_qa'].update(mode='none',raw_sha256=package['assets']['raw']['sha256'],web_sha256=package['assets']['web']['sha256'])
 summary_path=run/'prebrowser-acceptance-summary.json';registration_path=run/'registration.draft.json';metadata_path=run/'model-metadata.json'
 assert all(not p.exists() for p in (summary_path,registration_path,metadata_path))
 write_new(summary_path,summary);proof=descriptor(summary_path)
 prov=package['provenance'];entry={k:prov[k] for k in ('id','name','district','source_provider','source_url','source_license','asset_license','appearance_epoch')}
 entry.update(geometry_input=descriptor(HERE/'geometry-input.json'),assets=package['registration_assets'],source_photos=source_photos,primary_photo='124610746',source_package='source/precise/xuhui-longhua-pagoda',height={'metres':40.64,'estimated':True,'note':notes['height_evidence']},uncertainty=summary['limitations'],navigation=nav['navigation'],navigation_evidence=descriptor(args.navigation),navigation_scope=nav['navigation_semantics'],architecture_style='七级八面砖木塔；黄抹灰塔身、朱框、灰褐回廊与曲瓦挑檐',detail_note='真实门龛/回廊栏杆/斗拱/椽瓦和七相轮塔刹；估计比例与未知首层门向保留说明。',browser_accepted=False,geographic_opening_alignment=None)
 entry['acceptance']={key:{'status':'passed','evidence':proof,'section':key} for key in KEYS};entry['acceptance']['browser_proof']={'status':'pending','reason':'Independent model delivery; browser/owner/LOD/navigation acceptance belongs to the subsequent integration workflow.'}
 write_new(registration_path,{'schema':'precise-registration-input-v1','buildings':[entry]})
 metadata=load(run/'raw/asset-metadata.json');metadata['native_visual_passed']=True;metadata['native_visual_evidence']=descriptor(args.native_review);metadata['package_evidence']=descriptor(package_path);metadata['browser_passed']=False;metadata['stage']='independent model delivery; original raw metadata remains unchanged';write_new(metadata_path,metadata)
 print(json.dumps({'summary':descriptor(summary_path),'registration':descriptor(registration_path),'model_metadata':descriptor(metadata_path)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
