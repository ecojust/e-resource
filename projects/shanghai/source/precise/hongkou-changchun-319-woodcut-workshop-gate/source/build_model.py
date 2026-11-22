"""Build and verify three GLB roles for the courtyard gate at No. 319 Changchun Road."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

SOURCE = Path(__file__).resolve().parent
PROJECT = next(p for p in SOURCE.parents if (p / 'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(PROJECT / 'tools'))
from package_architectural_model import Builder, check_pair, glb_stats
from workshop_gate import add_gate,PALETTE
ID='hongkou-changchun-319-woodcut-workshop-gate'
CAMERAS={
 'front':[[0.,1.40,-.20],[0.,.015,1.],3.8,3.55],
 'oblique':[[0.,1.40,-.20],[-.6,.10,1.],3.9,3.7],
 'cap':[[1.20,2.48,-.24],[-.40,.24,1.],1.64,1.24],
 'door':[[0.,1.22,-.36],[.06,.01,1.],2.16,2.56],
 'plaques':[[0.,1.89,-.035],[-.23,.04,1.],3.55,1.70]}
META=dict(id=ID,name='长春路319号木刻讲习会旧址院门',viewer_page='changchun-319-woodcut-workshop-gate.html',
          heritage_group='5F014',address='上海市虹口区长春路319号',scope='街前双砖柱、阶状压顶、四片斜页、右扇五字与两铭牌。',
          photo_author='蒋迪雯（上观，2021）；上海虹口（2023）；高参88（2015）',
          photo_source='https://export.shobserver.com/baijiahao/html/408688.html',
          photo_license='原照片仅作测绘研究，未嵌入、转载。',photos_embedded=False,geometry_license='MIT',code_license='MIT',
          letterforms_license='SIL OFL 1.1; Noto Serif CJK',license_url='https://opensource.org/license/mit/',
          copyright='Original geometric reconstruction under MIT. Typeset signage uses Noto Serif CJK, SIL Open Font License 1.1.',
          camera_views=CAMERAS)
def add_building(builder,lod=False):add_gate(builder,lod)
def write_model(path,lod):
    builder=Builder(PALETTE);add_building(builder,lod);builder.save(path,META)
def metadata_copy(path, original):
    def header(data):
        size=struct.unpack_from('<I',data,12)[0]
        return size,json.loads(data[20:20+size])
    size,doc=header(data:=path.read_bytes())
    _,first=header(original.read_bytes())
    doc['extras']=first['extras']
    doc['asset']['copyright']=first['asset']['copyright']
    part=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode()
    part+=b' '*(-len(part)%4)
    tail=data[20+size:]
    path.write_bytes(struct.pack('<4sIIII',b'glTF',2,20+len(part)+len(tail),len(part),0x4e4f534a)+part+tail)

def package(out, decoded, tool):
    out.mkdir(parents=True, exist_ok=True)
    decoded.mkdir(parents=True, exist_ok=True)
    raw=out/(ID+'-raw.glb')
    write_model(raw,False)
    with tempfile.TemporaryDirectory(dir=decoded) as stage:
        low=Path(stage)/'before-lod.glb'
        write_model(low,True)
        for role,ref in [('full',raw),('lod',low)]:
            path=out/(ID+('-web.glb' if role=='full' else '-lod.glb'))
            subprocess.run([str(tool),'-i',str(ref),'-o',str(path),'-cc','-noq','-vnf','-km','-kn','-ke'],check=True)
            metadata_copy(path,ref)
            check_pair(ref,path,decoded/('decoded-'+role+'.glb'))
    roles={}
    for role,suffix in [('raw','raw'),('full','web'),('lod','lod')]:
        path=out/(ID+'-'+suffix+'.glb')
        roles[role]={**glb_stats(path),'bytes':path.stat().st_size,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    assert roles['full']['triangles']==roles['raw']['triangles']>roles['lod']['triangles']
    (out/'manifest.json').write_text(json.dumps({**META,'assets':roles},ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output',type=Path,help='Write a single uncompressed GLB')
    group.add_argument('--out',type=Path,help='Directory for the three packaged downloads and manifest')
    parser.add_argument('--lod',action='store_true',help='Use the reduced mesh for single-file output')
    parser.add_argument('--decoded',type=Path,help='Directory for independently decoded QA files')
    parser.add_argument('--gltfpack',default=shutil.which('gltfpack') or 'gltfpack')
    args=parser.parse_args()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        write_model(args.output,args.lod)
    else:
        if args.lod:parser.error('--lod applies to --output')
        if args.decoded:package(args.out,args.decoded,args.gltfpack)
        else:
            with tempfile.TemporaryDirectory() as temporary:package(args.out,Path(temporary),args.gltfpack)
