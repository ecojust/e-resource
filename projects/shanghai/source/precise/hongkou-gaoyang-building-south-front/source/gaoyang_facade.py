"""South street front of the former Nanyang Brothers headquarters on East Daming Road."""
from pathlib import Path
import json
import math
from shapely.geometry import Polygon, box as rect
from photo_architecture import Facade, opening

P = json.loads(Path(__file__).with_name('parameters.json').read_text())
WALL = 'weathered grey render'
STONE = 'pale cast stone'
REVEAL = 'carved pale stone'
RUSTIC = 'shaded horizontal masonry joints'
GLASS = 'recessed grey glazing'
FRAME = 'dark window joinery'
ROOF = 'grey roof flashing'
GRILLE = 'painted metal grille'
POLE = 'dull metal finials'
DOOR = 'dark entrance joinery'
PALETTE = {
    WALL: {'color':[.638,.625,.577],'roughness':.89},
    STONE: {'color':[.745,.717,.649],'roughness':.83},
    REVEAL: {'color':[.67,.649,.596],'roughness':.87},
    RUSTIC: {'color':[.466,.449,.404],'roughness':.93},
    GLASS: {'color':[.144,.196,.202],'roughness':.32,'metallic':.23},
    FRAME: {'color':[.174,.167,.147],'roughness':.58},
    ROOF: {'color':[.383,.397,.385],'roughness':.77},
    GRILLE: {'color':[.258,.252,.217],'roughness':.68,'metallic':.2},
    POLE: {'color':[.396,.393,.344],'roughness':.57,'metallic':.35},
    DOOR: {'color':[.297,.252,.196],'roughness':.70},
}
L,R,WI,EI=(P[k] for k in ['front_west','front_east','west_inner','east_inner'])
F,C,B=P['front_y'],P['central_y'],P['detail_depth']
CY=(WI+EI)/2
# The rounded east arris can be seen in both the 1937 plates and the 2026 oblique.
RING=[(L,F),(WI,F),(WI,C),(EI,C),(EI,F),(R-1.65,F),(R-0.48,F+.48),
      (R,F+1.65),(R,B),(L,B)]
NAMES=['West street wing','West inner return','Central recess',
       'East inner return','East street wing','East corner 1',
       'East corner 2','Eastern street return','Rear cut face','Western street return']

def spaced(width,count,pad):
    span=width-2*pad
    return [0.] if count==1 else [-span/2+span*j/(count-1) for j in range(count)]


def window_grid(wall,holes,lod):
    carved=[]
    for u,z,width,height,arc,label in holes:
        profile=opening(u,z,width,height,arc,segments=8 if lod else 16)
        carved.append((profile,label,arc,width))
    wall.wall(.03,P['central_parapet']-.81 if wall.label==NAMES[2] else P['wing_parapet']-1.35,
              [shape for shape,*_ in carved],thickness=.39,material=WALL)
    for profile,label,arc,width in carved:
        wall.window(profile,1 if lod or width<1.20 else 2,1 if lod else 2,
                    frame=FRAME,trim=False,glass=GLASS,label=label)
        if arc and not lod:
            border=profile.buffer(.075,join_style=2).difference(profile)
            wall.prism(border,-.035,.055,STONE,label+'/curved hood')


