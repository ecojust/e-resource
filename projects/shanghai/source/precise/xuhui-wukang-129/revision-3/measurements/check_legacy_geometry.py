"""Compare oriented position and normal triples of every retained authoring component."""
from pathlib import Path
import argparse
from collections import Counter,defaultdict
import hashlib
import json
import struct
import numpy as np

LEGACY_SHA='c0915a9d76761865b4020d31397b8ef66ddb6efc4112bbee150264119754afa9'

def components(path):
    blob=path.read_bytes()
    json_size=struct.unpack_from('<I',blob,12)[0]
    doc=json.loads(blob[20:20+json_size])
    binary=memoryview(blob)[28+json_size:]
    report=json.loads(path.with_suffix('.geometry.json').read_bytes())
    assert hashlib.sha256(blob).hexdigest()==report['sha256']
    def array(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
        dtype=np.dtype({5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
        n={'VEC3':3,'SCALAR':1}[a['type']]
        return np.ndarray((a['count'],n),dtype=dtype,buffer=binary,
                          offset=v.get('byteOffset',0)+a.get('byteOffset',0),
                          strides=(v.get('byteStride',dtype.itemsize*n),dtype.itemsize))
    mesh={}
    for obj in doc['meshes']:
        for prim in obj['primitives']:
            material=doc['materials'][prim['material']]['name']
            assert material not in mesh
            ix=array(prim['indices']).reshape(-1,3)
            mesh[material]=(array(prim['attributes']['POSITION']),array(prim['attributes']['NORMAL']),ix)
    offsets=Counter();occurrences=Counter();out={}
    for part in report['part_summary']:
        m=part['material'];label=part['label'];key=(m,label,occurrences[m,label]);occurrences[m,label]+=1
        pos,normal,index=mesh[m];start=offsets[m];count=part['triangles'];ix=index[start:start+count]
        digest=hashlib.sha256();digest.update(pos[ix].tobytes());digest.update(normal[ix].tobytes())
        out[key]=(count,digest.hexdigest());offsets[m]+=count
    assert all(offsets[m]==len(vals[2]) for m,vals in mesh.items())
    return report['sha256'],out

def revised_opening(label):
    return label.startswith('E-upper-arched-door/') or any(label=='D-low-entrance/'+n for n in ('thick-arched-door-surround','nested-arch-moulding'))

def check(original,changed,lod):
    base,a=components(original);sig,b=components(changed)
    assert base==LEGACY_SHA
    records=defaultdict(list)
    for key,value in a.items():
        m,label,occurrence=key
        if revised_opening(label):
            records['original_opening_components_replaced'].append([label,m,occurrence]);continue
        if lod and ('tile' in label and ('lapped' in label or 'radial' in label)):
            assert key in b,key
            records['same_tile_layout_simplified_cross_sections'].append([label,m,occurrence]);continue
        if b.get(key)!=value:
            raise ValueError((key,value,b.get(key)))
        records['unchanged_components'].append([label,m,occurrence,value[0],value[1]])
    counts={k:len(v) for k,v in records.items()}
    return dict(original=base,changed=sig,lod=lod,comparison='Every corner of every original protected component is compared in material, triangle order, FLOAT32 position and normal. Metric UVs and revised colours are allowed. The far level separately checks the continued presence of every simplified roof tile.',
                counts=counts,unchanged_triangles=sum(r[3] for r in records['unchanged_components']),
                unchanged_signature=hashlib.sha256(json.dumps(records['unchanged_components'],separators=(',',':')).encode()).hexdigest(),
                replaced=records['original_opening_components_replaced'])
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('old',type=Path);cli.add_argument('new',type=Path);cli.add_argument('report',type=Path);cli.add_argument('--lod',action='store_true')
    args=cli.parse_args();report=check(args.old,args.new,args.lod)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(report['counts'],report['unchanged_triangles'])
