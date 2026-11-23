"""Render the GLB from three measured photo stations using bounded native memory."""
import argparse
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import struct
import subprocess
from tempfile import TemporaryDirectory

from PIL import Image

HERE=Path(__file__).absolute().parent
VIEWS=[
    ('portrait','portrait',(0,0,1280,1919),442),
    ('wide','wide',(129,135,386,350),442),
    ('pier-number','portrait',(229,1370,337,1537),270),
    ('iron-fanlight','portrait',(385,650,944,996),544),
    ('heritage-plaque','portrait',(77,979,242,1128),348),
    ('courtyard-elevation','wide',(75,71,424,345),526),
    ('scaffold-station','atlas',(48,14,352,293),456),
    ('dormer','atlas',(110,39,190,105),344),
]


def export_scene(mesh,target):
    """Read this project's single identity-node, triangle-only authored GLB."""
    data=mesh.read_bytes()
    magic,version,length,size,kind=struct.unpack_from('<4sIIII',data)
    if (magic,version,length,kind)!=(b'glTF',2,len(data),0x4e4f534a):
        raise ValueError('Invalid GLB')
    doc=json.loads(data[20:20+size]);binary=memoryview(data)[28+size:]
    if len(doc['meshes'])!=1 or len(doc['nodes'])!=1 or any(k in doc['nodes'][0] for k in ('matrix','translation','rotation','scale')):
        raise ValueError('Expected one authored mesh with identity transform')
    def view(i):
        entry=doc['bufferViews'][i];a=entry.get('byteOffset',0)
        return binary[a:a+entry['byteLength']]
    def reader(i):
        attr=doc['accessors'][i];entry=doc['bufferViews'][attr['bufferView']]
        kind={5121:'B',5123:'H',5125:'I',5126:'f'}[attr['componentType']]
        dims={'VEC3':3,'VEC2':2,'SCALAR':1}[attr['type']]
        fmt=struct.Struct('<'+kind*dims);raw=view(attr['bufferView']);off=attr.get('byteOffset',0);stride=entry.get('byteStride',fmt.size)
        if attr.get('normalized'):raise ValueError('Expected authored float geometry')
        return lambda n:fmt.unpack_from(raw,off+n*stride)
    primitives=doc['meshes'][0]['primitives']
    if any(p.get('mode',4)!=4 for p in primitives):raise ValueError('Expected triangle geometry')
    triangles=sum(doc['accessors'][p['indices']]['count']//3 for p in primitives)
    with target.open('wb')as out:
        out.write(struct.pack('<8sIII',b'COURT003',len(doc['materials']),len(doc.get('textures',[])),triangles))
        for material in doc['materials']:
            pbr=material['pbrMetallicRoughness'];factor=pbr.get('baseColorFactor',[1,1,1,1])
            if factor[3]!=1:raise ValueError('A translucent material needs alpha compositing')
            out.write(struct.pack('<4fii',*factor,pbr.get('baseColorTexture',{}).get('index',-1),
                                  material.get('normalTexture',{}).get('index',-1)))
        for texture in doc.get('textures',[]):
            image=doc['images'][texture['source']]
            with Image.open(BytesIO(view(image['bufferView'])))as original:
                rgb=original.convert('RGB');out.write(struct.pack('<II',*rgb.size));out.write(rgb.tobytes())
        record=struct.Struct('<I15f')
        for p in primitives:
            attr=p['attributes'];position=reader(attr['POSITION'])
            uv=reader(attr['TEXCOORD_0']) if 'TEXCOORD_0' in attr else lambda n:(0.,0.)
            indices=reader(p['indices']);count=doc['accessors'][p['indices']]['count']
            for j in range(0,count,3):
                vertices=[]
                for k in (j,j+1,j+2):
                    index=indices(k)[0];x,z,minus_y=position(index)
                    vertices.extend((x,-minus_y,z,*uv(index)))
                out.write(record.pack(p['material'],*vertices))


def render(mesh,output):
    output.mkdir(parents=True,exist_ok=True)
    cameras=json.loads((HERE/'portico-camera-pair.json').read_bytes())['stations']
    cameras['atlas']=json.loads((HERE/'joint-court-roof.json').read_bytes())['atlas_camera']
    records={}
    with TemporaryDirectory(dir=output) as temp:
        tmp=Path(temp);scene=tmp/'scene.bin';raster=tmp/'raster'
        subprocess.run([os.environ.get('CC','cc'),'-std=c99','-O2',str(HERE/'court_raster.c'),'-lm','-o',raster],check=True)
        export_scene(mesh,scene)
        for name,station,crop,width in VIEWS:
            cam=cameras[station];K=cam['K'];height=round(width*(crop[3]-crop[1])/(crop[2]-crop[0]))
            # Four samples per displayed pixel tame moire on the distant brick courses.
            line=[2*width,2*height,*crop[:2],2*width/(crop[2]-crop[0]),K[0][0],K[1][1],K[0][2],K[1][2],
                  *(v for row in cam['R'] for v in row),*cam['C']]
            pose=tmp/'camera.txt';pose.write_text(' '.join(map(str,line))+'\n')
            frame=tmp/'frame.ppm';subprocess.run([raster,scene,pose,frame],check=True)
            target=output/(name+'-model.jpg')
            with Image.open(frame)as pic:
                pic.resize((width,height),Image.Resampling.LANCZOS).save(target,quality=93)
            records[name]=dict(station=station,crop=crop,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    report=dict(model_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),views=records)
    (output/'rendered-views.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path)
    args=cli.parse_args();render(args.mesh,args.output)
