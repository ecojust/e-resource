"""Build three ordinary GLB files with original, embedded masonry textures. Python stdlib."""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
from model import Model
from finish import PALETTE, TEXTURES, make_png

def linear(c):
    f=c/255
    return f/12.92 if f<=.04045 else ((f+.055)/1.055)**2.4


class Scene:
    def __init__(self):
        self.binary=bytearray()
        self.graph={'asset':{'version':'2.0','generator':'Yicun no. 4 gate and photographed gable / build.py'},
                    'scene':0, 'scenes':[{'nodes':[]}], 'nodes':[], 'meshes':[], 'materials':[],
                    'bufferViews':[], 'accessors':[], 'buffers':[], 'images':[], 'textures':[],
                    'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}]}

    def view(self,data,target=None):
        self.binary.extend(b'\0'*(-len(self.binary)%4))
        view={'buffer':0,'byteOffset':len(self.binary),'byteLength':len(data)}
        if target:view['target']=target
        self.graph['bufferViews'].append(view)
        self.binary.extend(data)
        return len(self.graph['bufferViews'])-1

    def accessor(self,values,fmt,ctype,kind,target,bounds=False):
        pack=struct.Struct('<'+fmt).pack
        buffer=self.view(b''.join(pack(*v) for v in values),target)
        a={'bufferView':buffer,'componentType':ctype,'count':len(values),'type':kind}
        if bounds:
            a['min']=list(map(min,zip(*values)));a['max']=list(map(max,zip(*values)))
        self.graph['accessors'].append(a)
        return len(self.graph['accessors'])-1

    def materials(self):
        for name,(label,color) in PALETTE.items():
            pbr={'metallicFactor':0.04 if name=='steel' else 0,'roughnessFactor':.29 if name=='glass' else .82}
            if name in TEXTURES:
                idx=len(self.graph['images'])
                self.graph['images'].append({'name':name+'-authored','bufferView':self.view(make_png(name)),'mimeType':'image/png'})
                self.graph['textures'].append({'sampler':0,'source':idx})
                pbr['baseColorTexture']={'index':idx}
            else:pbr['baseColorFactor']=[linear(v) for v in color]+[1.]
            self.graph['materials'].append({'name':label,'pbrMetallicRoughness':pbr})

    def primitive(self,mat,faces):
        positions=[];normals=[];texcoords=[];ids=[];slots={}
        for a,b,c in faces:
            u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
            n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            length=math.sqrt(sum(q*q for q in n))
            if length<1e-8:continue
            n=tuple(round(k/length,6) for k in n)
            for x,y,z in (a,b,c):
                uv=(x/1.5,y/1.5) if abs(n[2])>.65 else (x/1.5,-z/1.5)
                if mat=='paint':
                    uv=((x+1.15)/2.30,1-(z-.026)/2.064)
                if abs(n[0])>.8 and abs(n[1])<.5:uv=(y/1.5,z/1.5)
                pos=tuple(round(k,6) for k in (x,z,-y))
                uv=tuple(round(k,6) for k in uv)
                key=(pos,n,uv)
                if key not in slots:
                    slots[key]=len(positions);positions.append(pos);normals.append((n[0],n[2],-n[1]));texcoords.append(uv)
                ids.append((slots[key],))
        attrs={'POSITION':self.accessor(positions,'fff',5126,'VEC3',34962,True),
               'NORMAL':self.accessor(normals,'fff',5126,'VEC3',34962),
               'TEXCOORD_0':self.accessor(texcoords,'ff',5126,'VEC2',34962)}
        return {'attributes':attrs,'indices':self.accessor(ids,'H',5123,'SCALAR',34963),
                'material':list(PALETTE).index(mat),'mode':4},len(ids)//3

    def save(self,parts,path):
        self.materials()
        total=0
        for name,materials in parts.items():
            idx=len(self.graph['nodes']);self.graph['scenes'][0]['nodes'].append(idx)
            self.graph['nodes'].append({'name':name,'mesh':idx})
            primitives=[]
            for mat,triangles in materials.items():
                prim,n=self.primitive(mat,triangles);primitives.append(prim);total+=n
            self.graph['meshes'].append({'name':name,'primitives':primitives})
        self.graph['buffers']=[{'byteLength':len(self.binary)}]
        txt=json.dumps(self.graph,separators=(',',':'),ensure_ascii=False).encode()
        txt+=b' '*(-len(txt)%4)
        self.binary.extend(b'\0'*(-len(self.binary)%4))
        data=struct.pack('<4sII',b'glTF',2,28+len(txt)+len(self.binary))+struct.pack('<I4s',len(txt),b'JSON')+txt+struct.pack('<I4s',len(self.binary),b'BIN\0')+self.binary
        path.write_bytes(data)
        return dict(file=path.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),triangles=total,editable_mesh_groups=len(parts))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    result={}
    for name in ('raw','full','lod'):
        result[name]=Scene().save(Model(name).build(),args.output/(name+'.glb'))
    (args.output/'mesh-build.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
