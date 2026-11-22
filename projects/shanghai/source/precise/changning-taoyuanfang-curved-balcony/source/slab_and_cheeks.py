"""Shallow bowed slab with successive mouldings, stepped dividing screen and rear wall cut."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon,box
from photo_architecture import Facade
from geometry_reference import on_plane,frontage
from wrought_guard import ribbon

CAST='Warm grey balcony finish';EDGE='Pale concrete moulding';LINE='Darker edge groove'
SOFFIT='Yellowed soffit';REAR='Cream wall in shade';RED='Red facing brick';MORTAR='Buff brick joint'
CHEEK='Grey-green pier stripe';SASH='Dark rear sash';GLASS=['Blue reflected glass','Pale reflected glass','Shadowed blue glass']
XS,F=frontage()
def floor(b,lod):
    samples=np.unique(np.r_[XS,np.linspace(XS[0],XS[-1],32 if lod else 94)])
    left,right=XS[0],XS[-1];back=1.61
    def plan(front_out,depth=back):
        # The end return includes the narrow fascia wrapped around the photographed corner.
        return Polygon([*zip(samples,F(samples)+front_out),[right,depth],[left,depth]])
    b.plan_prism(plan(.031),-.399,-.144,CAST,'Balcony slab/curving fascia and paving')
    b.plan_prism(plan(.034),-.409,-.396,SOFFIT,'Balcony slab/shaded underside')
    b.plan_prism(plan(.003),-.37,-.332,EDGE,'Balcony slab/lower pale bead')
    b.plan_prism(plan(.019),-.332,-.303,LINE,'Balcony slab/separating dark recess')
    b.plan_prism(plan(0.),-.301,-.259,EDGE,'Balcony slab/upper pale bead')
    b.plan_prism(plan(.027),-.147,-.135,EDGE,'Balcony slab/paving lip')
    # Grey propped haunch at the visible left junction with the party wall.
    face=Facade(b,(left+1.36,-.5),(left+1.36,.5),'Under balcony')
    face.prism(Polygon([[.35,-.403],[1.61,-.403],[1.61,-.69],[1.04,-.66],[.53,-.46]]),-.089,.089,CHEEK,'tapered beam end')
def cheeks(b,lod):
    left,right=XS[0],XS[-1];back=1.61
    # Dividing screen top has two steps where the adjacent open bay begins.
    side=Facade(b,(left+.16,-.5),(left+.16,.5),'Party screen')
    lo=float(F(left))+.045
    shape=Polygon([[lo,-.135],[back,-.135],[back,1.99],[1.17,2.10],[1.15,2.28],[.51,2.28],[.50,2.45],[lo,2.45]])
    side.prism(shape,-.14,.012,CAST,'stepped dividing cheek')
    rim=Polygon([[lo,2.41],[.50,2.41],[.50,2.24],[1.15,2.24],[1.15,2.08],[back,1.96],[back,2.03],[1.19,2.14],[1.19,2.31],[.54,2.31],[.54,2.48],[lo,2.48]])
    side.prism(rim,-.15,.031,EDGE,'stepped coping')
    # Only the visible short end of the right wall and its weathered vertical stripe are retained.
    shade=Facade(b,(right-.16,-.5),(right-.16,.5),'End cheek');front=float(F(right))+.15
    shade.prism(box(front,-.135,back,2.95),-.106,.083,CAST,'short right return to rear wall')
    end=Facade(b,(-.5,front),(.5,front),'End pier')
    end.box(right-.16,1.39,.24,3.05,.106,.032,CAST,'street face')
    end.box(right-.19,1.02,.072,2.31,.033,.092,CHEEK,'weathered green vertical inset')
    # The rear cut includes the lower portions of the windows which can actually be read behind the guard.
    f=Facade(b,(-.5,back),(.5,back),'Back of balcony')
    wall=box(left,-.92,right,2.64)
    openings=[(-2.57,.31,-1.45,2.37),(-.90,.57,.828,2.45),(1.40,.39,2.52,2.61)]
    for bounds in openings:wall=wall.difference(box(*bounds))
    f.prism(wall,-.14,0,REAR,'rear wall cut with three visible openings')
    f.prism(box(left,-.92,right,-.48),.001,.007,SOFFIT,'warm underside wall strip')
    # A restrained red-brick pier is visible to the left of the two reflective sashes.
    for a,c in [(-1.44,-1.14),(.847,1.05)]:
        f.prism(box(a,-.10,c,2.64),.001,.012,MORTAR,'brick pier bed')
        for i,z in enumerate(np.arange(-.09,2.64,.067)):
            ends=[a,c]if i%2 else[a,a+(c-a)*.53,c]
            for x,y in zip(ends,ends[1:]):
                f.prism(box(x+.004,z+.003,y-.004,min(z+.063,2.64)),.01,.019,RED,'red brick pier course')
    for i,(a,z,c,h)in enumerate(openings):
        outer=box(a,z,c,h);inner=outer.buffer(-.045,join_style='mitre')
        f.prism(outer.buffer(.014),-.177,-.164,'Deep recess','glazing backstop')
        f.prism(outer.difference(inner),-.082,-.024,SASH,'outside sash frame')
        cols,rows=[(3,3),(4,4),(2,2)][i];width=(c-a-.09)/cols;height=(h-z-.09)/rows
        for j in range(cols):
            for k in range(rows):
                col=GLASS[(k//2+j)%3]if i==1 else('Shaded rear pane'if i==0 else'Deep recess')
                f.box(a+.045+(j+.5)*width,z+.045+(k+.5)*height,width-.016,height-.017,.012,-.085,col,'glazing panel')
        for j in range(1,cols):f.box(a+.045+j*width,(h+z)/2,.020,h-z-.075,.036,-.060,SASH,'fixed glazing upright')
        for j in range(1,rows):f.box((a+c)/2,z+.045+j*height,c-a-.076,.018,.034,-.060,SASH,'fixed glazing transom')
def pendant(b,lod):
    # Small, wall-mounted swan-neck lamp visible beneath the end balcony.
    b.box((-1.43,1.554,-.68),(.085,.06,.148),'Lamp enamel',label='Lamp/wall mount')
    t=np.linspace(0,1,11 if lod else 26)
    points=np.column_stack([-1.43-.025*np.sin(t*np.pi),1.555-.27*t,-.687+.236*np.sin(np.pi*t)-.012*t])
    b.tube(points,.015,'Lamp enamel',sides=6 if lod else 10,label='Lamp/swan-neck tube')
    b.lathe((-1.43,1.285),[(-.763,.125),(-.75,.13),(-.725,.079),(-.698,.029)],'Lamp enamel',segments=14 if lod else 30,label='Lamp/flared shade')
    b.lathe((-1.43,1.285),[(-.808,.011),(-.796,.028),(-.759,.03)],'Pale light bulb',segments=9 if lod else 16,label='Lamp/pale bulb')
