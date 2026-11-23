"""Six uneven axes of the garden facade: masonry, projecting stair bay, frames, panelling and operable shutters."""
from pathlib import Path
import json
import math
import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from entrance import material, face, solid

HERE=Path(__file__).absolute().parent
WALL='Yihe | buff courtyard masonry'
TRIM='Yihe | pale carved window surrounds'
JOINT='Yihe | shaded masonry beds'
WOOD='Yihe | oxblood painted shutter'
RECESS='Yihe | deep shutter slat'
SASH='Yihe | brown wood sash'
PANE='Yihe | muted courtyard reflections'
PIPE='Yihe | painted rainwater pipe'
BRONZE='Yihe | weathered entrance plaques'
GRAPHITE='Yihe | dark exterior fittings'
PALE='Yihe | frosted lantern panes'
PALETTE={WALL:material('#c3c1b1',.94),TRIM:material('#d0cbb8',.91),JOINT:material('#a5a498',.95),
         WOOD:material('#643f3b',.72),RECESS:material('#50332e',.83),SASH:material('#4e3b31',.61),
         PANE:material('#656a62',.36),PIPE:material('#c8c5b6',.7),BRONZE:material('#8b8671',.65),
         GRAPHITE:material('#393f38',.68),PALE:material('#c1bda3',.62)}
# Angles follow the visible left and right leaves in the 2015 Commons photograph; 0 is closed.
STATES={'upper':[(0,0),(70,89),(66,72),(0,0),(0,0),(70,106)],
        'middle':[(84,105),(0,0),(77,73),(68,111),(82,81),(82,77)],
        'ground':[(82,103),(68,76),None,(77,84),(73,78),(86,74)]}
YBAY=-.33;BAY_L=-1.94;BAY_R=1.86
def window(b,l,r,base,top,y,level,index,lod):
    w=r-l;h=top-base;label=f'Courtyard | {level} {index+1} | '
    # Slightly recessed masonry reveals continue all the way around cut openings.
    outside=box(l-.104,base-.068,r+.104,top+.105)
    inside=box(l,base,r,top)
    face(b,outside.difference(inside),y-.055,y+.008,TRIM,label+'stone jambs')
    face(b,box(l-.083,base-.075,r+.083,base+.025),y-.125,y+.14,TRIM,label+'projecting sill')
    head=box(l-.12,top+.067,r+.12,top+.13)
    face(b,head,y-.070,y+.009,TRIM,label+'moulded head')
    sg=.048
    face(b,inside.difference(box(l+sg,base+sg,r-sg,top-sg)),y+.125,y+.23,SASH,label+'rebated wood lining')
    solid(b,l+sg,r-sg,y+.244,y+.259,base+sg,top-sg,PANE,label+'setback casement glazing')
    trans=base+h*.694
    for x in [l+w*.25,l+w*.5,l+w*.75]:
        thick=.029 if x==l+w*.5 else .016
        solid(b,x-thick,x+thick,y+.135,y+.19,base+sg,top-sg,SASH,label+'upright')
    for q,width in [(trans,.045),(base+h*.39,.018)]:
        solid(b,l+sg,r-sg,y+.129,y+.185,q-width,q+width,SASH,label+'sash and transom rails')
    angles=STATES[level][index]
    for hand,(hinge,angle) in enumerate(zip((l+.015,r-.015),angles)):
        sign=(1,-1)[hand];t=math.radians(angle);leafw=w*.49
        ax=np.array([sign*math.cos(t),-math.sin(t)])
        # The extrusion uses a right handed local coordinate system.
        normal=np.array([ax[1],-ax[0]])
        anchor=np.array([hinge,y-.068])
        def mapper(u,z,d):
            p=anchor+u*ax+d*normal
            return p[0],p[1],z
        panel=box(0,base+.025,leafw,top-.026);bw=min(.063,leafw*.115)
        regions=[(base+.10,trans-.063),(trans+.066,top-.095)]
        openings=unary_union([box(bw,z0,leafw-bw,z1) for z0,z1 in regions])
        b.prism(panel.difference(openings),-.019,.022,mapper,WOOD,label+'hinged two-field shutter')
        for z0,z1 in regions:
            n=max(3,round((z1-z0)/(.134 if lod else .079)))
            lines=np.linspace(z0,z1,n+1)
            # Separate slats expose their thickness and lower edges in oblique views.
            bars=unary_union([box(bw,lo+.009,leafw-bw,hi-.004) for lo,hi in zip(lines,lines[1:])])
            b.prism(bars,-.012,.012,mapper,WOOD,label+'louvres')
            b.prism(box(bw,z0,leafw-bw,z1),-.020,-.013,mapper,RECESS,label+'louvre shadow')
    if level=='ground' or (level=='middle' and index in (2,5)):
        low=base-.54
        apron=Polygon([(l-.16,base-.07),(r+.16,base-.07),(r+.16,low),
                       (r-.22,low),(r-.22,low+.16),(l+.22,low+.16),(l+.22,low),(l-.16,low)])
        face(b,apron,y-.068,y+.005,TRIM,label+'notched stone apron')
    if level=='upper':
        z0=9.30;z1=base-.28
        panel=box(l-.02,z0,r+.02,z1)
        face(b,panel.difference(box(l+.052,z0+.075,r-.052,z1-.075)),y-.05,y+.02,TRIM,label+'panel between the two floors')
        if not lod:
            beads=[]
            for x in (l+.01,r-.01):
                for z in np.arange(z0+.10,z1-.06,.136):
                    beads.append(box(x-.022,z-.027,x+.022,z+.027))
            for z in (z0+.047,z1-.047):
                for x in np.arange(l+.08,r-.04,.14):
                    beads.append(box(x-.025,z-.014,x+.025,z+.014))
            face(b,unary_union(beads),y-.066,y-.047,TRIM,label+'small relief along panel margin')
