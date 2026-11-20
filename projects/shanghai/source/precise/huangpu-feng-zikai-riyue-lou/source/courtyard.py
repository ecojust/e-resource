"""The numbered entrance, casements and front path of the photographed No. 93 dwelling."""
import math

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade, opening

IVORY='ochre cream roughcast'
TIMBER='brown painted joinery'
GLASS='shaded courtyard glass'
STONE='pale granite steps'
IRON='dark garden ironwork'
TILE='red ochre clay tile'
SILL='painted off-white sill'
GREY='lead-grey flashings'
GREEN='green enamel house number'
LETTER='pale ceramic numerals'
BRONZE='patinated commemorative plaque'
PALETTE={IVORY:{'color':[.76,.72,.59],'roughness':.89},TIMBER:{'color':[.186,.118,.101],'roughness':.69},
 GLASS:{'color':[.20,.266,.26],'roughness':.25,'metallic':.13},STONE:{'color':[.50,.495,.452],'roughness':.82},
 IRON:{'color':[.131,.154,.133],'roughness':.57,'metallic':.30},TILE:{'color':[.483,.256,.169],'roughness':.85},
 SILL:{'color':[.812,.781,.681],'roughness':.82},GREY:{'color':[.431,.454,.443],'roughness':.68},
 GREEN:{'color':[.028,.27,.186],'roughness':.52},LETTER:{'color':[.838,.821,.689],'roughness':.65},
 BRONZE:{'color':[.201,.274,.224],'roughness':.62,'metallic':.16}}


def front(builder, lo, hi, y, label):
    return Facade(builder,(lo,y),(hi,y),label)


def casement(f,shape,columns,rows,label,depth=.07):
    """Glazing and muntins sit within the shallow timber rebates of the house."""
    x0,z0,x1,z1=shape.bounds
    clear=shape.buffer(-.044,join_style=2)
    bars=[]
    for i in range(1,columns):
        x=x0+(x1-x0)*i/columns
        bars.append(box(x-.014,z0,x+.014,z1))
    for i in range(1,rows):
        z=z0+(z1-z0)*i/rows
        bars.append(box(x0,z-.014,x1,z+.014))
    panes=clear.difference(unary_union(bars)) if bars else clear
    f.prism(shape,-depth-.018,-depth,GLASS,label+' glass')
    f.prism(shape.difference(panes),-depth+.008,-depth+.032,TIMBER,label+' frame')

def number_plate(f,lod):
    xpos,zpos=-.64,2.36
    f.box(xpos,zpos,.265,.188,.019,.06,GREEN,'green enamel plate')
    nine=[(.049,.015),(.037,.045),(.010,.059),(-.018,.054),(-.035,.034),
          (-.034,.008),(-.013,-.006),(.011,-.005),(.030,.008),
          (.025,-.025),(.012,-.047),(-.010,-.059)]
    three=[(-.035,.045),(-.010,.060),(.020,.055),(.035,.038),(.033,.019),
           (.016,.004),(-.005,.000),(.022,-.006),(.039,-.023),(.037,-.043),(.019,-.057),(-.014,-.059),(-.035,-.045)]
    for offset,path in ((-.047,nine),(.050,three)):
        points=[f.point(xpos+offset+x*.78,zpos+z*.80,.076) for x,z in path]
        f.builder.tube(points,.0053,LETTER,5 if lod else 8,'Entrance/number 93')
    if not lod:
        # Edge bosses on the green enamel are separate pieces from the digits.
        for u in (-.118,.118):
            f.box(xpos+u,zpos,.012,.012,.005,.071,TIMBER,'plate fixing')


def plaque(f):
    u=-1.10;z=1.96
    outline=Polygon([(u-.205,z-.266),(u+.205,z-.266),(u+.205,z+.17),
                     (u+.156,z+.20),(u+.083,z+.22),(u+.049,z+.251),
                     (u,z+.270),(u-.047,z+.25),(u-.09,z+.22),(u-.155,z+.20),(u-.205,z+.17)])
    f.prism(outline,-.004,.042,SILL,'pale shaped plaque edge')
    f.prism(outline.buffer(-.018,join_style=2),.040,.052,BRONZE,'historic marker face')


