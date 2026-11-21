"""Read the delivered additive primitives, confirm the roof silhouette and trace horizontal sight lines."""
from pathlib import Path
import argparse,collections,hashlib,json,struct
import numpy as np

HERE=Path(__file__).resolve().parent
def read_glb(path):
    with path.open('rb')as f:
        header=f.read(20);length=struct.unpack_from('<I',header,12)[0]
        d=json.loads(f.read(length));f.read(8);binary=f.read()
    def array(idx):
        a=d['accessors'][idx];bv=d['bufferViews'][a['bufferView']]
        offset=bv.get('byteOffset',0)+a.get('byteOffset',0)
        size={'VEC3':3,'SCALAR':1}[a['type']];dtype={5123:'<u2',5126:'<f4'}[a['componentType']]
        return np.frombuffer(binary,dtype=dtype,count=size*a['count'],offset=offset).reshape(-1,size)
    return d,array

def first_hit(origin,ray,tri):
    edge=tri[:,1]-tri[:,0];side=tri[:,2]-tri[:,0];normal=np.cross(ray,side)
    den=np.einsum('ij,ij->i',edge,normal);inv=np.divide(1,den,out=np.zeros_like(den),where=abs(den)>1e-10)
    delta=origin-tri[:,0];u=np.einsum('ij,ij->i',delta,normal)*inv;q=np.cross(delta,edge)
    v=(q@ray)*inv;t=np.einsum('ij,ij->i',side,q)*inv
    mask=(abs(den)>1e-10)&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(t>0)
    return int(np.argmin(np.where(mask,t,np.inf))) if mask.any()else None

def main():
    cli=argparse.ArgumentParser();cli.add_argument('dir',type=Path);cli.add_argument('report',type=Path);args=cli.parse_args()
    c=json.loads((HERE/'geometry-input.json').read_bytes());front=c['front'];old_masonry_top=33.400001525878906
    mid=np.array(front['center_local_east_north_m']);tan=np.array(front['tangent_east_north']);out=np.array(front['outward_normal_east_north'])
    P=np.array(c['source_projection']);rows={}
    for role in ['raw','web','lod']:
        d,get=read_glb(args.dir/(role+'.glb'));tr=[];tags=[];parts={};top=None;rawtip=None
        for mesh in d['meshes'][-3:]:
            prim,=mesh['primitives'];pos=get(prim['attributes']['POSITION']).astype(float)
            rel=pos[:,[0,2]]*np.array([1,-1])-mid;local=np.c_[rel@tan,pos[:,1],rel@out];faces=get(prim['indices']).reshape(-1,3);tet=local[faces]
            counts=collections.Counter((int(a),int(b)) for row in faces for a,b in zip(row,np.roll(row,-1)))
            assert all(counts[(b,a)]==n==1 for (a,b),n in counts.items()),mesh['name']
            # glTF is right-handed; facade-u/height/depth is left handed for this wall.
            t=pos[faces]-pos[faces[0,0]];vol=np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6
            assert vol>1e-6
            parts[mesh['name']]={'triangles':len(tet),'volume_m3':float(vol),'lowest_z_m':float(pos[:,1].min()),'highest_z_m':float(pos[:,1].max())}
            tr.extend(tet);tags.extend([mesh['name']]*len(tet))
            if 'finial'in mesh['name']:rawtip=local[local[:,1]>=local[:,1].max()-.00001].mean(axis=0);top=float(local[:,1].max())
            if 'hanging'in mesh['name']:cloth=local
        tr=np.array(tr);u,_,depth=rawtip
        image=P@np.r_[rawtip,1];err=np.linalg.norm(image[:2]/image[2]-c['mast_tip_px']);assert err<1.5 and top>old_masonry_top
        probes=[]
        for s,z,part in [(u,34.5,'roof staff'),(u,35.45,'roof staff'),(u,35.636,'staff finial'),(.48,33.55,'hanging flag'),(.62,33.18,'hanging flag'),(.92,33.4,None),(-.48,34.2,None),(.72,35.72,None)]:
            hit=first_hit(np.array([s,z,0.]),np.array([0.,0.,-1.]),tr)
            name=tags[hit]if hit is not None else None
            assert (name is None if part is None else name and part in name),(role,s,z,part,name)
            probes.append(dict(u_m=float(s),z_m=z,part=name))
        rows[role]={'parts':parts,'ray_checks':probes,'apex_m':top,'original_masonry_top_m':old_masonry_top,
            'staff_cap_reprojection_error_px':float(err),'all_new_parts_above_m':float(tr[:,:,1].min()),'new_facade_local_limits_m':[tr.min((0,1)).tolist(),tr.max((0,1)).tolist()]}
    args.report.write_text(json.dumps({'passed':True,'variants':rows},indent=2)+'\n')
if __name__=='__main__':main()
