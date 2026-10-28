"""Ordinary asset/catalog contracts; no network, rewriting or acceptance decisions.

The registration's reviewed acceptance hashes are declarations, not a substitute
for its separate photographic/browser evidence audit. Candidates never enter an
active catalog. --candidate-only permits an explicitly marked static QA entry.
"""
import hashlib
import json
import re
import struct
from pathlib import PurePosixPath
from urllib.parse import urlsplit

LIMIT=100_000_000
CHECKS=('source_photos','identity_footprint','height_evidence','visible_facade_opening_grid','roof','texture_mapping_qa','geometry_proof','size_proof','browser_proof','uncertainty')
SHA=re.compile(r'^[a-f0-9]{64}$')
REMOTE_POLICY='remote-research-only-v1'
MATERIAL_ROLES={'basecolor','normal','orm'}
def require(value,message):
    if not value:raise ValueError(message)
def digest(data):return hashlib.sha256(data).hexdigest()
def path(value):
    require(isinstance(value,str) and value and not any(c in value for c in '\\:%?#\x00') and not any(ord(c)<32 or ord(c)==127 for c in value),'Unsafe ordinary path')
    p=PurePosixPath(value)
    require(not p.is_absolute() and p.as_posix()==value and all(c not in ('','.','..') for c in value.split('/')),'Unsafe ordinary path')
    return value
def url(value):
    u=urlsplit(value);require(u.scheme in ('https','http') and u.hostname and not u.username and not u.password,'Explicit public provenance URL required')
def descriptor(meta):
    require(isinstance(meta,dict) and type(meta.get('bytes')) is int and 0<meta['bytes']<LIMIT and isinstance(meta.get('sha256'),str) and SHA.fullmatch(meta['sha256']),'Invalid ordinary byte/SHA declaration')
    return path(meta.get('file'))
def read(project,meta):
    name=descriptor(meta);p=project/name
    require(p.is_file() and p.stat().st_size==meta['bytes'],'Ordinary asset missing/changed: '+name)
    data=p.read_bytes();require(digest(data)==meta['sha256'],'Ordinary asset SHA differs: '+name);return data

def remote_reference_contract(row):
    """Explicit alternative to a redistributed photograph; never substitutes a material sample."""
    ident=row['id'];prefix='source/precise/'+ident+'/'
    require(row.get('reference_policy')==REMOTE_POLICY,'Unknown ordinary reference policy')
    require(row.get('source_photos')==[] and 'reference' not in row,
            'Remote research must not declare a local reference photograph')
    register=row.get('source_reference_register',{})
    require(descriptor(register)==prefix+'source-reference-register.json','Remote reference register must be model-local')
    images=row.get('material_images')
    require(isinstance(images,list) and len(images)==3,'Original PBR requires three material images')
    require({p.get('role') for p in images}==MATERIAL_ROLES,'Original PBR material roles differ')
    require(len({p.get('file') for p in images})==3 and len({p.get('sha256') for p in images})==3,
            'Original PBR material images must be distinct')
    for image in images:
        require(descriptor(image).startswith(prefix+'textures/') and image['file'].endswith('.png'),
                'Original material image must be a model-local PNG')
        require(image.get('kind')=='procedural_material' and image.get('embedded_as_texture') is True
                and image.get('license')=='MIT','Original material identity/license must be explicit')
        require(all(isinstance(image.get(k),str) and image[k].strip() for k in
                    ('author','license_url','source','limitations')),'Original material provenance incomplete')
        url(image['license_url']);url(image['source'])
        require(descriptor(image.get('generator',{})).startswith(prefix+'source/')
                and image['generator']['file'].endswith('.py'),'Original material requires its public generator')
        require(isinstance(image.get('pixels'),list) and len(image['pixels'])==2
                and all(type(v)is int and 0<v<=4096 for v in image['pixels']),'Invalid material pixel dimensions')
    texture=row.get('material_texture',{})
    require(texture.get('mode')=='original-procedural-pbr'
            and texture.get('expected_images')=={'raw':3,'web':3,'lod':3},'Original material image-count contract differs')
    require('photo_texture' not in row,'Remote research must not be represented as photographic texture')

