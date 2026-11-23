"""Check the three embedded brick finishes against world position, scale and sharing of edges."""
from collections import defaultdict
from pathlib import Path
import argparse
import hashlib
import json
import struct
import numpy as np

SPECS = {
 'Yanqing 121 | grey Flemish bond':((1.332,1.020),'88b77f655e6ea192d69b12db2e350465ab06dc268ae40d8f80f6a18890f8efac'),
 'Yanqing 121 | red soldier course':((.800,.400),'dab04eb5d2c78e96ecfbc845b19aa472a7b31ee1cc7076be2b38ec38abdb9ae8'),
 'Yanqing 121 | herringbone spandrel':((.64*np.sqrt(2),.64*np.sqrt(2)),'83a696c38d5a9a5a27bebc9178406eb4cdfd23dd73b9b7a3e8185d04697cbe11'),
}
TYPES={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}


def glb(path):
    b=path.read_bytes()
    if b[:4]!=b'glTF' or struct.unpack_from('<II',b,4)!=(2,len(b)):
        raise ValueError('Invalid GLB header')
    offset=12;chunks={}
    while offset<len(b):
        size,kind=struct.unpack_from('<II',b,offset);offset+=8
        chunks[kind]=b[offset:offset+size];offset+=size
    return json.loads(chunks[0x4e4f534a]),chunks[0x004e4942],hashlib.sha256(b).hexdigest()


