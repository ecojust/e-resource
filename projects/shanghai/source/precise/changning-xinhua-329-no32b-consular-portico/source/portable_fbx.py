"""Build a single binary FBX with baked centimetre / Y-up coordinates and embedded colour and normal maps."""
import argparse
from collections import Counter
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import zipfile

class Scene(C.Structure):
    _fields_=[('flags',C.c_uint),('root',C.c_void_p),('meshes',C.c_uint),('meshp',C.c_void_p),
              ('materials',C.c_uint),('matp',C.c_void_p),('animations',C.c_uint),('animp',C.c_void_p),
              ('textures',C.c_uint),('texturep',C.c_void_p)]

def sha(b):return hashlib.sha256(b).hexdigest()

def cyclic(tri):return min(tri,tri[1:]+tri[:1],tri[2:]+tri[:2])

def main(package, source, target, report):
    a=C.CDLL('libassimp.so.5')
    a.aiImportFile.argtypes=[C.c_char_p,C.c_uint]; a.aiImportFile.restype=C.POINTER(Scene)
    a.aiExportScene.argtypes=[C.POINTER(Scene),C.c_char_p,C.c_char_p,C.c_uint]
    a.aiExportScene.restype=C.c_int
    a.aiReleaseImport.argtypes=[C.POINTER(Scene)]; a.aiGetErrorString.restype=C.c_char_p
    expected=Counter()
    palette=list(package['materials'])
    names={'material_'+str(i+1):f'author_mat_{i+1:06d}' for i,_ in enumerate(palette)}
    material_ids={n:f'author_mat_{i+1:06d}' for i,n in enumerate(palette)}
    def source_material(name):
        if name in names.values():return name
        cleaned=name.removesuffix('_material')
        return cleaned if cleaned in names.values() else name
    for i,p in enumerate(package['parts'],1):
        n=f"part_{i:06d}"
        uv=p.get('texcoords')
        for face in p['triangles']:
            tri=tuple(tuple(round(x,5) for x in p['vertices'][j])+tuple(round(v,5)for v in uv[j]) if uv else tuple(round(x,5) for x in p['vertices'][j]) for j in face)
            expected[n,material_ids[p['material']],cyclic(tri)]+=1
    with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
        folder=Path(tmp)
        with zipfile.ZipFile(source) as z:z.extractall(folder)
        obj=next(folder.glob('*.obj'));mtl=obj.with_suffix('.mtl')
        buf=[]
        for line in obj.read_text().splitlines():
            if line.startswith('v '):
                x,y,z=map(float,line.split()[1:])
                line=f'v {100*x:.12g} {100*z:.12g} {-100*y:.12g}'
            elif line.startswith('usemtl '):line='usemtl '+names[line.split()[1]]
            buf.append(line)
        obj.write_text('\n'.join(buf)+'\n')
        material_lines=mtl.read_text().splitlines()
        mtl.write_text('\n'.join('newmtl '+names[line.split()[1]] if line.startswith('newmtl ') else line for line in material_lines)+'\n')
        sc=a.aiImportFile(os.fsencode(obj),0x10000008)
        if not sc:raise ValueError(a.aiGetErrorString().decode())
        try:
            assert sc.contents.meshes==len(package['parts']) and sc.contents.textures==len(package['textures'])
            if a.aiExportScene(sc,b'fbx',os.fsencode(target),0)!=0:raise ValueError(a.aiGetErrorString().decode())
        finally:a.aiReleaseImport(sc)
        obj.unlink();mtl.unlink()
        for image in package['textures']:(folder/image).unlink()
        reader=a.aiImportFile(os.fsencode(target),8)
        if not reader:raise ValueError(a.aiGetErrorString().decode())
        glb=folder/'readback.glb'
        try:
            assert reader.contents.meshes==len(package['parts']) and reader.contents.textures==len(package['textures'])
            assert a.aiExportScene(reader,b'glb2',os.fsencode(glb),0)==0
        finally:a.aiReleaseImport(reader)
        b=glb.read_bytes();size=struct.unpack_from('<I',b,12)[0];doc=json.loads(b[20:20+size]);data=b[28+size:]
        def accessor(i,n):
            ac=doc['accessors'][i];v=doc['bufferViews'][ac['bufferView']]
            base=v.get('byteOffset',0)+ac.get('byteOffset',0)
            fmt=struct.Struct('<'+{5121:'B',5123:'H',5125:'I',5126:'f'}[ac['componentType']]*n)
            return [fmt.unpack_from(data,base+j*v.get('byteStride',fmt.size)) for j in range(ac['count'])]
        actual=Counter();uv_corners=0
        for node in doc['nodes']:
            assert not any(k in node for k in ('matrix','rotation','scale','translation'))
            if 'mesh' not in node:continue
            for prim in doc['meshes'][node['mesh']]['primitives']:
                attr=prim['attributes'];m=doc['materials'][prim['material']]
                points=[(x*.01,-z*.01,y*.01) for x,y,z in accessor(attr['POSITION'],3)]
                uv=accessor(attr['TEXCOORD_0'],2) if 'TEXCOORD_0'in attr else [()]*len(points)
                corners=[tuple(round(x,5)for x in (*p,*u))for p,u in zip(points,uv)]
                ids=accessor(prim['indices'],1)
                if 'TEXCOORD_0'in attr:uv_corners+=len(ids)
                for j in range(0,len(ids),3):
                    tri=tuple(corners[k[0]]for k in ids[j:j+3]);actual[node['name'],source_material(m['name']),cyclic(tri)]+=1
        # Sequential float32 conversions through centimetres introduce sub-micrometre errors.
        missing=list((expected-actual).elements())
        surplus=list((actual-expected).elements())
        max_delta=0.
        for name,material,shape in missing:
            matches=[]
            for j,(other_name,other_material,tri) in enumerate(surplus):
                if (name,material)!=(other_name,other_material) or any(len(a)!=len(b) for a,b in zip(shape,tri)):continue
                for rotation in range(3):
                    shifted=tri[rotation:]+tri[:rotation]
                    err=max(abs(x-y) for corner_a,corner_b in zip(shape,shifted) for x,y in zip(corner_a,corner_b))
                    if err<=3e-5:matches.append((err,j))
            if not matches:raise ValueError(('No matching oriented triangle',name,material,shape,surplus[:3]))
            error,j=min(matches)
            max_delta=max(max_delta,error)
            surplus.pop(j)
        assert not surplus
        import base64
        original_images={name:sha(base64.b64decode(blob)) for name,blob in package['textures'].items()}
        actual_images=[]
        for im in doc.get('images',[]):
            view=doc['bufferViews'][im['bufferView']]
            start=view.get('byteOffset',0)
            actual_images.append(sha(data[start:start+view['byteLength']]))
        assert Counter(actual_images)==Counter(original_images.values())
        bound={}
        for material in doc['materials']:
            slot=source_material(material.get('name',''))
            source_name=next((s for s in palette if material_ids[s]==slot),None)
            if source_name is None:continue
            expected_mat=package['materials'][source_name]
            for key,binding in [('texture',material.get('pbrMetallicRoughness',{}).get('baseColorTexture')),('normal',material.get('normalTexture'))]:
                if key not in expected_mat:continue
                if not binding: raise ValueError(f'{slot}: lost {key} in FBX round trip')
                if key=='normal' and abs(binding.get('scale',1.)-expected_mat.get('normal_strength',1.))>1e-5:
                    raise ValueError(f'{slot}: changed normal-map strength')
                actual_sha=actual_images[doc['textures'][binding['index']]['source']]
                assert actual_sha==original_images[expected_mat[key]]
                bound.setdefault(source_name,{})[key]=actual_sha
    reports=dict(file=target.name,bytes=target.stat().st_size,sha256=sha(target.read_bytes()),
                 exchange_units='FBX centimetre, +Y up; authored coordinates metre, +Z up',
                 library='Assimp 5',parts=len(package['parts']),materials=len(palette),triangles=sum(actual.values()),
                 textured_corners=uv_corners,embedded_images=original_images,material_image_bindings=bound,part_labels={f'part_{i:06d}':p['label'] for i,p in enumerate(package['parts'],1)},material_ids=material_ids,oriented_positions_and_uv_checked=True,maximum_rounded_component_difference=max_delta)
    report.write_text(json.dumps(reports,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('components','obj','target','report'):p.add_argument(name,type=Path)
    a=p.parse_args()
    main(json.loads(a.components.read_bytes()),a.obj,a.target,a.report)
