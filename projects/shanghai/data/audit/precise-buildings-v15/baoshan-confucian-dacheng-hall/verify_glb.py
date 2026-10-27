#!/usr/bin/env python3
"""Read actual uncompressed model buffers; independently check mesh and courtyard geometry."""
import argparse, hashlib, json, struct
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon

def verify(path, source):
    data=path.read_bytes()
    assert len(data)<100_000_000
    magic,version,size=struct.unpack_from('<4sII',data)
    assert (magic,version,size)==(b'glTF',2,len(data))
    length,kind=struct.unpack_from('<II',data,12)
    assert kind==0x4e4f534a
    doc=json.loads(data[20:20+length]); off=20+length
    blen,bkind=struct.unpack_from('<II',data,off)
    assert bkind==0x004e4942
    binary=data[off+8:off+8+blen]
    assert not doc.get('images'), 'This authored model declares no photographic textures'
    assert all(not b.get('uri') for b in doc['buffers'])
    def array(i):
        a=doc['accessors'][i]; b=doc['bufferViews'][a['bufferView']]
        assert not a.get('sparse') and not b.get('extensions'), 'Decode compressed model first'
        dt={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
        n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
        stride=b.get('byteStride',np.dtype(dt).itemsize*n)
        start=b.get('byteOffset',0)+a.get('byteOffset',0)
        result=np.ndarray((a['count'],n),dtype=dt,buffer=binary,offset=start,strides=(stride,np.dtype(dt).itemsize))
        assert np.isfinite(result).all()
        return result
    all_tri=[]; rows=[]; mins=[]; maxs=[]
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            assert p.get('mode',4)==4
            xyz=array(p['attributes']['POSITION']); normals=array(p['attributes']['NORMAL'])
            ids=array(p['indices']).ravel().astype(np.int64)
            assert len(ids)%3==0 and ids.min()>=0 and ids.max()<len(xyz)
            triangles=xyz[ids.reshape(-1,3)].astype(np.float64)
            cross=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
            area=np.linalg.norm(cross,axis=1)/2
            assert (area>1e-10).all(), 'Degenerate triangles'
            error=float(np.abs(np.linalg.norm(normals,axis=1)-1).max())
            assert error<.002, 'Non-unit normals'
            all_tri.append(triangles);mins.append(xyz.min(0));maxs.append(xyz.max(0))
            rows.append({'mesh':mesh.get('name'),'triangles':len(triangles),'vertices':len(xyz),'normal_max_length_error':error,'minimum_triangle_area_m2':float(area.min())})
    tris=np.concatenate(all_tri)
    # Actual source rings share the model's fixed ENU origin. Sample the interior
    # of each courtyard independently, then check for any overhead model triangle.
    local=source['model_geometry_local_east_north_m']
    if isinstance(local,dict): rings=local['coordinates']
    else: rings=local
    probes=[]
    for i,ring in enumerate(rings[1:],1):
        pt=Polygon(ring).representative_point(); x,y=pt.x,-pt.y
        a=tris[:,0][:,[0,2]];u=tris[:,1][:,[0,2]]-a;v=tris[:,2][:,[0,2]]-a
        det=u[:,0]*v[:,1]-u[:,1]*v[:,0]; good=np.abs(det)>1e-10
        w=np.array([x,y])-a
        s=np.zeros(len(tris));t=s.copy()
        s[good]=(w[good,0]*v[good,1]-w[good,1]*v[good,0])/det[good]
        t[good]=(u[good,0]*w[good,1]-u[good,1]*w[good,0])/det[good]
        hit=good&(s>=-1e-8)&(t>=-1e-8)&(s+t<=1+1e-8)
        z=tris[:,0,1]+s*(tris[:,1,1]-tris[:,0,1])+t*(tris[:,2,1]-tris[:,0,1])
        roof=z[hit&(z>.5)]
        probes.append({'source_courtyard':i,'probe_enu':[pt.x,pt.y], 'overhead_triangles_above_half_metre':int(len(roof)),'highest_hit_m':float(roof.max()) if len(roof) else None})
    assert len(probes)==len(rings)-1 and all(p['overhead_triangles_above_half_metre']==0 for p in probes), 'Source courtyard sample covered by geometry'
    rounded = np.round(tris, 8)
    order = np.lexsort((rounded[:,:,2], rounded[:,:,1], rounded[:,:,0]), axis=1)
    canonical = np.take_along_axis(rounded, order[:,:,None], axis=1).reshape(len(tris), 9)
    packed = np.ascontiguousarray(canonical).view(np.dtype((np.void, canonical.dtype.itemsize*9))).ravel()
    duplicate_count = len(packed)-len(np.unique(packed))
    assert duplicate_count==0, f'Duplicate coincident triangles: {duplicate_count}'
    return {'file':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'triangles':len(tris),'bounds_gltf':[np.min(mins,axis=0).tolist(),np.max(maxs,axis=0).tolist()],'meshes':rows,'courtyard_probes':probes,'duplicate_coincident_triangles':duplicate_count,'passed':True,'scope':'Actual buffers/indices/normals/degeneracy and sky probes for each source courtyard (none for this solid footprint) plus coincident-face checks; no claim of survey accuracy or every opening.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--geometry',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('models',type=Path,nargs='+');a=p.parse_args()
    assert not a.output.exists(), 'Preserve prior review'
    result={'models':[verify(x,json.loads(a.geometry.read_text())) for x in a.models]}
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([{k:r[k] for k in ('file','bytes','triangles','bounds_gltf','courtyard_probes','passed')} for r in result['models']],indent=2))
