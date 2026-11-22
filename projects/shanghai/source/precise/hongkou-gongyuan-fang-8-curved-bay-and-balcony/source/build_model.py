"""Build and verify three GLB roles for the brick bay and recessed balcony of No. 8 Gongyuan Fang."""
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
from curved_bay import add_bay,PALETTE
ID='hongkou-gongyuan-fang-8-curved-bay-and-balcony'
CAMERAS={
 'front':[[0,2.05,-.22],[.04,-.16,1],5.7,5.3],
 'oblique':[[0,2.02,-.22],[-.7,-.29,1],5.75,5.55],
 'above':[[0,2.87,-.21],[-.24,.42,1],4.05,5.35],
 'rail':[[0,2.98,-.28],[.16,-.14,1],2.9,4.60],
 'sash':[[0,.94,-.10],[.07,-.09,1],2.5,3.95]}
META=dict(id=ID,name='公园坊8号弧窗与退台阳台',viewer_page='gongyuan-fang-8-curved-bay-and-balcony.html',
          heritage_group='5F018',address='上海市虹口区西江湾路476弄8号',
          scope='图像中可辨的二层三窗、曲形砖石墙带、三层铁栏和后退玻璃窗。',
          photo_author='上海虹口，2019年9月公开影像',photo_source='https://boot-img.xuexi.cn/contribute_img/20190912160103/30762293038669391.jpg',
          photo_license='原照片仅作测绘研究，著作权归摄影者、发布者。',photos_embedded=False,
          geometry_license='MIT',code_license='MIT',license_url='https://opensource.org/license/mit/',
          copyright='Original geometric reconstruction and procedural materials under MIT. No source photographs are included.',camera_views=CAMERAS)
def add_building(builder,lod=False):add_bay(builder,lod)
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
