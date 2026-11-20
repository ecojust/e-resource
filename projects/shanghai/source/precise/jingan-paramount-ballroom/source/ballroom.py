"""The east-facing rounded entrance and the two street wings of the Paramount."""
import math
from pathlib import Path
import sys

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

COMMON=Path(__file__).resolve().parents[2]/'hongkou-general-post-office/source/common'
sys.path.insert(0,str(COMMON))
from photo_architecture import Facade,opening

STONE='grey cement facing'; METAL='bronzed street trim'; GLASS='street glazing'; FRAME='sash metal'
SIGN='red enamel';IVORY='ivory enamel';LAMP='opal tower glass'; GOLD='aged gold tower'; ROOF='flat roof'; BLUE='blue grey hall roof'
PALETTE={STONE:{'color':[.416,.415,.373],'roughness':.77},METAL:{'color':[.303,.266,.205],'metallic':.38,'roughness':.48},
         GLASS:{'color':[.173,.226,.238],'roughness':.29,'metallic':.21},FRAME:{'color':[.155,.162,.151],'roughness':.56,'metallic':.38},
         SIGN:{'color':[.493,.079,.062],'roughness':.49}, IVORY:{'color':[.81,.755,.62],'roughness':.51},
         LAMP:{'color':[.88,.84,.69],'metallic':.07,'roughness':.31},GOLD:{'color':[.51,.391,.22],'roughness':.49,'metallic':.37},
         ROOF:{'color':[.30,.301,.284],'roughness':.83},BLUE:{'color':[.162,.216,.282],'roughness':.70},
         'darker cement joint':{'color':[.295,.292,.271],'roughness':.84},'entrance floor':{'color':[.33,.309,.275],'roughness':.76}}
RADIUS=15.15
ANGLES=(-52.1,-40,-29,-17,-6,6,17,29,40,52.1)

def curve(degrees,radius=RADIUS):
    a=math.radians(degrees)
    return (.20+radius*math.sin(a),15.27-radius*math.cos(a))

ARC=[curve(a)for a in ANGLES]
SOUTH=(-31.83,43.33); SOUTH_END=(-21.95,51.12); INNER=(-5.63,21.61); NORTH_END=(13.83,48.03); NORTH=(32.76,35.10)
FOOTPRINT=[SOUTH,*ARC,NORTH,NORTH_END,INNER,SOUTH_END]

def panel(f,u,z,w,h,back,front,material,name):
    f.box(u,z,w,h,front-back,(back+front)/2,material,name)

def window(f,u,z,w,h,lod,label,tall=False,door=False):
    q=opening(u,z,w,h);depth=1.37 if door else .34
    f.prism(q.buffer(.012,join_style=2),-depth-.03,-depth,GLASS,label+' recessed glazing')
    inset=q.buffer(-.056,join_style=2)
    cross=[box(u-w/2,z+h*.66-.026,u+w/2,z+h*.66+.026)]
    if door or not lod:cross.append(box(u-.026,z,u+.026,z+h))
    if tall:
        for y in [.27,.46,.84]:cross.append(box(u-w/2,z+h*y-.025,u+w/2,z+h*y+.025))
    grid=q.buffer(-.009,join_style=2).difference(inset.difference(unary_union(cross)))
    f.prism(grid,-depth+.022,-depth+.115,METAL if door else FRAME,label+' metal divisions')
    if door:
        for side in [-1,1]:
            panel(f,u+side*(w/2+.021),z+h/2,.049,h,-1.45,-.27,STONE,'inset entry jamb')
            panel(f,u+side*.13,z+1.25,.034,.27,-1.23,-1.14,METAL,'paired entry pulls')
        panel(f,u,z+h+.012,w+.05,.075,-1.44,-.27,STONE,'inset entry soffit')
        panel(f,u,.072,w+.17,.14,-1.47,.12,'entrance floor','entry threshold')
    elif not lod:
        panel(f,u,z-.047,w+.13,.09,-.028,.088,METAL,label+' shallow sill')
    return q

# Simple raised geometric strokes match the vertical block lettering on the
# two façade-mounted signs. Coordinates are authored for this sign only.
LETTERS={
 'P':[[(-.42,0),(-.42,1),(.16,1),(.42,.82),(.42,.62),(.16,.49),(-.42,.49)]],
 'A':[[(-.47,0),(0,1),(.47,0)],[(-.27,.39),(.27,.39)]],
 'R':[[(-.42,0),(-.42,1),(.16,1),(.42,.81),(.42,.64),(.16,.49),(-.42,.49)],[(.02,.49),(.45,0)]],
 'M':[[(-.45,0),(-.45,1),(0,.48),(.45,1),(.45,0)]],
 'O':[[(-.27,.02),(-.44,.23),(-.44,.78),(-.26,.98),(.25,.98),(.44,.78),(.44,.21),(.25,.02),(-.27,.02)]],
 'U':[[(-.43,1),(-.43,.23),(-.27,.04),(.24,.04),(.43,.23),(.43,1)]],
 'N':[[(-.43,0),(-.43,1),(.43,0),(.43,1)]], 'T':[[(-.49,.97),(.49,.97)],[(0,.97),(0,0)]]}

