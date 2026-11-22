"""Build and verify three GLB roles for the acanthus gable at Lane 225, Wujin Road."""
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
from gable import GableBuilder, PALETTE, add_gable

ID = 'hongkou-wujin-225-acanthus-gable'
CAMERAS = {
    'front': [[0.,2.5,0.],[0.,0.03,1.],10.8,8.1],
    'oblique': [[0.,2.5,0.],[-0.36,0.07,1.],10.8,8.2],
    'window': [[0.,0.3,0.],[-0.16,0.04,1.],5.2,6.7],
    'relief': [[0.,0.,0.],[-0.12,0.07,1.],1.5,2.15]
}
META = {
    'id':ID, 'name':'武进路225弄住宅卷草山墙',
    'viewer_page':'wujin-225-acanthus-gable.html',
    'heritage_group':'5F010', 'address':'武进路225弄3–11号保护条目内；具体门牌待考',
    'scope':'照片可见的卷草饰板、砖砌山墙、两侧窗洞与屋檐。',
    'measurement':'局部坐标原点取自卷草外框中心，展示尺度以外框宽1.82、高1.10为基准。',
    'camera_views':CAMERAS, 'photo_author':'Fayhoo',
    'photo_source':'https://commons.wikimedia.org/wiki/File:Wujinlu_225_Long_9,_11_Hao_Zhuzhai.jpg',
    'photo_license':'CC BY-SA 3.0', 'photos_embedded':False,
    'geometry_license':'CC BY-SA 3.0', 'procedural_texture_license':'MIT', 'code_license':'MIT',
    'license_url':'https://creativecommons.org/licenses/by-sa/3.0/',
    'copyright':'Geometry based on the facade photograph by Fayhoo, under CC BY-SA 3.0. Procedural textures and software under the MIT license.'
}

def add_building(builder, lod=False):
    add_gable(builder, lod)

def write_model(path, lod):
    builder=GableBuilder(PALETTE)
    add_building(builder, lod)
    builder.save(path, META)

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
