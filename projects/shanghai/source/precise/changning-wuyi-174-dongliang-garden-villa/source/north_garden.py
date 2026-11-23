"""North courtyard paving and clipped shrubs documented in the September 2025 front view."""
from math import cos, pi, sin
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from wuyi_fabric import PAVING, slab, paint

GRAVEL='174 | light gravel'
HEDGE='174 | clipped boxwood'
LEAF='174 | sunlit boxwood leaves'
PALETTE={GRAVEL:paint((192,182,159)),HEDGE:paint((78,102,66)),LEAF:paint((100,120,80))}


def north_ground(u,v):
    # Project a point on the garden surface; u,v refer to Wang's 549x740 working chart.
    focal=392.6153846153846
    depth=focal*1.73/(v-538.8153846153846)
    return (3.70+(u-244.5769230769231)*depth/focal,-8.80+depth)


def clipped_crown(b,x,y,r,h,seed,lod):
    sides=10 if lod else 18
    rings=5 if lod else 9
    verts=[(x,y,.036)]
    for k in range(rings):
        angle=-.56+(pi*.5+.55)*k/rings
        for j in range(sides):
            az=2*pi*j/sides
            variation=1+.055*cos(3*az+.9*seed)*cos(angle)+.031*sin(5*az+seed+3*angle)
            rr=r*cos(angle)*variation
            verts.append((x+rr*cos(az),y+rr*.91*sin(az),.04+h*(sin(angle)+.53)/1.53))
    verts.append((x,y,.04+h))
    base=[];crown=[]
    for j in range(sides):
        n=(j+1)%sides;base.append((0,1+n,1+j))
        for k in range(rings-1):
            q=1+k*sides
            base.append((q+j,q+n,q+sides+n,q+sides+j))
        crown.append((1+(rings-1)*sides+j,1+(rings-1)*sides+n,len(verts)-1))
    b.add(verts,base+crown,HEDGE if seed%3 else LEAF,'north garden clipped shrub '+str(seed))


def add_north_garden(b,lod=False):
    # Only the photographed part of the north forecourt is included.
    outline=Polygon([(-.55,-.03),(7.15,-.03),(7.89,-1.32),(8.04,-3.42),
                     (7.62,-4.88),(-.80,-4.88),(-1.34,-3.83)])
    west_path=[(1.66,-.78),(3.12,-.78),(2.74,-2.79),(1.23,-4.88),(-.34,-4.88),(1.05,-2.62)]
    footpath=Polygon(west_path)
    slab(b,outline.difference(footpath),-.065,-.031,GRAVEL,'raked gravel forecourt')
    for i in range(11):
        y=-4.88+i*.402
        band=box(-1.3,y-.001,4.22,y+.383)
        for j in range(5):
            left=-.75+j*.78+(i%2)*.36
            tile=footpath.intersection(band).intersection(box(left,y-.01,left+.754,y+.389))
            if tile.area>.019:slab(b,tile,-.065,-.012,PAVING,'staggered entrance paving')
    samples=[(220,638,.39,.58),(192,654,.32,.45),(231,665,.42,.58),(262,661,.30,.41),
             (279,649,.42,.68),(304,659,.33,.54),(321,648,.38,.60),(342,649,.44,.75),
             (365,670,.53,.68),(129,655,.34,.49),(98,664,.37,.55),(78,679,.42,.57),
             (48,686,.44,.64),(21,688,.39,.55)]
    for n,(u,v,r,h)in enumerate(samples):
        x,y=north_ground(u,v)
        clipped_crown(b,x,y,r,h,n+1,lod)
