"""The five eastern bays facing the Bund, measured laterally from the frozen parcel."""
from math import cos, pi, sin
from pathlib import Path
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from sign_lettering import add_facade_lettering
from ornament import STONE, TRIM, DARK, balcony, ellipse, ionic, plate, ribbon, shell, spiral, swag

HALF = 10.965
BAYS = (-8.77, -4.56, 0, 4.56, 8.77)
FONT = Path(__file__).with_name('fonts') / 'BundBankLetters.otf'
GLASS = 'green-grey glazing'
SASH = 'dark window joinery'
PALETTE = {
    STONE:{'color':[.53,.49,.42],'roughness':.84},
    TRIM:{'color':[.64,.59,.50],'roughness':.77},
    DARK:{'color':[.40,.36,.30],'roughness':.87},
    GLASS:{'color':[.14,.20,.19],'metallic':.12,'roughness':.28},
    SASH:{'color':[.14,.14,.12],'metallic':.18,'roughness':.57},
    'portal oak':{'color':[.13,.095,.071],'roughness':.60},
    'modern white lettering':{'color':[.84,.82,.74],'roughness':.55},
    'section':{'color':[.42,.40,.36],'roughness':.91},
}


def glazing(f, cut, cols, rows, lod, label):
    f.prism(cut.buffer(.009,join_style=2),-.425,-.402,GLASS,label+' glass')
    x0,z0,x1,z1=cut.bounds
    divisions=[]
    for i in range(1,cols):
        x=x0+(x1-x0)*i/cols
        divisions.append(box(x-.034,z0,x+.034,z1))
    for j in range(1,rows if not lod else min(2,rows)):
        z=z0+(z1-z0)*j/(rows if not lod else min(2,rows))
        divisions.append(box(x0,z-.032,x1,z+.032))
    ins=cut.buffer(-.078,join_style=2).difference(unary_union(divisions))
    f.prism(cut.buffer(-.016,join_style=2).difference(ins),-.38,-.264,SASH,label+' sash')
    plate(f,(x0+x1)/2,z0-.065,x1-x0+.24,.13,-.025,.25,TRIM,label+' sill')


