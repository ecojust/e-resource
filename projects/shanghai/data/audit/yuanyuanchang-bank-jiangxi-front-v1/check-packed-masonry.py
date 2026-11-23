"""Verify the original firebrick PNG in the three GLBs and the independent Blender reopen."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
ID = 'huangpu-yuanyuanchang-bank-jiangxi-front'
BRICKS = {'brown firebrick and pale joints':'brown-firebrick.png'}

def images_glb(path, source):
    blob = path.read_bytes()
    assert blob[:4] == b'glTF' and struct.unpack_from('<I',blob,8)[0] == len(blob)
    length = struct.unpack_from('<I',blob,12)[0]
    assert blob[16:20] == b'JSON' and blob[24+length:28+length] == b'BIN\x00'
    tree = json.loads(blob[20:20+length])
    binary_start = 28 + length
    result = {}
    for name,file in BRICKS.items():
        index,mat = next((i,m) for i,m in enumerate(tree['materials']) if m['name']==name)
        texture = tree['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]
        image = tree['images'][texture['source']]
        view = tree['bufferViews'][image['bufferView']]
        start = binary_start + view.get('byteOffset',0)
        data = blob[start:start+view['byteLength']]
        assert image['mimeType'] == 'image/png' and data == (source/file).read_bytes()
        assert struct.unpack_from('>II',data,16) == (1024,1024)
        primitives = [g for mesh in tree['meshes'] for g in mesh['primitives'] if g['material']==index]
        assert primitives and all('TEXCOORD_0' in item['attributes'] for item in primitives)
        result[name] = dict(file=file,sha256=sha256(data).hexdigest(),size=[1024,1024],uv_primitives=len(primitives))
    return result

if __name__ == '__main__':
    cli = ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    cli.add_argument('--native-report',type=Path,default=HERE/'geometry-native.json')
    cli.add_argument('--out',type=Path,default=HERE/'brick-texture-checks.json')
    args = cli.parse_args()
    manifest = json.loads(args.manifest.read_bytes())
    assert manifest['id'] == ID
    source = PROJECT/'source/precise'/ID/'source'
    results = {}
    for role in ('raw','full','lod'):
        asset = manifest['assets'][role]
        model = args.manifest.parent/asset['file']
        assert sha256(model.read_bytes()).hexdigest() == asset['sha256']
        results[role] = images_glb(model,source)
    native = json.loads(args.native_report.read_bytes())['native_reopened_and_compared']['packed_images_and_uvs']
    for material in BRICKS:
        assert native[material]['sha256'] == results['raw'][material]['sha256'] and native[material]['checked_corner_uvs']>0
    args.out.write_text(json.dumps(dict(id=ID,passed=True,assets=results,native=native,checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