def vertical_sign(f,lod):
    panel(f,0,13.61,.86,7.72,-.06,.19,METAL,'projecting vertical sign frame')
    panel(f,0,13.61,.74,7.58,.18,.221,IVORY,'ivory vertical sign')
    for n,letter in enumerate('PARAMOUNT'):
        bottom=16.71-n*.765
        for stroke in LETTERS[letter]:
            pts=[f.point(x*.54,bottom+z*.623,.261)for x,z in stroke]
            f.builder.tube(pts,.038 if lod else .041,SIGN,5 if lod else 8,f.label+'/PARAMOUNT red letters')

def courses(f,surface,lod,low,high):
    if lod:return
    for z in [q*.81 for q in range(1,23)if low+.16<q*.81<high-.11]:
        strip=surface.intersection(box(-f.length/2,z-.012,f.length/2,z+.012))
        if strip.area>.015:f.prism(strip,.001,.009,'darker cement joint','horizontal facing joints')

def curved_facade(f,i,lod):
    centre=i in [3,4,5]; signed=i in [2,6];edge=i in [0,8]
    top=18.24 if centre else 17.94 if signed else 17.43 if not edge else 16.96
    holes=[]
    if centre:
        holes.append(window(f,0,.13,min(2.19,f.length-.58),2.86,lod,'three front openings',door=True))
        width=.81 if i==4 else .70
        for u in [-.55,.55]:
            holes.append(window(f,u,4.20,width,9.57,lod,'tall central window',tall=True))
            panel(f,u,14.75,width+.15,.13,-.02,.11,METAL,'upper panel trim')
        panel(f,0,15.92,f.length-.11,3.00,-.02,.065,FRAME,'stepped central dark facing')
        # A sectional curved canopy follows the rounded shopfront line.
        lo,hi=ANGLES[i],ANGLES[i+1];roof=Polygon([curve(lo),curve(hi),curve(hi,RADIUS+1.44),curve(lo,RADIUS+1.44)])
        f.builder.plan_prism(roof,3.03,3.27,METAL,'curved entrance canopy')
        for j in range(3):panel(f,(j-1)*f.length/3,3.03,f.length/3-.09,.049,.13,1.24,LAMP,'canopy underside panels')
        panel(f,0,3.64,f.length+.015,.20,-.04,.15,METAL,'entrance sign frieze')
    else:
        holes.append(window(f,0,.52,min(1.73,f.length-.64),2.55,lod,'street showcase'))
        for z in [4.28,8.21,12.25]:
            if signed and z>9:continue
            holes.append(window(f,0,z,.82 if edge else .91,1.93,lod,'vertical side light'))
    body=box(-f.length/2,0,f.length/2,top).difference(unary_union(holes))
    f.prism(body,-.38,0,STONE,'curved cement facade');courses(f,body,lod,0,top)
    for sign in [-1,1]:
        side=sign*(f.length/2-.11)
        panel(f,side,(3.73+top)/2,.19,top-3.73,-.03,.148,METAL if centre else STONE,'projecting facade rib')
        if not centre:panel(f,side,top-.61,.125,.80,.12,.17,LAMP,'parapet light slit')
    panel(f,0,top-.18,f.length+.014,.20,-.025,.12,STONE,'parapet coping')
    if signed:vertical_sign(f,lod)
    return top

def street_wing(f,levels,windows,lod,bright):
    heights=[3.74,7.55,11.46];holes=[];spacing=f.length/windows
    for j in range(windows):
        u=(j-(windows-1)/2)*spacing
        holes.append(window(f,u,.53,min(2.03,spacing-.76),2.41,lod,'street-level opening'))
        for z in heights[:levels]:holes.append(window(f,u,z,1.12,1.82,lod,'upper street window'))
        if not lod and j<windows-1:panel(f,u+spacing/2,7.8,.17,10.88,-.02,.09,STONE,'vertical facing strip')
    h=14.77 if levels==3 else 11.14
    body=box(-f.length/2,0,f.length/2,h).difference(unary_union(holes));f.prism(body,-.38,0,STONE,'perforated street wing')
    courses(f,body,lod,0,h)
    for z,thick in [(3.29,.19),(h-1.05,.13),(h-.12,.24)]:panel(f,0,z,f.length+.015,thick,-.035,.145,STONE,'continuous facade course')
    if bright:
        for j in range(windows):panel(f,(j-(windows-1)/2)*spacing,h-.54,.24,.65,.016,.084,LAMP,'roofline light slits')
    return h

def split_edge(a,b,s):return (a[0]+(b[0]-a[0])*s,a[1]+(b[1]-a[1])*s)

