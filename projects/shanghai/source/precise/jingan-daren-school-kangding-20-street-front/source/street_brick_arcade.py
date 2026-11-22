"""Fourteen measured arches in the street wall of the former Daren School.

The middle two openings are narrow and consecutive. No.8 is the timber door
onto the terrace. All other openings have real masonry reveals and glazing.
"""
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
SECTIONS=HERE.parent/'measurements/brick-arcade-sections.json'
GREY='Daren arcade | ash-grey face brick'
MORTAR='Daren arcade | fine warm mortar'
TRIM='Daren arcade | raised red brick hood'
BEAD='Daren arcade | weathered red edge'
BRICKS=[f'Daren arcade | red voussoir {i}' for i in range(1,6)]
REVEAL='Daren arcade | shaded jamb brick'
FRAME='Daren arcade | charcoal steel sash'
GRILLE='Daren arcade | dark protective bars'
GLASS=['Daren arcade | glazing '+k for k in ['pale','silver-grey','slate','dark']]
SILL='Daren arcade | pale weathered sill'
TIMBER='Daren arcade | amber painted timber'
DOORFRAME='Daren arcade | dark timber stile'

def pigment(rgb,roughness,metal=0.):
    c=[v/255 for v in rgb]
    return {'color':[a/12.92 if a<=.04045 else ((a+.055)/1.055)**2.4 for a in c],
            'roughness':roughness,'metallic':metal}

PALETTE={GREY:{'color':[1.,1.,1.],'roughness':.94,'texture':str(HERE/'daren-grey-brick.png')},
         MORTAR:pigment((159,135,120),.96),TRIM:pigment((149,98,84),.92),
         BEAD:pigment((170,116,95),.91),REVEAL:pigment((97,78,72),.94),
         FRAME:pigment((58,57,55),.62,.13),GRILLE:pigment((47,45,42),.68,.15),
         SILL:pigment((205,196,175),.84),TIMBER:pigment((169,113,65),.74),
         DOORFRAME:pigment((91,63,48),.69),
         **{n:pigment(rgb,.93)for n,rgb in zip(BRICKS,[(143,92,81),(158,106,91),(168,115,95),(150,99,83),(175,123,101)])},
         **{n:pigment(rgb,.29,.13) for n,rgb in zip(GLASS,[(167,169,158),(148,157,150),(87,98,99),(54,60,60)])}}


def front(x,z,d):
    return (x,-d,z)


def brick_uv(part):
    # Reuse seam positions in each plane. Edge returns retain a real material
    # scale; vertical, sloped and horizontal polygon faces all have an area in UV.
    xyz=np.asarray(part['vertices']);vertices=[];uvs=[];indices=[];lookup={}
    for tri in part['triangles']:
        q=xyz[tri,:];n=np.cross(q[1]-q[0],q[2]-q[0]);n/=np.linalg.norm(n)
        if abs(n[1])>.999:
            uv=np.column_stack((q[:,0]/2.016,-q[:,2]/1.024))
        elif abs(n[2])>.999:
            uv=np.column_stack((q[:,0]/2.016,-q[:,1]/1.024))
        else:
            ex=np.cross([0.,0.,1.],n);ex/=np.linalg.norm(ex);up=np.cross(n,ex)
            uv=np.column_stack((q@ex/2.016,-q@up/1.024))
        out=[]
        for idx,tex in zip(tri,uv):
            key=(idx,*np.round(tex,8))
            if key not in lookup:
                lookup[key]=len(vertices);vertices.append(xyz[idx].tolist());uvs.append(tex.tolist())
            out.append(lookup[key])
        indices.append(out)
    part.update(vertices=vertices,texcoords=uvs,triangles=indices)


def _extrude(b,shape,back,face,material,name):
    if shape.is_empty or shape.area<1e-6:
        return
    first=len(b.parts);b.prism(shape,back,face,front,material,name)
    if material==GREY:
        for part in b.parts[first:]:brick_uv(part)


def _point(o,t,offset=0.):
    a=o['half_width'];h=o['top']-o['spring'];p=2.*o['profile_exponent']
    c=math.cos(t);s=max(0.,math.sin(t))
    x=o['center']+a*c;z=o['spring']+h*(s**p)
    if not offset:return (x,z)
    if s<1e-8:return (x+math.copysign(offset,c),z)
    nx=h*p*s**(p-1)*c;nz=a*s;length=math.hypot(nx,nz)
    return (x+offset*nx/length,z+offset*nz/length)