def ring(f,x,spring,rx,rz,thickness,lod,name):
    steps=18 if lod else 36
    segments=9 if lod else 13
    for j in range(segments):
        start=pi*(j+.025)/segments
        end=pi*(j+.975)/segments
        angles=[start+(end-start)*i/steps for i in range(max(3,steps//segments)+1)]
        # Resolve each wedge independently to leave a narrow recessed mortar joint.
        angles=[start+(end-start)*i/(len(angles)-1) for i in range(len(angles))]
        outside=[(x+(rx+thickness)*cos(a),spring+(rz+thickness)*sin(a))for a in angles]
        inside=[(x+rx*cos(a),spring+rz*sin(a))for a in reversed(angles)]
        f.prism(Polygon(outside+inside),-.028,.18 if j!=segments//2 else .24,
                TRIM if j==segments//2 else STONE,name+' voussoirs')


def courses(f,wall,low,high,lo,hi,lod,label):
    rows=max(1,round((high-low)/.52))
    count=max(1,round((hi-lo)/1.7))
    dx=(hi-lo)/count
    for k in range(rows):
        z=low+(high-low)*k/rows;zt=low+(high-low)*(k+1)/rows
        for j in range(-1,count):
            x=lo+dx*(j+.5*(k%2))
            clip=box(max(lo,x+.014),z+.021,min(hi,x+dx-.014),zt-.020) if x+dx>lo and x<hi else None
            if clip is None: continue
            piece=wall.intersection(clip)
            if piece.area>.009:
                f.prism(piece,.003,.045 if lod else .068,STONE,label)


def portal(f,holes,lod):
    opening_c=opening(0,.10,2.20,4.03)
    holes.append(opening_c)
    f.prism(opening_c.buffer(.012,join_style=2),-1.15,-1.12,'portal oak','deep double entrance doors')
    f.prism(opening_c.buffer(-.024,join_style=2).difference(opening_c.buffer(-.15,join_style=2)),-1.115,-1.04,SASH,'door lining')
    plate(f,0,2.09,.066,3.91,-1.125,-1.065,SASH,'door meeting stile')
    for side in [-1,1]:
        for z in [1.06,2.74]:
            pane=box(side*.52-.37,z-.51,side*.52+.37,z+.51)
            f.prism(pane.difference(pane.buffer(-.045,join_style=2)),-1.118,-1.066,SASH,'raised door panels')
        ionic(f,side*1.28,.09,4.53,.19,.24,lod,'portal columns',False)
        plate(f,side*1.32,4.61,.66,.22,-.04,.53,TRIM,'portal impost')
    plate(f,0,4.86,3.21,.45,-.03,.48,TRIM,'portal lintel')
    plate(f,0,5.10,3.43,.15,-.01,.57,TRIM,'portal projecting lintel')
    # The paired broken scrolls lift away from the horizontal lintel towards the center.
    for s in [-1,1]:
        xs=[1.73,1.69,1.48,1.18,.90,.68,.52,.43]
        zs=[5.16,5.48,5.87,6.17,6.40,6.52,6.50,6.40]
        pts=[(s*x,z) for x,z in zip(xs,zs)]
        ribbon(f,pts,.17,.06,.49,STONE,'arched broken pediment')
        ribbon(f,[(x,z+.12)for x,z in pts],.071,.47,.60,TRIM,'broken pediment moulding')
        ellipse(f,s*.61,5.71,.30,.32,.15,.32,DARK,'portal volute field',12 if lod else 22)
        spiral(f,s*.61,5.71,.28,s,.31,.47,'portal scroll ornament',lod)
    crest=Polygon([(-.20,5.28),(.20,5.28),(.25,5.48),(.13,5.77),(.26,5.93),
                   (.09,6.05),(.03,6.34),(-.12,6.11),(-.25,5.96),(-.14,5.73),(-.24,5.49)])
    f.prism(crest,.12,.39,TRIM,'portal central upright crest')
    plate(f,0,5.45,.61,.12,.12,.44,STONE,'portal crest pedestal')


def upper_bay(f,holes,x,j,lod):
    outer=j in (0,4)
    middle=j==2
    width=1.43 if outer else 2.48 if middle else 2.56
    glazing_shape=opening(x,9.32,width,3.61)
    holes.append(glazing_shape)
    glazing(f,glazing_shape,2 if not middle else 3,3,lod,'principal tall window')
    for side in [-1,1]:
        ionic(f,x+side*(width*.5+.19),9.12,13.13,.135,.14,lod,'window colonnettes',False)
    head_width=width+.50
    tym=opening(x,13.12,head_width,.04+head_width*.45,head_width*.45,12 if lod else 27)
    f.prism(tym,-.012,.042,DARK,'blind semicircular tympanum')
    shell(f,x,13.15,head_width/2,head_width*.45,.043,lod,'carved window head')
    ring(f,x,13.16,head_width/2,head_width*.45,.16,lod,'upper archivolt')
    plate(f,x,13.10,head_width+.20,.16,.0,.30,TRIM,'window arch spring')
    balcony(f,x,width+.41,8.92,.85,.28,lod,'window balustrade')
    top_count=1 if outer else 3 if middle else 2
    pitch=1.00 if middle else 1.28
    for i in range(top_count):
        u=x+(i-(top_count-1)/2)*pitch
        width=.78 if middle else .93 if not outer else 1.27
        cut=opening(u,15.00,width,2.58)
        holes.append(cut); glazing(f,cut,1 if width<1 else 2,2,lod,'upper rectangular window')
        f.prism(cut.buffer(.115,join_style=2).difference(cut),-.02,.11,TRIM,'upper window lining')


def add_riverfront(b,lod):
    f=Facade(b,(-HALF,0),(HALF,0),'Bund riverfront')
    holes=[]
    portal(f,holes,lod)
    for j,x in enumerate(BAYS):
        if j!=2:
            cut=opening(x,1.35,2.02,5.05,1.01,18 if lod else 36)
            holes.append(cut);glazing(f,cut,2,4,lod,'ground arched light')
            ring(f,x,5.39,1.01,1.01,.42,lod,'ground round arch')
            key=Polygon([(x-.19,6.37),(x+.19,6.37),(x+.30,7.30),(x-.30,7.30)])
            f.prism(key,.09,.29,TRIM,'ground arch keystone')
        upper_bay(f,holes,x,j,lod)
    wall=f.wall(0,19.26,holes,1.41,STONE)
    courses(f,wall,0,8.18,-HALF,HALF,lod,'ground rusticated ashlar')
    for x in [-10.37,-7.20,7.20,10.37]:
        courses(f,wall,8.27,18.20,x-.52,x+.52,lod,'coursed upper pilasters')
        plate(f,x,17.77,.99,.60,.06,.28,TRIM,'pilaster capital block')
        for sign in [-1,1]:
            spiral(f,x+sign*.20,17.82,.15,sign,.28,.34,'pilaster carved capital',lod)
        plate(f,x,18.13,1.13,.20,.02,.38,TRIM,'pilaster abacus')
    for side in [-1,1]:
        # Giant smooth Ionic columns separate the middle three bays.
        x=side*2.49
        plate(f,x,8.62,1.24,.72,-.05,.61,TRIM,'giant column high plinth')
        ionic(f,x,8.96,18.09,.455,.41,lod,'giant Ionic columns')
    for z,h,d in [(7.69,.15,.18),(8.12,.30,.32),(8.35,.14,.43),
                  (17.99,.19,.36),(18.27,.25,.43),(19.18,.16,.41),
                  (19.52,.22,.54),(19.74,.16,.62)]:
        plate(f,0,z,2*HALF,h,-.12,d,TRIM,'continuous entablature and courses')
    for side in [-1,1]:
        plate(f,side*(HALF+1.10)/2,.25,HALF-1.10,.50,-.12,.17,TRIM,'ground plinth')
    plate(f,0,18.78,2*HALF,.81,-.04,.20,STONE,'frieze field')
    for k in range(31 if lod else 48):
        n=31 if lod else 48
        x=(k+.5)*2*HALF/n-HALF
        plate(f,x,19.37,.19 if lod else .14,.22,.17,.45,TRIM,'cornice dentils')
    add_facade_lettering(f,'中国光大银行',.68,18.79,5.32,.57,.21,.258,
                        'modern white lettering',label='current bank name',font=FONT)
    for side in [-1,1]:
        x=side*8.66; w=4.60
        plate(f,x,20.48,w,1.36,-.56,.12,STONE,'attic decorated end wall')
        plate(f,x,21.20,w+.01,.19,-.53,.20,TRIM,'attic cornice')
        plate(f,x+side*.33,21.46,w-.67,.28,-.46,.17,STONE,'raised attic outer shoulder')
        plate(f,x+side*.33,21.55,w-.65,.10,-.48,.21,TRIM,'attic coping')
        swag(f,x,20.74,w,lod)
    for x in [-2.5,2.5]:
        plate(f,x,20.25,.70,1.04,-.48,.16,STONE,'attic rail intermediate piers')
        plate(f,x,20.80,.81,.13,-.53,.23,TRIM,'attic piers caps')
    for lo,hi in [(-6.36,-2.82),(-2.18,2.18),(2.82,6.36)]:
        balcony(f,(lo+hi)/2,hi-lo,19.80,.81,-.08,lod,'perforated parapet')
    # Short returns and a single neutral section plane terminate the study before the deep office block.
    for side in [-1,1]:
        b.box((side*(HALF-.14),1.49,9.87),(.28,1.10,19.74),'section',label='Bounded section/end return')
    b.box((0,1.96,9.87),(2*HALF,.16,19.74),'section',label='Bounded section/rear cut face')
    b.box((0,1.15,19.71),(2*HALF,1.78,.10),'section',label='Bounded section/short roof cap')
