"""Courtyard paving, low garden beds and the circular timber table in the municipal photograph."""
import math
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from north_block import pigment

SLATE=('Court warm slate','Court grey stone flags','Court pale stone flags','Court dark flags')
EARTH='Court planted earth'
FOLIAGE='Court low planting'
BED='Court grey mortar'
EDGING='Court granite border'
TIMBER='Court aged timber'
STEEL='Court black iron feet'
GARDEN_PALETTE={**{name:pigment(rgb) for name,rgb in zip(SLATE,
                ((153,144,133),(149,150,148),(172,168,159),(132,133,129)))},
                EARTH:pigment((107,99,74)),FOLIAGE:pigment((104,117,78)),
                BED:pigment((137,136,127)),EDGING:pigment((141,138,125)),
                TIMBER:pigment((117,83,66)),STEEL:pigment((54,55,50),.65,.28)}
DATA=json.loads((Path(__file__).resolve().parent.parent/'measurements/garden-court.json').read_bytes())

def furniture(b,lod):
    cx,cy=DATA['table_centre_estimated_m']
    for radius,low,top in [(.24,.026,.08),(.084,.07,.72),(.38,.72,.75)]:
        b.lathe((cx,cy),[(low,radius),(top,radius)],STEEL,12 if lod else 24,'Court table pedestal')
    b.lathe((cx,cy),[(.748,.66),(.813,.69)],TIMBER,20 if lod else 48,'Court circular timber tabletop')
    count=11 if lod else 20
    for side in [-1,1]:
        start=math.pi*(0 if side==1 else 1)+.104;end=start+math.pi-.208
        for theta in np.linspace(start+.12,end-.12,4):
            x=cx+math.cos(theta)*1.23;y=cy+math.sin(theta)*1.23
            b.lathe((x,y),[(.018,.079),(.061,.082),(.066,.043),(.412,.043)],
                    STEEL,8,'Court bench iron feet')
        for k in range(count):
            t0=start+(end-start)*k/count+.0025;t1=start+(end-start)*(k+1)/count-.0025
            shell=Polygon([(cx+math.cos(t)*r,cy+math.sin(t)*r)
                           for t,r in [(t0,1.02),(t1,1.02),(t1,1.46),(t0,1.46)]])
            b.plan_prism(shell,.408,.478,TIMBER,'Court radial timber bench slats')

def add_paving(b,region,lod):
    b.plan_prism(region,-.025,.002,BED,'Court ground paving bed')
    # Stone is seen as a mix of long grey and brown flags. Each surface is separated by a real joint.
    piles={key:([],[]) for key in SLATE}
    rng=np.random.default_rng(20250401)
    dy=.66 if lod else .47;dx=.98 if lod else .78
    x0,y0,x1,y1=region.bounds
    for j in range(math.ceil((y1-y0)/dy)):
        bottom=y0+j*dy;shift=(.5*dx if j%2 else 0)
        for i in range(-1,math.ceil((x1-x0)/dx)+1):
            left=x0+i*dx+shift
            tile=box(left+.008,bottom+.008,left+dx-.008,bottom+dy-.008)
            material=SLATE[int(rng.choice(4,p=(.25,.38,.23,.14)))]
            if not tile.intersects(region):continue
            cut=region.intersection(tile)
            for poly in ([cut]if cut.geom_type=='Polygon' else getattr(cut,'geoms',())):
                if poly.geom_type!='Polygon' or poly.area<.001:continue
                # The court beds curve gently. Convex fragments can use a single fan.
                if poly.area < poly.convex_hull.area-.00001:
                    b.plan_prism(poly,.002,.014,material,'Court clipped flags')
                    continue
                vs,fs=piles[material];points=list(poly.exterior.coords)[:-1];n=len(vs)
                if not poly.exterior.is_ccw:points.reverse()
                vs.extend([(x,y,.014)for x,y in points]);fs.append(tuple(range(n,n+len(points))))
    for material,(vertices,faces)in piles.items():
        if faces:b.add(vertices,faces,material,'Court staggered stone flags')

def build_garden(b,lod,walk_corners):
    court=Polygon(DATA['inner_ground_boundary_m'])
    gardens=[Polygon(row).buffer(.42,join_style=1).buffer(-.42,join_style=1)
             for row in DATA['garden_beds_m']]
    planted=unary_union(gardens)
    walkway=Polygon(walk_corners)
    add_paving(b,court.difference(planted.union(walkway)),lod)
    for i,bed in enumerate(gardens):
        b.plan_prism(bed,-.021,.065,EARTH,'Court planted bed')
        b.plan_prism(bed.buffer(-.18),.065,.081,FOLIAGE,'Court planted cover')
        edge=bed.buffer(.115,join_style=1).difference(bed)
        b.plan_prism(edge,.002,.115,EDGING,'Court low beds edging')
    furniture(b,lod)
