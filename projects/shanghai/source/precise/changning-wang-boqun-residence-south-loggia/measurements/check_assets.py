"""Independently decode shipped GLB triangles, shoot two-sided rays, and verify real voids."""
from pathlib import Path
import hashlib,json,struct,sys,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
R=10.6; H=6.15; LOWER=2.6; UPPER=6.94; ROOF=11.39
def pt(s,d,z):
    return np.array([(R-d)*math.sin(s/R), R*math.cos(H/R)-(R-d)*math.cos(s/R), z])
def get_mesh(file):
    data=file.read_bytes();magic,version,total=struct.unpack_from('<4sII',data)
    assert (magic,version,total)==(b'glTF',2,len(data))
    length,kind=struct.unpack_from('<I4s',data,12);assert kind==b'JSON'
    j=json.loads(data[20:20+length]);raw=memoryview(data)[28+length:]
    def value(k):
        a=j['accessors'][k];v=j['bufferViews'][a['bufferView']]
        t={'VEC3':3,'VEC2':2,'SCALAR':1}[a['type']]
        n=a['count'];dt={5123:'<u2',5126:'<f4'}[a['componentType']]
        return np.frombuffer(raw,dtype=dt,count=n*t,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(n,t)
    faces=[];names=[];mat=[];uv=[]
    for node in j['nodes']:
        for prim in j['meshes'][node['mesh']]['primitives']:
            ids=value(prim['indices']).reshape(-1,3)
            xyz=value(prim['attributes']['POSITION']).astype(float)
            norm=value(prim['attributes']['NORMAL']);tex=value(prim['attributes']['TEXCOORD_0'])
            assert np.isfinite(xyz).all() and np.isfinite(tex).all() and np.allclose(np.linalg.norm(norm,axis=1),1,atol=.00001)
            uv.append(len(tex));author=xyz[:,[0,2,1]].copy();author[:,1]*=-1
            faces.append(author[ids]);names.extend([node['name']]*len(ids));mat.extend([j['materials'][prim['material']]['name']]*len(ids))
    return np.concatenate(faces),np.array(names),np.array(mat),sum(uv)

def queries():
    rays=[]
    def front(label,s,h,expected,d0=-.65,d1=.77):
        rays.append((label,pt(s,d0,h),pt(s,d1,h),expected))
    for i,(a,b) in enumerate(zip([-H,-2.14,2.14],[-2.14,2.14,H])):
        for frac in [.23,.5,.77]:
            front(f'lower open bay {i+1} {frac}',a+frac*(b-a),4.62,None)
        front(f'lower arch crown {i+1}',(a+b)/2,6.34,'Open_arcade')
    for i,s in enumerate([-H,-2.14,2.14,H]):front('lower pier '+str(i+1),s,4.5,'Arcade_pier')
    edges=[-H,-4.05,-2.07,2.07,4.05,H]
    for i,(a,b) in enumerate(zip(edges,edges[1:])):
        for f in [.16,.53,.84]:
            front(f'upper glass {i+1} {f}',a+.15+f*(b-a-.3),9.1,'glass')
        span=b-a-.30;cells=4 if i==2 else 2
        for k in range(cells):
            mid=a+.15+(k+.5)*span/cells
            front(f'quatrefoil hole {i+1}.{k+1}',mid,UPPER+.765,None)
            front(f'quatrefoil stone {i+1}.{k+1}',mid+.40*span/cells,UPPER+.765+.27,'pierced_apron')
    for i,(a,b) in enumerate(zip([-H,-2.07,2.07],[-2.07,2.07,H])):
        width=(b-a)/14
        for k in [2,6,10]:
            front(f'terrace baluster {i+1}.{k}',a+width*(k+.5),ROOF+.57,'balusters')
            front(f'terrace air {i+1}.{k}',a+width*(k+.84),ROOF+.57,None)
    for sign in (-1,1):
        for k in [1,4,7,10,13]:
            s=sign*(2.05+(k+.5)*(6.85-2.05)/15);z=LOWER*(1-k/15)
            rays.append((f'tread {sign:+}/{k+1}',pt(s,-1.1,z+.10),pt(s,-1.1,z-.11),'treads'))
    for c in [-.54,.82]:front('basement opening '+str(c),c,.65,None,-3.,-2.15)
    return rays

def test(file):
    faces,names,materials,uv_count=get_mesh(file)
    v0=faces[:,0];e1=faces[:,1]-v0;e2=faces[:,2]-v0;output=[]
    for label,origin,end,expected in queries():
        ray=end-origin
        p=np.cross(ray,e2);det=np.einsum('ij,ij->i',e1,p);good=np.abs(det)>1e-10
        idet=np.zeros_like(det);idet[good]=1/det[good]
        offset=origin-v0;u=np.einsum('ij,ij->i',offset,p)*idet
        q=np.cross(offset,e1);v=q@ray*idet;t=np.einsum('ij,ij->i',e2,q)*idet
        hit=np.flatnonzero(good&(u>=-1e-8)&(v>=-1e-8)&((u+v)<=1.00000001)&(t>1e-7)&(t<1.000001))
        closest=hit[np.argmin(t[hit])] if len(hit) else None
        obj=str(names[closest]) if closest is not None else None
        assert (obj is None) if expected is None else (obj and expected in obj), (file.name,label,obj,expected)
        output.append({'ray':label,'expected_group_contains':expected,'actual_group':obj,'hit_material':None if closest is None else str(materials[closest])})
    return {'file':file.name,'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'triangles':len(faces),'uv_vertices':uv_count,'actual_bbox_xyz_m':[faces.min(axis=(0,1)).tolist(),faces.max(axis=(0,1)).tolist()],'rays':output}
if __name__=='__main__':
    directory=Path(sys.argv[1]);dest=Path(sys.argv[2])
    out=[test(directory/(name+'.glb')) for name in ('raw','full','lod')]
    assert out[0]['triangles']>out[1]['triangles']>out[2]['triangles']
    dest.write_text(json.dumps({'passed':True,'roles':out},indent=2)+'\n')
    print([(r['file'],len(r['rays']),r['triangles']) for r in out])
