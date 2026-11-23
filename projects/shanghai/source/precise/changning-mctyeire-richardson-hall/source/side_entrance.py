"""Detached study of the outward-opening side door in Ctny's 2017 exterior photograph.

Coordinates are local to the midpoint of the threshold. No registration to the
lawn elevation or the separate interior photograph is asserted.
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').exists())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder, Facade

STATION=HERE.parent/'measurements/side-entrance-photo.json'
ASH='side door | coursed grey wall'
STONE='side door | dressed arch and window stone'
WOOD='side door | brown door joinery'
FIELD='side door | inset timber panel'
GLASS='side door | reflected window glass'
SHUTTER='side door | warm blind behind window'
IRON='side door | dark window lattice'
PIPE='side door | dark rainwater pipe'
CANVAS='side door | pale awning sheet'
ROLL='side door | grey rolled front edge'
STEP='side door | worn stair stone'
SHADOW='side door | recessed dark passage'
KNOB='side door | round bronze knob'
PALETTE={key:dict(color=color,roughness=roughness) for key,color,roughness in [
    (ASH,[.49,.48,.44],.9),(STONE,[.52,.51,.465],.85),(WOOD,[.193,.106,.055],.56),
    (FIELD,[.162,.080,.039],.69),(GLASS,[.085,.102,.103],.26),(SHUTTER,[.264,.129,.075],.74),
    (IRON,[.111,.108,.095],.61),(PIPE,[.064,.066,.062],.56),(CANVAS,[.68,.65,.55],.86),
    (ROLL,[.42,.44,.39],.52),(STEP,[.40,.38,.32],.91),(SHADOW,[.035,.035,.028],.98),
    (KNOB,[.60,.46,.267],.31)]}


class Photo:
    def __init__(self):
        self.data=json.loads(STATION.read_bytes())
        self.outlines=self.data['outlines']
        matrix=np.array(self.data['projection'])
        self.inverse=np.linalg.inv(matrix[:,:3])
        self.eye=-self.inverse@matrix[:,3]

    def on_plane(self,pixel,axis,value):
        ray=self.inverse@[*pixel,1.]
        return self.eye+ray*(value-self.eye[axis])/ray[axis]

    def elevation(self,key,y=0):
        return Polygon([self.on_plane(p,1,y)[[0,2]] for p in self.outlines[key]])

def fanlight(f,photo,arches):
    inner,wood,outer=arches
    f.prism(outer.difference(wood),-.079,.064,STONE,'cut-stone doorway surround')
    f.prism(wood.difference(inner),-.086,.031,WOOD,'arched inner casing')
    h=photo.data['fitted_clear_height_m']
    light=inner.intersection(box(-1.05,h,1.05,3.2))
    f.prism(light,-.080,-.067,GLASS,'pointed fanlight glazing')
    ribs=[box(-2,h,2,h+.047),box(-2,2.466,2,2.491)]
    for x in [-.715,-.498,-.246,-.008,.224,.473,.716]:
        ribs.append(box(x-.012,h,x+.012,3.2))
    f.prism(light.intersection(unary_union(ribs)),-.060,-.027,WOOD,'fanlight muntins and head rail')

def open_leaf(b,photo,key,lod):
    points=photo.outlines[key]
    hinge=[photo.on_plane(points[i],1,0) for i in [0,3]]
    free=[photo.on_plane(points[i],1,-.87) for i in [1,2]]
    hinge_xy=np.mean([p[:2] for p in hinge],axis=0)
    end_xy=np.mean([p[:2] for p in free],axis=0)
    leaf=Facade(b,hinge_xy,end_xy,key)
    # Projected hinge and free corners constrain a slightly tapered visible silhouette.
    half=leaf.length/2
    outline=Polygon([(-half,hinge[1][2]),(half,free[1][2]),(half,free[0][2]),(-half,hinge[0][2])])
    leaf.prism(outline,-.019,.018,WOOD,'timber door')
    # Between the rails, the photographed leaves have two parallel rows of three fielded panels.
    coords=[(-half+.085,-.036),(.035,half-.078)]
    panels=unary_union([box(left,low,right,high) for left,right in coords for low,high in [(.119,.70),(.79,1.275),(1.39,2.015)]])
    panels=panels.intersection(outline.buffer(-.047,join_style=2))
    # Both open leaves expose the same garden-facing side despite opposite hinge orientations.
    for sign in [-1,1]:
        base=.020 if sign==1 else -.024
        leaf.prism(panels,base,base+.004,FIELD,'recessed panel faces')
        rings=panels.difference(panels.buffer(-(.014 if lod else .019),join_style=2))
        lo,hi=(.025,.038) if sign==1 else (-.038,-.025)
        leaf.prism(rings,lo,hi,WOOD,'panel moulding')
    if key=='right_leaf':
        p=photo.outlines['right_knob'][0]
        ray=photo.inverse@[*p,1.]; n=leaf.n
        near=photo.eye+ray*((leaf.center-photo.eye)@n/(ray@n))
        toward=1 if (photo.eye-near)@n>0 else -1
        start=near+n*toward*.018
        b.tube([start,start+n*toward*.068],.021,KNOB,8 if lod else 14,'right door/knob spindle')
        tip=start+n*toward*.077
        b.lathe(tip[:2],[(tip[2]+z,r) for z,r in [(-.030,.008),(-.022,.023),(0.,.031),(.022,.023),(.030,.008)]],KNOB,10 if lod else 18,'right door/knob')

def cross_window(f,opening,index,lod,photo):
    x0,z0,x1,z1=opening.bounds
    u,v=photo.data['window_mullion_edges_native_at_row_368'][index-1]
    a,b=[photo.on_plane((x,368),1,-.034)[0] for x in (u,v)]
    cx=(a+b)/2
    centre_height=z1-.724
    verticals=[box(a,z0,b,z1)]
    cross=opening.intersection(unary_union(verticals+[box(x0,centre_height-.044,x1,centre_height+.044)]))
    f.prism(cross,-.059,.034,STONE,'window '+str(index)+'/stone mullion and transom')
    f.prism(opening,-.118,-.107,GLASS,'window '+str(index)+'/glazing')
    if index<3:
        blinds=opening.intersection(box(cx+.055,z0+.04,x1-.039,z1-.043))
        f.prism(blinds,-.102,-.097,SHUTTER,'window '+str(index)+'/brown blind')
        if not lod:
            for z in np.arange(z0+.08,z1-.052,.053):
                f.prism(blinds.intersection(box(x0,z,x1,z+.007)),-.096,-.090,WOOD,'blind/slat')
    bars=[box(x-.009,z0,x+.009,z1) for x in np.arange(x0+.216,x1-.065,.26)]
    bars.extend(box(x0,z,x1,z+.014) for z in np.arange(z0+.19,z1-.09,.298))
    f.prism(opening.intersection(unary_union(bars)),-.088,-.064,IRON,'window '+str(index)+'/dark glazing bars')
    edges=opening.difference(opening.buffer(-.027,join_style=2))
    if index==3:
        # The right border of the image cuts the last light without showing a jamb.
        edges=edges.intersection(box(x0-.01,z0-.01,x1-.14,z1+.01))
    f.prism(edges,-.08,-.035,IRON,'window '+str(index)+'/frame')

def awning(b,photo,lod):
    uv=photo.outlines['awning']
    back=[photo.on_plane(uv[i],1,-.01) for i in [0,1]]
    # Determine projection from the far-end return; the sloping sheet is visible from below.
    front=[]
    for i,j in [(2,1),(3,0)]:
        front.append(photo.on_plane(uv[i],0,back[j][0]))
    # Left attachment is obscured by foliage; its unsupported apparent depth differs
    # from the visible right end. Continue the straight observed roller to that cut.
    front[1]=photo.on_plane(uv[3],1,front[0][1])
    points=[*back,*front]
    faces=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    # Sloping sheet vertex loop is clockwise in plan, so reverse it for a positive shell.
    points=points[::-1]
    b.add(points+[p+np.array([0.,0.,.027]) for p in points],faces,CANVAS,'awning/visible sloping cover')
    b.tube([front[0],front[1]],.050,ROLL,10 if lod else 20,'awning/round front bar')
    b.tube([back[0],back[1]],.024,ROLL,8 if lod else 12,'awning/wall edge')
    b.tube([back[1],front[0]],.019,ROLL,8 if lod else 12,'awning/exposed right edge')

def stair(b,photo):
    edges=[]
    nose=photo.outlines['stair_front']
    for i,uv in enumerate(nose[1:]):
        p=photo.on_plane(uv,2,-i*.135)
        edges.append(p[1])
    left=photo.on_plane(nose[0],2,0)[0]
    right=photo.on_plane(nose[1],2,0)[0]
    back=.07
    for i,front in enumerate(edges):
        top=-i*.135
        b.box([(left+right)/2,(back+front)/2,(top-.13+top)/2],
              [right-left,back-front,.13],STEP,label='stair/visible tread '+str(i+1))
        back=front
    b.box([right+.105,(edges[-1]+.04)/2,-.20],[.198,.04-edges[-1],.56],STEP,label='stair/right solid curb')
    b.box([right+.105,(edges[-1]+.045)/2,.119],[.226,.045-edges[-1],.066],STONE,label='stair/right curb cap')

def add_side_entrance(b,lod=False):
    """Add the detached side doorway and the photograph's adjoining window strip."""
    for name,values in PALETTE.items(): b.palette.setdefault(name,values)
    p=Photo()
    f=Facade(b,(-10,0),(10,0),'Side door')
    arches=[p.elevation(key) for key in ['arch_open','arch_wood_outer','arch_stone_outer']]
    windows=[p.elevation('window'+str(i)) for i in [1,2,3]]
    # Trim the detached patch at the photo boundary, without adding a vertical end jamb.
    xend=8.32
    patch=box(-1.69,-.52,xend,4.48)
    windows[-1]=windows[-1].intersection(patch)
    finish=patch.difference(unary_union([arches[-1],*windows]))
    f.prism(finish,-.26,0,ASH,'perforated masonry strip')
    # Six ashlar joints are clearly visible around the gutter and can be followed along the wall.
    if not lod:
        for i,z in enumerate([.62,1.11,1.64,2.13,2.63,3.13,3.64,4.16]):
            band=finish.intersection(box(-1.68,z,xend,z+.005))
            f.prism(band,.001,.002,STONE,'fine horizontal masonry joint')
    fanlight(f,p,arches)
    for i,opening in enumerate(windows,1):cross_window(f,opening,i,lod,p)
    for key in ['left_leaf','right_leaf']:open_leaf(b,p,key,lod)
    # A short dark passage terminates the cropped doorway, including its floor.
    for x in [-.99,.99]:
        b.box([x,.665,1.12],[.15,1.25,2.26],SHADOW,label='passage/side return')
    b.box([0,1.19,1.20],[2.06,.12,2.42],SHADOW,label='passage/dark rear')
    b.box([0,.57,-.043],[1.95,1.14,.077],STEP,label='passage/threshold')
    awning(b,p,lod);stair(b,p)
    a,c=[p.on_plane(uv,1,-.075) for uv in p.outlines['pipe']]
    x=(a[0]+c[0])*.5
    b.tube([[x,-.075,-.02],[x,-.075,4.48]],.045,PIPE,9 if lod else 16,'rainwater/pipe')
    for z in [.57,2.45,3.95]:
        b.tube([[x,-.075,z],[x,-.075,z+.036]],.052,PIPE,9 if lod else 16,'rainwater/collar')
    return b

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('out',type=Path);args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    for name,lod in [('full',False),('lod',True)]:
        b=add_side_entrance(Builder(),lod)
        out=b.save(args.out/(name+'-side-entrance.glb'),{'id':'richardson-hall-side-entrance-study','detached':True,'datum':'threshold centre','role':name})
        print(name,len(b.parts),out['triangles'],out['sha256'])
