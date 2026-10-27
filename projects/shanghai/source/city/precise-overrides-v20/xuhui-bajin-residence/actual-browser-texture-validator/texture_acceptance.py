"""Bind exact served PNG/primitive proof to actual Three materials, including uniform surfaces.

No atlas or photograph assumptions. Mapped surfaces use the frozen original pebble-dash PBR.
Distinct named surfaces may share its exact three maps. REPEAT UVs may exceed [0,1]; physical 0.40m scale is proved statically.
"""
import math,re
from collections import Counter
from helpers import need

SLOTS={'baseColorTexture':'map','normalTexture':'normalMap','metallicRoughnessTexture':'roughnessMap','occlusionTexture':'aoMap'}
ROLES={'baseColorTexture':'basecolor','normalTexture':'normal','metallicRoughnessTexture':'orm','occlusionTexture':'orm'}
FROZEN_MATERIAL_SHA='63c678c23396d988f97bda094537e86d87b69f4542c0e51678bc75570fadd894'

def close(a,b):return isinstance(a,(float,int)) and math.isfinite(a) and abs(a-b)<=1e-6

def vector(a,b):return isinstance(a,list) and len(a)==len(b) and all(close(x,y) for x,y in zip(a,b))

def primitive_key(p,with_uv=True):
    uv=p.get('uv')
    return (p['material'],p['position_count'],p['has_tangent'],p['triangle_count'],
            None if not with_uv or uv is None else (uv['count'],uv['itemSize'],uv['finite'],tuple(round(x,6) for x in uv['bounds'])))

def glazing(name):return bool(re.search('glass|glaz',name,re.I) and not re.search('clock|opal|lamp|frame|mullion|muntin|division|grille|gate|bronze|stone',name,re.I) and not name.startswith('PhotoFacade_'))

