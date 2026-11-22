"""Visible jambs and the green folded gate on the August 2017 Rongkang south portal."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from lane_head import material

SOURCE = Path(__file__).resolve().parents[1]/'measurements/south-gate-leaves-and-piers.json'
OBS = json.loads(SOURCE.read_bytes())
POST = 'South gate | grey pier face'
SIDE = 'South gate | pale side return'
CAP = 'South gate | cap and upper course'
STEEL = 'South gate | green painted steel'
EDGE = 'South gate | raised steel edge'
PALETTE = {POST:material([142,144,136]),SIDE:material([165,164,152]),CAP:material([182,177,157]),
           STEEL:material([53,94,83]),EDGE:material([67,104,89])}


def leaf(index):
    a, b = OBS['edges'][index:index+2]
    start = np.array(a['world_bottom'][:2]); end = np.array(b['world_bottom'][:2])
    length = np.linalg.norm(end - start)
    along = (end-start)/length
    outward = np.array([along[1],-along[0]])
    base = (a['world_bottom'][2]+b['world_bottom'][2])/2
    height = (a['world_top'][2]+b['world_top'][2])/2-base
    return start, along, outward, length, base, height


def leaf_point(index,u,t,d=0.):
    start,along,outward,length,base,height = leaf(index)
    p = start+along*u*length+outward*d
    return np.r_[p,base+t*height]


def slots():
    # Measured in separate plane-rectifications of the open August leaves.
    # Dark intervals at each end of the upper and lower fins reveal five slots.
    return [(.075+i*.182,.155+i*.182) for i in range(5)]


def add_lane_piers_gate(b,lod=False):
    low = lod is True or lod=='lod'
    def block(x0,x1,y0,y1,z0,z1,mat,label):
        b.box([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],
              [x1-x0,y1-y0,z1-z0],mat,label=label)
    south,north = (OBS['jambs'][k] for k in ('south','north'))
    a,c=south['outer_x'],south['inner_x']
    block(a,c,.026,.27,0,2.44,POST,'South passage pier below shoulder')
    block(c-.045,c+.010,.063,.312,0,2.44,SIDE,'South passage pier exposed inner edge')
    block(a,c-.015,.020,.273,2.44,2.585,CAP,'South pier shallow upper course')
    block(a+.018,c-.042,.041,.248,2.585,2.815,POST,'South pier recessed grey head')
    block(a-.021,c+.032,-.005,.286,2.815,2.875,CAP,'South pier pale cap below the lintel')
    a,c=north['inner_x'],north['outer_x']
    block(a+.078,c,.026,.286,0,2.665,POST,'North passage upright grey face')
    block(a,a+.078,.026,.479,0,2.665,SIDE,'North upright pale inner corner')
    block(a+.003,a+.086,.469,.552,.025,2.654,SIDE,'North upright visible return at folded leaf')

    for i,side in enumerate(('Inner leaf','Jamb leaf')):
        _,_,_,width,base,height=leaf(i)
        def map_point(x,z,d):
            return leaf_point(i,x/width,(z-base)/height,d)
        def shape(coords):
            return Polygon([(u*width,base+t*height) for u,t in coords])
        holes=[]
        for left,right in slots():
            for lo,hi in ((.125,.402),(.69,.976),(.017,.097)):
                holes.append(box(width*left,base+height*lo,width*right,base+height*hi))
        # Nine real horizontal openings are present in both source rectifications.
        for k in range(9):
            lo=.435+k*.0273
            holes.append(box(width*.075,base+height*lo,width*.92,base+height*(lo+.0147)))
        full_frame=box(0,base,width,base+height).difference(unary_union(holes))
        b.prism(full_frame,-.016,.020,map_point,STEEL,side+' | pierced frame and nine horizontal slots')
        for n,(left,right) in enumerate(slots(),1):
            # Recess each narrow angled blade behind the lips, leaving the
            # photographed dark end slots unfilled. Its plan is a closed solid.
            for lo,hi,label in ((.145,.384,'lower'),(.711,.953,'upper')):
                z0,z1=base+lo*height,base+hi*height
                front=np.asarray(map_point(left*width,z0,-.018))[:2]
                end=np.asarray(map_point((left+.50*(right-left))*width,z0,-.037))[:2]
                along=end-front; normal=np.array([-along[1],along[0]])
                normal*=.0032/np.linalg.norm(normal)
                outline=Polygon([front-normal,end-normal,end+normal,front+normal])
                b.plan_prism(outline,z0,z1,STEEL,f'{side} | {label} recessed fin {n}')
        for t in (.099,.412,.686,.982):
            band=box(0,base+t*height,width,base+(t+.008)*height)
            b.prism(band,.018,.024,map_point,EDGE,f'{side} | shallow horizontal tie {t:g}')
        fins=(.09,.265,.47,.68,.865) if i==0 else (.55,)
        for n,u in enumerate(fins,1):
            top=1.052 if i==1 else 1.028+(.010 if n%2 else 0)
            path=[(u-.018,.995),(u+.018,.995),(u+.016,1.013),(u,top),(u-.016,1.013)]
            if low:path=[path[0],path[1],path[3]]
            b.prism(shape(path),-.011,.004,map_point,EDGE,f'{side} | visible head point {n}')
        if not low:
            for u in (.013,.969):
                b.prism(box(width*u,base,width*(u+.013),base+height),
                        .020,.024,map_point,EDGE,side+' | narrow edge fillet '+str(u))
