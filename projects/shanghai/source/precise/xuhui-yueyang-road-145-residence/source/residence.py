"""The South Garden elevation of No. 145 from the published 2021 and 2023 views."""
import math
from shapely.geometry import Polygon, box
from photo_architecture import Facade
from roof import painted_roof, FOLDS, GABLES, TILE, LIGHT_TILE, DARK_TILE, EDGE

WALL='warm white stucco'
STONE='buff painted band'
TERRACE='aged terrace paving'
GLASS='green grey garden glazing'
FRAME='painted window frames'
WOOD='varnished door leaves'
GREEN='green canvas sunshade'
RAIL='grey tubular railing'
DARK='shadowed smoke outlet'
PALETTE={name:{'color':rgb,'roughness':rough}for name,rgb,rough in [
    (WALL,[.80,.775,.68],.90),(STONE,[.65,.54,.355],.80),
    (TERRACE,[.39,.319,.254],.86),(GLASS,[.19,.237,.214],.29),(FRAME,[.25,.24,.201],.63),
    (WOOD,[.39,.255,.145],.70),(GREEN,[.258,.429,.325],.91),(RAIL,[.48,.503,.47],.51),
    (DARK,[.121,.117,.105],.92),(TILE,[.505,.201,.129],.88),(LIGHT_TILE,[.57,.237,.159],.9),
    (DARK_TILE,[.475,.188,.128],.9),(EDGE,[.375,.192,.138],.81)]}

def front(builder,x0,x1,y,label):
    return Facade(builder,(x0,y),(x1,y),label)

def opening(cx,z,w,h):return box(cx-w/2,z,cx+w/2,z+h)

def window(f,cx,z,w,h,cols=3,rows=2,door=False):
    edge=WOOD if door else FRAME
    f.box(cx,z+h/2,w,h,.075,-.23,GLASS,'glass behind reveal')
    f.box(cx,z+.045,w+.13,.09,.20,-.08,STONE,'projecting sill')
    for i in range(cols+1):
        u=cx-w/2+w*i/cols;f.box(u,z+h/2,.055 if i in (0,cols) else .045,h,.09,-.15,edge,'casement and door jamb')
    lines=[z+.035]+([z+h*.72]if rows>1 else[])+[z+h-.035]
    for z0 in lines:f.box(cx,z0,w,.058,.09,-.15,edge,'window and door transom')

def block(builder,cx,cy,cz,sx,sy,sz,m,label):builder.box((cx,cy,cz),(sx,sy,sz),m,label=label)

def sides(builder,x0,x1,y0,y1,z0,z1,label):
    for start,end in [((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))]:
        Facade(builder,start,end,label).wall(z0,z1,material=WALL,thickness=.18)

def canvas(builder,c,y,z,w,depth,lod):
    z0=z-.34;front_y=y-depth
    vertices=[(c-w/2,y,z),(c+w/2,y,z),(c+w/2,front_y,z0),(c-w/2,front_y,z0),
              (c-w/2,front_y,z0-.12),(c+w/2,front_y,z0-.12)]
    builder.add(vertices,[(0,3,2,1),(3,4,5,2),(0,4,3),(2,5,1)],GREEN,'projecting canvas awning')
    count=math.ceil(w/(.29 if lod else .20));span=w/count
    for i in range(count):
        x=c-w/2+(i+.5)*span
        pts=[(x-span/2,z0-.10),(x+span/2,z0-.10),(x+span*.49,z0-.16),(x+span*.25,z0-.22),
             (x-span*.25,z0-.22),(x-span*.49,z0-.16)]
        builder.prism(Polygon(pts),0,.026,lambda u,v,d:(u,front_y-d,v),GREEN,'scalloped canvas valance')

def chimney(builder,x,y,base,top,width,depth):
    block(builder,x,y,(top+base)/2,width,depth,top-base,WALL,'painted chimney stack')
    block(builder,x,y,top-.12,width+.10,depth+.10,.14,STONE,'chimney cap ledge')
    count=max(1,round(width/.34)); space=(width-.10)/count
    for i in range(count):
        block(builder,x-width/2+.05+(i+.5)*space,y,top+.006,space*.62,depth*.53,.012,DARK,'dark flue opening')

