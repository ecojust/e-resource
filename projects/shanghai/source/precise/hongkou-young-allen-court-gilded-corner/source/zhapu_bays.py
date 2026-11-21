"""The Zhapu Road bay windows and the shallow curved gable over the first oriel."""
import math
import numpy as np
from shapely.geometry import LineString,Polygon,box
from photo_architecture import Facade
from frontage import BRICK,BRIGHT,CLAY,GLASS,METAL,PLASTER,RED,SASH,SLATE,STONE,brick_arch,sash,storefront
from pitched_roofs import roof_panel


def gable(b,axis,p,lod):
    x=p['shell']['west']-.12;y=-axis;e=p['eave'];w=3.25
    f=Facade(b,[x,y+w/2],[x,y-w/2],'Zhapu gable')
    # Two low shoulders step up to meet a single shallow central circular cap.
    canopy=[(-w/2,e+1.00),(-w/2,e+1.59),(-1.14,e+1.62),(-.66,e+1.72),
            (-.66,e+1.82),(-.48,e+1.82)]
    for t in np.linspace(math.pi,0.,9 if lod else 21):
        canopy.append((.48*math.cos(t),e+1.82+.20*math.sin(t)))
    canopy.extend([(.66,e+1.82),(.66,e+1.72),(1.14,e+1.62),(w/2,e+1.59),(w/2,e+1.00)])
    # A finite wall below the crest carries one recessed timber casement.
    outline=Polygon([(u,v) for j,(u,v) in enumerate(canopy) if not j or (u,v)!=canopy[j-1]])
    f.prism(outline,-.22,0,PLASTER,'Rendered curved crest')
    lip=LineString(canopy[1:-1]).buffer(.046,cap_style=2,join_style=2)
    f.prism(lip,-.25,.082,STONE,'Stepped coping')
    h=1.01;bottom=e-.07
    hole=sash(f,0.,bottom+.10,1.00,.92,.028,lod,hood=False)
    f.wall(bottom,e+1.04,[hole],.27,BRICK)
    roof_panel(b,[[x,y+w/2,e+1.015],[x,y-w/2,e+1.015],[x+2.,y-w/2,e+1.75],[x+2.,y+w/2,e+1.75]],SLATE,'Zhapu gable / connecting roof')


def bay(b,p,axis,front_width,reach,span,lod,feature):
    sx=p['shell']['west'];y=-axis;h=p['eave'];plinth=3.49
    profile=[[sx,y+span/2],[sx-reach,y+front_width/2],[sx-reach,y-front_width/2],[sx,y-span/2]]
    polygon=Polygon(profile)
    b.plan_prism(polygon,plinth-.11,plinth+.025,STONE,'Zhapu bays / projected soles')
    for i,(a,c) in enumerate(zip(profile,profile[1:])):
        f=Facade(b,a,c,'Zhapu fanlight bay' if feature else 'Zhapu south bay')
        face=i==1
        holes=[]
        for k,(z,ht) in enumerate(((3.88,2.36),(8.24 if feature else 7.82,1.55 if feature else 1.77))):
            if not face and feature and i==0:
                continue
            width=((1.77 if k==0 else 2.06) if feature else min(front_width-.31,1.35)) if face else max(.36,min(f.length-.20,.93))
            isfan=feature and face and k==0
            ar=width*.45 if isfan else (.18 if not face else .07)
            holes.append(sash(f,0,z,width,ht,ar,lod,fan=isfan,hood=not isfan))
            if isfan:
                # The round head's radial bricks match the grey field of this bay.
                first=len(b.parts);brick_arch(f,0,z+ht-ar,width,ar,lod,label='Grey radial fanlight arch')
                for part in b.parts[first:]:part['material']=BRICK
        f.wall(plinth,h,holes,.27,BRICK)
        for z,th,mat in ((6.59,.12,STONE),(6.71,.08,RED),(h-.24,.095,STONE),(h-.085,.15,STONE)):
            f.beam(z,th,.095,mat,label='Oriel ledges')
    b.plan_prism(polygon,h-.08,h+.02,METAL,'Zhapu bays / upper cap')
    return profile


def west_front(f,p,lod):
    b=f.builder;h=p['eave'];s=p['shell'];first,second=p['west_oriels']
    # Construct the breaks in the street plane. The arch and the narrow
    # windows live in the projected walls, with clear glass behind each reveal.
    gaps=[]
    for axis,front,reach,span,feature in [(first,2.83,.79,4.45,True),(second,2.46,.63,4.06,False)]:
        bay(b,p,axis,front,reach,span,lod,feature)
        y=-axis;u=f.t[1]*(y-f.center[1]);gaps.append(box(u-span/2,3.47,u+span/2,h+.02))
    f.wall(3.49,h,gaps,.28,BRICK)
    shops=np.linspace(-f.length/2,f.length/2,5)
    storefront(f,[((a+c)/2,(c-a)*.81)for a,c in zip(shops,shops[1:])],3.49,lod)
    for interval in ([(s['west'],f.a[1],-first+2.225),(s['west'],-first-2.225,-second+2.03),(s['west'],-second-2.03,f.b[1])]):
        x,y1,y2=interval
        if abs(y1-y2)<.04:continue
        edge=Facade(b,[x,y1],[x,y2],'Zhapu flush walls')
        for z,th in ((6.69,.10),(h-.23,.12),(h-.072,.11)):
            edge.beam(z,th,.077,RED,label='Red belt courses')
        if edge.length>2:
            edge.box(0,7.05,.28,7.0,.07,.022,RED,'Brick pier')
    gable(b,first,p,lod)
