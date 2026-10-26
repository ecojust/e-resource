#!/usr/bin/env python3
"""Compress staging variants, retain original JPEG bytes and verify preservation."""
from pathlib import Path
import sys,json,hashlib,struct,subprocess,collections,importlib.util,argparse,numpy as np
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--project',required=True);ap.add_argument('--baseline-raw');ap.add_argument('--gltfpack',required=True);args=ap.parse_args();R=Path(args.project).resolve();RAW=Path(args.baseline_raw) if args.baseline_raw else R/'assets/models/bund/bund12.glb';BASE=json.loads((P/'baseline-source.json').read_text());assert hashlib.sha256(RAW.read_bytes()).hexdigest()==BASE['assets']['raw']['sha256'], 'Use pinned baseline raw from baseline-source.json with --baseline-raw'
spec=importlib.util.spec_from_file_location('lod_checks',R/'tools/build_bund_lods.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
source=json.loads((P/'photo-source.json').read_text());credit=f"Photographic six-window samples: {source['author']} (2025-05-01), CC0-1.0. {source['source_page']} ; {source['license_url']}. Building geometry retains existing project attribution; dimensions are photo-derived estimates."
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rewrite(p):
 j,b=mod.read_glb(p);j['asset']['copyright']=credit;j['asset']['extras']={'photo_sha256':source['sha256'],'photo_scope':'Six individual recessed windows only','lod_has_photo':False} if not j.get('images') else{'photo_sha256':source['sha256'],'photo_original_bytes_embedded':True,'photo_scope':'Six individual recessed windows only'}
 s=json.dumps(j,separators=(',',':'),ensure_ascii=False).encode();s+=b' '*((-len(s))%4);b+=b'\0'*((-len(b))%4);p.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(s)+len(b))+struct.pack('<II',len(s),0x4e4f534a)+s+struct.pack('<II',len(b),0x004e4942)+b)
for n in ['bund12-photo-raw.glb','bund12-geometry-lod-source.glb']:rewrite(P/n)
commands=[]
for src,dst,opts in [('bund12-photo-raw.glb','bund12-photo-web.glb',[]),('bund12-geometry-lod-source.glb','bund12-geometry-lod.glb',['-si','0.35','-se','0.002','-sp'])]:
 cmd=[args.gltfpack,'-i',str(P/src),'-o',str(P/dst),*opts,'-cc','-noq','-km','-ke'];subprocess.run(cmd,check=True);rewrite(P/dst);commands.append({'source':src,'target':dst,'options':[*opts,'-cc','-noq','-km','-ke']})
G=json.loads((R/'source/bund/classical_bank/geometry-input.json').read_text())['bund12']; C=json.loads((P/'calibration.json').read_text())['windows']
def triangle_multiset(p,exclude_materials,skip_selected=False):
 j,b=mod.read_glb(p);result=collections.defaultdict(collections.Counter)
 def visit(idx,par):
  n=j['nodes'][idx];M=par@mod.node_matrix(n)
  if 'mesh' in n:
   for prim in j['meshes'][n['mesh']]['primitives']:
    name=j['materials'][prim.get('material',0)]['name']
    if name in exclude_materials:continue
    vs=mod.accessor_values(j,b,prim['attributes']['POSITION']);vs=(vs@M[:3,:3].T)+M[:3,3];ix=mod.accessor_values(j,b,prim['indices']).reshape(-1);ts=vs[ix].reshape(-1,3,3)
    for t in ts:
     if skip_selected and name in ('Recessed reflecting glazing','Bronze window framing'):
      # GLB east/up/south -> baseline Blender east/north/up -> architectural frame.
      bx=t[:,0];by=-t[:,2];zz=t[:,1];u=G['world_basis_u'];v=G['world_basis_v'];fc=G['front_center'];xx=bx*u[0]+by*u[1]-fc[0];yy=bx*v[0]+by*v[1]-fc[1];selected=False
      for w in C:
       cx=12.7+(w['bay']+.5)*(G['front_width']-25.4)/14;z0,z1,width=(19.6,22.7,1.95) if w['level']==3 else(13.8,17.9,2.2)
       if np.all(xx>=cx-width/2-1e-4) and np.all(xx<=cx+width/2+1e-4) and np.all(zz>=z0-1e-4) and np.all(zz<=z1+1e-4) and np.all(yy>.2) and np.all(yy<.65):selected=True;break
      if selected:continue
     result[name][tuple(sorted(tuple(float(x) for x in v) for v in np.round(t,5)))]+=1
  for c in n.get('children',[]):visit(c,M)
 for i in j['scenes'][j.get('scene',0)]['nodes']:visit(i,np.eye(4))
 return result