def plaque_and_lamps(b,lod):
    # Ratios and spacings follow the panel to the west of the doorway. Lettering would be below photograph resolution.
    x=-3.23;y=-.047
    solid(b,x-.43,x+.43,y,.018,1.42,4.22,GRAPHITE,'Entrance | common metal plaque backing')
    for i,(a,t) in enumerate([(3.63,4.215),(3.09,3.61),(2.53,3.07),(1.98,2.51),(1.43,1.96)]):
        solid(b,x-.417,x+.417,y-.024,y,a,t,BRONZE,'Entrance | separate metal directory plate '+str(i+1))
        if not lod:
            for xx in (x-.365,x+.365):
                for zz in (a+.055,t-.055):
                    b.tube([(xx,y-.024,zz),(xx,y-.033,zz)],.012,GRAPHITE,6,'Entrance | plate fastener')
    for x in (-6.25,4.57):
        z=8.48
        b.tube([(x,.015,z-.24),(x,-.25,z-.19),(x,-.33,z-.08)],.035,GRAPHITE,8,'Courtyard | curved wall lantern arm')
        b.lathe((x,-.34),[(z-.13,.048),(z-.07,.11),(z+.13,.145)],PALE,4,'Courtyard | lantern glass')
        b.lathe((x,-.34),[(z+.125,.16),(z+.16,.16),(z+.29,.023)],GRAPHITE,4,'Courtyard | lantern hood')
        for dx,dy in ((.11,0),(-.11,0),(0,.11),(0,-.11)):
            b.tube([(x+dx*.7,-.34+dy*.7,z-.1),(x+dx*1.22,-.34+dy*1.22,z+.13)],.012,GRAPHITE,6,'Courtyard | lantern upright')
def add_courtyard_front(b,lod=False):
    c=json.loads((HERE.parent/'measurements/court-cameras.json').read_bytes())
    xs=c['axis_left_jambs_m'];widths=c['opening_widths_m'];zt,zb,zm=c['window_heights_m']
    door=box(-2.32,.54,.12,4.195)
    apertures=[]
    for n,(l,w) in enumerate(zip(xs,widths)):
        y=YBAY if n==2 else 0
        l+=-.34 if n==2 else 0
        for level,z0,z1 in [('upper',zb,zt),('middle',5.52 if n in (0,1,3,4) else 6.64,zm),('ground',1.62,4.33)]:
            if n==2 and level=='ground':continue
            apertures.append(box(l,z0,l+w,z1))
            window(b,l,l+w,z0,z1,y,level,n,lod)
    holes=unary_union([door,*apertures])
    for i,(a,e,y) in enumerate([(-10.42,BAY_L,0),(BAY_L,BAY_R,YBAY),(BAY_R,12.51,0)]):
        panel=box(a,-.015,e,15.09).difference(holes)
        face(b,panel,y,.39,WALL,'Courtyard | bay '+str(i+1)+' masonry cut for every opening')
        # The masonry courses break at the projecting central bay, doors and window openings.
        lines=[]
        for j,z in enumerate(np.arange(.06,15.0,.405)):
            lines.append(box(a,z,e,z+.010))
            for x in np.arange(a+.56+(j%2)*.53,e,1.06):
                lines.append(box(x,z+.011,x+.008,min(z+.405,15.06)))
        joints=unary_union(lines).intersection(panel)
        face(b,joints,y-.004,y+.001,JOINT,'Courtyard | staggered ashlar beds')
    # 2015 and 2018 both show vertical downpipes at the outer limits of the front.
    for x in [-10.32,12.38]:
        b.tube([(x,-.065,.14),(x,-.065,14.67),(x,-.18,15.0)],.068,PIPE,10 if lod else 16,'Courtyard | metal rainwater pipe')
        if not lod:
            for z in np.arange(.48,14.81,1.7):
                b.lathe((x,-.065),[(z-.018,.07),(z-.013,.085),(z+.014,.085),(z+.019,.07)],PIPE,12,'Courtyard | downpipe neck')
    plaque_and_lamps(b,lod)
