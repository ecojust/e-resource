"""Compress corrected full/LOD assets; preserve image bytes and attribution."""
from pathlib import Path
import argparse,importlib.util,json,hashlib,struct,subprocess,numpy as np
P=Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--gltfpack',required=True);ap.add_argument('--directory',type=Path,required=True);ap.add_argument('--building',choices=['bund12','bund15'],required=True);args=ap.parse_args();D=args.directory;ident=args.building
spec=importlib.util.spec_from_file_location('glb',args.project/'tools/build_bund_lods.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
raw=D/(ident+'-clean-raw.glb');source,bin=m.read_glb(raw);credit='Shanghai Explorer architectural reconstruction. Spatial provenance: © OpenStreetMap contributors, ODbL-1.0, https://www.openstreetmap.org/copyright . '+('Photographic six-window samples: Suicasmo, CC0-1.0, https://commons.wikimedia.org/wiki/File:HSBC_Building,_Shanghai_20250501-1.jpg ; https://creativecommons.org/publicdomain/zero/1.0/ . Dimensions are photo-derived estimates.' if ident=='bund12' else 'Reference photograph only (not a texture): Suicasmo, CC0-1.0, https://commons.wikimedia.org/wiki/File:Former_Russo-Chinese_Bank_Building,_Shanghai_20250501.jpg ; https://creativecommons.org/publicdomain/zero/1.0/ . No photographic image is embedded; dimensions are photo-derived estimates.');photo_sha='bbb15e71ba67f99daab1aa2827494db9c6af6f9b349a2f4ccea6f6609c9ec684'
def attribution(p,lod=False):
 j,b=m.read_glb(p)
 if credit:j['asset']['copyright']=credit+(' This distant variant contains no photographic image.' if lod and ident=='bund12' else '')
 extras=dict(source['asset'].get('extras',{}));extras.update(structural_wall_cleanup='Shared-node same-plane wall union; original projected wall regions and openings preserved.',wall_cleanup_stage='classical-bank-wall-v4.4')
 if lod:extras.pop('photo_original_bytes_embedded',None);extras['lod_has_photo']=False
 j['asset']['extras']=extras;s=json.dumps(j,separators=(',',':'),ensure_ascii=False).encode();s+=b' '*((-len(s))%4);b+=b'\0'*((-len(b))%4);p.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(s)+len(b))+struct.pack('<II',len(s),0x4e4f534a)+s+struct.pack('<II',len(b),0x004e4942)+b)
# Preserve the approved raw BIN verbatim; normalize only JSON attribution. Native is never changed.
original_raw_bin_sha=hashlib.sha256(bin).hexdigest();attribution(raw,False);assert hashlib.sha256(m.read_glb(raw)[1]).hexdigest()==original_raw_bin_sha
lod_source=D/(ident+'-clean-lod-source.glb') if ident=='bund12' else raw
if ident=='bund12':attribution(lod_source,True)
commands=[]
for input_,target,opts in[(raw,D/(ident+'-clean-web.glb'),[]),(lod_source,D/(ident+'-clean-lod.glb'),['-si','0.35','-se','0.002','-sp'])]:
 subprocess.run([args.gltfpack,'-i',str(input_),'-o',str(target),*opts,'-cc','-noq','-km','-ke'],check=True);attribution(target,'-lod.' in target.name);commands.append({'source':input_.name,'target':target.name,'options':[*opts,'-cc','-noq','-km','-ke']})
rows=[]
for p in[raw,D/(ident+'-clean-web.glb'),D/(ident+'-clean-lod.glb')]+([lod_source] if ident=='bund12' else[]):
 j,b=m.read_glb(p);count=sum(j['accessors'][pr['indices']]['count']//3 for mesh in j['meshes'] for pr in mesh['primitives']);bounds,render_count,prims=m.measure(p,source=p==raw or p==lod_source);images=[]
 for im in j.get('images',[]):
  v=j['bufferViews'][im['bufferView']];data=b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];images.append({'mime_type':im['mimeType'],'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 is_lod='-lod' in p.stem;expected=1 if ident=='bund12' and not is_lod else 0;assert len(images)==len(j.get('textures',[]))==expected
 if expected:assert images[0]['sha256']==photo_sha and images[0]['bytes']==7580249
 if ident=='bund12' and is_lod:
  glass=[x for x in j['materials'] if x['name']=='Bund12_Distant_Geometric_Glazing'];assert len(glass)==1 and np.allclose(glass[0]['pbrMetallicRoughness']['baseColorFactor'][:3],[.075,.14,.16],rtol=0,atol=1e-7)
 assert 'KHR_mesh_quantization' not in j.get('extensionsUsed',[])
 for mesh in j['meshes']:
  for pr in mesh['primitives']:assert all(j['accessors'][pr['attributes'][attr]]['componentType']==5126 for attr in('POSITION','NORMAL'))
 assert p.stat().st_size<100000000
 rows.append({'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'triangles':count,'rendered_triangles':render_count,'primitives':prims,'bounds_xyz_m':bounds.tolist(),'images':images,'texture_count':len(j.get('textures',[])),'copyright':j['asset'].get('copyright'),'asset_extras':j['asset'].get('extras',{})})
assert rows[0]['triangles']==rows[1]['triangles'];delta=float(np.max(abs(np.array(rows[0]['bounds_xyz_m'])-np.array(rows[2]['bounds_xyz_m']))));assert delta<.35
native=D/(ident+'-clean.blend');report={'schema_version':'classical-bank-wall-export-v1','building':ident,'status':'passed','full_raw_web_triangle_count_identical':True,'position_normal_float32':True,'lod_no_photograph':True,'original_photo_bytes_unchanged':ident=='bund12','lod_maximum_bounds_change_m':delta,'compression_commands':commands,'assets':rows,'native':{'file':native.name,'bytes':native.stat().st_size,'sha256':sha(native)},'current_wall_validation':'wall-clean-validation.json','pre_wall_photo_preservation_is_historical':ident=='bund12','approved_raw_binary_sha256':original_raw_bin_sha,'copyright_only_raw_update_preserved_binary':True,'browser_validation_performed_by_this_script':False};wpath=D/'wall-clean-validation.json';wall=json.loads(wpath.read_text());wall['raw']={k:rows[0][k] for k in('file','bytes','sha256','triangles')};wall['copyright_metadata_updated_after_geometry_review']=True;wall['approved_geometry_binary_sha256']=original_raw_bin_sha;wpath.write_text(json.dumps(wall,ensure_ascii=False,indent=2)+'\n');(D/'export-clean-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'building':ident,'assets':[{k:r[k] for k in('file','bytes','sha256','triangles')} for r in rows],'native':report['native'],'lod_bounds_delta':delta},indent=2))
