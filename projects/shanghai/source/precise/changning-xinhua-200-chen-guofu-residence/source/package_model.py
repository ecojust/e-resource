"""Encode the garden house and compare oriented float positions, UVs and both material maps."""
import argparse
import hashlib
import json
import mmap
import os
from pathlib import Path
import runpy
import shutil
import struct
import subprocess

from build_model import ID, PROJECT
from build_blender_source import attribution, digest, texture_bindings


def surface_records(path):
    """Hash the sorted multiset of cyclically oriented triangles, one material at a time."""
    geometries = {}
    textured = {}
    with path.open('rb') as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as data:
        size = struct.unpack_from('<I', data, 12)[0]
        doc = json.loads(data[20:20+size])
        base = 28 + size
        # The project bakes all transforms into one mesh in both stages.
        roots = doc['scenes'][doc.get('scene', 0)]['nodes']
        assert len(roots) == 1
        node = doc['nodes'][roots[0]]
        assert set(node) <= {'mesh', 'name'}

        def reader(index, dimension):
            accessor = doc['accessors'][index]
            view = doc['bufferViews'][accessor['bufferView']]
            assert 'sparse' not in accessor and not accessor.get('normalized', False)
            code = {5121:'B', 5123:'H', 5125:'I', 5126:'f'}[accessor['componentType']]
            view_format = struct.Struct('<' + dimension * code)
            start = base + view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
            step = view.get('byteStride', view_format.size)
            return lambda i: view_format.unpack_from(data, start + i*step), accessor['count']

        primitives = doc['meshes'][node['mesh']]['primitives']
        for material_index in sorted({p['material'] for p in primitives}):
            name = doc['materials'][material_index]['name']
            positions, corners = [], []
            for primitive in primitives:
                if primitive['material'] != material_index:
                    continue
                assert primitive.get('mode', 4) == 4
                attr = primitive['attributes']
                point, count = reader(attr['POSITION'], 3)
                has_uv = 'TEXCOORD_0' in attr
                uv, uv_count = reader(attr['TEXCOORD_0'], 2) if has_uv else (None, count)
                assert uv_count == count
                index, indices = reader(primitive['indices'], 1)
                assert indices % 3 == 0
                xyz = [struct.pack('<3f', *(v or 0. for v in point(i))) for i in range(count)]
                textured_vertices = ([x + struct.pack('<2f', *(v or 0. for v in uv(i))) for i, x in enumerate(xyz)]
                                     if has_uv else None)
                def cyclic(a, b, c):
                    return min(a+b+c, b+c+a, c+a+b)
                for offset in range(0, indices, 3):
                    a, b, c = (index(j)[0] for j in (offset, offset+1, offset+2))
                    positions.append(cyclic(xyz[a], xyz[b], xyz[c]))
                    if has_uv:
                        corners.append(cyclic(textured_vertices[a], textured_vertices[b], textured_vertices[c]))
            def fingerprint(rows):
                result = hashlib.sha256()
                rows.sort()
                for row in rows:
                    result.update(row)
                return {'triangles':len(rows), 'sha256':result.hexdigest()}
            geometries[name] = fingerprint(positions)
            if corners:
                textured[name] = fingerprint(corners)
    return geometries, textured


def package(source, output, encoder, resume=False):
    shim = PROJECT/'source/precise/xuhui-shaanxi-222-no20-residence-gate/source/package_model.py'
    common = runpy.run_path(str(shim))['packager']
    output.mkdir(exist_ok=True, parents=True)
    decoder = PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    roles, geometry, finishes, bindings = {}, {}, {}, {}
    resume_file = output/'decoder-receipts.json'
    decode_records = json.loads(resume_file.read_bytes()) if resume and resume_file.is_file() else {}
    metadata = attribution(source/'full-source.glb')
    for role, suffix in (('full','web'), ('lod','lod')):
        original = source/(role+'-source.glb')
        assert attribution(original) == metadata
        encoded = output/(ID+'-'+suffix+'.glb')
        decoded = output/('decoded-'+role+'.glb')
        if not (resume and encoded.is_file() and encoded.stat().st_size):
            staging = encoded.with_name(encoded.stem+'.encoding.glb')
            subprocess.run([encoder,'-i',original,'-o',staging,'-cc','-noq','-vnf','-km','-kn','-ke'],check=True)
            common.retain_metadata(staging,original)
            staging.replace(encoded)
        assert attribution(encoded) == metadata
        previous = decode_records.get(role, {})
        if not (decoded.exists() and previous.get('encoded') == digest(encoded) and previous.get('decoded') == digest(decoded)):
            subprocess.run(['node',decoder,encoded,decoded,PROJECT/'vendor/meshopt_decoder.module.js'],check=True)
            decode_records[role] = dict(encoded=digest(encoded),decoded=digest(decoded),decoder_sha256=digest(decoder))
            common.write_json(resume_file,decode_records)
        shapes, uvs = surface_records(original)
        if (shapes, uvs) != surface_records(decoded):
            raise ValueError(f'Oriented position or texture coordinates differ after decoding {role}')
        images = texture_bindings(original)
        if images != texture_bindings(decoded) or sum('normal' in v for v in images.values()) != 4:
            raise ValueError(f'Embedded colour and normal maps changed in {role}')
        n = sum(r['triangles'] for r in shapes.values())
        if role == 'full':
            raw = output/(ID+'-raw.glb')
            if not raw.is_file() or digest(raw) != digest(original):
                shutil.copyfile(original,raw)
            roles['raw'] = common.asset(raw,n)
        roles[role] = common.asset(encoded,n)
        geometry[role] = dict(source=common.asset(original,n),decoded=common.asset(decoded,n),oriented_surfaces=shapes)
        finishes[role] = dict(source_sha256=digest(original),decoded_sha256=digest(decoded),oriented_uvs=uvs,
                              materials=images,pbr_parameters=common.check_materials(original,decoded))
        bindings[role] = images
    common.write_json(output/'mesh-decode-comparisons.json',geometry)
    common.write_json(output/'decoded-texture-comparisons.json',finishes)
    common.write_json(output/'decoded-xinhua-200-finishes.json',bindings)
    shutil.copyfile(source/'full-source.geometry.json',output/'source-part-order.json')
    common.write_json(output/'manifest.json',dict(model_id=ID,**metadata,assets=roles))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('source_dir',type=Path)
    cli.add_argument('out',type=Path)
    cli.add_argument('--gltfpack',default=os.environ.get('GLTFPACK','gltfpack'))
    cli.add_argument('--resume',action='store_true',help='Decode and revalidate each existing encoded role against its original mesh')
    args=cli.parse_args()
    package(args.source_dir,args.out,args.gltfpack,args.resume)
