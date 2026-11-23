"""Produce both meshopt web roles and compare decoded geometry, UVs and embedded raster bytes."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import os
import shutil
import struct
import subprocess
import tempfile

def sha(data):
    return hashlib.sha256(data).hexdigest()

def chunks(path):
    buf=path.read_bytes()
    if buf[:4]!=b'glTF' or struct.unpack_from('<I',buf,8)[0]!=len(buf):
        raise ValueError('Invalid GLB container')
    size=struct.unpack_from('<I',buf,12)[0]
    return json.loads(buf[20:20+size]),buf[28+size:]

def store(path,doc,binary):
    text=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode()
    text+=b' '*((-len(text))%4);binary+=b'\0'*((-len(binary))%4)
    path.write_bytes(struct.pack('<4sIIII',b'glTF',2,28+len(text)+len(binary),len(text),0x4e4f534a)+text+
                     struct.pack('<II',len(binary),0x004e4942)+binary)

def fingerprints(path):
    doc,data=chunks(path)
    def accessor(i,n):
        a=doc['accessors'][i]
        view=doc['bufferViews'][a['bufferView']]
        fmt=struct.Struct('<'+{5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']]*n)
        offset=view.get('byteOffset',0)+a.get('byteOffset',0)
        stride=view.get('byteStride',fmt.size)
        return [fmt.unpack_from(data,offset+j*stride) for j in range(a['count'])]
    result=collections.defaultdict(list);mats={}
    for primitive in doc['meshes'][0]['primitives']:
        p=primitive['attributes']
        verts=accessor(p['POSITION'],3)
        uv=accessor(p['TEXCOORD_0'],2) if 'TEXCOORD_0' in p else [()] * len(verts)
        indices=accessor(primitive['indices'],1)
        material=doc['materials'][primitive['material']]
        name=material['name'];pbr=material.get('pbrMetallicRoughness',{})
        numerical=dict(baseColorFactor=pbr.get('baseColorFactor',[1,1,1,1]),
                       roughnessFactor=pbr.get('roughnessFactor',1),metallicFactor=pbr.get('metallicFactor',1))
        if 'baseColorTexture' in pbr:
            tex=doc['textures'][pbr['baseColorTexture']['index']]
            view=doc['bufferViews'][doc['images'][tex['source']]['bufferView']]
            start=view.get('byteOffset',0)
            numerical['image_sha256']=sha(data[start:start+view['byteLength']])
            sampler=doc.get('samplers',[{}])[tex.get('sampler',0)]
            numerical['wrap']=[sampler.get(key,10497) for key in ('wrapS','wrapT')]
        for field in ('roughnessFactor','metallicFactor'):
            numerical[field]=struct.unpack('<f',struct.pack('<f',numerical[field]))[0]
        numerical['baseColorFactor']=list(struct.unpack('<4f',struct.pack('<4f',*numerical['baseColorFactor'])))
        mats[name]=numerical
        corners=[tuple(0. if x==0 else x for x in (*v,*w)) for v,w in zip(verts,uv)]
        for start in range(0,len(indices),3):
            tri=tuple(corners[e[0]] for e in indices[start:start+3])
            result[name].append(min(tri,tri[1:]+tri[:1],tri[2:]+tri[:2]))
    return {name:dict(triangles=len(rows),xyz_uv_sha256=sha(json.dumps(sorted(rows),separators=(',',':')).encode()),**mats[name]) for name,rows in sorted(result.items())}

def run(src,out,audit,project,gltfpack):
    key='changning-xinhua-231-rong-garden-roof'
    out.mkdir(parents=True,exist_ok=True);audit.mkdir(parents=True,exist_ok=True)
    decoder=project/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    module=project/'vendor/meshopt_decoder.module.js'
    roles={};reports=[]
    def asset(p,n):
        return dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p.read_bytes()),triangles=n)
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        for role,suffix in [('full','web'),('lod','lod')]:
            old=src/(role+'-source.glb');encoded=Path(tmp)/(key+'-'+suffix+'.glb')
            subprocess.run([gltfpack,'-i',old,'-o',encoded,'-cc','-noq','-vnf','-km','-kn','-ke'],check=True)
            orig,_=chunks(old);web,blob=chunks(encoded)
            web['asset']['copyright']=orig['asset']['copyright'];web['extras']=orig['extras']
            store(encoded,web,blob)
            decoded=Path(tmp)/('decoded-'+role+'.glb')
            subprocess.run(['node',decoder,encoded,decoded,module],check=True)
            original=fingerprints(old)
            actual=fingerprints(decoded)
            if actual!=original:
                print({name:(expected,actual.get(name)) for name,expected in original.items() if actual.get(name)!=expected},flush=True)
                raise ValueError(f'Triangle, UV, material or image mismatch in {role}')
            assert chunks(decoded)[0]['extras']==orig['extras']
            n=sum(v['triangles']for v in original.values())
            assetpath=out/encoded.name;shutil.copyfile(encoded,assetpath);roles[role]=asset(assetpath,n)
            if role=='full':
                raw=out/(key+'-raw.glb');shutil.copyfile(old,raw);roles['raw']=asset(raw,n)
            reports.append(dict(role=role,source=asset(old,n),encoded=roles[role],decoded=asset(decoded,n),materials=original))
    (audit/'encoded-and-decoded.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
    (out/'manifest.json').write_text(json.dumps(dict(**orig['extras'],model_id=key,assets=roles),indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for key in ('src','out','audit','project'):ap.add_argument(key,type=Path)
    ap.add_argument('--gltfpack',default=os.environ.get('GLTFPACK','gltfpack'))
    args=ap.parse_args()
    run(args.src,args.out,args.audit,args.project,args.gltfpack)
