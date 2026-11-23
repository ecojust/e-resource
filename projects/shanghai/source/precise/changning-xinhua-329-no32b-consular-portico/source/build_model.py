"""Reconstruct the two-column garden entrance of house 32B in Lane 329, Xinhua Road."""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
from pier_projection import paint_number
from fanlight import fit_fanlight
from court_elevation import courtyard_wall
from inscriptions import add_ink
from arch_masonry import arch_course
from court_roofs import add_roofs
from stair_tower import add_tower
import finishes
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder

class PorticoBuilder(CrownBuilder):
    def add(self, vertices, faces, material='limestone', label='detail'):
        super().add(vertices,faces,material,label)
        if material in finishes.SCALES:
            _,width,height,_ = finishes.SCALES[material]
            part = self.parts[-1]
            part['texcoords'] = (np.asarray(part['texcoords']) / [.78*width,.78*height]).tolist()

    def save(self,path,metadata=None):
        Builder.save(self,path,metadata)
        return finishes.writer.embed_normals(path)


STONE='weathered light stone'
PLINTH='dark foundation stone'
BRICK='exposed red brick'
WOOD='deep red door joinery'
GLASS='smoked transom glazing'
IRON='aged ironwork'
METAL='brass door fittings'
PAPER='red paper'
GILT='pale paper and gilt ink'
PLAQUE='pale enamel heritage plaque'
SASH='dark courtyard window joinery'
TILE='weathered flat roof tile'
CREAM='cream-painted dormer sash'
JOINT='arch bedding mortar'
CLAYS=('warm radial brick','dark radial brick','russet radial brick')
BLUE='deep blue house-number paint'
PALETTE={name:dict(color=color,roughness=roughness) for name,color,roughness in [
    (CREAM,[.73,.72,.64],.69),(JOINT,[.114,.088,.073],.93),(CLAYS[0],[.178,.055,.030],.91),(CLAYS[1],[.132,.044,.029],.91),(CLAYS[2],[.151,.053,.037],.91),(PLAQUE,[.46,.60,.60],.65),(SASH,[.047,.053,.05],.73),(GILT,[.83,.67,.43],.84),(BLUE,[.022,.033,.075],.86),(STONE,[.48,.44,.34],.93),(PLINTH,[.215,.211,.185],.91),
    (BRICK,[.334,.118,.077],.93),(WOOD,[.275,.049,.040],.66),
    (GLASS,[.105,.121,.114],.32),(IRON,[.086,.075,.056],.81),
    (METAL,[.454,.326,.155],.4),(PAPER,[.596,.061,.048],.94)]}
CAL=json.loads((HERE.parent/'measurements/portico-camera-pair.json').read_bytes())
PORTRAIT=CAL['stations']['portrait'];WALL=CAL['wall_y_m']
MAPPER=np.array(PORTRAIT['R']).T@np.linalg.inv(PORTRAIT['K']);EYE=np.array(PORTRAIT['C'])

def point(u,v,y=0.):
    """Intersect the source portrait pixel with a plane parallel to the front entablature."""
    ray=MAPPER@np.array([u*1280/537,v*1919/805,1.])
    return EYE+ray*(y-EYE[1])/ray[1]

def outline(pixels,y):
    return Polygon([point(u,v,y)[[0,2]] for u,v in pixels])

def plate(b,shape,near,far,material,name):
    b.prism(shape,-far,-near,lambda x,z,d:(x,-d,z),material,name)

def block(b,pixels,y,near,far,material,name):
    plate(b,outline(pixels,y),near,far,material,name)

def rect(b,x0,z0,x1,z1,near,far,material,name):
    plate(b,box(min(x0,x1),min(z0,z1),max(x0,x1),max(z0,z1)),near,far,material,name)

def turned(b,axis,y,rings,n,material,name):
    points=[(axis+r*math.cos(j*2*math.pi/n),y+r*math.sin(j*2*math.pi/n),z)
            for z,r in rings for j in range(n)]
    faces=[tuple(range(n-1,-1,-1))]
    for i in range(len(rings)-1):
        faces.extend((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j)for j in range(n))
    faces.append(tuple(range((len(rings)-1)*n,len(rings)*n)))
    b.add(points,faces,material,name)

def half_arch(x,z0,zs,rx,rz,count):
    cap=[(x+rx*math.cos(t),zs+rz*math.sin(t))for t in np.linspace(0,math.pi,count+1)]
    return Polygon([(x-rx,z0),(x+rx,z0),*cap])

