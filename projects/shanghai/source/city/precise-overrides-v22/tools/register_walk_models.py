from pathlib import Path
import json,hashlib,shutil,re,html,sys,struct
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[4]);args=ap.parse_args();p=args.project.resolve();sys.path.insert(0,str(p/'tools'));import ordinary_assets as oa
IDS=['xuhui-zikawei-south-building','huangpu-sun-yatsen-residence']
def read(f):return json.loads(f.read_text())
def write(f,d):f.parent.mkdir(parents=True,exist_ok=True);f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def meta(f):return {'file':str(f.relative_to(p)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
nav=read(p/'data/landmarks.json');reg=read(p/'data/precise-buildings-v6.json');catalog=read(p/'data/precise-buildings/catalog.json')
for ident in IDS:
 checks=json.loads((p/f'data/audit/precise-buildings-v22/{ident}/walk-final.json').read_text());assert checks['errors']==[] and checks['blocking']=={'inside':'building','player':None} and checks['initial']['asset']['visible'] and checks['returned']['asset']['variant']=='full'
 proof=json.loads((p/f'data/audit/precise-buildings-v22/{ident}/baseline-preservation.json').read_text());assert proof['position_material_winding']['pass'] and proof['position_normal_material_winding']['pass'] and proof['negative_removed_neighbor_rejected']
 row=next(r for r in nav if r['id']==ident);macro=row['owner']['macro_id'];source=p/f'source/precise/{ident}';audit=p/f'data/audit/precise-buildings-v22/{ident}';oldaudit=p/('data/audit/zikawei-south-building-v1' if ident.startswith('xuhui') else 'data/audit/sun-yatsen-residence-v1');manifest=p/f'assets/models/candidates/{ident}/manifest.json';mf=read(manifest)
 installed_proof=[]
 raw_data=(manifest.parent/mf['assets']['raw']['file']).read_bytes();raw_copyright=json.loads(raw_data[20:20+struct.unpack_from('<I',raw_data,12)[0]])['asset']['copyright']
 for role,key in [('raw','raw'),('web','full'),('lod','lod'),('native','native')]:
  src=manifest.parent/mf['assets'][key]['file'];prefix='assets/native/precise' if role=='native' else 'assets/models/precise';dst=p/f'{prefix}/{macro}/{ident}'/src.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  if role in ['web','lod']:
   data=dst.read_bytes();length=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+length]);tail=data[20+length:];doc['asset']['copyright']=raw_copyright;jb=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();jb+=b' '*((-len(jb))%4);dst.write_bytes(struct.pack('<4sII',b'glTF',2,20+len(jb)+len(tail))+struct.pack('<II',len(jb),0x4e4f534a)+jb+tail);installed_proof.append({'role':role,'original':meta(src),'installed':meta(dst),'original_binary_chunk_sha256':hashlib.sha256(tail).hexdigest(),'installed_binary_chunk_sha256':hashlib.sha256(dst.read_bytes()[20+len(jb):]).hexdigest(),'change':'Restore authored copyright in GLB asset metadata only; compressed buffers untouched.'})
  row['assets'][role]=meta(dst)
  field={'raw':'editable_model','web':'model','lod':'lod_model','native':'native_model'}[role];row[field]=str(dst.relative_to(p))
  for k in ['bytes','sha256']:row[f'{role}_{k}']=row['assets'][role][k]
 write(audit/'installed-assets.json',{'assets':row['assets'],'copyright_metadata_changes':installed_proof,'all_single_files_below_100MB':all(a['bytes']<100000000 for a in row['assets'].values())})
 next(x for x in reg['landmarks'] if x['id']==ident)['source_geometry_correction']['variants']={k:{'asset_sha256':row['assets'][k]['sha256']} for k in ['web','lod']}
 row['model_geometry']=row['assets']['raw']['file'];row['accepted']=True;row['candidate_only']=False;row['browser_passed']=True;row['pending_stages']=[];row['catalog_lifecycle_browser_passed']=False
 for x in row['source_license']:x['role']='Source identity and estimated footprint context'
 for x in row['asset_license']:x['role']='Original authored geometry, code and procedural materials'
 photos=read(source/'public-photo-register.json');photos=photos['photos'] if isinstance(photos,dict) else photos;declared=[]
 for photo in photos:
  src=source/photo['file'];dst=p/f'assets/references/precise/{ident}'/src.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  if 'commons' in photo:
   info=photo['commons']['imageinfo'][0];m=info['extmetadata'];data={'author':html.unescape(re.sub('<[^>]+>','',m['Artist']['value'])),'license':m['LicenseShortName']['value'],'license_url':m['LicenseUrl']['value'],'source':info['descriptionurl']}
  else:data={k:photo[k] for k in ['author','license','license_url','source']}
  declared.append({**meta(dst),**data,'embedded_as_texture':False})
 row['source_photos']=declared;row['reference']={**declared[0],'image':declared[0]['file']};row['reference_policy']=oa.LICENSED_PBR_POLICY
 row['material_images']=[]
 for role in ['basecolor','normal','orm']:
  f=next((source/'textures').glob('*-'+role+'.png'));row['material_images'].append({**meta(f),'role':role,'kind':'procedural_material','embedded_as_texture':True,'license':'MIT','author':'agent','license_url':'https://opensource.org/license/mit','source':f'https://github.com/ecojust/e-resource/tree/master/projects/shanghai/source/precise/{ident}','limitations':'Original estimated material, not a surface scan or reference-photo pixels.','pixels':[512,512],'generator':meta(source/'source/generate_material.py')})
 row['material_texture']={'mode':'original-procedural-pbr','expected_images':{'raw':3,'web':3,'lod':3}}
 bindings={'source_photos':(source/'public-photo-register.json','Licensed original reference images, individually credited; not embedded.'),'identity_footprint':(audit/'placement.json','Exact source identity, separate neighboring building, conservative obstacle and 9-macro neighborhood screen.'),'height_evidence':(source/'design-input.json','Metric height and hidden dimensions remain explicit estimates, not survey measurements.'),'visible_facade_opening_grid':(oldaudit/'structure-full.json','Independent model opening and roof probes, with documented estimated hidden elevations.'),'roof':(oldaudit/'geometry.json','Original full/LOD geometry verified; roof form follows published photo evidence, hidden intersections estimated.'),'texture_mapping_qa':(oldaudit/'pbr.json','Original PBR images and UVs preserved through compression.'),'geometry_proof':(audit/'baseline-preservation.json','Actual Three/Meshopt decoded baseline positions, normals, materials and winding exactly preserved while partitioning owner groups; model geometry retains its separate original audit.'),'size_proof':(audit/'installed-assets.json','Four assets byte/SHA-bound, each strictly below 100000000 bytes.'),'browser_proof':(audit/'walk-final.json','Actual third-person start, keyboard movement/key release, conservative wall collision and full/LOD/full on virtual outdoor ground; separate failure/fallback report.'),'uncertainty':(source/'design-input.json','Estimated exterior only, without measured terrain, indoor, stair or veranda walking.')}
 mf.update(status='installed-estimated-exterior-outdoor-walk',map_replacement=True,walk_integration=True,integration_record=f'data/audit/precise-buildings-v22/{ident}/README.md');write(manifest,mf)
 row['acceptance']={key:{'status':'passed','evidence_file':meta(file)['file'],'evidence_bytes':meta(file)['bytes'],'evidence_sha256':meta(file)['sha256'],'scope':scope} for key,(file,scope) in bindings.items()}
 status=read(source/'registration-status.json');status.update(status='installed-estimated-exterior-outdoor-walk',city_replacement=True,walk_integration=True,count_as_completed_source_feature=False,pending=['Metric scale and unobserved exterior refinement; no complete historical or surveyed reconstruction claim.'],walk_scope='Virtual outdoor flat ground; conservative closed building obstacle, no indoor, stair or veranda access.',integration_evidence=f'../../../data/audit/precise-buildings-v22/{ident}/README.md');write(source/'registration-status.json',status)
 oa.record_contract(row,{'310101':'黄浦区','310104':'徐汇区'});oa.bind(row,reg);oa.verify_assets(p,row)
 # Single-macro catalog shares the exact static ownership and model record.
 r={k:v for k,v in reg.items() if k not in ['ordinary_catalog','geometry_inputs','macros','landmarks']};r['macros']=[m for m in reg['macros'] if m['id']==macro];r['landmarks']=[x for x in reg['landmarks'] if x['id']==ident];r['geometry_inputs']={ident:reg['geometry_inputs'][ident]};r['validation']={'file':str((audit/'baseline-preservation.json').relative_to(p)),'sha256':meta(audit/'baseline-preservation.json')['sha256']}
 folder=p/f'data/precise-buildings/macros/{macro}';write(folder/'replacement.json',r);index={'schema':'precise-building-macro-v1','macro_id':macro,'url_base':'project-root','record_count':1,'models':[row],'replacement_registry':meta(folder/'replacement.json')};write(folder/'index.json',index)
 catalog['macros']=[m for m in catalog['macros'] if m['id']!=macro]+[{'id':macro,'bbox':row['bbox'],'record_count':1,**meta(folder/'index.json')}]
 write(p/f'data/precise-buildings/by-id/{ident}.json',{'schema':'precise-building-pointer-v1','id':ident,'feature_local_id':row['owner']['feature_local_id'],'macro_id':macro,'macro_index':str((folder/'index.json').relative_to(p))})
catalog['macro_count']=len(catalog['macros']);catalog['record_count']=sum(x['record_count'] for x in catalog['macros']);write(p/'data/precise-buildings/catalog.json',catalog);reg['ordinary_catalog']=meta(p/'data/precise-buildings/catalog.json');write(p/'data/precise-buildings-v6.json',reg);write(p/'data/landmarks.json',nav)
result=oa.inspect(p,nav,reg,verify_files=False);print('PASS ordinary metadata contracts',len(result['records']),'models; full asset/PBR verification for the two new records')