ex={'Recessed reflecting glazing','Bronze window framing','PhotoFacade_Bund12_Glazing_OriginalPhoto','PhotoFacade_Bund12_Glass_Edge','PhotoFacade_Bund12_Measured_Casement_Bronze'}
a=triangle_multiset(RAW,ex);b=triangle_multiset(P/'bund12-photo-raw.glb',ex)
assert a==b,'A non-window structural triangle changed in actual exported raw GLB'
full_ex={x for x in ex if x.startswith('PhotoFacade_')}
full_a=triangle_multiset(RAW,full_ex,True);full_b=triangle_multiset(P/'bund12-photo-raw.glb',full_ex,False);assert full_a==full_b,'An unselected original glass/frame or structural triangle changed'
assets=[]
for name in ['bund12-photo-raw.glb','bund12-photo-web.glb','bund12-geometry-lod-source.glb','bund12-geometry-lod.glb']:
 p=P/name;j,b=mod.read_glb(p);row={'file':name,'bytes':p.stat().st_size,'sha256':sha(p),'images':len(j.get('images',[])),'textures':len(j.get('textures',[])),'triangles':sum(j['accessors'][pr['indices']]['count']//3 for m in j['meshes'] for pr in m['primitives']),'copyright':j['asset']['copyright'],'embedded_image_sha256':[]}
 assert row['bytes']<100_000_000
 for im in j.get('images',[]):
  bv=j['bufferViews'][im['bufferView']];ib=b[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']];h=hashlib.sha256(ib).hexdigest();assert h==source['sha256'];row['embedded_image_sha256'].append(h)
 if 'geometry-lod' in name:
  assert not j.get('images') and not j.get('textures');glass=[m for m in j['materials'] if m['name']=='Bund12_Distant_Geometric_Glazing'];assert len(glass)==1;assert np.allclose(glass[0]['pbrMetallicRoughness']['baseColorFactor'][:3],[.075,.14,.16],atol=1e-7,rtol=0)
 else:assert row['images']==row['textures']==1
 # Full compressed model keeps FLOAT32 POSITION/NORMAL, with no mesh quantization.
 assert 'KHR_mesh_quantization' not in j.get('extensionsUsed',[])
 for m in j['meshes']:
  for pr in m['primitives']:
   assert all(j['accessors'][pr['attributes'][attr]]['componentType']==5126 for attr in ('POSITION','NORMAL'))
 bounds,tris,prims=mod.measure(p,source=('source' in name or 'raw' in name));row.update(bounds_xyz_m=bounds.tolist(),rendered_triangles=tris,primitives=prims);assets.append(row)
raw=assets[0];web=assets[1];lod=assets[3];assert raw['rendered_triangles']==web['rendered_triangles'];delta=float(np.max(np.abs(np.array(raw['bounds_xyz_m'])-np.array(lod['bounds_xyz_m']))));assert delta<.35
report={'schema_version':'bund12-photo-export-validation-v1','status':'passed','browser_test_performed':False,'raw_preserved_structural_triangles_by_material':{k:sum(v.values()) for k,v in a.items()},'raw_non_glass_non_frame_triangles_identical_at_10micrometre_resolution':True,'native_exact_preservation_report':'model-validation.json','all_unselected_original_triangles_identical_at_10micrometre_resolution':True,'all_unselected_original_triangle_count':sum(sum(v.values()) for v in full_a.values()),'texture_single_shared_original_jpeg':True,'photo_lod_absent':True,'photo_gpu_mip_estimate_bytes':5184*3456*4*4//3,'full_web_preserves_float32_position_normal':True,'lod_maximum_bounds_change_m':delta,'compression_commands':commands,'assets':assets}
(P/'export-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
