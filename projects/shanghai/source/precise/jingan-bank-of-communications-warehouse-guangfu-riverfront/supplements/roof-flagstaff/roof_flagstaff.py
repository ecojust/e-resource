"""Editable roof-mounted flagstaff for the south terrace, in the warehouse's ENU frame."""
from pathlib import Path
import argparse
import json
import math
import struct
import sys

STEEL='Flagstaff | muted silvery metal'
STONE='Flagstaff | light foot block'
PALETTE={STEEL:{'color':[.29,.306,.315],'roughness':.45,'metallic':.55},
         STONE:{'color':[.36,.354,.327],'roughness':.86,'metallic':0.}}
AXIS=(.01,1.02)
DECK=18.20
TIP=27.00

def add_flagstaff(builder,lod,layout):
    """Add two closed, editable solids at the measured roof position."""
    builder.palette.update(PALETTE)
    z=layout['roof_deck_z']
    x,y=AXIS
    n=8 if lod else 24
    verts=[]
    # The clear lower shaft and upper finial are subpixel in some views.
    # A continuous taper represents their observed apparent width.
    for h,r in ((z+.19,.045),(z+3.9,.043),(TIP-.035,.026),(TIP,.017)):
        for i in range(n):
            t=2.*math.pi*i/n
            verts.append([x+r*math.cos(t),y+r*math.sin(t),h])
    faces=[list(reversed(range(n))),list(range(3*n,4*n))]
    for k in range(3):
        for i in range(n):
            j=(i+1)%n;faces.append([k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i])
    builder.add(verts,faces,STEEL,'Flagstaff | tapered metal shaft')
    # The adjacent pale patch is clearest in frame 39. Its rectangular top
    # and partly concealed vertical dimension are approximate.
    builder.box((-.07,1.13,z+.10),(.40,.32,.20),STONE,label='Flagstaff | foot block')

def save_model(path,lod,project):
    sys.path.insert(0,str(project/'source/precise/hongkou-general-post-office/source/common'))
    from photo_architecture import Builder
    b=Builder()
    add_flagstaff(b,lod,{'roof_deck_z':DECK})
    b.save(path,{'title':'光复路195号南露台旗杆与杆脚','units':'metres','frame':'shared riverfront warehouse local ENU','mesh_role':'lod' if lod else 'source'})
    data=path.read_bytes()
    size,kind=struct.unpack_from('<II',data,12);assert kind==0x4e4f534a
    doc=json.loads(data[20:20+size]);blob=data[20+size:]
    prims=doc['meshes'][0]['primitives'];assert len(prims)==len(b.parts)==2
    doc['meshes']=[];doc['nodes']=[]
    names={part['material']:part['label'] for part in b.parts}
    for i,pr in enumerate(prims):
        name=names[doc['materials'][pr['material']]['name']]
        doc['meshes'].append({'name':name,'primitives':[pr]})
        doc['nodes'].append({'name':name,'mesh':i})
    doc['scenes'][0]['nodes']=list(range(len(prims)))
    txt=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode()
    txt+=b' '*(-len(txt)%4)
    path.write_bytes(struct.pack('<4sIIII',b'glTF',2,20+len(txt)+len(blob),len(txt),kind)+txt+blob)
    path.with_suffix('.geometry.json').unlink()

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('project',type=Path);ap.add_argument('output',type=Path)
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    for lod,name in [(False,'flagstaff-raw.glb'),(True,'flagstaff-simple.glb')]:save_model(args.output/name,lod,args.project)
