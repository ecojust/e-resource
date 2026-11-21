"""Clay roof ridge and street-facing slate apron with individually modelled dormers."""
import math
import numpy as np
from shapely.geometry import Polygon,box
from photo_architecture import Facade
from frontage import BRICK,SLATE,TILE,CLAY,PLASTER,METAL,RED,STONE,SASH,GLASS


def roof_panel(b,points,material,label,thickness=.075):
    upper=np.asarray(points,dtype=float)
    normal=np.cross(upper[1]-upper[0],upper[2]-upper[0])
    if normal[2]<0:upper=upper[::-1]
    n=len(upper);lower=upper-[0,0,thickness]
    fs=[list(range(n)),list(reversed(range(n,2*n)))]
    for i in range(n):
        j=(i+1)%n;fs.append([i,n+i,n+j,j])
    b.add([*upper,*lower],fs,material,label)


def dormer(b,x,y,p,lod):
    eave=p['eave'];width=1.42;depth=1.83
    # White triangular pediment above the wooden casement; the roofs slope
    # from a projecting central ridge down to the two darker side cheeks.
    y=p['dormer_front'];z=eave+1.43;peak=p['dormer_apex']-.075;shoulder=peak-.63
    f=Facade(b,[x+width*.5,y],[x-width*.5,y],'Kunshan dormers')
    border=Polygon([(-width/2,z),(width/2,z),(width/2,shoulder),(0,peak),(-width/2,shoulder)])
    ap=box(-.425,z+.11,.425,shoulder-.15)
    f.prism(border.difference(ap),-.16,0,PLASTER,'Punched gable ends')
    f.prism(ap.buffer(.012,join_style=2),-.251,-.226,GLASS,'Dormer glazing')
    inn=ap.buffer(-.055);bars=[box(-.024,z,.024,shoulder),box(-.46,shoulder-.55,.46,shoulder-.50)]
    f.prism(ap.difference(inn.difference(bars[0].union(bars[1]))),-.185,-.09,SASH,'Dormer sashes')
    for side in (-1,1):
        xx=x+side*width/2
        b.box((xx,y-depth/2,(z+shoulder)/2),(.085,depth,shoulder-z),SLATE,label='Kunshan dormers / slate cheeks')
        ridge=[x,y+.17,peak+.07];upper=[x,y-depth,peak+.07]
        lip=xx+side*.13
        roof_panel(b,[ridge,upper,[lip,y-depth,shoulder+.06],[lip,y+.17,shoulder+.06]],TILE,'Kunshan dormers / paired tile roofs')
        b.tube([[lip,y+.17,shoulder+.06],ridge],.048,CLAY,6 if lod else 10,'Kunshan dormers / gable verges')
        if not lod:
            for yy in np.linspace(y-depth+.14,y-.03,7):
                b.tube([[lip,yy,shoulder+.07],[x,yy,peak+.08]],.014,CLAY,5,'Kunshan dormers / tile laps')
    b.tube([[x,y+.18,peak+.088],[x,y-depth,peak+.088]],.057,CLAY,7 if lod else 12,'Kunshan dormers / ridge tiles')


def pitched_roof(b,p,front,lod):
    s=p['shell'];n=s['north'];w=s['west'];e=s['east'];south=s['south']
    yr=(n+south)*.5+.46;eave=p['eave'];crest=p['ridge']
    # Registered overhead views show one long axial ridge, a cross hip over
    # the short west return, and clay slopes on both sides of the ridge.
    for y0,step,name in [(n,-1,'North'),(south,1,'South')]:
        width=(.89 if name=='North' else 2.06)
        y1=y0+step*width
        z1=eave+(1.88 if name=='North' else 1.41)
        # The west hip and tilted short slope meet this end diagonally.
        A=[w,y0,eave];B=[e,y0,eave];C=[e,y1,z1];D=[w+(.62 if name=='North' else .88),y1,z1]
        roof_panel(b,[A,B,C,D],SLATE if name=='North' else TILE,name+' roof / lower pitched apron')
        roof_panel(b,[D,C,[e,yr,crest],[w+2.63,yr,crest]],TILE,name+' roof / clay pitch')
        if not lod:
            for t in np.linspace(.045,.96,15):
                y=y1+(yr-y1)*t;z=z1+(crest-z1)*t+.008
                x=D[0]+(w+2.63-D[0])*t
                b.tube([[x,y,z],[e,y,z]],.014,CLAY,6,name+' roof / horizontal tile laps')
        b.tube([[w,y0,eave],[e,y0,eave]],.068,METAL,8,name+' roof / eaves channel')
    roof_panel(b,[[w,n,eave],[w+.62,n-.89,eave+1.88],[w+2.63,yr,crest]],SLATE,'West roof / front hip')
    roof_panel(b,[[w,n,eave],[w+2.63,yr,crest],[w,south,eave]],SLATE,'West roof / central hip')
    roof_panel(b,[[w,south,eave],[w+2.63,yr,crest],[w+.88,south+2.06,eave+1.41]],TILE,'West roof / rear hip')
    east=Facade(b,[e,south],[e,n],'Attached gable')
    outline=Polygon([(-east.length/2,eave),(east.length/2,eave),(n-.89-east.center[1],eave+1.88),(yr-east.center[1],crest),(south+2.06-east.center[1],eave+1.41)])
    east.prism(outline,-.24,0,BRICK,'Sloping end closure')
    b.tube([[w+2.63,yr,crest+.016],[e+.06,yr,crest+.016]],.109,CLAY,8 if lod else 14,'Roof / continuous clay ridge')
    for x in p['roof_cross_cappings']:
        pts=[[x,n,eave+.028],[x,n-.89,eave+1.908],[x,yr,crest+.032],[x,south+2.06,eave+1.438],[x,south,eave+.028]]
        for left,right in zip(pts,pts[1:]):
            l=np.asarray(left);r=np.asarray(right);o=np.array([.103,0,0])
            roof_panel(b,[l+o,r+o,r-o,l-o],STONE,'Roof / two cross-slope cappings',thickness=.094)
    for x in p['north_dormers']:dormer(b,x,n,p,lod)
    for x in p.get('chimneys',[]):
        y=n-1.26 if x<5. else n-2.54;bottom=eave+1.65;top=(15.29 if x<5. else bottom+1.54)
        b.box([x,y,(bottom+top)/2],[.56 if x<5. else .4,.55,top-bottom],PLASTER if x<5. else RED,label='Roof / chimney shafts')
        b.box([x,y,top+.06],[.54,.60,.13],STONE,label='Roof / chimney copings')
        b.box([x,y,top+.131],[.27,.31,.018],METAL,label='Roof / flue mouths')
