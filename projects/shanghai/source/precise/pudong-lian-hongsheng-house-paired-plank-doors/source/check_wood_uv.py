"""Compare every plank UV to its measured door-plane coordinates in a decoded or raw glTF."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import numpy as np

def verify(path):
    contents=Path(path).read_bytes()
    size=int.from_bytes(contents[12:16],'little')
    document=json.loads(contents[20:20+size])
    blob=contents[28+size:]
    def data(accessor):
        a=document['accessors'][accessor]
        v=document['bufferViews'][a['bufferView']]
        width={'VEC2':2,'VEC3':3}[a['type']]
        dt=np.dtype({5126:'<f4',5123:'<u2',5121:'u1'}[a['componentType']])
        arr=np.ndarray((a['count'],width),dtype=dt,buffer=blob,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*dt.itemsize),dt.itemsize))
        if a.get('normalized'):
            return arr.astype('float64')/np.iinfo(dt).max
        return arr
    image=document['images'][0]
    view=document['bufferViews'][image['bufferView']]
    start=view.get('byteOffset',0)
    checksum=sha256(blob[start:start+view['byteLength']]).hexdigest()
    assert checksum==sha256(Path(__file__).with_name('weathered-planks.png').read_bytes()).hexdigest()
    checked=0;worst=0.
    for obj in document['meshes']:
        for part in obj['primitives']:
            material=document['materials'][part['material']]
            if 'baseColorTexture' not in material['pbrMetallicRoughness']:
                continue
            positions=data(part['attributes']['POSITION'])
            uv=data(part['attributes']['TEXCOORD_0'])
            expected=np.clip(np.column_stack(((positions[:,0]/.00345+252)/500,(751-positions[:,1]/.00345)/752)),0,1)
            worst=max(worst,float(abs(expected-uv).max()))
            checked+=len(uv)
    assert checked>=160 and worst<.0003,(checked,worst)
    return dict(vertices_with_source_uv=checked,max_difference_in_normalized_coordinates=worst,embedded_original_wood_png_sha256=checksum)

if __name__=='__main__':
    cli=ArgumentParser()
    cli.add_argument('mesh',nargs='+',type=Path)
    options=cli.parse_args()
    print(json.dumps({file.name:verify(file) for file in options.mesh},indent=2))
