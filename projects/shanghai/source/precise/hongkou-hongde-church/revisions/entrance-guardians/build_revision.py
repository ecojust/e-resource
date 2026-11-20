"""Append the two dated entrance sculptures to the three published Hongde GLBs."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import runpy
from guardians import HERE, PALETTE, meshes

PROJECT = HERE.parents[4]
# These helpers preserve the original GLB binary (including meshopt fallbacks).
GLB = runpy.run_path(str(PROJECT/'source/precise/bund17/revisions/street-wing-doors/build_wing_doors.py'))
BASE = json.loads((HERE/'baseline.json').read_bytes())


def payload(lod):
    result={}
    for name,materials in meshes(lod).items():
        item=GLB['Parts']()
        item.by_material=materials
        assert all(len(v)<=65535 for v,_ in materials.values())
        result[name]=item.data()
    return result


def append_sculptures(doc, original_binary, sculpture):
    binary=bytearray(original_binary)
    slots={}
    for name,(rgba,roughness) in PALETTE.items():
        assert all(old.get('name') != name for old in doc['materials'])
        slots[name]=len(doc['materials'])
        doc['materials'].append(dict(name=name,pbrMetallicRoughness=dict(
            baseColorFactor=rgba,metallicFactor=0,roughnessFactor=roughness)))

    def add_array(data, target, kind, component_type, include_bounds=False):
        binary.extend(b'\0'*(-len(binary)%4))
        start=len(binary)
        binary.extend(data.tobytes())
        doc['bufferViews'].append(dict(buffer=0,byteOffset=start,byteLength=data.nbytes,target=target))
        accessor=dict(bufferView=len(doc['bufferViews'])-1,componentType=component_type,count=len(data),type=kind)
        if include_bounds:
            accessor.update(min=data.min(axis=0).tolist(),max=data.max(axis=0).tolist())
        doc['accessors'].append(accessor)
        return len(doc['accessors'])-1

    count=0
    for name,materials in sculpture.items():
        primitives=[]
        for mat,(positions,normals,faces) in materials.items():
            attributes=dict(POSITION=add_array(positions,34962,'VEC3',5126,True),
                            NORMAL=add_array(normals,34962,'VEC3',5126))
            indices=add_array(faces.ravel(),34963,'SCALAR',5123)
            primitives.append(dict(attributes=attributes,indices=indices,material=slots[mat]))
            count+=len(faces)
        doc['meshes'].append(dict(name=name,primitives=primitives))
        doc['nodes'].append(dict(name=name,mesh=len(doc['meshes'])-1))
        doc['scenes'][doc.get('scene',0)]['nodes'].append(len(doc['nodes'])-1)
    doc['buffers'][0]['byteLength']=len(binary)
    return bytes(binary),count


def main():
    cli=ArgumentParser(description=__doc__)
    cli.add_argument('--project',type=Path,default=PROJECT)
    cli.add_argument('--output',type=Path,required=True)
    args=cli.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    reports={}
    for role in ['raw','web','lod']:
        ref=BASE['assets'][role];source=args.project/ref['file']
        assert sha256(source.read_bytes()).hexdigest()==ref['sha256']
        doc,binary=GLB['chunks'](source)
        new_binary,n=append_sculptures(doc,binary,payload(role=='lod'))
        out=args.output/source.name
        GLB['glb'](out,doc,new_binary)
        reports[role]=dict(sha256=sha256(out.read_bytes()).hexdigest(),bytes=out.stat().st_size,
                           added_triangles=n,triangles=BASE['prior_triangles'][role]+n)
    (args.output/'build-report.json').write_text(json.dumps(reports,indent=2)+'\n')


if __name__=='__main__':
    main()
