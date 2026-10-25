"""Read-only GLB integrity, geometry, size, bounds and external-resource checks."""
import hashlib,json,struct
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
results=[]
for name in ['shanghai-club','union-building','north-china-daily-news']:
    path=ROOT/(name+'.glb')
    if not path.exists():continue
    blob=path.read_bytes();magic,version,length=struct.unpack_from('<III',blob)
    assert magic==0x46546c67 and version==2 and length==len(blob)
    jl,jt=struct.unpack_from('<II',blob,12);assert jt==0x4e4f534a
    g=json.loads(blob[20:20+jl]);pos=20+jl;bl,bt=struct.unpack_from('<II',blob,pos);assert bt==0x004e4942
    buf=blob[pos+8:pos+8+bl]
    def array(i):
        a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
        dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
        n={'SCALAR':1,'VEC3':3,'VEC2':2,'VEC4':4}[a['type']]
        offset=v.get('byteOffset',0)+a.get('byteOffset',0);size=np.dtype(dtype).itemsize
        return np.ndarray((a['count'],n),dtype=dtype,buffer=buf,offset=offset,strides=(v.get('byteStride',size*n),size))
    mn=np.full(3,np.inf);mx=-mn;count=0;degen=0;finite=True;normerror=0
    for mesh in g['meshes']:
        for prim in mesh['primitives']:
            assert prim.get('mode',4)==4
            v=array(prim['attributes']['POSITION']);idx=array(prim['indices']).reshape(-1,3)
            assert idx.max()<len(v)
            mn=np.minimum(mn,v.min(0));mx=np.maximum(mx,v.max(0));finite &= bool(np.isfinite(v).all())
            a=v[idx];areas=np.linalg.norm(np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]),axis=1)*.5
            degen+=int((areas<=1e-10).sum());count+=len(idx)
            if 'NORMAL' in prim['attributes']:
                norms=array(prim['attributes']['NORMAL']);finite &= bool(np.isfinite(norms).all())
                normerror=max(normerror,float(np.abs(np.linalg.norm(norms,axis=1)-1).max()))
    assert finite and normerror<.001 and degen==0
    assert len(blob)<100_000_000 and not any('uri' in x for x in g.get('buffers',[])+g.get('images',[]))
    assert mn[1]>=-1e-6
    meta=json.loads((ROOT/(name+'.json')).read_text());assert meta['bytes']==len(blob)
    r={'id':name,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest(),'triangles':count,
      'boundsGltfXYZ':[mn.tolist(),mx.tolist()],'finitePositionsAndNormals':finite,'maxNormalLengthError':normerror,
      'degenerateTriangleCount':degen,'externalResources':0,'under100MB':True,'metadataBytesMatch':True}
    results.append(r);print(json.dumps(r))
(ROOT/'validation.json').write_text(json.dumps({'status':'pass','models':results},indent=2))
