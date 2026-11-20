"""Measure bridge clearances and ray-test six glazed bays on the actual three GLBs."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import struct
import numpy as np


def load_geometry(path):
    data=path.read_bytes()
    n,kind=struct.unpack_from('<II',data,12)
    assert kind==0x4e4f534a
    doc=json.loads(data[20:20+n])
    binary=memoryview(data)[28+n:]

    def values(index):
        item=doc['accessors'][index]
        view=doc['bufferViews'][item['bufferView']]
        dtype=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[item['componentType']])
        width={'SCALAR':1,'VEC3':3}[item['type']]
        stride=view.get('byteStride',dtype.itemsize*width)
        return np.ndarray((item['count'],width),dtype=dtype,buffer=binary,
                          offset=view.get('byteOffset',0)+item.get('byteOffset',0),
                          strides=(stride,dtype.itemsize))

    triangles=[]
    material_indices=[]
    scene_nodes=doc['scenes'][doc['scene']]['nodes']
    assert len(scene_nodes)==len(doc['nodes'])
    for index in scene_nodes:
        node=doc['nodes'][index]
        assert not set(node)&{'translation','rotation','scale','matrix','children'}
        for prim in doc['meshes'][node['mesh']]['primitives']:
            assert prim.get('mode',4)==4
            pts=values(prim['attributes']['POSITION'])
            tri=pts[values(prim['indices']).reshape((-1,3))].astype(float)
            triangles.append(tri)
            material_indices.extend([prim['material']]*len(tri))
    triangles=np.concatenate(triangles)
    return triangles,np.asarray(material_indices),[s['name'] for s in doc['materials']]


def face_hit(triangles, material, names, x, height):
    """Cast from local north, or negative GLB Z. Test barycentric containment in XY."""
    a,b,c=triangles.transpose((1,0,2))
    u=b-a
    v=c-a
    dx=x-a[:,0]
    dy=height-a[:,1]
    den=u[:,0]*v[:,1]-v[:,0]*u[:,1]
    ok=np.abs(den)>1e-11
    w1=np.divide(dx*v[:,1]-dy*v[:,0],den,out=np.zeros(len(a)),where=ok)
    w2=np.divide(u[:,0]*dy-u[:,1]*dx,den,out=np.zeros(len(a)),where=ok)
    ok &= (w1>=-1e-8)&(w2>=-1e-8)&(w1+w2<=1.00000001)
    z=np.where(ok,a[:,2]+w1*u[:,2]+w2*v[:,2],np.inf)
    first=z.argmin()
    assert np.isfinite(z[first]), (x,height)
    return names[material[first]],round(float(z[first]),4)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    manifest_path=args.assets/'manifest.json'
    manifest=json.loads(manifest_path.read_bytes())
    dims=manifest['selected_dimensions']
    base=dims['soffit_above_ground_m']
    height=dims['height_m']
    span=dims['span_m']
    checks={}
    for variant,asset in manifest['assets'].items():
        path=args.assets/asset['file']
        content=path.read_bytes()
        assert len(content)==asset['bytes']<100_000_000 and sha256(content).hexdigest()==asset['sha256']
        if variant=='native':
            continue
        tri,material,names=load_geometry(path)
        low,high=tri.min(axis=(0,1)),tri.max(axis=(0,1))
        assert np.isfinite(tri).all() and len(tri)==asset['triangles']
        assert abs(low[1]-base)<1e-4 and 20.7<high[1]<20.8
        cross=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)
        assert (cross>1e-10).all()
        hits=[]
        for col in range(6):
            x=-span/2+span*(col+.5)/6+.17
            for row,frac in enumerate((.4775,.9145)):
                m,z=face_hit(tri,material,names,x,base+height*frac)
                assert m=='Grey green glazing' and z > -dims['depth_m']/2 + .10, (variant,col,row,m,z)
                hits.append({'bay':col+1,'row':row+1,'north_glazing_glb_z_m':z})
            m,z=face_hit(tri,material,names,x,base+height*.74)
            assert ('brick' in m or 'masonry' in m) and z<=-dims['depth_m']/2+.001
        checks[variant]={'asset_sha256':asset['sha256'],'bounds_glb_m':[low.tolist(),high.tolist()],
                         'triangles':len(tri),'glazed_opening_probes':hits,'brick_spandrel_probes':6}
    result={'model_id':manifest['id'],'checked_at_utc':datetime.now(timezone.utc).isoformat(),'passed':True,
            'manifest_sha256':sha256(manifest_path.read_bytes()).hexdigest(),
            'checker_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
            'scope':'Actual geometry in metres; route navigation and precise wall ties are reviewed separately.',
            'geometry':checks,'actual_clearance_m':base}
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    main()
