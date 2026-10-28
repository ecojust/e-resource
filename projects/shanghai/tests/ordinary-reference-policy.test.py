#!/usr/bin/env python3
"""Public reference-policy regressions, including actual legacy model assets."""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import struct
import sys
import tempfile
import unittest
import zlib

parser=argparse.ArgumentParser(add_help=False)
parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1])
args,remaining=parser.parse_known_args()
PROJECT=args.project.resolve()
TOOL=Path(__file__).resolve().parents[1]/'tools/ordinary_assets.py'
spec=importlib.util.spec_from_file_location('ordinary_reference_policy',TOOL)
ordinary=importlib.util.module_from_spec(spec);spec.loader.exec_module(ordinary)
ID='reference-policy-fixture'
PREFIX='source/precise/'+ID+'/'

def write(project,name,data):
    path=project/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    return {'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def png(rgb):
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))
            +chunk(b'IDAT',zlib.compress(b'\x00'+bytes(rgb)))+chunk(b'IEND',b''))

def glb(images,mutation=None):
    binary=b'';views=[]
    for data in images:
        binary+=b'\x00'*((-len(binary))%4)
        views.append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data)});binary+=data
    doc={'asset':{'version':'2.0','copyright':'Copyright agent; MIT'},
         'buffers':[{'byteLength':len(binary)}],'bufferViews':views,
         'images':[{'bufferView':i,'mimeType':'image/png'} for i in range(3)],
         'textures':[{'source':i} for i in range(3)],
         'materials':[{'pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicRoughnessTexture':{'index':2}},
                       'normalTexture':{'index':1},'occlusionTexture':{'index':2}}]}
    if mutation:mutation(doc)
    raw=json.dumps(doc,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4)
    binary+=b'\x00'*((-len(binary))%4)
    return (struct.pack('<4sII',b'glTF',2,28+len(raw)+len(binary))
            +struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(binary),0x004e4942)+binary)

class ReferencePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nav=json.loads((PROJECT/'data/landmarks.json').read_bytes())
        cls.registry=json.loads((PROJECT/'data/precise-buildings-v6.json').read_bytes())
        cls.districts={str(d['id']):d['name'] for d in json.loads((PROJECT/'data/districts.json').read_bytes())['districts']}
        cls.legacy=[r for r in cls.nav if r.get('kind')=='building' and r.get('reference_policy')!=ordinary.REMOTE_POLICY]

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='ordinary-reference-policy-')
        self.addCleanup(self.temp.cleanup);self.project=Path(self.temp.name)
        self.row=copy.deepcopy(self.legacy[0]);r=self.row;r['id']=ID
        r['reference_policy']=ordinary.REMOTE_POLICY;r['source_photos']=[]
        r.pop('reference',None);r.pop('photo_texture',None)
        self.register={'schema':'building-reference-register-v1','model_id':ID,'reference_policy':ordinary.REMOTE_POLICY,
                       'references':[{'id':'front','title':'Fixture public reference','url':'https://example.org/front',
                                      'publisher':'Fixture publisher','published_at':'Unknown',
                                      'license_status':'redistribution-permission-not-established','usage':'observation-only',
                                      'redistributed':False,'embedded_as_texture':False}]}
        self.store_register()
        generator=write(self.project,PREFIX+'source/generate.py',b'# Original fixture material generator, MIT\n')
        self.images=[png(c) for c in [(100,90,80),(128,128,255),(220,230,0)]]
        r['material_images']=[]
        for role,data in zip(('basecolor','normal','orm'),self.images):
            r['material_images'].append({**write(self.project,PREFIX+'textures/'+role+'.png',data),
                'role':role,'kind':'procedural_material','embedded_as_texture':True,'license':'MIT',
                'license_url':'https://opensource.org/license/mit','author':'agent',
                'source':'https://example.org/generate.py','limitations':'Synthetic contract fixture, not a building photograph.',
                'pixels':[1,1],'generator':generator})
        r['material_texture']={'mode':'original-procedural-pbr','expected_images':{'raw':3,'web':3,'lod':3}}
        self.store_assets()

    def store_register(self):
        self.row['source_reference_register']=write(self.project,PREFIX+'source-reference-register.json',
                                                    json.dumps(self.register).encode())

    def store_assets(self,mutation=None,images=None):
        r=self.row;r['assets']={}
        for role,key in [('raw','editable_model'),('web','model'),('lod','lod_model'),('native','native_model')]:
            name=('assets/native/precise/' if role=='native' else 'assets/models/precise/')+ID+'/'+role+('.blend' if role=='native' else '.glb')
            meta=write(self.project,name,b'BLENDER-fixture-only' if role=='native' else glb(images or self.images,mutation))
            r['assets'][role]=meta;r[key]=name;r[role+'_bytes']=meta['bytes'];r[role+'_sha256']=meta['sha256']

    def test_actual_legacy_catalog_assets_remain_accepted(self):
        self.assertGreaterEqual(len(self.legacy),18)
        result=ordinary.inspect(PROJECT,self.legacy,self.registry,verify_files=True)
        self.assertTrue({r['id'] for r in self.legacy}<=set(result['records']))

    def test_legacy_missing_photo_still_rejected(self):
        row=copy.deepcopy(self.legacy[0]);row['source_photos']=[]
        with self.assertRaisesRegex(ValueError,'source photos missing'):ordinary.record_contract(row,self.districts)

    def test_legacy_reference_mismatch_still_rejected(self):
        row=copy.deepcopy(self.legacy[0]);row['reference']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'reference does not match'):ordinary.record_contract(row,self.districts)

    def test_unknown_reference_policy_rejected(self):
        self.row['reference_policy']='skip-photos'
        with self.assertRaisesRegex(ValueError,'Unknown ordinary reference policy'):ordinary.record_contract(self.row,self.districts)

    def test_remote_research_and_original_pbr_assets_accepted(self):
        ordinary.record_contract(self.row,self.districts)
        ordinary.verify_assets(self.project,self.row)

    def test_remote_material_cannot_masquerade_as_reference(self):
        self.row['reference']={'image':self.row['material_images'][0]['file']}
        with self.assertRaisesRegex(ValueError,'local reference photograph'):ordinary.record_contract(self.row,self.districts)

    def test_remote_material_cannot_claim_photo_texture(self):
        self.row['photo_texture']={'expected_images':{'raw':3,'web':3,'lod':3}}
        with self.assertRaisesRegex(ValueError,'photographic texture'):ordinary.record_contract(self.row,self.districts)

    def test_remote_material_missing_role_rejected(self):
        self.row['material_images'][2]['role']='normal'
        with self.assertRaisesRegex(ValueError,'roles differ'):ordinary.record_contract(self.row,self.districts)

    def test_remote_register_wrong_identity_rejected(self):
        self.register['model_id']='different';self.store_register()
        with self.assertRaisesRegex(ValueError,'identity differs'):ordinary.verify_assets(self.project,self.row)

    def test_remote_register_cannot_claim_photo_redistribution(self):
        self.register['references'][0]['redistributed']=True;self.store_register()
        with self.assertRaisesRegex(ValueError,'claim redistribution'):ordinary.verify_assets(self.project,self.row)

    def test_remote_register_cannot_bundle_local_photo(self):
        self.register['references'][0]['file']='private/front.jpg';self.store_register()
        with self.assertRaisesRegex(ValueError,'local/image payload'):ordinary.verify_assets(self.project,self.row)

    def test_remote_register_rejects_duplicate_identity(self):
        self.register['references'].append(copy.deepcopy(self.register['references'][0]));self.store_register()
        with self.assertRaisesRegex(ValueError,'Duplicate remote reference'):ordinary.verify_assets(self.project,self.row)

    def test_material_generator_bytes_must_match(self):
        (self.project/self.row['material_images'][0]['generator']['file']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'missing/changed'):ordinary.verify_assets(self.project,self.row)

    def test_actual_material_pixels_must_match_declaration(self):
        self.row['material_images'][0]['pixels']=[2,1]
        with self.assertRaisesRegex(ValueError,'dimensions/format'):ordinary.verify_assets(self.project,self.row)

    def test_glb_embedded_pixels_must_be_declared_originals(self):
        images=list(self.images);images[0]=png((101,90,80));self.store_assets(images=images)
        with self.assertRaisesRegex(ValueError,'original bytes differ'):ordinary.verify_assets(self.project,self.row)

    def test_glb_wrong_pbr_texture_slot_rejected(self):
        self.store_assets(lambda d:d['materials'][0]['normalTexture'].update(index=0))
        with self.assertRaisesRegex(ValueError,'semantic differs'):ordinary.verify_assets(self.project,self.row)

    def test_embedded_but_unused_pbr_images_rejected(self):
        self.store_assets(lambda d:d.update(materials=[]))
        with self.assertRaisesRegex(ValueError,'used in all declared material slots'):ordinary.verify_assets(self.project,self.row)

    def test_missing_orm_occlusion_binding_rejected(self):
        self.store_assets(lambda d:d['materials'][0].pop('occlusionTexture'))
        with self.assertRaisesRegex(ValueError,'used in all declared material slots'):ordinary.verify_assets(self.project,self.row)

    def test_glb_attribution_must_cover_original_material(self):
        self.store_assets(lambda d:d['asset'].update(copyright='Unattributed'))
        with self.assertRaisesRegex(ValueError,'attribution differs'):ordinary.verify_assets(self.project,self.row)

    def test_asset_equal_to_100m_rejected(self):
        self.row['assets']['web']['bytes']=100_000_000
        with self.assertRaisesRegex(ValueError,'byte/SHA declaration'):ordinary.record_contract(self.row,self.districts)

if __name__=='__main__':unittest.main(argv=[sys.argv[0],*remaining])
