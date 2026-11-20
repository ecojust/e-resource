"""Add two carved fruit pendants beside Bund 3's northeast entrance arch."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
DOORS=HERE.parents[2]/'bund17/revisions/street-wing-doors'
sys.path.insert(0,str(DOORS))
from build_wing_doors import Parts,chunks,glb

STONE='Bund 3 carved fruit limestone'
BAND='Bund 3 recessed ribbon limestone'
MATERIALS={STONE:([.74,.71,.64,1],0,.76),BAND:([.659,.625,.553,1],0,.79)}

def berry(parts,x,z,d,radii,lod):
    """An individually carved berry or bud. Rings converge to distinct poles."""
    rx,rz,rd=radii
    sides,rings=(7,4) if lod else (12,7)
    pts=[(x,z-rz,d)]
    for j in range(1,rings):
        a=math.pi*j/rings
        for k in range(sides):
            b=math.tau*k/sides
            pts.append((x+rx*math.sin(a)*math.cos(b),z-rz*math.cos(a),d+rd*math.sin(a)*math.sin(b)))
    pts.append((x,z+rz,d));top=len(pts)-1
    faces=[]
    for i in range(sides):
        ni=(i+1)%sides
        faces.append((0,1+i,1+ni))
        for j in range(rings-2):
            a=1+sides*j+i;b=1+sides*j+ni
            faces.extend([(a,a+sides,b+sides),(a,b+sides,b)])
        faces.append((top,1+(rings-2)*sides+ni,1+(rings-2)*sides+i))
    # Local coordinates are (u,height,outward); geometric normals point
    # away from the sphere and the shell remains closed at both poles.
    pos=np.asarray(pts)
    f=np.asarray(faces)
    n=np.cross(pos[f[:,1]]-pos[f[:,0]],pos[f[:,2]]-pos[f[:,0]])
    dot=np.mean(np.einsum('ij,ij->i',n,pos[f].mean(axis=1)-[x,z,d]))
    if dot<0:f=f[:,[0,2,1]]
    parts.surface(STONE,pts,f.tolist())

def blade(parts,start,end,width,front,lod,material=STONE):
    """Ridged, lobed leaf with a closed underside and upturned point."""
    start,end=np.array(start),np.array(end);axis=end-start;side=np.array([-axis[1],axis[0]])/np.linalg.norm(axis)
    rings=6 if lod else 12;rows=[]
    for j in range(rings+1):
        t=j/rings;cen=start+axis*t
        lobe=(.72+.28*math.sin(t*5*math.pi)**2)*math.sin(t*math.pi)**.66
        half=max(.001,width*lobe)
        left,right=cen-side*half,cen+side*half
        profile=front+.055*math.sin(t*math.pi)+.020*t*t
        rows.extend([(*left,profile-.021),(*cen,profile+.029*lobe),(*right,profile-.021),(*cen,profile-.072)])
    faces=[]
    for j in range(rings):
        for i in range(4):
            a=j*4+i;b=j*4+(i+1)%4;faces.extend([(a,b,b+4),(a,b+4,a+4)])
    faces.extend([(0,2,1),(0,3,2),(4*rings,4*rings+1,4*rings+2),(4*rings,4*rings+2,4*rings+3)])
    rr=np.array(rows);fi=np.array(faces)
    volume=np.sum(np.einsum('ij,ij->i',rr[fi[:,0]],np.cross(rr[fi[:,1]],rr[fi[:,2]])))
    if volume<0:fi=fi[:,[0,2,1]]
    parts.surface(material,rows,fi.tolist())

def band(parts,z,lod):
    """A broad winding stone ribbon across the raised bunch, with two edges."""
    steps=8 if lod else 17;verts=[]
    for t in np.linspace(0,1,steps):
        x=-.169+.339*t;h=z+.115*t+.035*math.sin(t*math.pi)
        d=.148+.118*math.sin(t*math.pi)**.74
        verts.extend([(x,h-.036,d-.016),(x,h+.036,d-.016),(x,h+.036,d+.020),(x,h-.036,d+.020)])
    faces=[]
    for j in range(steps-1):
        for i in range(4):
            a=j*4+i;b=j*4+(i+1)%4;faces.extend([(a,b,b+4),(a,b+4,a+4)])
    ix=4*(steps-1);faces.extend([(0,2,1),(0,3,2),(ix,ix+1,ix+2),(ix,ix+2,ix+3)])
    xy=np.array(verts);f=np.array(faces);volume=np.einsum('ij,ij->',xy[f[:,0]],np.cross(xy[f[:,1]],xy[f[:,2]]))
    if volume<0:f=f[:,[0,2,1]]
    parts.surface(BAND,verts,f.tolist())

def pendant(lod):
    # The 2013 detail shows a top fixing, scalloped bow, two curled lateral
    # stems ending in round buds, two slanting bands, berries and a leafy tip.
    p=Parts();p.box(STONE,0,4.65,.087,.16,.016,.111)
    for s in (-1,1):
        for i in range(4):
            a=math.pi*(.10+i*.11)
            blade(p,(s*.045,4.48),(s*(.09+.11*math.cos(a)),4.48+.094*math.sin(a)),.037,.086,lod)
        p.tube(BAND,[(s*x,z,d)for x,z,d in [(.03,4.52,.123),(.12,4.47,.152),(.21,4.40,.158),(.29,4.39,.195),(.365,4.45,.212)]],.015,6 if lod else 10)
        berry(p,s*.367,4.45,.213,(.039,.040,.042),lod)
        for i in range(3):
            blade(p,(s*(.055+.055*i),4.51-.024*i),(s*(.16+.073*i),4.38+.006*i),.051-.006*i,.123-.010*i,lod)
    loop=[(.044*math.cos(a),4.51+.030*math.sin(a),.125)for a in np.linspace(0,math.tau,10 if lod else 20)]
    p.tube(BAND,loop,.012,6 if lod else 9)
    berry(p,0,3.91,.105,(.168,.432,.094),lod)
    tiers=[(4.31,[0],.073),(4.22,[-.080,.065],.076),(4.13,[-.124,0,.116],.074),
           (4.02,[-.134,-.041,.058,.139],.069),(3.92,[-.104,.001,.109],.072),
           (3.81,[-.103,.000,.100],.067),(3.70,[-.066,.047],.067),(3.60,[.010],.060)]
    for j,(z,positions,rad)in enumerate(tiers):
        for i,x in enumerate(positions):
            berry(p,x,z+.010*math.sin(j*2+i*1.6),.167+.033*(1-abs(x)/.18),(rad,rad*1.12,rad*.89),lod)
    for z in (3.83,4.08):band(p,z,lod)
    for s in (-1,1):
        blade(p,(s*.06,4.35),(s*.178,4.17),.053,.124,lod)
        blade(p,(s*.097,3.73),(s*.045,3.52),.046,.118,lod)
    blade(p,(-.032,3.68),(.006,3.42),.040,.13,lod)
    return p.data()

def instances(lod):
    # GroundPolygonLocalXZ is glTF east/south. Convert the northeast chamfer
    # to east/north before placing the two opposite jamb ornaments.
    v=json.loads((HERE/'geometry-input.json').read_bytes())
    a,b=np.asarray(v['chamfer_ends_east_north_m']);t=(b-a)/np.linalg.norm(b-a)
    outward=np.array([t[1],-t[0]]);mid=(a+b)/2
    basis=np.array([[t[0],0,-t[1]],[0,1,0],[outward[0],0,-outward[1]]])
    form=pendant(lod)
    for sign,side in [(-1,'east jamb'),(1,'west jamb')]:
        xy=mid+sign*v['distance_from_chamfer_axis_m']*t
        shift=[xy[0],0,-xy[1]]
        yield 'Bund03 | '+side+' | grape pendant',{label:((pos@basis+shift).astype('<f4'),(norm@basis).astype('<f4'),faces)for label,(pos,norm,faces)in form.items()}


def augment(original,binary,lod):
    doc=deepcopy(original);blob=bytearray(binary)
    indices={}
    for label,(base,metal,rough)in MATERIALS.items():
        assert not any(m.get('name')==label for m in doc['materials'])
        indices[label]=len(doc['materials']);doc['materials'].append({'name':label,'pbrMetallicRoughness':
            {'baseColorFactor':base,'metallicFactor':metal,'roughnessFactor':rough}})
    def add_array(array,target,kind,component,bounds=False):
        blob.extend(b'\0'*(-len(blob)%4));v=len(doc['bufferViews']);payload=array.tobytes()
        doc['bufferViews'].append({'buffer':0,'byteOffset':len(blob),'byteLength':len(payload),'target':target});blob.extend(payload)
        acc={'bufferView':v,'componentType':component,'count':len(array),'type':kind}
        if bounds:acc.update(min=array.min(0).tolist(),max=array.max(0).tolist())
        doc['accessors'].append(acc);return len(doc['accessors'])-1
    count=0;scene=doc['scenes'][doc.get('scene',0)]
    for name,parts in instances(lod):
        primitives=[]
        for material,(points,normals,faces)in parts.items():
            pos=add_array(points,34962,'VEC3',5126,True);normal=add_array(normals,34962,'VEC3',5126)
            idx=add_array(faces.ravel(),34963,'SCALAR',5123)
            primitives.append({'attributes':{'POSITION':pos,'NORMAL':normal},'indices':idx,'material':indices[material]})
            count+=len(faces)
        n=len(doc['meshes']);doc['meshes'].append({'name':name,'primitives':primitives})
        scene['nodes'].append(len(doc['nodes']));doc['nodes'].append({'name':name,'mesh':n})
    doc['buffers'][0]['byteLength']=len(blob)
    return doc,bytes(blob),count


def main():
    parser=argparse.ArgumentParser();parser.add_argument('prior',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();args.output.mkdir(exist_ok=True,parents=True)
    reference=json.loads((HERE/'baseline.json').read_bytes())['assets'];result={}
    for role in ('raw','web','lod'):
        path=args.prior/reference[role]['file']
        assert sha256(path.read_bytes()).hexdigest()==reference[role]['sha256']
        doc,binary=chunks(path);new,b,total=augment(doc,binary,role=='lod')
        target=args.output/(role+'.glb');glb(target,new,b)
        result[role]={'original_sha256':reference[role]['sha256'],'sha256':sha256(target.read_bytes()).hexdigest(),
                      'bytes':target.stat().st_size,'added_triangles':total,'new_editable_parts':2}
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
