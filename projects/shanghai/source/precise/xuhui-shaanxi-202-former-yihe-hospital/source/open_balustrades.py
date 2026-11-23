"""Three photographed stone balcony enclosures on the former Yihe Hospital."""
from pathlib import Path
import json
import numpy as np
from shapely import set_precision
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

MEASUREMENT=Path(__file__).absolute().parent.parent/'measurements'
STONE='Yihe | buff stone balcony'
EDGE='Yihe | weathered pale coping'
RELIEF='Yihe | raised stone plaques'
PALETTE={STONE:dict(color=[.589,.551,.441],roughness=.91),
         EDGE:dict(color=[.61,.578,.484],roughness=.92),
         RELIEF:dict(color=[.655,.613,.506],roughness=.91)}

def balustrade_layout():
    return json.loads((MEASUREMENT/'balustrade-sections.json').read_bytes())

def diamond(cx,cz,r):
    return Polygon([(cx-r,cz),(cx,cz+r),(cx+r,cz),(cx,cz-r)])

def horizontal_slab(builder,points,z0,z1,material,label,offset=0):
    plan=Polygon(points)
    if offset:
        plan=plan.buffer(offset,join_style=2)
    builder.plan_prism(plan,z0,z1,material,label)

def panel(builder,a,b,z0,z1,figures,label,lod):
    """A directed edge has its outside to the right. All openwork is cut through its complete depth."""
    face=Facade(builder,a,b,label)
    height=z1-z0;length=face.length
    footing=z0+.178*height;head=z1-.13*height
    bottom=footing+.061*height;top=head-.010*height
    center=(bottom+top)/2;R=(top-bottom)/2
    edge_width=min(.18,length*.073)
    step=(length-2*edge_width)/len(figures)
    origin=-length/2+edge_width
    bar=min(.061,R*.15)
    depth=.19
    solid=[box(-length/2,bottom,-length/2+edge_width,top),box(length/2-edge_width,bottom,length/2,top)]
    raised=[]
    for i,letter in enumerate(figures):
        cx=origin+step*(i+.5)
        if letter=='O':
            number=9 if lod else 25
            disc=Point(cx,center).buffer(R,quad_segs=number)
            ring=disc.difference(Point(cx,center).buffer(R-bar,quad_segs=number))
            plaque=box(cx-.42*R,center-.42*R,cx+.42*R,center+.42*R)
            solid.extend([ring,plaque,box(cx-bar/2,bottom,cx+bar/2,top),
                          box(cx-step/2,center-bar/2,cx+step/2,center+bar/2)])
            raised.append(box(cx-.21*R,center-.21*R,cx+.21*R,center+.21*R))
            if not lod:
                inset=plaque.buffer(-.020,join_style=2)
                raised.append(inset.difference(inset.buffer(-.022,join_style=2)))
        else:
            l,r=cx-step*.44,cx+step*.44
            limits=box(cx-step/2,bottom,cx+step/2,top)
            crossed=unary_union([LineString([(l,bottom),(r,top)]).buffer(bar*.62,cap_style=3),
                                 LineString([(l,top),(r,bottom)]).buffer(bar*.62,cap_style=3)]).intersection(limits)
            core=diamond(cx,center,.55*R)
            solid.extend([crossed,core,box(cx-step/2,center-bar/2,cx+step/2,center+bar/2),
                          box(cx-bar/2,bottom,cx+bar/2,top)])
            raised.append(diamond(cx,center,.29*R))
            if not lod:
                inset=core.buffer(-.019,join_style=2)
                raised.append(inset.difference(inset.buffer(-.018,join_style=2)))
        if i:
            post=origin+i*step
            solid.append(box(post-bar*.90,bottom,post+bar*.90,top))
            for h in (bottom+.033,top-.033):
                solid.append(box(post-bar*1.23,h-.033,post+bar*1.23,h+.033))
    face.prism(set_precision(unary_union(solid),1e-6),-.075,.0,STONE,'pier and perforated ring-diamond field')
    face.prism(set_precision(unary_union(raised),1e-6),-.002,.022,RELIEF,'stone centers in shallow relief')
    # Narrow horizontal openings are clearly visible below the ring field in the Commons photograph.
    feet=[box(-length/2,z0+.104*height,-length/2+edge_width,footing),
          box(length/2-edge_width,z0+.104*height,length/2,footing)]
    for i in range(1,len(figures)):
        at=origin+i*step
        feet.append(box(at-bar,z0+.104*height,at+bar,footing))
    face.prism(unary_union(feet),-depth,0.,STONE,'spaced feet below lower rail')
    face.prism(box(-length/2,footing,length/2,bottom),-depth-.025,.017,STONE,'lower rail')
    face.prism(box(-length/2,top,length/2,head+.028*height),-depth-.012,.017,STONE,'neck under coping')
    face.prism(box(-length/2-.024,head+.028*height,length/2+.024,z1),-depth-.060,.060,EDGE,'overhanging handrail')
    if not lod:
        face.prism(box(-length/2-.014,head+.030*height,length/2+.014,head+.051*height),
                   -depth-.035,.040,STONE,'lower quirk on handrail')

def add_balustrades(builder,lod=False):
    for name,spec in PALETTE.items():
        builder.palette.setdefault(name,spec)
    entries=balustrade_layout()
    for name,b in entries.items():
        prefix='Yihe balcony | '+name
        z0,z1=b['z0'],b['z1'];p=b['plan']
        horizontal_slab(builder,p,z0,z0+.104*(z1-z0),EDGE,prefix+'/floor and eaves',.044)
        horizontal_slab(builder,p,z0+.061*(z1-z0),z0+.086*(z1-z0),STONE,prefix+'/fascia mould',.062)
        for edge,pattern in b['panels']:
            start,end=edge
            panel(builder,p[start],p[end],z0,z1,pattern,prefix+'/edge '+str(start),lod)
        if name=='upper west bay':
            for (start,end),pattern in b['panels']:
                a,c=p[start],p[end];f=Facade(builder,a,c,prefix+'/cornice')
                count=max(2,round(f.length/.24))
                for i in range(count):
                    at=-f.length/2+(i+.5)*f.length/count
                    f.box(at,z0-.037,.096,.074,.105,-.004,STONE,'dentil')
        else:
            # The springing consoles can be seen under the 2018 close view.
            xleft,xright=p[0][0],p[1][0];y=p[0][1]
            for x in (xleft+.45,xright-.45):
                section=Polygon([(y+.14,z0),(0,z0),(0,z0-.51),(y+.89,z0-.38)])
                builder.prism(section,x-.13,x+.13,lambda y,z,x:(x,y,z),STONE,prefix+'/sloping console')
    return entries
