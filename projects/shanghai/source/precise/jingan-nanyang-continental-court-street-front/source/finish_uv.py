import numpy as np
def metric_uv(p,scale_x=.92,scale_y=.52):
    xyz=np.asarray(p['vertices']);vs=[];uv=[];tris=[];ref={}
    for old in p['triangles']:
        a,b,c=xyz[list(old)];n=np.cross(b-a,c-a);n=n/np.linalg.norm(n)
        u=(1,0,0) if abs(n[2])>.65 else (-n[1],n[0],0)
        v=(0,1,0) if abs(n[2])>.65 else (0,0,1)
        u=np.asarray(u)/np.linalg.norm(u);key=tuple(u.round(4))+tuple(v);new=[]
        for i in old:
            pair=(i,key)
            if pair not in ref:
                ref[pair]=len(vs);vs.append(tuple(xyz[i]));uv.append((xyz[i]@u/scale_x,xyz[i]@v/scale_y))
            new.append(ref[pair])
        tris.append(tuple(new))
    p.update(vertices=vs,texcoords=uv,triangles=tris)

def map_return_faces(part,period_m):
    """Preserve the ornament face texture and map the cut side faces in their own plane."""
    xyz=list(part['vertices'])
    uv=list(part['texcoords'])
    tri=[]
    seams={}
    for indices in part['triangles']:
        local=np.array([uv[i]for i in indices]);area=np.linalg.det(local[1:]-local[0])
        if abs(area)>1.e-9:
            tri.append(indices)
            continue
        p=np.array([xyz[i]for i in indices]);n=np.cross(p[1]-p[0],p[2]-p[0])
        axis=int(np.argmax(np.abs(n)));keep=[j for j in range(3)if j!=axis]
        new=[]
        for i in indices:
            key=(i,axis)
            if key not in seams:
                seams[key]=len(xyz);xyz.append(xyz[i]);uv.append((np.asarray(xyz[i])[keep]/period_m).tolist())
            new.append(seams[key])
        tri.append(new)
    part.update(vertices=xyz,triangles=tri,texcoords=uv)
