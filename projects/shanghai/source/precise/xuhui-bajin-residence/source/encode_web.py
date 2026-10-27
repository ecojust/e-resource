#!/usr/bin/env python3
"""Portable Ba Jin WEB/LOD encoding; reads only supplied GLBs and gltfpack.
Copyright agent, MIT. This reports artifacts, not review or publication approval.
"""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess
FLAGS=['-cc','-noq','-vtf','-vnf','-km','-ke']
ID='xuhui-bajin-residence'
def doc(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0]
    return json.loads(raw[20:20+n])
def preserve_metadata(target,source):
    before=target.read_bytes();size=struct.unpack_from('<I',before,12)[0]
    d=json.loads(before[20:20+size]);tail=before[20+size:];original=doc(source)
    d['asset']['copyright']=original['asset']['copyright'];d['extras']=original.get('extras',{})
    raw=json.dumps(d,ensure_ascii=False,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4)
    # Rewrite this disposable build output directly; no second large temp GLB.
    target.write_bytes(struct.pack('<4sII',b'glTF',2,20+len(raw)+len(tail))+struct.pack('<II',len(raw),0x4e4f534a)+raw+tail)
def info(path):
    d=doc(path);prims=[p for m in d['meshes'] for p in m['primitives']]
    assert all(p.get('mode',4)==4 and 'TANGENT' not in p['attributes'] for p in prims)
    for p in prims:
        for key in ['POSITION','NORMAL','TEXCOORD_0']:
            if key in p['attributes']:assert d['accessors'][p['attributes'][key]]['componentType']==5126
    size=path.stat().st_size;assert 0<size<100000000
    return {'file':path.name,'bytes':size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'triangles':sum(d['accessors'][p['indices']]['count']//3 for p in prims)}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True)
    p.add_argument('--lod',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--gltfpack',default='gltfpack',help='Executable from PATH, or an explicit installation path')
    a=p.parse_args()
    if a.out.exists():raise FileExistsError('Use a fresh output directory')
    a.out.mkdir(parents=True);assets={};commands=[]
    for role,source in [('web',a.raw),('lod',a.lod)]:
        target=a.out/(ID+'-'+role+'.glb');report=a.out/(role+'-gltfpack.json')
        cmd=[a.gltfpack,'-i',str(source.resolve()),'-o',str(target.resolve()),*FLAGS,'-r',str(report.resolve())]
        subprocess.run(cmd,check=True);commands.append(cmd);preserve_metadata(target,source)
        assets[role]=info(target);assert assets[role]['triangles']==info(source)['triangles']
        assert doc(target)['asset']['copyright']==doc(source)['asset']['copyright']
        assert doc(target)['extras']==doc(source)['extras']
    result={'schema':'bajin-portable-web-build-v1','gltfpack_version':subprocess.check_output([a.gltfpack,'-v'],text=True).strip(),
            'flags':FLAGS,'commands':commands,'assets':assets,'does_not_assert_acceptance_or_publication':True}
    (a.out/'encoding-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
