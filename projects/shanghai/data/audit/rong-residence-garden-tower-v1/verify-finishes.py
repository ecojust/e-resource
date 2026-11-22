"""Compare the two embedded images and every indexed UV corner to the original surface generators."""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
SOURCE=PROJECT/'source/precise/jingan-rong-residence-garden-tower/source'
sys.path.insert(0,str(SOURCE))
from native_layout import CAMERAS,MAIN,MATERIALS,uv_for_face


def sha(file):
    with file.open('rb')as handle:return hashlib.file_digest(handle,'sha256').hexdigest()


def reader(path):
    data=path.read_bytes();assert struct.unpack_from('<4sII',data)==(b'glTF',2,len(data))
    length,kind=struct.unpack_from('<II',data,12);assert kind==0x4e4f534a
    doc=json.loads(data[20:20+length]);n,kind=struct.unpack_from('<II',data,20+length)
    assert kind==0x004e4942 and n==len(data)-length-28
    return doc,memoryview(data)[28+length:]


def accessor(doc,blob,index):
    entry=doc['accessors'][index];view=doc['bufferViews'][entry['bufferView']]
    size={'SCALAR':1,'VEC2':2,'VEC3':3}[entry['type']]
    code={5121:'B',5123:'H',5125:'I',5126:'f'}[entry['componentType']]
    item=struct.Struct('<'+code*size);stride=view.get('byteStride',item.size)
    start=view.get('byteOffset',0)+entry.get('byteOffset',0)
    return [item.unpack_from(blob,start+stride*i)for i in range(entry['count'])]


def embedded(doc,binary):
    result={}
    for material in doc['materials']:
        name=material['name']
        if name not in MATERIALS:continue
        pbr=material['pbrMetallicRoughness']
        texture=doc['textures'][pbr['baseColorTexture']['index']]
        image=doc['images'][texture['source']]
        sampler=doc['samplers'][texture['sampler']]
        assert sampler['wrapT']==sampler['wrapS']==33071 and image['mimeType']=='image/png'
        view=doc['bufferViews'][image['bufferView']]
        offset=view.get('byteOffset',0);png=binary[offset:offset+view['byteLength']]
        file=SOURCE/MATERIALS[name][0]
        assert bytes(png)==file.read_bytes()
        result[name]=dict(png_sha256=sha(file),bytes=len(png),pixels=list(struct.unpack_from('>II',png,16)),
                          indexed_corners=0,maximum_uv_error=0.)
    assert result.keys()==MATERIALS.keys()
    return result


def frame(points):
    def unit(v):
        norm=math.sqrt(sum(n*n for n in v))
        return [n/norm for n in v]
    def sub(a,b):return [x-y for x,y in zip(a,b)]
    def dot(a,b):return sum(x*y for x,y in zip(a,b))
    def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
    eye,focus,scale=CAMERAS[MAIN];direction=unit(sub(focus,eye));right=unit(cross(direction,[0,0,1]));up=cross(right,direction)
    xy=[(.5+dot(sub(p,focus),right)/scale,.5+dot(sub(p,focus),up)/(scale*760/880))for p in points]
    edges=[min(x for x,y in xy),min(y for x,y in xy),max(x for x,y in xy),max(y for x,y in xy)]
    assert min(edges[:2])>.015 and max(edges[2:])<.985,edges
    return edges


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('folder',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();folder=args.folder
    manifest=json.loads((folder/'manifest.json').read_bytes());measurements={};main_frame=None
    for role in ('raw','full','lod'):
        asset=manifest['assets'][role];path=folder/asset['file'];assert asset['sha256']==sha(path)
        doc,binary=reader(path);textures=embedded(doc,binary)
        compressed='EXT_meshopt_compression' in doc.get('extensionsRequired',[])
        assert compressed==(role!='raw')
        decoded=folder/f'decoded-{role}.glb' if compressed else path
        scene,blob=reader(decoded)
        assert 'EXT_meshopt_compression' not in scene.get('extensionsRequired',[])
        fall=[]
        for mesh in scene['meshes']:
            for primitive in mesh['primitives']:
                coords=accessor(scene,blob,primitive['attributes']['POSITION'])
                positions=[(x,-z,y)for x,y,z in coords]
                if role=='raw':fall.extend(positions)
                material=scene['materials'][primitive['material']]['name']
                if material not in textures:continue
                uv=accessor(scene,blob,primitive['attributes']['TEXCOORD_0'])
                indices=[idx[0]for idx in accessor(scene,blob,primitive['indices'])]
                metric=textures[material]
                for k in range(0,len(indices),3):
                    face=indices[k:k+3];expected=uv_for_face(material,[positions[i]for i in face])
                    for i,(u,v) in zip(face,expected):
                        eu=abs(uv[i][0]-u);ev=abs(uv[i][1]-(1-v))
                        metric['maximum_uv_error']=max(metric['maximum_uv_error'],eu,ev)
                    metric['indexed_corners']+=3
        assert all(t['indexed_corners'] and t['maximum_uv_error']<.00001 for t in textures.values()),(role,textures)
        measurements[role]=dict(asset_sha256=sha(path),decoded_sha256=sha(decoded),textures=textures)
        if role=='raw':main_frame=frame(fall)
    parts=json.loads((folder/'raw.geometry.json').read_bytes())['part_summary']
    groups=defaultdict(Counter)
    for part in parts:groups[part['label']][part['material']]+=part['triangles']
    assert len(groups)==115 and max(len(n.encode())for n in groups)<=63
    packed=json.dumps(groups,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    result=dict(id=manifest['id'],parts=len(parts),editable_groups=len(groups),material_face_schedule_sha256=hashlib.sha256(packed).hexdigest(),
                assets=measurements,main_camera=MAIN,whole_model_frame=main_frame,orthographic_cameras=CAMERAS)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
