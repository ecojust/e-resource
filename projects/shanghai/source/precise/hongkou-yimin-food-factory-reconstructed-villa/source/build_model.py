"""Build and verify three GLB roles for the relocated, reduced Yimin Food Factory villa."""
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
from villa_walls import add_walls, PALETTE, LAYOUT
ID='hongkou-yimin-food-factory-reconstructed-villa'
CAMERAS={
 'front':[[0,4.5,-1],[.04,-.06,1],23.5,26.2],
 'oblique':[[0,4.6,-.55],[-.30,.13,1],23.8,26.5],
 'above':[[0,5.2,-2.0],[.33,.59,.94],23.8,27],
 'arcade':[[0,1.97,-.1],[.19,.02,1],8.2,9.8],
 'oriel':[[6.25,2.19,1.14],[-.32,.03,1],5.5,6.3],
 'roof':[[0,5.3,-1.7],[-.19,.18,1],12.5,15.4]}
META=dict(id=ID,name='益民食品一厂复建西班牙式小楼',viewer_page='yimin-food-factory-reconstructed-villa.html',
 heritage_group='5F022',address='上海市虹口区香烟桥路13号',scope='易地缩小复建的小楼，含正面双山墙、三券门廊、前凸窗、屋顶与院侧窗。1937年始建的原楼于1985年拆除。',
 estimated='按照片拟合建筑外部比例，暂以门廊中央券净宽1.75米作展示尺度。现场测绘值与复建缩尺系数均未获见。',
 source_reference='source/precise/'+ID+'/SOURCES-LICENSE.md',geometry_license='MIT',code_license='MIT',photos_embedded=False,
 copyright='Original geometry, procedural masonry and roof materials under MIT. Reference photographs are not included.',camera_views=CAMERAS)
def add_building(builder,lod=False):
    from villa_roof import add_roofs
    add_walls(builder,lod,LAYOUT)
    add_roofs(builder,lod,LAYOUT)
def write_model(path,lod):
    builder=Builder(PALETTE)
    add_building(builder,lod)
    builder.save(path,META)
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