def band_shell(b,ring,top,label,skip=()):
    quad=Polygon(ring);b.plan_prism(quad,top-.19,top,ROOF,label+'/flat roof')
    for i,(a,c) in enumerate(zip(ring,ring[1:]+ring[:1])):
        if i not in skip:Facade(b,a,c,label+' '+str(i)).wall(.02,top,material=STONE,thickness=.24)

def hall_roof(b,lod):
    # The large continuous covered roof belongs to the broad north wing in
    # all three imagery releases. Its shallow pitch and colour are estimates.
    outer=split_edge(ARC[-1],NORTH,.25);outer_w=split_edge(ARC[-1],NORTH,.955)
    inner=split_edge(INNER,NORTH_END,.12);inner_w=split_edge(INNER,NORTH_END,.954)
    corners=[outer,outer_w,inner_w,inner];centre=split_edge(outer,inner,.49);back=split_edge(outer_w,inner_w,.49)
    eave=14.72;ridge=15.70
    vertices=[(*a,eave)for a in corners]+[(*centre,ridge),(*back,ridge)]
    b.add(vertices,[(0,1,5,4),(4,5,2,3),(0,4,3),(1,2,5)],BLUE,'north hall/shallow roof')
    for y in range(1,7 if lod else 17):
        n=y/(7 if lod else 17);pa=split_edge(outer,outer_w,n);pb=split_edge(inner,inner_w,n);pm=split_edge(centre,back,n)
        b.tube([(*pa,eave+.018),(*pm,ridge+.018),(*pb,eave+.018)],.030,FRAME,5,'north hall/roof seams')

def tower(b,lod):
    cx,cy=.16,5.56;seg=36 if lod else 64
    tiers=[(4.52,17.63,20.01,GOLD,32),(3.36,20.00,22.73,GOLD,26),(2.03,22.70,29.63,LAMP,22),(1.28,29.61,32.90,LAMP,16)]
    for i,(rad,lo,hi,material,divisions) in enumerate(tiers):
        label='illuminated tower/tier '+str(i+1)
        b.lathe([cx,cy],[(lo,rad-.045),(lo+.075,rad),(hi-.09,rad),(hi,rad-.075)],material,seg,label)
        for z in [lo+.075,hi-.14]:b.lathe([cx,cy],[(z,rad+.02),(z+.066,rad+.02)],METAL,seg,label+' band')
        for j in range(divisions):
            a=math.tau*j/divisions;x=cx+(rad+.008)*math.cos(a);y=cy+(rad+.008)*math.sin(a)
            b.tube([(x,y,lo+.09),(x,y,hi-.083)],.027 if i>=2 else .044,METAL if i<2 else FRAME,5 if lod else 7,label+' upright')
        if i>=2:
            for j in range(1,4 if i==2 else 3):
                z=lo+(hi-lo)*j/(4 if i==2 else 3);b.lathe([cx,cy],[(z-.021,rad+.014),(z+.021,rad+.014)],FRAME,seg,label+' glass division')
    b.lathe([cx,cy],[(32.90,.19),(33.46,.11),(35.24,.035)],METAL,12 if lod else 20,'illuminated tower/slender mast')

def add_ballroom(b,lod):
    for i,(a,c)in enumerate(zip(ARC,ARC[1:])):curved_facade(Facade(b,a,c,'rounded corner '+str(i)),i,lod)
    south_step=split_edge(SOUTH,ARC[0],.49);north_step=split_edge(ARC[-1],NORTH,.59)
    street_wing(Facade(b,SOUTH,south_step,'Yuyuan Road rear wing'),2,4,lod,False)
    street_wing(Facade(b,south_step,ARC[0],'Yuyuan Road upper wing'),3,4,lod,False)
    street_wing(Facade(b,ARC[-1],north_step,'Wanhangdu Road upper wing'),3,5,lod,True)
    street_wing(Facade(b,north_step,NORTH,'Wanhangdu Road hall'),3,3,lod,True)
    back_step=split_edge(SOUTH_END,INNER,.50);axis=(0,15.36)
    band_shell(b,[SOUTH,south_step,back_step,SOUTH_END],11.12,'south lower wing',{0})
    band_shell(b,[south_step,ARC[0],axis,INNER,back_step],14.74,'south higher wing',{0})
    band_shell(b,[ARC[-1],north_step,NORTH,NORTH_END,INNER,axis],14.74,'north hall',{0,1})
    # Terraced roof planes between the angular window bays. The front rim
    # stays curved and the wall at each step closes in the actual radial plane.
    level=[16.96,17.43,17.94,18.24,18.24,18.24,17.94,17.43,16.96]
    for i,(a,c)in enumerate(zip(ARC,ARC[1:])):
        b.plan_prism(Polygon([a,c,axis]),level[i]-.18,level[i],ROOF,'rounded corner/stepped crown base')
        for x,other in [(a,level[i-1] if i else 14.74),(c,level[i+1] if i+1<len(level) else 14.74)]:
            if level[i]>other:Facade(b,x,axis,'rounded corner/radial parapet').wall(other,level[i],material=STONE,thickness=.11)
    hall_roof(b,lod);tower(b,lod)
