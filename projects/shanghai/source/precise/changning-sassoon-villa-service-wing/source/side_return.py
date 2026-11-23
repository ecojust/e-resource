"""Garden wing's left return and two registered dormers on its hipped roof."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from service_materials import BRICK, EDGE, FRAME, GLASS, PLASTER, TILE

READINGS = json.loads((Path(__file__).resolve().parents[1]/'measurements/west-return-observations.json').read_bytes())
PREFIX = 'Eves return / '


def wall_segment(builder, profile, outer_x, inner_x, material, name):
    builder.prism(profile,outer_x,inner_x,lambda y,z,x:(x,y,z),material,PREFIX+name)


def wall_point(frame, uv):
    return frame.design.plane(uv,[0,0,0],[1,0,0])[[1,2]]


def rectangle(frame, corners):
    yz=np.array([wall_point(frame,p) for p in corners])
    return box(yz[[1,2],0].mean(),yz[[2,3],1].mean(),yz[[0,3],0].mean(),yz[[0,1],1].mean())


def hip(frame):
    eave=frame.roof_level(-.25)
    slope=(frame.ridge-eave)/(frame.left_hip+.29)
    return slope,eave+.29*slope


def dormer(frame, obs):
    slope,base=hip(frame)
    cam=frame.design
    bottom=[cam.plane(obs[key],[0,0,base],[-slope,0,1]) for key in ('front_left_foot','front_right_foot')]
    front=float(np.mean([p[0] for p in bottom]))
    def face(uv):
        return cam.plane(uv,[front,0,0],[1,0,0])
    left,right=sorted([face(obs[key])[1] for key in ('front_right_foot','front_left_foot')])
    eave=face(obs['front_top'])[2];foot=base+slope*front;centre=(left+right)/2
    crest=cam.plane(obs['ridge_leading'],[0,centre,0],[0,1,0])
    # The right-hand eave disappears where it meets the host hip.
    back=(eave-base)/slope
    ridge_back=(crest[2]-base)/slope
    return front,left,right,foot,eave,back,crest,ridge_back


def side_roof_apertures(frame):
    holes=[]
    for obs in READINGS['dormers']:
        x,l,r,_,_,back,_,tip=dormer(frame,obs)
        holes.append(Polygon([(x+.024,l+.026),(back,l+.026),(tip,(l+r)/2),(back,r-.026),(x+.024,r-.026)]))
    return holes


def slab(builder, points, thickness, material, label):
    points=np.array(points,dtype=float)
    v=[*points,*list(points-[0,0,thickness])];n=len(points)
    faces=[list(range(n)),list(reversed(range(n,n*2)))]
    faces.extend(([i,n+i,n+(i+1)%n,(i+1)%n] for i in range(n)))
    # Window heads and both roof pitches may be supplied in either winding.
    if np.cross(points[1]-points[0],points[2]-points[0])[2]<0:
        faces=[f[::-1] for f in faces]
    builder.add(v,faces,material,PREFIX+label)


def add_dormer(b, frame, obs, lod):
    x,l,r,foot,top,back,crest,tip=dormer(frame,obs)
    slope,base=hip(frame);mid=(l+r)/2;h=crest[2]
    name=obs['name']+' hip dormer'
    opening=box(l+.075,foot+.075,r-.075,top-.085)
    wall_segment(b,box(l,foot-.052,r,top).difference(opening),x,x+.08,FRAME,name+' face and reveals')
    wall_segment(b,opening,x+.044,x+.060,GLASS,name+' recessed shadowed light')
    wall_segment(b,box(mid-.023,foot+.06,mid+.023,top-.074),x+.004,x+.055,FRAME,name+' centre mullion')
    for edge,sign in ((l,1),(r,-1)):
        profile=Polygon([(x,foot-.049),(back+.026,top-.008),(back+.026,top+.02),(x,top+.02)])
        b.prism(profile,min(-edge,-edge-sign*.074),max(-edge,-edge-sign*.074),lambda u,z,d:(u,-d,z),BRICK,PREFIX+name+' triangular brick cheek')
    # Clipped hip at the exposed nose; two tile planes run back to the host roof.
    dx=crest[0];a=x-.055;le=l-.05;re=r+.05;end=back+.055
    slab(b,[(a,le,top+.06),(a,re,top+.06),(dx,mid,h+.06)],.068,TILE,name+' clipped nose')
    slab(b,[(a,le,top+.06),(dx,mid,h+.06),(tip+.048,mid,h+.06),(end,le,top+.06)],.068,TILE,name+' garden pitch')
    slab(b,[(a,re,top+.06),(end,re,top+.06),(tip+.048,mid,h+.06),(dx,mid,h+.06)],.068,TILE,name+' rear pitch')
    b.box([a+.024,mid,top-.015],[.048,re-le,.10],EDGE,label=PREFIX+name+' outer fascia')


def add_side(b,frame,lod=False):
    rail=frame.rail;top=frame.eave;step=wall_point(frame,READINGS['band_step'])[0]
    windows=[(k,rectangle(frame,k['outline']),rectangle(frame,k['clear'])) for k in READINGS['wall_windows']]
    # The return's midrail steps above the smaller, partly screened rear bay.
    brick=unary_union([box(0,0,step,rail),box(step,0,frame.depth,rail+.18)])
    wall_segment(b,brick.difference(unary_union([rect for _,rect,_ in windows])),0,.21,BRICK,'brick wall with two clear openings')
    wall_segment(b,box(0,0,frame.depth,top).difference(brick),.014,.21,PLASTER,'lime timber panels')
    for y0,y1,z in ((0,step,rail),(step,frame.depth,rail+.18)):
        wall_segment(b,box(y0,z-.060,y1,z+.067),-.053,.045,FRAME,'continuous stepped midrail')
    for uv in READINGS['vertical_studs']:
        y=wall_point(frame,uv)[0];z=rail if y<step else rail+.18
        wall_segment(b,box(y-.043,z,y+.043,top),-.040,.030,FRAME,'upper upright')
    for aa,bb in READINGS['diagonals']:
        a=wall_point(frame,aa);c=wall_point(frame,bb)
        a[1],c[1]=np.clip([a[1],c[1]],rail+.04,top-.02)
        dy,dz=c-a;n=np.array([-dz,dy])*.045/np.linalg.norm(c-a)
        wall_segment(b,Polygon([a+n,c+n,c-n,a-n]),-.045,.024,FRAME,'inclined half-timber')
    for p in READINGS['lower_posts']:
        y=wall_point(frame,p)[0]
        wall_segment(b,box(y-.061,.0,y+.061,rail+.047),-.032,.051,FRAME,'lower oak posts')
    for obs,outer,light in windows:
        name=obs['name']+' return window'
        wall_segment(b,outer.difference(light),.035,.14,FRAME,name+' outer joinery')
        wall_segment(b,light,.103,.124,GLASS,name+' recessed panes')
        y0,z0,y1,z1=light.bounds;y=(y0+y1)/2
        wall_segment(b,box(y-.016,z0,y+.016,z1),.067,.108,FRAME,name+' centre bar')
        for v in obs['crossbars_y']:
            z=wall_point(frame,((obs['clear'][0][0]+obs['clear'][1][0])*.5,v))[1]
            wall_segment(b,box(y0,z-.016,y1,z+.016),.067,.108,FRAME,name+' crossbar')
    for obs in READINGS['dormers']:
        add_dormer(b,frame,obs,lod)
