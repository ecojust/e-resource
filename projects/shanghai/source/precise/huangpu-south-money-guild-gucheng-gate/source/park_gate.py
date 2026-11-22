"""Present-day south gate, with three arched pairs of black leaves and a carved brick lintel."""
from math import cos, pi, sin
from pathlib import Path
import numpy as np
from shapely.affinity import scale,translate
from shapely.geometry import Point, Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from sign_lettering import add_facade_lettering
from tiled_canopies import PALETTE as ROOF_PALETTE, roofs, RIDGE, SOFFIT

PLASTER='Pale limewashed masonry'
BASE='Bluish grey stone plinth'
FRAME='Green grey arch stones'
KEY='Muted joints between arch blocks'
DOOR='Nearly black timber leaves'
IRON='Dark iron ring and bosses'
STONE='Worn grey granite steps'
LIGHT='Pale drum stones'
BRICK='Grey carved inscription stone'
EDGE='Recessed dark brick joints'
RAISED='Raised pale inscription strokes'
RELIEF='Weathered brick relief'
BACK='Deep relief shadow'
PALETTE=dict(ROOF_PALETTE)
PALETTE.update({k:{'color':v,'roughness':.9 if k!=IRON else .62,'metallic':.25 if k==IRON else 0} for k,v in [
    (PLASTER,[.84,.835,.77]),(BASE,[.298,.337,.332]),(FRAME,[.466,.502,.424]),(KEY,[.392,.413,.354]),
    (DOOR,[.114,.105,.094]),(IRON,[.265,.25,.201]),(STONE,[.485,.478,.420]),(LIGHT,[.649,.649,.556]),
    (BRICK,[.57,.553,.473]),(EDGE,[.324,.314,.273]),(RAISED,[.692,.662,.556]),(RELIEF,[.425,.405,.341]),(BACK,[.294,.292,.260])]})
FONT=Path(__file__).parent/'fonts/SouthGuildhallSign.otf'
HALF=9.7046
AXES=(-3.99,0.,3.99)


def moulding(f,c,z,w,h,depth,mat,label):
    f.box(c,z,w,h,depth*2,depth*.46,mat,label)


def frame(f,c,z,w,h,th,back,front,material,label):
    rect=box(c-w/2,z-h/2,c+w/2,z+h/2)
    f.prism(rect.difference(rect.buffer(-th,join_style=2)),back,front,material,label)


def doorway(f,axis,middle,lod):
    bottom=.48 if middle else .42;top=3.91 if middle else 3.51
    spring=2.86 if middle else 2.72
    outer=1.31 if middle else 1.;half=outer-(.245 if middle else .19)
    steps=18 if lod else 42
    void=opening(axis,bottom-.012,2*half,top-bottom+.012,top-spring,steps)
    outline=opening(axis,.16,2*outer,top+outer-half-.16,top-spring+outer-half,steps)
    f.prism(outline.difference(void),-.06,.049,FRAME,'Dressed green grey arch stones')
    for i in range(1,10):
        angle=pi*i/10
        q=[(axis+half*cos(angle),spring+(top-spring)*sin(angle)),(axis+outer*cos(angle),spring+(top-spring+outer-half)*sin(angle))]
        f.builder.tube([f.point(x,z,.052)for x,z in q],.0085,KEY,4,'Arched voussoir joints')
    for side in (-1,1):
        for z in [.96,1.61,2.27]:
            moulding(f,axis+side*(half+outer)/2,z,outer-half,.014,.038,KEY,'Jamb bed joints')
        cut=box(axis+(.014 if side==1 else -half-.02),bottom-.03,axis+(half+.02 if side==1 else -.014),top+.012)
        f.prism(void.intersection(cut),-.253,-.187,DOOR,'Paired closed black plank doors')
        if not lod:
            for frac in (0.26,.52,.78):
                u=axis+side*half*frac;cap=spring+(top-spring)*max(0,1-frac**2)**.5
                f.box(u,(bottom+cap)/2,.012,cap-bottom-.052,.008,-.182,DOOR,'Subtle vertical timber joints')
        u=axis+side*.19;zc=1.91 if middle else 1.79
        boss=Polygon([(u+(.103 if k%2 else .137)*cos(k*pi/10),zc+(.103 if k%2 else .137)*sin(k*pi/10))for k in range(20)])
        f.prism(boss,-.187,-.151,IRON,'Lobed knocker backplates')
        ring=[f.point(u+.069*cos(2*pi*k/24),zc-.081+.079*sin(2*pi*k/24),-.113)for k in range(25)]
        f.builder.tube(ring,.018,IRON,5 if lod else 9,'Paired iron ring knockers')
    return void