def elevation(b,index,lod):
    a,z=RING[index],RING[(index+1)%len(RING)]
    wall=Facade(b,a,z,NAMES[index]);holes=[]
    if index==8:
        wall.wall(.02,P['central_parapet']-.72,material=WALL)
        return
    central=index==2
    wing=index in (0,4)
    curb=index in (5,6)
    narrow=wall.length<2.05
    if curb:
        # The archive and oblique city photographs each show two lights wrapping
        # around the chamfer. Both short faces contain a real recessed opening.
        width=wall.length*.65
        for floor,zbase in enumerate(P['window_floors_m']):
            holes.append((0,zbase,width,P['rect_height'],0,f'corner level {floor+2}'))
        holes.append((0,P['arcade_sill'],width,P['arcade_height'],width/2,'corner arcade'))
        holes.append((0,.20,width,3.18,.32,'corner entrance light'))
        window_grid(wall,holes,lod)
    else:
        if central:
            groups=spaced(wall.length,5,2.40)
            regular=[u+d for u in groups for d in (-1.23,0,1.23)]
            upper=spaced(wall.length,15,.78)
        elif wing:
            regular=spaced(wall.length,4,2.13 if index==0 else 1.75)
            upper=regular
        else:
            count=max(1,round(wall.length/2.32))
            regular=spaced(wall.length,count,1.02)
            upper=regular
        for floor,zbase in enumerate(P['window_floors_m']):
            for u in regular:
                width=1.00 if central else (1.51 if wing else 1.20)
                holes.append((u,zbase,width,P['rect_height'],0,f'level {floor+2} openings'))
        for u in upper:
            width=1.18 if central else (1.52 if wing else 1.24)
            holes.append((u,P['arcade_sill'],width,P['arcade_height'],min(width/2,.76),'arcade window'))
        if central:
            for u in (-7.20,-3.32,1.60,6.45):
                holes.append((u,.18,2.83,3.31,0,'street doors'))
        elif wing:
            for u in spaced(wall.length,2,wall.length*.28):
                holes.append((u,.13,2.70,3.36,.94,'ground-floor arch'))
        elif wall.length>3:
            for u in spaced(wall.length,max(1,round(wall.length/3.4)),1.36):
                holes.append((u,.24,1.63,3.21,.46,'side ground opening'))
        window_grid(wall,holes,lod)
    top=P['central_parapet'] if central else P['wing_parapet']
    for height,thick,projection in [(4.66,.22,.26),(9.37,.14,.13),(14.17,.14,.13),
                                      (18.91,.30,.34),(top-1.28,.24,.42),(top-.99,.28,.57)]:
        wall.beam(height,thick,projection,STONE,label='continuous stringcourses')
    if central or wing:
        if central:
            supports=[(groups[i]+groups[i+1])/2 for i in range(4)]
        else:
            supports=[-wall.length/2+.48,wall.length/2-.48]
        for u in supports:
            wall.box(u,11.92,.42 if central else .73,14.35,.42,.03,STONE,'tall pilaster')
            wall.box(u,19.05,.56 if central else .87,.37,.54,.07,STONE,'pilaster capital')
        if not lod:
            for u in spaced(wall.length,max(4,round(wall.length/.66)),.34):
                wall.box(u,top-1.59,.20,.30,.44,.12,REVEAL,'cornice consoles')
    if (wing or index in (7,9)) and not lod:
        for u in [-wall.length/2+.52,wall.length/2-.52]:
            for i in range(21):
                wall.box(u,.48+i*.88,.79,.045,.15,.16,RUSTIC,'quoin course joints')
    if central:
        wall.beam(top-.32,.50,.18,STONE,label='central parapet')
        # Three low stepped slabs above the middle of the recessed range.
        for i,(width,lo) in enumerate([(9.15,top-.04),(7.55,top+.23),(5.35,top+.44)]):
            wall.box(0,lo,width,.29,.55,0,STONE,'stepped central roofline')


def balcony_rail(b,a,z,height,lod,label):
    f=Facade(b,a,z,label)
    for h in [height+.11,height+.79]:
        f.box(0,h,f.length,.18,.27,0,STONE,'rail coping')
    count=max(3,round(f.length/(.86 if lod else .51)))
    for u in spaced(f.length,count,.25):
        x,y,_=f.point(u,0)
        b.lathe((x,y),[(height+.13,.081),(height+.24,.124),
                (height+.46,.081),(height+.62,.065),(height+.72,.089)],STONE,6 if lod else 8,label+'/turned balusters')