def verify_reference_register(project,row):
    register=json.loads(read(project,row['source_reference_register']))
    require(register.get('schema')=='building-reference-register-v1'
            and register.get('model_id')==row['id'] and register.get('reference_policy')==REMOTE_POLICY,
            'Remote reference register identity differs')
    refs=register.get('references')
    require(isinstance(refs,list) and 0<len(refs)<=32,'Remote reference register is empty or oversized')
    ids=set()
    for item in refs:
        require(all(isinstance(item.get(k),str) and item[k].strip() for k in
                    ('id','title','url','publisher','published_at','license_status','usage')),
                'Remote research reference incomplete')
        require(item['id'] not in ids,'Duplicate remote reference ID');ids.add(item['id']);url(item['url'])
        require(item['license_status']=='redistribution-permission-not-established'
                and item['usage']=='observation-only' and item.get('redistributed') is False
                and item.get('embedded_as_texture') is False,'Remote research must not claim redistribution or embedding')
        require(not any(k in item for k in ('file','path','image','image_data','blob')),
                'Remote research register cannot contain local/image payload references')
    return register

def record_contract(row,districts,*,candidate_only=False):
    ident=row.get('id');require(isinstance(ident,str) and re.fullmatch('[a-z0-9][a-z0-9-]{0,95}',ident),'Invalid ordinary ID')
    require(row.get('kind')=='building' and row.get('detail_level')=='architectural' and not row.get('candidate_id') and not row.get('bund_number'),'Ordinary building must not pretend to be Bund')
    require(isinstance(row.get('source_provider'),str) and row['source_provider'].strip(),'Missing ordinary provider');url(row.get('source_url',''))
    district=row.get('district',{});require(districts.get(str(district.get('id')))==district.get('name') and row.get('districtId')==district.get('id') and row.get('district_name')==district.get('name'),'Explicit ordinary district differs')
    for field in ('source_license','asset_license'):
        licenses=row.get(field);require(isinstance(licenses,list) and licenses,'Missing explicit '+field)
        for item in licenses:
            require(all(isinstance(item.get(k),str) and item[k].strip() for k in ('id','url','attribution','role')),'Incomplete ordinary license attribution');url(item['url'])
    require(set(row.get('acceptance',{}))==set(CHECKS) and all(row['acceptance'][k].get('status') in ('passed','pending','failed') for k in CHECKS),'All ordinary acceptance stages must be explicit')
    accepted=row.get('accepted') is True and row.get('pending_stages')==[] and all(row.get('acceptance',{}).get(k,{}).get('status')=='passed' for k in CHECKS)
    require(accepted and not row.get('candidate_only') and row.get('browser_passed') is not False or candidate_only and row.get('accepted') is False and row.get('candidate_only') is True,'Ordinary building is not accepted; candidate-only mode is for isolated static QA only')
    if accepted:
        for k in CHECKS:
            evidence=row['acceptance'][k]
            require(SHA.fullmatch(str(evidence.get('evidence_sha256',''))) and type(evidence.get('evidence_bytes')) is int and evidence['evidence_bytes']>0 and evidence.get('scope'),'Accepted stage lacks registered evidence binding: '+k)
    assets=row.get('assets',{});require(set(assets)=={'raw','web','lod','native'},'Ordinary assets require raw/web/LOD/native')
    for role,key in (('raw','editable_model'),('web','model'),('lod','lod_model'),('native','native_model')):
        a=assets[role];name=descriptor(a);prefix='assets/native/precise/' if role=='native' else 'assets/models/precise/'
        require(name.startswith(prefix) and row.get(key)==name and row.get(role+'_bytes')==a['bytes'] and row.get(role+'_sha256')==a['sha256'],'Ordinary role path/SHA alias differs: '+role)
        require(name.endswith('.blend') if role=='native' else name.endswith('.glb'),'Ordinary asset suffix differs')
    require(len({a['file'] for a in assets.values()})==4,'Ordinary assets alias each other')
    require(type(row.get('lod_triangles')) is int and row['lod_triangles']>0 and 0<row.get('lod_switch_in_m',0)<row.get('lod_switch_out_m',0),'Missing ordinary LOD budget/hysteresis')
    owner=row.get('owner',{});ids=owner.get('baseline_near_feature_local_ids',[]);target=owner.get('feature_local_id')
    require(type(target)is int and target>0 and ids and len(ids)==len(set(ids)) and owner.get('replace_only_local_ids')==[target] and set(owner.get('preserve_neighbor_local_ids',[]))==set(ids)-{target},'Incomplete exact ordinary ownership/neighbor partition')
    require(re.fullmatch(r'building:[a-f0-9-]{36}',owner.get('feature_key','')) and re.fullmatch(r'\d+-\d+-\d+',owner.get('macro_id','')),'Invalid ordinary macro/source owner')
    for field in ('baseline_configuration_sha256','baseline_ready_sha256','baseline_feature_table_sha256','baseline_near_sha256'):
        require(SHA.fullmatch(str(owner.get(field,''))),'Missing ordinary baseline hash: '+field)
    if row.get('reference_policy')==REMOTE_POLICY:
        remote_reference_contract(row)
    else:
        require(row.get('reference_policy') in (None,'local-licensed-reference-v1'),'Unknown ordinary reference policy')
        photos=row.get('source_photos');require(isinstance(photos,list) and photos,'Ordinary source photos missing')
        for photo in photos:
            require(descriptor(photo).startswith('assets/references/precise/') and type(photo.get('embedded_as_texture')) is bool,'Invalid ordinary source photograph')
            require(all(photo.get(k) for k in ('author','license','license_url','source')),'Incomplete ordinary photograph provenance');url(photo['license_url']);url(photo['source'])
        reference=row.get('reference',{});require(any(p['file']==reference.get('image') and all(p.get(k)==reference.get(k) for k in ('author','license','license_url','source','sha256')) for p in photos),'Ordinary reference does not match a declared original photograph')
    return accepted