def bands(f,lod):
    # Six stone characters read from the viewer's right. The carved borders and relief strips
    # share the width-to-height relationships measured in the 2014 close photograph.
    f.box(0,6.14,6.00,1.92,.23,.060,BRICK,'Brick cartouche ground')
    for z,w,h,d,material in [(5.20,6.22,.10,.22,BRICK),(5.30,6.33,.08,.19,EDGE),(5.47,6.04,.24,.145,BRICK),(5.64,6.20,.07,.21,BRICK),(5.72,6.10,.045,.157,EDGE),(6.63,6.23,.055,.159,EDGE),(6.73,6.36,.095,.21,BRICK),(6.84,6.20,.05,.17,EDGE),(7.04,6.10,.28,.15,BRICK),(7.26,6.40,.105,.20,BRICK)]:
        moulding(f,0,z,w,h,d,material,'Stepped grey brick string courses')
    for w,h,d in [(3.62,.75,.161),(3.49,.64,.192),(3.39,.58,.201)]:
        frame(f,0,6.09,w,h,.043,d-.048,d,BRICK,'Stepped inscription border')
    f.box(0,6.09,3.30,.52,.027,.172,BRICK,'Six separate inscription grounds')
    for x in [-1.10,-.55,0,.55,1.10]:
        f.box(x,6.09,.009,.518,.012,.189,EDGE,'Inscription panel joints')
    add_facade_lettering(f,'所公業錢南滬',0,6.09,3.13,.415,.189,.226,RAISED,label='Carved right to left',font=FONT)
    for side in (-1,1):
        frame(f,2.28*side,6.1,.90,.66,.042,.121,.184,BRICK,'Inset side tablets')
        for j in [-1,0,1]:
            f.box(side*2.26+j*.099,6.08,.060,.159,.040,.165,RELIEF,'Side tablet relief marks')
    f.box(0,7.035,4.25,.235,.075,.187,BACK,'Dark upper relief recess')
    # Small cast shadows in the source resolve a procession of robed silhouettes.
    # Count and poses here represent their visible rhythm, without assigning individual identities.
    for i in range(11):
        x=-1.92+i*.382;z=6.925;s=1 if i%3 else -1
        shape=Polygon([(x+s*u,z+dz) for u,dz in [(-.12,0),(.11,0),(.07,.065),(.084,.146),(.015,.162),(-.062,.11)]])
        f.prism(shape,.222,.244,RELIEF,'Robed brick frieze silhouettes')
        if not lod:
            head=Point(x+.038*s,z+.188).buffer(.048,quad_segs=5)
            f.prism(head,.224,.252,RELIEF,'Small frieze head reliefs')
    f.box(0,5.465,3.84,.20,.053,.195,BACK,'Lower foliage relief recess')
    for i in range(11):
        x=-1.70+i*.34
        pts=[(x+.13*cos(2*pi*k/17),5.47+.064*sin(2*pi*k/17)+.022*cos(2*pi*k/17))for k in range(18)]
        f.prism(Polygon(pts),.222,.248,RELIEF,'Foliage and fruit relief')
    for side in (-1,1):
        f.box(side*2.81,5.15,.091,.26,.093,.155,BRICK,'Carved pendant blocks')


def steps(b,f):
    for i,axis in enumerate(AXES):
        w=2.27 if i==1 else 1.78
        for j in range(3):
            y=-1.22+.285*j;z=.145*(j+1)
            b.plan_prism(box(axis-w/2,y,axis+w/2,.25),0,z,STONE,'Three granite threshold risers')
    for side in (-1,1):
        x=side*1.38
        b.plan_prism(box(x-.132,-1.36,x+.132,.16),.018,.58,LIGHT,'Central stair cheeks')
        # Each flanking stone drum is vertical, with a recessed circular face seen obliquely.
        f2=Facade(b,(x,-.99),(x,-.15),'Granite drum')
        disk=scale(Point(0,.85).buffer(1,quad_segs=14),xfact=.44,yfact=.45,origin=(0,.85))
        f2.prism(disk,-.12,.12,LIGHT,'Circular cheek stone')
        ring=disk.buffer(-.043).difference(disk.buffer(-.095))
        f2.prism(ring,.120,.133,STONE,'Carved circular cheek rim')
        f2.prism(ring,-.133,-.120,STONE,'Carved circular cheek rim')


def gate(b,lod):
    face=Facade(b,(-HALF,0),(HALF,0),'Gucheng Park south gate')
    openings=[doorway(face,x,i==1,lod)for i,x in enumerate(AXES)]
    facade=Polygon([(-HALF,0),(HALF,0),(HALF,4.78),(7.82,4.78),(7.82,6.48),(3.07,6.48),(3.07,7.53),(-3.07,7.53),(-3.07,6.48),(-7.82,6.48),(-7.82,4.78),(-HALF,4.78)])
    wall=facade.difference(unary_union(openings))
    face.prism(wall,-.54,0,PLASTER,'Three bay limewashed front wall')
    base=wall.intersection(box(-HALF,0,HALF,1.025))
    face.prism(base,.001,.028,BASE,'Bluish grey stone dado')
    for x in np.arange(-HALF+.22,HALF,.79):
        seam=base.intersection(box(x-.005,.04,x+.005,.99))
        if not seam.is_empty:face.prism(seam,.029,.033,KEY,'Dado vertical joints')
    for z in [.31,.64,1.015]:
        line=base.intersection(box(-HALF,z-.006,HALF,z+.006))
        if not line.is_empty:face.prism(line,.029,.033,KEY,'Dado horizontal joints')
    for x in (-2.19,2.19):
        face.box(x,2.42,.67,.39,.06,.043,BRICK,'Small rectangular wall plaques')
        frame(face,x,2.42,.71,.43,.047,.043,.092,FRAME,'Raised plaque margins')
    for side in (-1,1):
        x=side*8.65
        frame(face,x,2.62,1.62,1.72,.095,.028,.103,FRAME,'Square mounts for side reliefs')
        oval=scale(Point(x,2.62).buffer(1,quad_segs=12 if lod else 22),xfact=.50,yfact=.71,origin=(x,2.62))
        face.prism(oval.difference(oval.buffer(-.08)),.052,.107,BRICK,'Elongated circular side relief')
        face.box(x,4.77,1.98,.13,.51,-.035,RIDGE,'Low wall coping')
    bands(face,lod);steps(b,face);roofs(b,lod)