def _arch(o,ts):
    lo=o['center']-o['half_width'];hi=o['center']+o['half_width']
    return Polygon([(lo,o['sill']),(hi,o['sill']),*[_point(o,t)for t in ts]])


def _ring(o,ts,inner,outer):
    return Polygon([*[_point(o,t,outer)for t in ts],*[_point(o,t,inner)for t in reversed(ts)]])


def _bar(b,x0,x1,z0,z1,back,face,mat,label):
    _extrude(b,box(x0,z0,x1,z1),back,face,mat,label)


def _joint_stations(o):
    dense=np.linspace(0.,math.pi,161)
    line=np.array([_point(o,t,.102)for t in dense]);length=np.r_[0,np.cumsum(np.linalg.norm(np.diff(line,axis=0),axis=1))]
    count=max(12,round(length[-1]/.084))
    return np.interp(np.linspace(0,length[-1],count+1),length,dense)


def _one_hood(b,o,far):
    i=o['number'];name=f'Daren {i:02d}';clip=box(o['partition_left'],o['spring']-.04,o['partition_right'],8.54)
    ts=np.linspace(0.,math.pi,26 if far else 62)
    _extrude(b,_ring(o,ts,0.,.300).intersection(clip),-.065,.008,MORTAR,name+' | mortar below red arch')
    joints=_joint_stations(o)
    if far:
        _extrude(b,_ring(o,ts,0.,.196).intersection(clip),-.060,.032,BRICKS[(i+1)%5],name+' | red arch face')
    else:
        for j,(first,last) in enumerate(zip(joints,joints[1:])):
            gap=(last-first)*.038
            subt=np.linspace(first+(gap if j else 0),last-(gap if j+2<len(joints) else 0),4)
            wedge=_ring(o,subt,0.,.196).intersection(clip)
            _extrude(b,wedge,-.064,.032,BRICKS[(3*j+i+j//5)%5],name+f' | radial brick {j+1:02d}')
    for inner,outer,inset,out,mat,tit in [(.196,.232,.002,.053,TRIM,'first raised hood'),
        (.230,.253,.007,.065,BEAD,'narrow crown arris'),(.251,.290,.007,.021,TRIM,'recessed course'),
        (.287,.319,.007,.048,BEAD,'outer hood')]:
        _extrude(b,_ring(o,ts,inner,outer).intersection(clip),inset,out,mat,name+' | '+tit)
    l=o['center']-o['half_width'];r=o['center']+o['half_width'];sp=o['spring']
    for side,ends in [('west',(o['partition_left'],l)),('east',(r,o['partition_right']))]:
        lo,hi=ends
        _bar(b,lo,hi,sp-.042,sp+.026,-.022,.042,BEAD,name+' | '+side+' impost band')
        _bar(b,lo,hi,sp-.104,sp-.046,-.022,.025,BRICKS[i%5],name+' | '+side+' spring brick')


def _sill(b,o):
    # The pale sill is visible against a black drip edge, with a broad pitched
    # weathering and a narrow toe. x cross z points towards the viewer (-Y).
    l=o['center']-o['half_width']-.043;r=o['center']+o['half_width']+.043;z=o['sill']
    depth=o['sill_thickness']
    profile=[(-.142,z-depth),(-.149,z-depth+.016),(-.145,z-.036),(-.105,z-.020),(.068,z+.012),(.079,z-depth)]
    # map Y/Z section along X with right-handed axes
    b.prism(Polygon(profile),l,r,lambda y,z,x:(x,y,z),SILL,f"Daren {o['number']:02d} | weathered sill")


def _window(b,o,shape,far):
    i=o['number'];name=f'Daren {i:02d}';front_depth=-o['glazing_setback_m'];l=o['center']-o['half_width'];r=o['center']+o['half_width'];s=o['sill'];sp=o['spring']
    # Behind the frame is a single closed surface. Subdivided lights sit in
    # front, so reveals remain visible through the full wall thickness.
    mat=DOORFRAME if i==8 else FRAME
    _extrude(b,shape,-.335,front_depth-.014,REVEAL,name+' | recessed arched back')
    frame=shape.buffer(-.012).difference(shape.buffer(-.061))
    _extrude(b,frame,front_depth-.020,front_depth+.015,mat,name+' | curved sash frame')
    if i==8:
        _bar(b,l+.07,r-.07,s+.055,sp-.17,front_depth-.016,front_depth+.002,TIMBER,name+' | orange terrace door')
        _bar(b,l+.060,r-.060,sp-.175,sp-.106,front_depth-.005,front_depth+.025,DOORFRAME,name+' | door head rail')
        _bar(b,l+.085,r-.082,sp-.097,sp+.038,front_depth-.016,front_depth+.003,GLASS[2],name+' | door transom')
        for x in [l+.073,r-.073]:_bar(b,x-.024,x+.024,s+.04,sp-.15,front_depth-.003,front_depth+.032,DOORFRAME,name+' | door post')
        return
    count,rows=o['glazing_grid'];inner=shape.buffer(-.057);width=(r-l-.116)/count;low=s+.060;glass_top=sp+.050;h=(glass_top-low)/rows
    for j in range(count):
        xmin=l+.058+j*width
        for k in range(rows):
            panel=box(xmin+.013,low+k*h+.012,xmin+width-.013,low+(k+1)*h-.012).intersection(inner)
            # Right-hand lights in the 2026 view have pale, closely-spaced
            # internal blinds. The left bays are darker behind their branches.
            shade=2 if i in (5,14) else (1 if i in (2,4,6,9) and j in (0,count-1) else 0)
            _extrude(b,panel,front_depth-.015,front_depth-.003,GLASS[shade],name+f' | light {j+1}-{k+1}')
    archlight=inner.intersection(box(l,glass_top+.012,r,o['top']))
    _extrude(b,archlight,front_depth-.015,front_depth-.003,GLASS[3],name+' | shaded arched transom')
    for j in range(1,count):
        x=l+.058+j*width;hw=.019 if j==count//2 else .013
        _extrude(b,box(x-hw,low-.02,x+hw,glass_top+.015).intersection(shape),front_depth-.012,front_depth+.018,FRAME,name+f' | steel mullion {j}')
    for k in range(rows+1):
        z=low+k*h;thick=.025 if k in (0,rows) else .012
        _extrude(b,box(l+.035,z-thick,r-.035,z+thick).intersection(shape),front_depth-.012,front_depth+.020,FRAME,name+f' | steel rail {k}')
    if not far and i in (1,2,3,4,6,7,9,11,12,13):
        for j in range(1,count+1):
            x=l+.058+(j-.5)*width
            _bar(b,x-.006,x+.006,low+.02,glass_top-.04,front_depth+.025,front_depth+.040,GRILLE,name+f' | protective rod {j}')
    _sill(b,o)


def add_brick_arcade(b,lod=False):
    far=lod is True or lod in ('lod','low','far','distant')
    b.palette.update(PALETTE)
    data=json.loads(SECTIONS.read_text());rows=data['openings'];xmin,xmax=data['wall_span_m'];bottom,top=data['wall_storey_Z_m']
    ts=np.linspace(0.,math.pi,26 if far else 62);holes=[_arch(o,ts) for o in rows]
    silhouette=box(xmin,bottom,xmax,top).difference(unary_union(holes))
    _extrude(b,silhouette,-data['wall_back_Y_m'],0.,GREY,'Daren main wall | fourteen cut masonry openings')
    for i,(o,opening) in enumerate(zip(rows,holes)):
        _one_hood(b,o,far);_window(b,o,opening,far)
        if i:
            left=rows[i-1];lo=left['center']+left['half_width'];hi=o['center']-o['half_width'];top_of_pier=min(o['spring'],left['spring'])-.103
            _bar(b,lo,hi,4.81,top_of_pier,-.026,.034,GREY,f'Daren pier {i:02d} | projecting grey brickwork')
            for j,z in enumerate([5.00,5.92]):
                _bar(b,lo+.005,hi-.005,z,z+.071,.031,.038,BRICKS[(i+j)%5],f'Daren pier {i:02d} | red bond {j+1}')
    for z0,z1,d,mat,tit in [(4.57,4.65,.084,TRIM,'lower drip'),(4.65,4.75,.057,BRICKS[1],'lower belt'),
           (4.75,4.81,.092,BEAD,'lower raised arris'),(8.34,8.40,.028,TRIM,'upper base course'),
           (8.40,8.46,.067,BEAD,'upper stringcourse'),(8.46,8.55,.045,BRICKS[2],'upper red course'),
           (8.55,8.59,.070,BEAD,'upper cap')]:
        _bar(b,xmin,xmax,z0,z1,-.04,d,mat,'Daren facade | '+tit)
