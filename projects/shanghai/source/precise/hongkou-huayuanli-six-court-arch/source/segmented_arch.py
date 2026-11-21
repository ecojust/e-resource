"""Segmental entrance, rounded drip, springing piers and threshold paving."""
import math
import numpy as np
from shapely.geometry import Polygon,box
from court_joinery import LIME,CHIP,STONE,FLOOR

AGED='Warm aged render'
LIP='Rounded light drip'


def profile(xs,crown,radius,center):
    return [crown-radius+math.sqrt(max(0,radius*radius-(x-center)**2)) for x in xs]


def band(x,lower,upper):
    return Polygon([*(zip(x,lower)),*(zip(reversed(x),reversed(upper)))])


def add_portal(b,f,d,lod):
    cx=d['arch_center_x'];rad=d['arch_radius'];z0=d['arch_center_z'];half=d['arch_half_opening'];crown=z0+rad
    width=d['outer_pier_x'];proj=d['canopy_projection']
    n=22 if lod else 76
    # The observable inner edge is a circular segment. Extend only as far as the visible side piers.
    inner_x=np.linspace(cx-half,cx+half,n+1).tolist()
    inner_z=profile(inner_x,crown,rad,cx)
    # Separate full-height piers and the curved spandrel to preserve the real open arch below.
    for side in(-1,1):
        inner=cx+side*half;outer=width*side
        lo,hi=sorted([inner,outer])
        flare=profile([lo,hi],d['porch_cap_crown']-.125,1.96,cx)
        shape=Polygon([(lo,0),(hi,0),(hi,flare[1]),(lo,flare[0])])
        f.prism(shape,-.018,proj,LIME,'Porch/springing pier '+str(side))
    body_cap=profile(inner_x,d['porch_cap_crown']-.125,1.96,cx)
    f.prism(band(inner_x,inner_z,body_cap),-.018,proj,LIME,'Porch/curved solid spandrel')
    # The cap projects forwards and beyond each pier. A section perpendicular
    # to the photographed elevation controls the real drip undercut.
    edge=.052
    xs=np.linspace(-width-edge,width+edge,n+1).tolist()
    zs=profile(xs,d['porch_cap_crown']-.125,1.96,cx)
    layers=[(-.025,.012,proj+.030,AGED,'edge shadow'),
            (.012,.054,proj+.078,CHIP,'stepped coping'),
            (.054,.109,proj+.102,LIP,'rounded drip'),
            (.109,.126,proj+.088,CHIP,'weathering top')]
    for lo,hi,depth,mat,name in layers:
        f.prism(band(xs,[z+lo for z in zs],[z+hi for z in zs]),-.038,depth,mat,'Arch cap/'+name)
    if not lod:
        # Fillet attested by the bright continuous line at the lip of the coping.
        rail=[f.point(x,z+.066,proj+.101)for x,z in zip(xs,zs)]
        b.tube(rail,.009,LIP,7,'Arch cap/outer arris')
    for side in(-1,1):
        inner=cx+side*half
        pier_width=width-abs(inner)
        f.box((inner+side*width)/2,.088,pier_width-.012,.176,proj+.026,proj/2-.008,AGED,'Porch/worn base')
    # Two adjacent flat slabs run across the original photograph at the door foot.
    for i,(low,high) in enumerate([(-1.08,-.69),(-.685,-.27),(-.265,.24)]):
        b.plan_prism(box(-1.54,low,1.54,high),-.045,-.002+(i*.001),FLOOR,'Court/slab '+str(i+1))
