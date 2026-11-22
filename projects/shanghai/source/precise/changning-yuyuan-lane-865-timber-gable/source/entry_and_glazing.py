"""Brick courses, recessed stone portal and the two visible planes of the high central glazing."""
from pathlib import Path
import json,math
import numpy as np
from shapely.geometry import box,Polygon,LineString
from shapely import constrained_delaunay_triangles
from shapely.geometry.polygon import orient
from photo_architecture import Facade,opening
from projection import world
from gable_frame import STONE,BLACK,WOOD,pixel_outline

M=Path(__file__).absolute().parent.parent/'measurements'
BRICKS=['Old rose brick','Pale fired brick','Iron red brick','Muted red brick','Dark fired brick']
MORTAR='Lime mortar'
PLINTH='Blue grey base'
SHADOW_STONE='Stone in reveal'
RECESS='Door panel recess'
DOOR='Dark entrance leaf'
FRAME='Dull steel glazing bars'
GLASS=['Cool blue grey glass','Smoky glass','Dark grey reflection','Blue reflected panes']

def brick_field(f,lod):
    field=pixel_outline([[195,644],[459,679],[447,393],[198,428]])
    portal=box(-.875,-.4,.845,2.36)
    wall=field.difference(portal)
    f.prism(wall,-.36,-.017,MORTAR,'brick wall with full-height entry opening')
    plinth=wall.intersection(box(-5,-.4,5,.28))
    f.prism(plinth,-.025,.021,PLINTH,'continuous grey base course')
    wall=wall.difference(box(-5,-.4,5,.275))
    measured=json.loads((M/'brick-courses.json').read_bytes())
    beds=measured['read_bed_centres_m'][:];pitch=measured['typical_pitch_m']
    while beds[0]>wall.bounds[1]-.03:beds.insert(0,beds[0]-pitch)
    while beds[-1]<wall.bounds[3]+.03:beds.append(beds[-1]+pitch)
    for i,(low,high)in enumerate(zip(beds,beds[1:])):
        width=.208;start=-3.23+.5*width*(i%2)
        for j in range(29):
            x=start+j*width
            p=wall.intersection(box(x+.004,low+.004,x+width-.004,high-.004))
            if p.area<.00004:continue
            col=(i*7+j*11+(j//3)*2)%len(BRICKS)
            label='running bond course %02d'%(i+1)
            if lod:
                # Each front sits on the continuous mortar wall. Individual edge returns
                # are below a distant pixel and are retained in the full geometry.
                patch=constrained_delaunay_triangles(p)
                points=[];faces=[]
                for tri in patch.geoms:
                    n=len(points);points.extend(f.point(u,z,.004)for u,z in list(orient(tri,sign=1.).exterior.coords)[:3])
                    faces.append((n,n+1,n+2))
                f.builder.add(points,faces,BRICKS[col],f.label+'/'+label)
            else:
                f.prism(p,-.014,.003+.002*((i+j)%3),BRICKS[col],label)

def door(f):
    # The tall outside opening is rectangular. The darker inner leaf has a low curved head.
    outer=box(-.875,-.095,.845,2.36);inner=box(-.532,-.12,.674,2.12)
    ring=outer.difference(inner)
    f.prism(ring,-.63,.038,STONE,'outer dressed jambs and square lintel')
    f.prism(box(-.90,2.317,.868,2.372),.03,.061,PLINTH,'outer top edge')
    for i,z in enumerate([.22,.85,1.49,1.98]):
        for side,a,b in [('left',-.928,-.792),('right',.794,.897)]:
            f.prism(box(a,z-.069,b,z+.069),.030,.053,STONE,'projecting jamb block '+side+' %d'%i)
    for i,z in enumerate(np.arange(.36,2.10,.253)):
        for a,b in [(-.873,-.533),(.675,.845)]:
            f.prism(box(a,z-.003,b,z+.003),.037,.041,SHADOW_STONE,'thin cut joint %02d'%i)
    f.prism(box(-.525,-.03,.67,.005),-.68,.029,PLINTH,'recess threshold')
    bore=opening(.037,0,1.126,2.045,.112,segments=28)
    f.prism(box(-.63,-.025,.75,2.24).difference(bore),-.686,-.625,SHADOW_STONE,'shallow arched head in deep entry')
    f.prism(bore.buffer(.009),-.72,-.696,DOOR,'door below curved head')
    for name,x,z,w,h in [('upper',-.02,1.36,.795,.78),('lower',-.02,.52,.79,.55)]:
        raised=box(x-w/2,z-h/2,x+w/2,z+h/2)
        f.prism(raised,-.697,-.688,RECESS,'dark recessed '+name+' field')
        f.prism(raised.difference(raised.buffer(-.019,join_style='mitre')),-.69,-.677,DOOR,'door '+name+' moulding')
    for x in [.216,.247]:f.box(x,1.77,.015,.068,.012,-.682,'Faded brass','two small marks on inner leaf')
    f.box(.39,.98,.025,.115,.036,-.668,'Faded brass','door pull')
    # The small box in the photograph attaches to the inward-facing left reveal.
    side=Facade(f.builder,(-.531,-.5),(-.531,.5),'Left reveal')
    side.box(.28,1.27,.14,.225,.045,.025,'Old switch box','doorbell casing')
    side.box(.28,1.27,.099,.147,.022,.05,'Faded brass','discoloured faceplate')

def sash(f,hole,lod):
    f.prism(hole.buffer(.19,join_style='mitre'),-.67,-.65,BLACK,'dark backing visible beside glazing')
    f.prism(hole.buffer(.02,join_style='mitre').difference(hole.buffer(-.043,join_style='mitre')),-.65,-.055,BLACK,'continuous dark head, sill and jamb returns')
    f.prism(hole.difference(hole.buffer(-.058,join_style='mitre')),-.13,.007,WOOD,'outer tall window frame')
    edges=json.loads((M/'central-glazing.json').read_bytes())
    nodes=np.array(edges['fitted_edges_xy_m']);levels=np.sort(edges['fitted_transom_levels_m'])
    low,top=hole.bounds[1]+.045,hole.bounds[3]-.042
    # The outer right portion is in deep shade behind its timber surround.
    side=Facade(f.builder,(-.5,.515),(.5,.515),'Recessed right pane')
    side.box(.29,(low+top)/2,.69,top-low,.026,0,'Deep glass reflection','right frame shadow')
    for j,(a,b)in enumerate(zip(nodes,nodes[1:])):
        face=Facade(f.builder,a,b,'Central glazing leaf '+str(j+1));width=face.length
        cuts=np.r_[low,levels,top]
        for i,(z0,z1)in enumerate(zip(cuts,cuts[1:])):
            for k in range(2):
                u=(-.25+.5*k)*width
                face.box(u,(z0+z1)/2,width*.5-.009,z1-z0-.012,.014,-.006,GLASS[(2*j+k+i//2)%4], 'reflected pane')
        for u in [-width/2,0,width/2]:
            face.box(u,(low+top)/2,.016 if u else .012,top-low,.028,.009,FRAME,'upright glazing bar')
        for z in cuts:
            face.box(0,z,width,.016,.029,.009,FRAME,'horizontal glazing bar')
    if not lod:
        f.box(-.26,low-.025,.68,.036,.115,.018,'Worn underside of timber','outer sill drip')