def add_residence(builder,lod):
    # The fully glazed later lower facade projects in front of the upper rooms.
    ground=front(builder,-8.41,8.88,.05,'garden winter garden')
    groups=[(-6.66,2.74),(-3.33,2.82),(0,2.84),(3.32,2.82),(6.67,2.82)]
    holes=[opening(c,.92 if c else .46,w,3.38 if c else 3.84)for c,w in groups]
    ground.wall(0,4.63,holes,thickness=.22,material=WALL)
    for c,w in groups:
        window(ground,c,.92 if c else .46,w,3.38 if c else 3.84,cols=3,door=c==0)
    for left,right in [(-8.40,-1.47),(1.47,8.87)]:
        ground.box((left+right)/2,.52,right-left,.68,.14,.015,STONE,'garden masonry plinth')
    for i in range(3):
        height=(i+1)*.15
        block(builder,0,-.72+i*.26,height/2,3.12,.30,height,STONE,'three garden approach steps')
    sides(builder,-8.41,8.88,.05,3.60,0,4.65,'terrace side walls')
    builder.plan_prism(box(-8.55,-.09,9.02,3.68),4.61,4.82,TERRACE,'garden terrace slab')
    # Contemporary metal terrace front, three horizontal rails in col2/467.
    for a,b in [((-8.49,-.07),(8.96,-.07)),((-8.49,-.07),(-8.49,2.96)),((8.96,-.07),(8.96,2.96))]:
        x0,y0=a;x1,y1=b
        segments=math.ceil(math.hypot(x1-x0,y1-y0)/1.7)
        for j in range(segments+1):
            x=x0+(x1-x0)*j/segments;y=y0+(y1-y0)*j/segments
            builder.tube([(x,y,4.82),(x,y,5.83)],.035,RAIL,6,'terrace posts')
        for z in [5.14,5.46,5.83]:
            builder.tube([(x0,y0,z),(x1,y1,z)],.028 if z<5.8 else .043,RAIL,6 if lod else 10,'horizontal terrace railing')
    # Rear exterior enclosure is a neutral mass beneath the photographed roof.
    # It has no speculative rear window rows or attached garden service block.
    sides(builder,-10.36,10.37,3.72,12.00,0,8.42,'main side and rear enclosing walls')
    mid=front(builder,-10.36,10.37,3.72,'recessed central terrace doorway')
    door=opening(0,4.82,3.12,2.54)
    mid.wall(0,8.42,[door],thickness=.21,material=WALL)
    window(mid,0,4.82,3.12,2.54,4,2,door=True)
    for center in GABLES:
        facade=front(builder,center-3.20,center+3.20,1.63,'forward roof gable')
        profile=[(-3.20,4.82),(3.20,4.82)]+[(3.20-t,z)for t,z in FOLDS]+[(-3.20+t,z)for t,z in reversed(FOLDS)]
        outline=Polygon(profile)
        holes=[opening(0,5.83,2.70,1.64),opening(0,9.04,3.04,1.75)]
        facade.wall(4.82,11.64,holes,thickness=.24,material=WALL,outline=outline)
        for z,w,h,depth in [(5.83,2.70,1.64,.74),(9.04,3.04,1.75,.55)]:
            window(facade,0,z,w,h,4,2)
            canvas(builder,center,1.63,z+h+.17,w+.20,depth,lod)
        facade.box(0,8.31,6.11,.19,.14,.028,STONE,'ochre belt below roof')
        for sign in [-1,1]:
            points=[(center+sign*(3.20-t),1.55,z)for t,z in FOLDS]
            builder.tube(points,.086,EDGE,8,'upturned gable edge')
            facade.box(sign*3.00,6.56,.37,3.48,.10,.02,STONE,'ochre wall quoin')
        sides(builder,center-3.20,center+3.20,1.63,3.74,4.82,8.4,'projecting gable returns')
    for end in [-10.27,10.28]:
        block(builder,end,3.705,4.17,.19,.09,8.32,STONE,'painted corner band of main wall')
    for end in [-8.31,8.77]:
        block(builder,end,.032,2.31,.21,.10,4.62,STONE,'garden room corner band')
    painted_roof(builder,lod)
    # Roof dormer cuts forward of the center skirt. The white pediment and its small casement are both visible.
    dorm=front(builder,-.83,.83,3.83,'center roof dormer')
    outline=Polygon([(-.80,9.12),(.80,9.12),(.80,10.52),(0,11.12),(-.80,10.52)])
    dorm.wall(9.12,11.12,[opening(0,9.33,1.03,1.09)],material=WALL,outline=outline,thickness=.16)
    window(dorm,0,9.33,1.03,1.09,2,1)
    for sign in [-1,1]:
        builder.add([(0,3.63,11.18),(sign*.91,3.63,10.52),(sign*.91,4.95,10.52),(0,4.95,11.18)],[(0,1,2,3)if sign>0 else(3,2,1,0)],TILE,'dormer pitched roof')
        builder.tube([(0,3.64,11.15),(sign*.92,3.64,10.50)],.065,STONE,8,'dormer pediment moulding')
    for item in [(-7.72,5.10,9.15,13.44,.49,.52),(9.15,6.04,9.8,13.42,.53,.55),
                 (-3.70,10.50,11.80,14.07,.53,.54),(0,9.85,12.05,14.50,1.06,.58),
                 (5.61,9.67,11.94,13.72,.49,.50)]:
        chimney(builder,*item)