def columns(b,lod):
    for label,base,cap in [('west',124,127),('east',427,422)]:
        axis=point(base,638)[0]
        # Image widths are sampled separately at each height, preserving the tapered shank and moulded rings.
        def ring(v,r):
            u=base+(cap-base)*(638-v)/(638-294)
            return (point(u,v)[2],abs(point(u+r,v)[0]-point(u-r,v)[0])/2)
        plinth=point(base,669);bottom=point(base,734)
        width=abs(point(base+37,700)[0]-point(base-37,700)[0])
        b.box((axis,0,(bottom[2]+plinth[2])/2),(width,.55,plinth[2]-bottom[2]),PLINTH,label=label+' column/square pedestal')
        for name,rows,mat in [
            ('moulded base',[(670,36),(664,36),(658,30),(654,34),(648,34),(644,29),(640,29),(636,26)],PLINTH),
            ('smooth shaft',[(636,26),(560,26),(475,25),(390,23.4),(310,21.3),(298,21)],STONE),
            ('capital',[(298,21),(295,24),(292,25),(289,21),(285,22),(280,26),(277,28)],STONE)]:
            turned(b,axis,0,[ring(v,r)for v,r in rows],14 if lod else 36,mat,label+' column/'+name)
        z0=point(cap,278)[2];z1=point(cap,267)[2]
        b.box((axis,0,(z0+z1)/2),(.53,.54,z1-z0),STONE,label=label+' column/square abacus')

def upper(b,lod):
    rows=[
        ('lower projecting lip',[(88,267),(458,267),(457,256),(89,256)],-.32,STONE),
        ('lower fascia',[(94,256),(454,256),(451,247),(99,247)],-.27,STONE),
        ('frieze',[(99,247),(450,247),(446,197),(102,197)],-.215,STONE),
        ('cornice bed',[(94,198),(455,198),(459,184),(90,184)],-.255,PLINTH),
        ('cornice',[(87,184),(462,184),(471,168),(77,168)],-.29,STONE),
        ('cornice face',[(75,168),(474,168),(477,151),(72,151)],-.325,PLINTH),
        ('coping',[(71,151),(478,151),(473,146),(76,145)],-.32,STONE)]
    for i,(name,loop,near,mat) in enumerate(rows):
        # The lower three mouldings face the court. The higher slab continues
        # to the house, leaving the brick arch crown visible below its soffit.
        back = .28 if i < 3 else WALL+.10
        block(b,loop,near,near,back,mat,'entablature/'+name)
    for label,u in [('west',127),('east',422)]:
        x=point(u,261)[0]
        low=point(u,264)[2]
        high=point(u,204)[2]
        b.box((x,(WALL+.28)/2,(low+high)/2),(.37,WALL-.28,high-low),STONE,label=label+' return of garden beam')
    for u in (129,420):
        centre=point(u,221,-.228)
        for j in range(4):
            angle=j*math.pi/2
            ellipse=[]
            for t in np.linspace(0,2*math.pi,9 if lod else 17)[:-1]:
                a=.041+.040*math.cos(t);v=.022*math.sin(t)
                ellipse.append((centre[0]+a*math.cos(angle)-v*math.sin(angle),centre[2]+a*math.sin(angle)+v*math.cos(angle)))
            plate(b,Polygon(ellipse),-.242,-.211,STONE,'frieze/rosette '+str(u)+' petal '+str(j+1))
    top=point(274,94)[2];base=point(274,142)[2]
    for i,u in enumerate([160,190,220,250,280,310,340,370]):
        axis=point(u,120)[0];profile=[(0,.061),(.08,.065),(.14,.04),(.28,.065),(.40,.078),(.52,.069),(.76,.036),(.87,.045),(.94,.062),(1,.062)]
        turned(b,axis,0,[(base+(top-base)*v,r)for v,r in profile],12 if lod else 24,STONE,f'balustrade/turned baluster {i+1}')
    for name,x0,x1 in [('left',110,149),('right',399,437)]:
        block(b,[(x0,145),(x1,145),(x1,88),(x0,88)],-.11,-.11,.15,STONE,'balustrade/'+name+' end pier')
    block(b,[(108,95),(439,95),(437,83),(110,83)],-.14,-.14,.18,STONE,'balustrade/upper rail')
    block(b,[(109,148),(439,148),(436,140),(112,140)],-.15,-.15,.18,STONE,'balustrade/lower rail')