def bind(row,registry):
    owner=row['owner'];matches=[]
    for macro in registry.get('macros',[]):
        for near in macro.get('near',[]):
            for group in near.get('groups',[]):
                if group.get('landmark_id')==row['id']:matches.append((macro,near,group))
    require(len(matches)==1,'Ordinary target must own one complete replacement group')
    macro,near,group=matches[0]
    for field in ('baseline_configuration_sha256','baseline_ready_sha256','baseline_feature_table_sha256'):
        require(macro.get(field)==owner.get(field),'Ordinary macro provenance hash differs: '+field)
    require(macro['id']==owner['macro_id'] and near['id']==owner['near_owner_id'] and near['baseline_sha256']==owner['baseline_near_sha256'] and near['featureLocalIds']==owner['baseline_near_feature_local_ids'] and group['local_ids']==owner['replace_only_local_ids'] and group['feature_keys']==[owner['feature_key']],'Ordinary replacement binding differs from exact owner')
    boundaries=[b for b in registry.get('landmarks',[]) if b['id']==row['id']]
    require(len(boundaries)==1 and boundaries[0]['confirmed_boundary']==row['confirmed_boundary'] and boundaries[0]['building_ids']==[owner['feature_key'][9:]] and boundaries[0]['building_part_ids']==[],'Ordinary source footprint/UUID differs')

def glb_images(data):
    require(len(data)>=20 and struct.unpack_from('<4sII',data)==(b'glTF',2,len(data)),'Invalid ordinary GLB')
    n,kind=struct.unpack_from('<II',data,12);require(kind==0x4e4f534a and n<=len(data)-20,'Invalid ordinary GLB JSON')
    doc=json.loads(data[20:20+n]);binary=b'';offset=20+n
    while offset+8<=len(data):
        length,kind=struct.unpack_from('<II',data,offset);offset+=8;require(offset+length<=len(data),'Invalid GLB chunk')
        if kind==0x004e4942:binary=data[offset:offset+length]
        offset+=length
    require(all('uri' not in r for r in doc.get('buffers',[])+doc.get('images',[])),'Ordinary GLB external image/buffer is not permitted')
    images=[]
    for image in doc.get('images',[]):
        view=doc['bufferViews'][image['bufferView']];a=view.get('byteOffset',0);b=a+view['byteLength'];require(0<=a<b<=len(binary),'Invalid embedded image');images.append(digest(binary[a:b]))
    return doc,images