def entry(f,lod):
    door=opening(0,.37,1.27,2.34)
    lights=[opening(x,1.66,.414,.575) for x in (-.291,.291)]
    trans=box(-.585,2.30,.585,2.655)
    f.prism(door.difference(unary_union([*lights,trans])),-.226,-.185,TIMBER,'recessed double door')
    for i in (-1,1):
        u=i*.291
        f.box(u,1.015,.546,1.20,.043,-.147,TIMBER,'separate lower leaf')
        f.box(u,1.12,.425,.88,.030,-.109,TIMBER,'raised lower panel')
        casement(f,opening(u,1.66,.414,.575),1,2,'door lights',.16)
        f.box(u,1.95,.425,.027,.024,-.103,TIMBER,'horizontal light bar')
    f.prism(trans,-.154,-.134,GLASS,'transom glass')
    for sign in (-1,1):
        for x in np.arange(-1.18,1.17,.40):
            path=LineString([(x,2.289),(x+sign*.43,2.663)]).intersection(trans)
            if not path.is_empty and path.length>.015:
                f.prism(path.buffer(.016,cap_style=2),-.109,-.078,TIMBER,'diagonal transom lattice')
    for x in (-.616,.616):
        f.box(x,1.55,.073,2.39,.13,-.031,TIMBER,'entrance jamb')
    for z in (2.266,2.690):
        f.box(0,z,1.32,.081,.13,-.033,TIMBER,'transom rail')
    f.box(0,1.28,.042,1.78,.06,-.08,TIMBER,'central meeting stile')
    f.box(-.086,1.29,.064,.12,.035,-.069,BRONZE,'old latch')
    number_plate(f,lod);plaque(f)
    return door


def garden(builder,lod):
    # The later autumn photograph documents open double gates and curved iron brackets.
    # Keep the centre of the path and the approach to the actual stairs open.
    for s in (-1,1):
        x=s*1.18
        builder.box((x,-2.18,.97),(.085,.09,1.94),IRON,label='Garden/gatepost')
        for j in range(7):
            builder.box((x+s*(j+.58)*.20,-2.18,.63),(.022,.033,1.24),IRON,label='Garden/fixed railing')
        for z in (.23,1.09):
            builder.box((s*1.91,-2.18,z),(1.52,.041,.037),IRON,label='Garden/railing rail')
        # Gate leaf stands open, almost perpendicular to the path.
        leaf=Facade(builder,(x,-2.17),(x+s*.16,-1.13),'Garden/open gate')
        for z in (.12,1.26):
            leaf.box(0,z,1.05,.035,.045,0,IRON,'frame rail')
        for i in range(7):
            leaf.box((i-3)*.161,.73,.024,1.17,.036,0,IRON,'picket')
        arc=[(x+s*.55*t,-2.18,1.91-.12*math.sin(math.pi*t))for t in np.linspace(0,1,6 if lod else 14)]
        builder.tube(arc,.019,IRON,5 if lod else 8,'Garden/curved lintel')
        scroll=[(x+s*(.29+.092*math.cos(t)),-2.18,1.76+.082*math.sin(t))for t in np.linspace(.25,math.tau*1.17,10 if lod else 23)]
        builder.tube(scroll,.013,IRON,5 if lod else 8,'Garden/lintel scroll')
    for i in range(3):
        depth=.25*(3-i)
        builder.box((0,-depth/2-.06,.06*(i+1)),(1.63,depth,.12*(i+1)),STONE,label='Entrance/three shallow steps')
    # Slender rail on the right of the stair is visible in the numbered doorway photograph.
    builder.tube([(.85,-.81,.69),(.85,-.47,.82),(.85,-.10,.98)],.024,IRON,6 if lod else 10,'Entrance/stair handrail')