def corniced_tower(b,x,y,lod,name):
    """Bell-shaped square shoulder supporting a rail terrace and four-sided lantern."""
    levels=[(24.70,5.23),(25.10,5.33),(25.40,5.08),(25.88,4.62),(26.60,4.04),
            (27.44,3.53),(28.35,3.10),(29.16,2.93),(29.53,2.94),(29.70,3.22),(30.04,3.25)]
    if lod:levels=levels[0:3]+[levels[i]for i in (4,6,8,10)]
    corners=[(-1,-1),(1,-1),(1,1),(-1,1)]
    verts=[(x+dx*r,y+dy*r,h)for h,r in levels for dx,dy in corners]
    faces=[(3,2,1,0)]
    for j in range(len(levels)-1):
        for i in range(4):
            k=j*4;faces.append((k+i,k+(i+1)%4,k+4+(i+1)%4,k+4+i))
    k=len(verts)-4;faces.append((k,k+1,k+2,k+3))
    b.add(verts,faces,WALL,name+'/curved square shoulder')
    def square(r):return [(x+r*dx,y+r*dy)for dx,dy in corners]
    b.box((x,y,30.17),(6.66,6.66,.36),STONE,label=name+'/lantern terrace')
    for i in range(4):
        a,z=square(3.15)[i],square(3.15)[(i+1)%4]
        balcony_rail(b,a,z,30.29,lod,name+'/upper balustrade')
        f=Facade(b,square(1.56)[i],square(1.56)[(i+1)%4],name+'/lantern face')
        arch=opening(0,30.72,1.17,1.92,.585,8 if lod else 16)
        f.wall(30.36,33.04,[arch],thickness=.24,material=STONE)
        f.window(arch,1,1 if lod else 2,frame=FRAME,glass=GLASS,trim=False,label='lantern aperture')
        for u in [-1.34,1.34]:
            f.box(u,31.59,.24,2.42,.32,.06,REVEAL,'corner pilasters')
        f.beam(33.10,.26,.23,STONE,label='lantern cornice')
        # Segmental pediments and arched grille appear at the feet of all four faces.
        g=Facade(b,square(4.98)[i],square(4.98)[(i+1)%4],name+'/dormer')
        crest=opening(0,24.82,4.67,2.96,2.18,10 if lod else 22)
        slit=opening(0,25.44,1.10,1.65,.53,8 if lod else 14)
        g.prism(crest.difference(slit),-.40,.22,STONE,'semicircular dormer')
        g.prism(slit,-.33,-.28,GRILLE,'inset vent')
        if not lod:
            for u in [-.32,0,.32]:
                g.box(u,26.02,.052,1.05,.08,-.17,FRAME,'vent bars')
        rim=crest.buffer(.16,join_style=2).difference(crest)
        g.prism(rim,-.02,.32,REVEAL,'pediment hood')
    widths=[(33.18,1.82),(33.38,1.76),(34.34,.56),(34.60,.36)]
    vv=[(x+dx*r,y+dy*r,h)for h,r in widths for dx,dy in corners]
    ff=[(3,2,1,0)]+[(k+i,k+(i+1)%4,k+4+(i+1)%4,k+i+4)
                       for k in (0,4,8)for i in range(4)]+[(12,13,14,15)]
    b.add(vv,ff,STONE,name+'/four-slope cap')
    b.lathe((x,y),[(34.53,.31),(34.78,.33),(34.91,.21),(35.18,.17),(35.46,.09)],STONE,10,name+'/finial')
    b.tube([(x,y,35.38),(x,y,P['spire'])],.049 if not lod else .060,POLE,8,name+'/flagstaff')


def entrance(b,lod):
    label='Street entrance'
    for x in [-9.71,-8.15,8.15,9.71]:
        xx=CY+x
        b.box((xx,.98,.24),(.89,.84,.48),STONE,label=label+'/pedestals')
        b.lathe((xx,.98),[(.47,.40),(.60,.42),(.72,.33),(3.93,.255),(4.09,.37),(4.23,.42)],
                STONE,10 if lod else 16,label+'/columns')
    b.box((CY,2.32,4.40),(21.17,4.03,.47),WALL,label=label+'/canopy')
    b.box((CY,2.32,4.69),(21.46,4.18,.20),STONE,label=label+'/canopy moulding')
    for x in [-10.31,10.31]:
        b.box((CY+x,2.31,4.88),(.59,3.96,.29),STONE,label=label+'/canopy side stops')
    b.box((CY,2.41,.08),(20.33,3.73,.16),STONE,label=label+'/portico floor')


def add_gaoyang(builder,lod=False):
    for i in range(len(RING)):elevation(builder,i,lod)
    plan=Polygon(RING)
    builder.plan_prism(plan,.00,.075,STONE,'street front/plinth')
    builder.plan_prism(plan,P['central_parapet']-1.04,P['central_parapet']-.79,ROOF,'street front/roof slab')
    for left,right,label in [(L,WI,'West tower'),(EI,R,'East tower')]:
        wing=rect(left,F,right,B)
        builder.plan_prism(wing,23.46,24.97,WALL,label+'/attic plinth')
        builder.plan_prism(wing.buffer(.19,join_style=2),24.74,24.94,STONE,label+'/attic coping')
        for edge,depth in [((left,F+.15),(right,F+.15)),((right,F+.32),(right,B-.15))]:
            balcony_rail(builder,edge,depth,24.92,lod,label+'/street balusters')
        corniced_tower(builder,(left+right)/2,F+5.04,lod,label)
    entrance(builder,lod)
    # Blender stores object names in a 63-byte UTF-8 field.
    for part in builder.parts:
        if len(part['label'].encode())>63:
            raise ValueError('Blender object name exceeds 63 bytes: '+part['label'])