def doorway(b,lod):
    n=16 if lod else 40
    left=point(212,398,WALL);right=point(340,398,WALL)
    cx=(left[0]+right[0])/2;radius=(right[0]-left[0])/2
    zs=(left[2]+right[2])/2;bottom=point(275,632,WALL)[2]
    rise=point(275,329,WALL)[2]-zs
    inner=half_arch(cx,bottom,zs,radius,rise,n)
    outer=arch_course(b,lod,point,plate,WALL,PLINTH,JOINT,CLAYS)
    courtyard_wall(b,CAL['stations'],WALL,outer,plate,point,(BRICK,PLINTH,SASH,GLASS,PLAQUE,METAL))
    plate(b,outer.difference(inner),WALL-.075,WALL+.075,PLINTH,'entrance/stone arch surround')
    leaf=box(cx-radius+.045,bottom+.035,cx+radius-.045,zs-.05)
    plate(b,leaf,WALL+.081,WALL+.135,WOOD,'door/panelled leaf')
    plate(b,inner.difference(leaf),WALL+.12,WALL+.15,WOOD,'door/frame behind reed and transom')
    fan=half_arch(cx,zs-.012,zs,radius-.028,rise-.032,n)
    plate(b,fan,WALL+.045,WALL+.068,GLASS,'door/fanlight')
    fit_fanlight(b,lod,point,plate,WALL,IRON,GILT,PAPER)
    for j,(a,c,e,f) in enumerate([(224,420,251,487),(295,420,327,486),(225,507,252,562),(263,506,291,563),(297,506,326,562),(223,577,327,608)]):
        shape=outline([(a,c),(e,c),(e,f),(a,f)],WALL+.079)
        plate(b,shape.difference(shape.buffer(-.021,join_style='mitre')),WALL+.040,WALL+.086,WOOD,f'door/raised panel {j+1}')
    shape=outline([(260,436),(272,423),(281,437),(281,474),(260,474)],WALL+.074)
    plate(b,shape,WALL+.031,WALL+.074,GLASS,'door/small inspection light')
    for x in [265,276]:
        u=point(x,449,WALL+.031)[0];rect(b,u-.008,point(x,472,WALL+.031)[2],u+.008,point(x,438,WALL+.031)[2],WALL+.015,WALL+.037,IRON,'door/light grille')
    block(b,[(251,477),(284,477),(284,485),(251,485)],WALL+.06,WALL+.012,WALL+.075,METAL,'door/letter plate')
    for i,(u,a,c,d) in enumerate([(189,422,203,534),(350,420,366,533)]):
        block(b,[(u,a),(c,a),(c,d),(u,d)],WALL-.08,WALL-.09,WALL-.071,PAPER,f'entrance/red couplet backing {i+1}')

def steps(b):
    for i,(u,v,u2,v2,near) in enumerate([(113,739,436,718,-.61),(151,719,401,699,-.38),(158,699,395,677,-.15),(165,677,387,657,.08)]):
        p=point(u,v,near);q=point(u2,v2,near)
        rect(b,p[0],p[2],q[0],q[2],near,WALL+.18,PLINTH,f'stair/stone tread and riser {i+1}')
    block(b,[(170,657),(386,657),(377,635),(180,635)],WALL-.19,WALL-.26,WALL+.13,PLINTH,'stair/door sill')

META=dict(id=HERE.parent.name,name='新华路329弄32号乙花园住宅双柱门廊',register='3M013',formal_id='sh-historic-b3-111',address='上海市长宁区新华路329弄32号乙',geometry_license='MIT',photos_embedded=False,scope='庭院面可辨门廊，尺度依据门扇净高2.10米暂估。整栋屋面与室内楼梯另核。')
def build(lod):
    b=PorticoBuilder(PALETTE | finishes.PALETTE)
    columns(b,lod)
    readings=json.loads((HERE/'pier-number-reading.json').read_bytes())['letters']
    paint_number(b,readings,EYE,MAPPER,BLUE)
    upper(b,lod);doorway(b,lod);steps(b)
    add_ink(b,point,plate,WALL,GILT,SASH)
    add_tower(b,CAL['stations'],dict(brick=BRICK,window=SASH,glass=GLASS))
    add_roofs(b,lod,plate,dict(tile=TILE,brick=BRICK,timber=WOOD,glass=GLASS,sash=CREAM,stone=STONE),CAL['stations']['wide'])
    return b
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',type=Path,required=True);cli.add_argument('--lod',action='store_true')
    args=cli.parse_args();args.output.parent.mkdir(exist_ok=True,parents=True);build(args.lod).save(args.output,META)