def read_accessor(doc,blob,index):
    a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']]
    if 'sparse' in a or 'EXT_meshopt_compression' in view.get('extensions',{}):
        raise ValueError('Run on the raw or decoded asset')
    dt=np.dtype(TYPES[a['componentType']]);dims={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
    offset=view.get('byteOffset',0)+a.get('byteOffset',0)
    out=np.ndarray((a['count'],dims),dtype=dt,buffer=blob,offset=offset,
                   strides=(view.get('byteStride',dims*dt.itemsize),dt.itemsize))
    if a.get('normalized'):
        out=np.maximum(out.astype(float)/np.iinfo(dt).max,-1.)
    return out


def seam_report(xyz,uv,normal):
    # Match geometric edges across duplicated texture vertices. Opposite or duplicate
    # sheets are deliberately outside this comparison of adjacent outward-facing faces.
    edges=defaultdict(list)
    q=np.rint(xyz*1e6).astype(np.int64)
    for i,t in enumerate(q):
        for a,b in ((0,1),(1,2),(2,0)):
            v,w=tuple(t[a]),tuple(t[b]);ia,ib=(a,b) if v<w else (b,a)
            edges[tuple(sorted((v,w)))].append((i,ia,ib))
    counts=dict(coplanar_edges=0,coplanar_phase_mismatches=0,vertical_corners=0,
                vertical_corner_course_mismatches=0,vertical_corner_u_phase_changes=0)
    for refs in edges.values():
        if len(refs)!=2:continue
        (i,a,b),(j,c,d)=refs;cos=float(normal[i]@normal[j]);delta=uv[i,[a,b]]-uv[j,[c,d]]
        error=np.abs(delta-np.rint(delta));maxerr=error.max(axis=0)
        if cos>.999999:
            counts['coplanar_edges']+=1
            counts['coplanar_phase_mismatches']+=int(maxerr.max()>2e-5)
        elif abs(normal[i,2])<1e-5 and abs(normal[j,2])<1e-5 and abs(cos)<.9999:
            counts['vertical_corners']+=1
            counts['vertical_corner_course_mismatches']+=int(maxerr[1]>2e-5)
            counts['vertical_corner_u_phase_changes']+=int(maxerr[0]>2e-5)
    return counts


def verify(path):
    doc,blob,sha=glb(path);rows={};names_seen=set();ok=True
    if len(doc.get('nodes',[]))!=1 or set(doc['nodes'][0])-{'mesh','name','extras'}:
        raise ValueError('These metre checks expect one untransformed architectural mesh')
    for prim in doc['meshes'][doc['nodes'][0]['mesh']]['primitives']:
        mat=doc['materials'][prim['material']];name=mat.get('name')
        if name not in SPECS:continue
        if name in names_seen:raise ValueError('Expected one batched primitive per brick finish')
        names_seen.add(name);repeat,expected_hash=SPECS[name]
        infos=mat['pbrMetallicRoughness']['baseColorTexture'];tex=doc['textures'][infos['index']];image=doc['images'][tex['source']]
        bv=doc['bufferViews'][image['bufferView']];a=bv.get('byteOffset',0);image_sha=hashlib.sha256(blob[a:a+bv['byteLength']]).hexdigest()
        sam=doc.get('samplers',[{}])[tex['sampler']] if 'sampler' in tex else {};wrap=[sam.get(k,10497) for k in ['wrapS','wrapT']]
        attrs=prim['attributes'];idx=read_accessor(doc,blob,prim['indices']).reshape(-1,3)
        vertices=read_accessor(doc,blob,attrs['POSITION']).astype(float);xyz=(vertices[:,[0,2,1]]*[1,-1,1])[idx]
        texcoords=read_accessor(doc,blob,attrs['TEXCOORD_'+str(infos.get('texCoord',0))]).astype(float);uv=texcoords[idx]
        if not np.isfinite(uv).all():raise ValueError('Non-finite UVs')
        # The model uses planar world coordinates, choosing floor coordinates near horizontal.
        edges=xyz[:,1:]-xyz[:,:1];n=np.cross(edges[:,0],edges[:,1]);n/=np.linalg.norm(n,axis=1)[:,None]
        tangent=np.column_stack([-n[:,1],n[:,0],np.zeros(len(n))]);wall=np.abs(n[:,2])<=.9
        tangent[wall]/=np.linalg.norm(tangent[wall],axis=1)[:,None];up=np.cross(n,tangent)
        tangent[~wall]=[1,0,0];up[~wall]=[0,1,0]
        expected=np.stack([np.einsum('tij,tj->ti',xyz,tangent),np.einsum('tij,tj->ti',xyz,up)],axis=2)
        predicted=expected/np.array(repeat)
        if name.endswith('herringbone spandrel'):
            predicted[:,:,1] *= -1  # GLB texture V runs down the original PNG.
        err=uv-predicted
        # Subtract one corner: metric scale is independently checked from absolute UV phase.
        edge_error=np.max(np.abs((err[:,1:]-err[:,:1])*np.array(repeat)),axis=(1,2))
        phase_error=np.max(np.abs(err-np.rint(err)),axis=(1,2))
        # Finite FLOAT32 coordinates on a 3 mm bevel can underdetermine its normal.
        # Propagate their half-ULP through the two-edge cross product and the world
        # tangent projection. UV gradients and coplanar shared edges remain independently tested.
        tiny=1e-12
        half_ulp=np.max(np.spacing(np.abs(xyz).astype(np.float32)),axis=(1,2))*.5
        edge_norm=np.linalg.norm(edges,axis=2)
        double_area=np.linalg.norm(np.cross(edges[:,0],edges[:,1]),axis=1)
        direction_error=4*np.sqrt(3)*half_ulp*(edge_norm.sum(axis=1))/np.maximum(double_area,tiny)
        phase_tolerance=.00002+(4*direction_error*np.max(np.linalg.norm(xyz,axis=2),axis=1)/min(repeat))
        phase_out=int(np.count_nonzero(phase_error>phase_tolerance))
        du,dv=uv[:,1]-uv[:,0],uv[:,2]-uv[:,0];uv_zero=int(np.count_nonzero(np.abs(du[:,0]*dv[:,1]-du[:,1]*dv[:,0])<1e-13))
        se=seam_report(xyz,uv,n)
        good=(image_sha==expected_hash and image['mimeType']=='image/png' and wrap==[10497,10497]
              and np.max(edge_error)<1e-4 and phase_out==0 and not uv_zero
              and not se['coplanar_phase_mismatches'] and not se['vertical_corner_course_mismatches'])
        ok=ok and good
        rows[name]=dict(texture_sha256=image_sha,exact_original_png=image_sha==expected_hash,repeat_m=repeat,wrap=wrap,
                         triangles=len(idx),degenerate_uv_triangles=uv_zero,mapping_error_p99_m=float(np.percentile(edge_error,99)),
                         max_mapping_error_m=float(np.max(edge_error)),max_phase_residual_cycles=float(np.max(phase_error)),phase_outside_float32_bound=phase_out,
                         mapping_errors_above_0_1mm=int((edge_error>=1e-4).sum()),edge_checks=se,passed=bool(good))
    return dict(file=path.name,sha256=sha,triangle_count=sum(v['triangles'] for v in rows.values()),
                passed=bool(ok and names_seen==set(SPECS)),materials=rows)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    report=verify(a.mesh);a.out.write_text(json.dumps(report,indent=2)+'\n');print(report['passed'],report['triangle_count'],report['sha256'])
