"""Append a photo-constrained flagstaff to the existing Bund 14 optical and LOD meshes."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'bund17/revisions/street-wing-doors'))
from build_wing_doors import Parts, chunks, glb

SHAFT = 'Bund 14 | painted flagstaff'
CAP = 'Bund 14 | rounded staff cap'
FLAG = 'Bund 14 | gathered red fabric'
MATERIALS = {SHAFT: ([.29,.27,.24,1], .37, .64), CAP: ([.20,.235,.22,1], .47,.54),
             FLAG: ([.63,.018,.026,1], 0,.91)}

def from_pixel(pixel, depth, projection):
    rows = projection[:2] - np.array(pixel)[:,None] * projection[2]
    return np.linalg.solve(rows[:,:2], -rows[:,2] * depth - rows[:,3])

def instances(lod):
    cfg = json.loads((HERE/'geometry-input.json').read_bytes())
    matrix = np.array(cfg['source_projection'])
    edge = cfg['front']; center = np.array(edge['center_local_east_north_m'])
    tangent = np.array(edge['tangent_east_north']); outward = np.array(edge['outward_normal_east_north'])
    depth = -cfg['staff_front_setback_m']
    u, tip = from_pixel(cfg['mast_tip_px'],depth,matrix)
    def point(s,z,d):
        east,north=center+s*tangent+d*outward
        return [east,z,-north]
    sides=10 if lod else 20
    shaft=Parts(); radius=cfg['shaft_radius_m']
    shaft.tube(SHAFT,[point(u,cfg['base_z_m']-.008,depth),point(u,tip-.048,depth)],radius,sides)
    yield 'Bund14 | roof staff',shaft.data()
    cap=Parts();verts=[];faces=[];knob=cfg['finial_radius_m']
    for z,scale in [(-.094,.36),(-.074,.85),(-.046,1.),(-.019,.77),(-.004,.33)]:
        for j in range(sides):
            theta=j*math.tau/sides
            verts.append(point(u+knob*scale*math.cos(theta),tip+z,depth+knob*scale*math.sin(theta)))
    # Internal ring order follows the facade's east/north basis transformed to glTF.
    for i in range(4):
        for j in range(sides):
            a=i*sides+j; b=i*sides+(j+1)%sides
            faces.extend(((a,b+sides,b),(a,a+sides,b+sides)))
    for j in range(1,sides-1):
        faces.extend(((0,j,j+1),(4*sides,4*sides+j+1,4*sides+j)))
    cap.surface(CAP,verts,faces)
    yield 'Bund14 | staff finial',cap.data()
    # Two sides and a closed hem give the hanging fabric thickness. Its visible outside
    # edge is registered to the red pixels, and its upper part falls behind the crest.
    edge_top,edge_bot=[from_pixel(x,depth,matrix)for x in cfg['visible_red_edge_px']]
    strips=8 if lod else 16;cols=4 if lod else 8
    cloth=Parts();net=[];idx=[]
    def vert(face,i,j):return (face*(strips+1)+i)*(cols+1)+j
    for face in range(2):
        for i in range(strips+1):
            v=i/strips
            free_u=np.interp(v,[0,.21,.62,1],[u+.032,u+.16,edge_top[0],edge_bot[0]])
            free_z=np.interp(v,[0,.62,1],[tip-.20,edge_top[1],edge_bot[1]])
            for j in range(cols+1):
                w=j/cols
                s=u+radius+(free_u-u-radius)*w
                held_z=(tip-.17)*(1-v)+(edge_bot[1]+.33)*v
                z=held_z*(1-w)+free_z*w
                fold=.040*math.sin(w*math.tau*1.7+v*.55)*math.sin(w*math.pi)*(.40+.60*v)
                net.append(point(s,z,depth+fold+.004*(1 if face else -1)))
    def quad(a,b,c,d):idx.extend(((a,b,c),(a,c,d)))
    for i in range(strips):
        for j in range(cols):
            for f in range(2):
                corners=[vert(f,i,j),vert(f,i+1,j),vert(f,i+1,j+1),vert(f,i,j+1)]
                quad(*(corners if f else corners[::-1]))
    rim=[(0,j)for j in range(cols+1)]+[(i,cols)for i in range(1,strips+1)]+[(strips,j)for j in range(cols-1,-1,-1)]+[(i,0)for i in range(strips-1,0,-1)]
    for a,b in zip(rim,rim[1:]+rim[:1]):quad(vert(0,*b),vert(0,*a),vert(1,*a),vert(1,*b))
    cloth.surface(FLAG,net,idx)
    yield 'Bund14 | 2025 hanging flag',cloth.data()

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
                      'bytes':target.stat().st_size,'added_triangles':total,'new_editable_parts':3}
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
