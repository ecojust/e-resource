"""Verify each original accessor, triangle order, instance transform and neighbor partition."""
import argparse
import gzip
import hashlib
import json
import struct
from pathlib import Path

def glb(path):
    data = path.read_bytes()
    if data.startswith(b'\x1f\x8b'):
        data = gzip.decompress(data)
    magic, version, length, metadata_length, kind = struct.unpack_from('<4sIII4s', data)
    assert (magic, version, length, kind) == (b'glTF', 2, len(data), b'JSON')
    scene = json.loads(data[20:20 + metadata_length])
    block_length, kind = struct.unpack_from('<I4s', data, 20 + metadata_length)
    block = data[28 + metadata_length:]
    assert kind == b'BIN\0' and block_length == len(block)
    return scene, block

def values(scene, block, accessor):
    a = scene['accessors'][accessor]
    view = scene['bufferViews'][a['bufferView']]
    width = {5120:1, 5121:1, 5122:2, 5123:2, 5125:4, 5126:4}[a['componentType']]
    width *= {'SCALAR':1, 'VEC2':2, 'VEC3':3, 'VEC4':4}[a['type']]
    offset = view.get('byteOffset',0) + a.get('byteOffset',0)
    stride = view.get('byteStride',width)
    return [block[offset+i*stride:offset+i*stride+width] for i in range(a['count'])]

def verify(src, dst, checks):
    old, old_bin = src
    new, new_bin = dst
    assert new_bin[:len(old_bin)] == old_bin
    for field in ('bufferViews','accessors','meshes'):
        assert new[field][:len(old[field])] == old[field], field
    for field in old.keys() - {'bufferViews','accessors','meshes','buffers','nodes','scenes','scene'}:
        assert new[field] == old[field], field
    roots = [new['nodes'][i] for i in new['scenes'][0]['nodes']]
    assert len(roots) == 2
    tag = roots[0]['extras']['cityReplacement']
    assert tag['local_ids'] == [checks['source_local_id']] and tag['feature_keys'] == [checks['source_key']]
    assert roots[1]['extras']['cityPreservedLocalIds'] == checks['unchanged_local_ids']
    summary = []
    parts = {(p['node'],p['primitive']):p for p in checks['parts']}
    def indices(part, target):
        ids = set(part['target_element_ordinals'])
        return [i for i in range(part['total']) if (i in ids) == target]

    for target, root in zip((True,False), roots, strict=True):
        children=iter(root['children'])
        triangles=0
        comparisons=0
        digest=hashlib.sha256()
        def check_values(a,b,ordinals):
            nonlocal comparisons
            for prop in ('componentType','type','normalized'):
                assert old['accessors'][a].get(prop) == new['accessors'][b].get(prop)
            old_values=values(old,old_bin,a)
            expected=[old_values[i] for i in ordinals]
            actual=values(new,new_bin,b)
            assert expected==actual, (a,b)
            digest.update(b''.join(actual))
            comparisons+=len(actual)

        for source_id in old['scenes'][0]['nodes']:
            node=old['nodes'][source_id]
            mesh=old['meshes'][node['mesh']]
            ext=node.get('extensions',{}).get('EXT_mesh_gpu_instancing')
            if ext:
                part=parts[source_id,None]
                subset=indices(part,target)
                if not subset:
                    continue
                after=new['nodes'][next(children)]
                assert {k:v for k,v in after.items()if k!='extensions'}=={k:v for k,v in node.items()if k!='extensions'}
                assert set(after['extensions']) == {'EXT_mesh_gpu_instancing'}
                attr=after['extensions']['EXT_mesh_gpu_instancing']['attributes']
                assert attr.keys()==ext['attributes'].keys()
                for name,a in ext['attributes'].items():
                    check_values(a,attr[name],subset)
                triangles+=len(subset)*part['triangles_per_element']
                continue
            prims=[]
            for i,primitive in enumerate(mesh['primitives']):
                subset=indices(parts[source_id,i],target)
                if subset: prims.append((primitive,subset))
            if not prims:
                continue
            after=new['nodes'][next(children)]
            assert {k:v for k,v in after.items()if k!='mesh'}=={k:v for k,v in node.items()if k!='mesh'}
            replaced=new['meshes'][after['mesh']]
            assert {k:v for k,v in replaced.items()if k!='primitives'}=={k:v for k,v in mesh.items()if k!='primitives'}
            for (primitive,subset),result in zip(prims,replaced['primitives'],strict=True):
                assert {k:v for k,v in primitive.items()if k!='indices'}=={k:v for k,v in result.items()if k!='indices'}
                check_values(primitive['indices'],result['indices'],[3*i+d for i in subset for d in range(3)])
                triangles+=len(subset)
        assert list(children)==[]
        assert triangles==checks['target_expanded_triangles' if target else 'retained_expanded_triangles']
        summary.append(dict(local_ids=tag['local_ids'] if target else checks['unchanged_local_ids'],
                            triangles=triangles,actual_typed_elements= comparisons,ordered_bytes_sha256=digest.hexdigest()))
    return summary

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('original',type=Path,help='Losslessly meshopt-decoded baseline GLB')
    ap.add_argument('split',type=Path,help='Registered split near GLB or its gzip file')
    ap.add_argument('owners',type=Path,help='Element membership measured against all original footprints')
    ap.add_argument('output',type=Path)
    args=ap.parse_args()
    checks=json.loads(args.owners.read_bytes())
    assert hashlib.sha256(args.original.read_bytes()).hexdigest()==checks['decoded_view_sha256']
    src=glb(args.original);dst=glb(args.split)
    groups=verify(src,dst,checks)
    scene,raw=dst
    # Alter one appended transform or index. This must fail even though every count stays intact.
    a=scene['accessors'][len(src[0]['accessors'])]
    pos=scene['bufferViews'][a['bufferView']].get('byteOffset',0)+a.get('byteOffset',0)
    b=bytearray(raw); b[pos]^=1
    try: verify(src,(scene,bytes(b)),checks)
    except AssertionError: pass
    else: raise ValueError('A changed transform or index was accepted')
    args.output.write_text(json.dumps({'model_id':scene['nodes'][scene['scenes'][0]['nodes'][0]]['extras']['cityReplacement']['landmark_id'],
        'compared_groups':groups,'original_binary_bytes_preserved':len(src[1]),'changed_numeric_element_rejected':True,
        'replacement_gzip_sha256':hashlib.sha256(args.split.read_bytes()).hexdigest()},indent=2)+'\n')
if __name__=='__main__': main()