def check_images_and_runtime(actual,proof,runtime,record,role,contract,contract_descriptor):
    need(proof['passed'] is True and all(actual[k]==proof[k] for k in ('bytes','sha256')),'Image proof is not for exact served asset')
    need(contract_descriptor['sha256']==FROZEN_MATERIAL_SHA,'Unreviewed original material contract')
    need(all(proof['material_contract'][k]==contract_descriptor[k] for k in ('bytes','sha256')),'Proof material contract differs')
    need(contract['schema']=='bajin-original-pebbledash-pbr-v1' and contract['dimensions_px']==[512,512] and contract['repeat_metres']==[.4,.4],'Wrong physical material contract')
    need(contract['sampler']['wrapS']==contract['sampler']['wrapT']==10497,'Original material must REPEAT')
    files={r['file'].rsplit('-',1)[1].split('.')[0]:r for r in contract['files']}
    need(set(files)=={'basecolor','normal','orm'},'Unexpected original PNG roles')
    images={r['image_index']:r for r in actual['images']};proof_images={r['image_index']:r for r in proof['images']}
    need(len(images)==len(proof_images)==3 and set(images)==set(proof_images),'Exactly three embedded original PNGs required')
    for index,row in images.items():
        need(all(row[k]==proof_images[index][k] for k in ('bytes','mime_type','sha256','decoded_dimensions')),'Decoded PNG proof mismatch')
        need(row['mime_type']=='image/png' and row['decoded_dimensions']==[512,512],'Wrong PNG type or dimensions')
    need({r['sha256'] for r in images.values()}=={r['sha256'] for r in files.values()},'Original PNG fingerprint set changed')
    need(Counter(primitive_key(p) for p in actual['primitives'])==Counter(primitive_key(p) for p in proof['primitives']),'Served primitive/UV proof differs')
    source={m['name']:m for m in actual['modelMaterials']}
    need(len(source)==len(actual['modelMaterials']),'Duplicate source material names')
    used={p['material'] for p in actual['primitives']}
    need(used<=set(source),'Primitive refers to absent material')
    expected_maps={};usage=set();textured=[]
    for name,m in source.items():
        pbr=m.get('pbrMetallicRoughness',{});slots={**pbr,**{k:v for k,v in m.items() if k!='pbrMetallicRoughness'}}
        active={s for s in SLOTS if s in slots}
        need(not m.get('emissiveTexture') and not m.get('extensions'),'Unexpected material shader extension or emissive image')
        if not active:
            expected_maps[name]=set();continue
        textured.append(name);need(active==set(SLOTS),'Pebble material requires all four PBR texture slots')
        need(vector(pbr.get('baseColorFactor',[1,1,1,1]),contract['baseColorFactor']) and close(pbr.get('roughnessFactor',1),contract['roughnessFactor']) and close(pbr.get('metallicFactor',1),contract['metallicFactor']),'Pebble PBR factors differ')
        need(close(m['normalTexture'].get('scale',1),contract['normalScale']) and close(m['occlusionTexture'].get('strength',1),contract['occlusionStrength']),'Pebble normal/AO factors differ')
        need(all(not p['has_tangent'] for p in actual['primitives'] if p['material']==name),'Frozen pebble normal contract requires no TANGENT')
        expected_maps[name]=set(SLOTS.values())|{'metalnessMap'}
        for slot in SLOTS:
            info=slots[slot];need(info.get('texCoord',0)==0 and not info.get('extensions'),'Expected untransformed TEXCOORD_0')
            texture=actual['modelTextures'][info['index']];image=images[texture['source']]
            need(image['sha256']==files[ROLES[slot]]['sha256'] and image['bytes']==files[ROLES[slot]]['bytes'],'Wrong PNG assigned to '+slot)
            sampler=actual['modelSamplers'][texture['sampler']] if 'sampler' in texture else {}
            defaults={'wrapS':10497,'wrapT':10497,'magFilter':9729,'minFilter':9987}
            need(all(sampler.get(k,defaults[k])==v for k,v in contract['sampler'].items()),'Effective sampler differs from frozen REPEAT contract')
            usage.add((image['image_index'],name,slot,0))
    proven={(r['image_index'],u['material'],u['slot'],u['texcoord']) for r in proof['images'] for u in r['usages']}
    need(textured and set(textured)=={u[1] for u in proven},'Mapped material names differ from exact final proof')
    need(proven==usage,'Independent PNG usage set differs from actual GLB')
    need(runtime['rootFound'] and runtime['traverseRestored'],'Runtime imported root unavailable or observer not restored')
    rows=runtime['materials'];need(rows and {r['material'] for r in rows}==used,'Actual material coverage differs')
    need(Counter(primitive_key(r,False) for r in rows)==Counter(primitive_key(p,False) for p in actual['primitives']),'Actual loaded primitive/material inventory differs')
    glass_count=0
    for row in rows:
        name=row['material'];m=source[name];pbr=m.get('pbrMetallicRoughness',{});factor=pbr.get('baseColorFactor',[1,1,1,1])
        color=factor[:3];roughness=pbr.get('roughnessFactor',1);metalness=pbr.get('metallicFactor',1)
        need(row['material_type']=='MeshStandardMaterial' and close(row['opacity'],factor[3]),'Actual material type/opacity differs')
        need(set(row['map_slots'])==expected_maps[name],'Actual material texture residency differs')
        if glazing(name):
            color=[v*.78 for v in color];roughness=max(.16,min(.30,roughness));metalness=min(metalness,.12);glass_count+=1
            env=row['envMap'];need(close(row['envMapIntensity'],1.05) and env and env['isTexture'] and env['shared'] and env['owner']=='realistic-lighting' and env['name'] in ('Shanghai Riverside photographic glazing reflection','Shared Bund glazing sky'),'Frozen glazing reflection missing')
        need(vector(row['color'],color) and close(row['roughness'],roughness) and close(row['metalness'],metalness),'Actual source material factors/frozen glazing override differ: '+name)
    observed=set();uv_evidence=[]
    for row in runtime['maps']:
        name=row['material'];slot=row['slot'];need(name in textured and slot in expected_maps[name],'Unexpected actual map')
        observed.add((name,slot))
        need(row['isTexture'] and row['decoded_dimensions']==[512,512],'Actual map is not decoded')
        need(row['channel']==0 and row['wrapS']==row['wrapT']==1000 and row['flipY'] is False,'Actual REPEAT/channel/flip differs')
        need(row['magFilter']==1006 and row['minFilter']==1008,'Actual linear/trilinear sampling differs')
        need(row['colorSpace']==('srgb' if slot=='map' else ''),'Actual PBR color space differs')
        need(row['transform_finite'] and vector(row['repeat'],[1,1]) and vector(row['offset'],[0,0]) and close(row['rotation'],0),'Unexpected map transform')
        need(vector(row['normalScale'],[contract['normalScale'],-contract['normalScale']]) and not row['has_tangent'],'Actual derivative-frame normal orientation differs')
        need(close(row['aoMapIntensity'],contract['occlusionStrength']),'Actual AO intensity differs')
        uv=row['uv'];need(uv and uv['finite'] and uv['itemSize']==2 and uv['count']==row['position_count'],'Actual finite per-vertex UV missing')
        need(any(p['material']==name and p['position_count']==row['position_count'] and p['uv'] and vector(p['uv']['bounds'],uv['bounds']) for p in actual['primitives']),'Loaded UV bounds differ from served decoded primitive')
        uv_evidence.append({'mesh':row['mesh'],'material':name,'slot':slot,'uv':uv})
    need(observed=={(n,s) for n,ss in expected_maps.items() for s in ss},'Actual PBR map slots incomplete')
    return {'passed':True,'material_contract':contract_descriptor,'embedded_png_count':3,'textured_materials':textured,
            'uniform_materials':sorted(used-set(textured)),'runtime_glazing_primitive_count':glass_count,
            'actual_uvs':uv_evidence,'scope':'Exact served images and decoded primitive proof; actual loaded PBR and uniform materials. Repeat UV bounds may exceed [0,1]. Physical 0.40m scale is inherited from exact static primitive proof, not inferred from a screenshot.'}