def verify_assets(project,row):
    remote=row.get('reference_policy')==REMOTE_POLICY
    if remote:
        verify_reference_register(project,row)
        for p in row['material_images']:
            data=read(project,p);read(project,p['generator'])
            require(data[:8]==b'\x89PNG\r\n\x1a\n' and len(data)>=29 and data[12:16]==b'IHDR'
                    and list(struct.unpack_from('>II',data,16))==p['pixels'] and data[24]==8 and data[25] in (2,6),
                    'Original material PNG dimensions/format differ')
        embedded={p['sha256']:p for p in row['material_images']}
    else:
        for p in row['source_photos']:read(project,p)
        embedded={p['sha256']:p for p in row['source_photos'] if p['embedded_as_texture']}
    for role,a in row['assets'].items():
        data=read(project,a)
        if role=='native':continue # Native bytes are exact; Blender geometry was reviewed separately.
        doc,images=glb_images(data)
        expected=row.get('material_texture' if remote else 'photo_texture',{}).get('expected_images',{}).get(role)
        require(type(expected)is int and len(images)==expected and set(images)<=set(embedded),'Ordinary embedded image count/original bytes differ: '+role)
        if remote:
            require(set(images)==set(embedded),'Original PBR must embed each of its three declared images')
            used_slots=set()
            for material in doc.get('materials',[]):
                slots=[('basecolor','baseColorTexture',material.get('pbrMetallicRoughness',{}).get('baseColorTexture')),
                       ('normal','normalTexture',material.get('normalTexture')),
                       ('orm','metallicRoughnessTexture',material.get('pbrMetallicRoughness',{}).get('metallicRoughnessTexture')),
                       ('orm','occlusionTexture',material.get('occlusionTexture'))]
                for semantic,slot_name,slot in slots:
                    if slot is not None:
                        image=doc['textures'][slot['index']]['source']
                        require(embedded[images[image]]['role']==semantic,'Original PBR texture semantic differs')
                        used_slots.add(slot_name)
            require(used_slots=={'baseColorTexture','normalTexture','metallicRoughnessTexture','occlusionTexture'},
                    'Original PBR images must be used in all declared material slots')
        copyright=doc.get('asset',{}).get('copyright','');token=re.sub('[^a-z0-9]','',copyright.lower())
        for image in images:
            photo=embedded[image];require(photo['author'] in copyright and re.sub('[^a-z0-9]','',photo['license'].lower()) in token,'Ordinary GLB attribution differs')

def inspect(project,landmarks,registry,*,candidate_only=False,verify_files=True):
    districts={str(d['id']):d['name'] for d in json.loads((project/'data/districts.json').read_bytes())['districts']}
    records={};immutable={};registries=[registry];catalog=None
    def register(row,reg,allow_candidate):
        record_contract(row,districts,candidate_only=allow_candidate);bind(row,reg)
        old=records.get(row['id']);require(old is None or old==row,'Static/catalog ordinary declarations differ')
        if old is None and verify_files:verify_assets(project,row)
        records[row['id']]=row
    for row in landmarks:
        if row.get('kind')=='building':register(row,registry,candidate_only)
    descriptor_=registry.get('ordinary_catalog')
    if descriptor_:
        name=descriptor(descriptor_);require(name.startswith('data/precise-buildings/') and descriptor_['bytes']<8*1024*1024,'Invalid/big catalog JSON');raw=read(project,descriptor_);immutable[name]=raw;catalog=json.loads(raw)
        require(catalog.get('schema')=='precise-building-catalog-v1' and catalog.get('url_base')=='project-root' and catalog.get('macro_count')==len(catalog.get('macros',[])),'Invalid ordinary catalog')
        macro_ids=set();catalog_ids=set();total=0
        for entry in catalog['macros']:
            require(entry['id'] not in macro_ids,'Duplicate ordinary macro');macro_ids.add(entry['id']);name=descriptor(entry);require(name.startswith('data/precise-buildings/') and entry['bytes']<8*1024*1024,'Invalid/big macro JSON');raw=read(project,entry);immutable[name]=raw;index=json.loads(raw)
            require(index.get('schema')=='precise-building-macro-v1' and index.get('macro_id')==entry['id'] and index.get('record_count')==entry['record_count']==len(index.get('models',[])) and index.get('url_base')=='project-root','Ordinary macro index/count differs')
            ref=index.get('replacement_registry');name=descriptor(ref);require(name.startswith('data/precise-buildings/') and ref['bytes']<8*1024*1024,'Invalid/big registry JSON');raw=read(project,ref);require(name not in immutable or immutable[name]==raw,'Conflicting catalog JSON');immutable[name]=raw;reg=json.loads(raw)
            require(reg.get('schema')=='city-precise-overrides-v1' and reg.get('complete') is True and len(reg.get('macros',[]))==1 and reg['macros'][0]['id']==entry['id'],'Audited single-macro registry missing')
            registries.append(reg)
            for row in index['models']:
                require(row['id'] not in catalog_ids and row['owner']['macro_id']==entry['id'],'Duplicate or cross-macro ordinary record');catalog_ids.add(row['id']);register(row,reg,False);total+=1
        require(total==catalog.get('record_count'),'Ordinary catalog total differs')
    return {'records':records,'catalog':catalog,'immutable':immutable,'registries':registries}
