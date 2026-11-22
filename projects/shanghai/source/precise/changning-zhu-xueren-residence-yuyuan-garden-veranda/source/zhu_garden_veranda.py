"""South garden veranda photographed in 2013. Distances are in metres."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from zhu_garden_materials import GLASS,GROOVE,MASONRY,PLASTER,REVEAL,STAIR,STONE,STONE_EDGE,WOOD


SOURCE=Path(__file__).resolve().parent


def garden_face(builder,shape,plane,rear,front,material,label):
    builder.prism(shape,rear,front,lambda x,z,d:(x,plane-d,z),material,label)


def arch_opening(left,right,spring,apex,bottom,trace,lod):
    pts=trace[::3] if lod else trace
    if pts[-1]!=trace[-1]:
        pts=[*pts,trace[-1]]
    return Polygon([(left,bottom),(right,bottom),(right,spring),
                    *[(left+(right-left)*u,spring+(apex-spring)*z) for u,z in reversed(pts)],
                    (left,spring)]).buffer(0)


def central_arch(plane,bottom,lod):
    survey=SOURCE.parent/'measurements'
    readings=json.loads((survey/'south-garden-centre-arch.json').read_bytes())
    proj=np.array(json.loads((survey/'south-veranda-depth-and-third-camera.json').read_bytes())['camera_08'])
    front=proj[:,[0,2,3]].copy()
    front[:,2]+=plane*proj[:,1]
    samples=[r['uv'] for r in readings['arc_trace']]
    if lod:samples=[*samples[::3],samples[-1]]
    def intersect(uv):
        q=np.linalg.solve(front,[*uv,1])
        return tuple(q[:2]/q[2])
    points=[intersect(uv) for uv in [readings['jamb_pixel_pairs']['west'][0],*samples,
                                       readings['jamb_pixel_pairs']['east'][0]]]
    return Polygon([(points[0][0],bottom),(points[-1][0],bottom),*reversed(points)])


def curve_points():
    data=json.loads((SOURCE.parent/'measurements/south-garden-centre-arch.json').read_bytes())
    col=[p['relative_x_z'] for p in data['arc_trace']]
    x0,x1=col[0][0],col[-1][0]
    z0=(col[0][1]+col[-1][1])*.5
    z1=max(z for _,z in col)
    return [((x-x0)/(x1-x0),max(0.,min(1.,(z-z0)/(z1-z0)))) for x,z in col]


def garden_stairs(b,layout,lod):
    west,east=layout['bay_edges'][1:3]
    mid=(west+east)/2
    plane=layout['front_y'][1]
    n=16 if lod else 44
    profile=json.loads((SOURCE.parent/'measurements/south-garden-five-curved-steps.json').read_bytes())
    for row in profile['steps']:
        level=row['level'];x0,x1=row['extent_x_m']
        a,beta,c=row['coefficients_y_of_x']
        outline=[]
        for i in range(n+1):
            x=x0+(x1-x0)*i/n
            dx=x-row['arc_mid_x_m']
            outline.append((x,(a*dx+beta)*dx+c))
        # Both ends continue back to the sheltered landing. Most of this is
        # covered by the tread above, leaving its curved nosing visible.
        back=max(.31,outline[0][1]+.10,outline[-1][1]+.10)
        if level==5:
            # The two ends continue into the landing behind the cheek walls.
            outline=[(mid-1.56,outline[0][1]),*outline,(mid+1.56,outline[-1][1])]
            x0,x1=mid-1.56,mid+1.56
        shape=Polygon([*outline,(x1,back),(x0,back)])
        top=row['z']
        b.plan_prism(shape,.003+top-layout['landing_z']/5,top,STAIR,'Garden stair | curved step '+str(level))
        lip=shape.buffer(.014,join_style=2).difference(shape.buffer(-.042,join_style=2))
        b.plan_prism(lip,top-.020,top+.002,STONE,'Garden stair | nosings')
    # The short pieces of the central balustrade form solid cheeks either
    # side of the access to the landing.
    for x0,x1 in [(west+1.04,mid-1.56),(mid+1.56,east-.99)]:
        b.box(((x0+x1)/2,plane+.1,(.70+1.42)/2),(x1-x0,.26,.72),MASONRY,label='Central arch | stair cheeks')
        b.box(((x0+x1)/2,plane+.1,1.435),(x1-x0+.09,.32,.065),STONE,label='Central arch | cheek cappings')


def add_joints(b,face,plane,base,top,label,lod):
    # Original photo 08 shows running joints offset along alternate courses.
    # Intersect with the cut wall so that joints end cleanly at its arch and jambs.
    x0,_,x1,_=face.bounds
    band=.354
    i=0
    while base+(i+1)*band < top-.012:
        z=base+(i+1)*band
        strip=box(x0,z-.006,x1,z+.006).intersection(face)
        if not strip.is_empty:
            garden_face(b,strip,plane,.001,.008,GROOVE,label+' bed joints')
        if not lod:
            columns=[]
            x=x0+(.47 if i%2 else .95)
            while x<x1-.06:
                columns.append(box(x-.005,z-band+.006,x+.005,z-.006))
                x+=.95
            if columns:
                strip=unary_union(columns).intersection(face)
                if not strip.is_empty:
                    garden_face(b,strip,plane,.001,.008,GROOVE,label+' vertical joints')
        i+=1


def add_garden(b,lod,layout):
    trace=curve_points()
    eaves=layout['upper_soffit_z']; soffit=layout['gallery_soffit_z']
    z_walk=layout['balcony_z']; ground=layout['landing_z']
    edges=layout['bay_edges']; fronts=layout['front_y']; depth=layout['veranda_depth']
    wall=layout['south_wall_thickness']
    openings=layout['garden_arches']
    for i,item in enumerate(openings):
        name=('West','Central','East')[i]+' garden bay'
        x0,x1=edges[i:i+2];plane=fronts[i]
        lo,hi=item['jamb_x'];spring,apex=item['spring_z'],item['crown_z']
        hole=central_arch(plane,ground-.015,lod) if i==1 else arch_opening(lo,hi,spring,apex,ground-.015,trace,lod)
        body=box(x0,0,x1,soffit).difference(hole)
        if i==1:
            mid=(x0+x1)*.5
            body=body.difference(box(mid-1.56,-.02,mid+1.56,ground+.025))
        garden_face(b,body,plane,-wall,0,MASONRY,name+' | arch wall')
        add_joints(b,body,plane,ground-.23,soffit,name,lod)
        ring=hole.buffer(.063,join_style=2).difference(hole).intersection(box(x0,ground+.035,x1,soffit))
        garden_face(b,ring,plane,-.01,.026,REVEAL,name+' | arch margin')
        interior=box(x0,plane,x1,depth)
        landing=interior
        if i==1:
            mid=(x0+x1)*.5
            landing=landing.difference(box(mid-1.56,plane-.1,mid+1.56,.30))
        b.plan_prism(landing,ground-.14,ground,STONE,name+' | ground landing')
        b.plan_prism(interior,soffit,z_walk,MASONRY,name+' | balcony slab')
        b.plan_prism(box(x0-.02,plane-.10,x1+.02,plane+.025),z_walk-.19,z_walk-.055,STONE_EDGE,name+' | floor drip')
        b.plan_prism(box(x0-.045,plane-.14,x1+.045,plane+.05),z_walk-.064,z_walk+.008,STONE,name+' | floor ledge')
        up_lo,up_hi=item['upper_clear_x']
        moving=box(x0,z_walk,x1,eaves).difference(box(up_lo,z_walk-.02,up_hi,eaves+.02))
        garden_face(b,moving,plane,-wall,0,MASONRY,name+' | broad gallery piers')
        add_joints(b,moving,plane,z_walk,eaves,name+' | upper',lod)
        b.plan_prism(box(x0-.07,plane-.10,x1+.07,depth),eaves,eaves+.15,MASONRY,name+' | upper fascia')
        b.plan_prism(box(x0-.13,plane-.20,x1+.13,depth),eaves+.15,eaves+.21,STONE_EDGE,name+' | upper drip')
    for x in edges[1:3]:
        y0=fronts[1]
        b.box((x,(y0+.03)/2,soffit/2),(.23,-y0+.06,soffit),MASONRY,label='Garden centre | projecting corner returns')
        b.box((x,(y0+.03)/2,(z_walk+eaves)/2),(.24,-y0+.06,eaves-z_walk),MASONRY,label='Garden centre | upper side returns')
    garden_stairs(b,layout,lod)
