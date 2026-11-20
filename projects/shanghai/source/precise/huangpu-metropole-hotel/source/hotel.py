"""Street-facing mass of the Shanghai Metropole at the circular intersection."""
import math
from pathlib import Path
import sys

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

COMMON = Path(__file__).resolve().parents[2] / 'hongkou-general-post-office/source/common'
sys.path.insert(0, str(COMMON))
from photo_architecture import Facade, opening

BRICK='buff face brick'; STONE='pale cast stone'; DARK='polished granite'; FRAME='dark metal sash'
GLASS='blue grey glass'; BRASS='aged bronze'; ROOF='grey roof'; GLOW='canopy panels'
PALETTE={BRICK:{'color':[.50,.387,.29],'roughness':.85},STONE:{'color':[.63,.52,.406],'roughness':.81},
         DARK:{'color':[.16,.151,.149],'roughness':.49},FRAME:{'color':[.104,.094,.079],'roughness':.55,'metallic':.26},
         GLASS:{'color':[.169,.204,.229],'roughness':.27,'metallic':.22},BRASS:{'color':[.45,.309,.159],'roughness':.48,'metallic':.43},
         ROOF:{'color':[.36,.33,.306],'roughness':.76},GLOW:{'color':[.78,.75,.625],'roughness':.37},
         'upper render':{'color':[.50,.444,.393],'roughness':.85}}

# The independently fitted street radius is 13.93 m. The central three bays
# occupy one chord, flanked by two double-window faces and two short facets.
RADIUS=13.93

def arc(degrees):
    a=math.radians(degrees)
    return (RADIUS*math.sin(a), RADIUS*(math.cos(a)-1))

ARC=[arc(a)for a in (-52.4,-39.4,-16.7,16.7,39.4,52.4)]
WEST=(-20.76,4.03); EAST=(17.52,1.02); REAR=(-2.96,21.09)
BASE=[WEST,*ARC,EAST,REAR]
LOWER_HEIGHT=32.35
TOPS=[43.05,48.12,56.23,48.12,43.05]

def panel(f,x,z,w,h,back,front,material,label):
    f.box(x,z,w,h,front-back,(back+front)/2,material,label)

def sash(f,x,z,width,height,lod,label,arch=0,transom=.68):
    shape=opening(x,z,width,height,arch,segments=7 if lod else 15)
    f.prism(shape.buffer(.013,join_style=2),-.442,-.416,GLASS,label+' recessed glass')
    inner=shape.buffer(-.061,join_style=2);bars=[box(x-width/2,z+height*transom-.027,x+width/2,z+height*transom+.027)]
    if not lod:bars.append(box(x-.026,z,x+.026,z+height))
    frame=shape.buffer(-.01,join_style=2).difference(inner.difference(unary_union(bars)))
    f.prism(frame,-.4,-.288,FRAME,label+' sash')
    if not lod:panel(f,x,z-.055,width+.11,.10,-.02,.095,STONE,label+' sill')
    return shape

def sill_band(f,z,mat=STONE):
    panel(f,0,z,f.length+.01,.16,-.04,.13,mat,'horizontal stone course')

def crescent_profile(f,x,z,scale,lod):
    # Raked chevrons on the entrance pilasters are visible on the 2022 close-up.
    h=scale
    path=[(x-.48*h,z-.06*h),(x-.16*h,z+.26*h),(x,z+.13*h),(x+.16*h,z+.26*h),(x+.48*h,z-.06*h)]
    f.builder.tube([f.point(u,v,.16)for u,v in path],.029*h,BRASS,5 if lod else 8,f.label+'/stepped chevron')

def entrance(f,lod):
    holes=[];centres=[-2.04,0,2.04]
    for x in centres:
        h=opening(x,.24,1.62,4.56);holes.append(h)
        # Return jambs and soffits leave a real recess in front of the doors.
        for sign in [-1,1]:panel(f,x+sign*.825,2.535,.06,4.59,-1.57,-.32,DARK,'entrance side reveal')
        panel(f,x,4.81,1.70,.10,-1.57,-.30,STONE,'entrance soffit')
        panel(f,x,2.53,1.68,4.58,-1.64,-1.58,'interior shadow','recess back')
        panel(f,x,2.32,1.53,4.10,-1.575,-1.55,GLASS,'bronze door glazing')
        for u in [-.75,0,.75]:panel(f,x+u,2.32,.069,4.12,-1.56,-1.48,BRASS,'door stiles')
        for z in [.27,1.22,3.60,4.36]:panel(f,x,z,1.54,.072,-1.56,-1.48,BRASS,'door transoms')
        if not lod:
            for u in [-.15,.15]:panel(f,x+u,1.66,.055,.36,-1.49,-1.34,BRASS,'paired door pulls')
    for x in [-3.13,-1.03,1.03,3.13]:
        panel(f,x,1.92,.32,3.68,-.06,.22,DARK,'stepped granite entrance pilaster')
        crescent_profile(f,x,3.49,.75,lod)
    for i in range(4):
        z=.043+i*.053;panel(f,0,z,6.85,.078,-1.66,.85-.19*i,DARK,'shallow entrance stairs')
    # The rectangular canopy and its square underside lights appear in the
    # dated operator-era close-up. Narrow rods support it above the entrance.
    panel(f,0,5.22,7.67,.23,-.13,2.26,BRASS,'projecting entrance canopy')
    for col in range(6):
        for row in range(2):
            u=(col-2.5)*1.23;d=.15+row*1.00
            f.box(u,5.085,1.16,.050,.88,d+.48,GLOW,'canopy underside glazing')
    for u in [-3.47,3.47]:f.builder.tube([f.point(u,5.34,2.01),f.point(u,7.72,.02)],.038,BRASS,6 if lod else 10,f.label+'/canopy suspension rods')
    for x in [-2.04,2.04]:
        # Photographed from immediately below the entrance ceiling. Each lantern
        # has its own suspended opal body, upper and lower dark bronze cages.
        centre=f.point(x,3.98,-.78)
        b=f.builder
        profile=[(centre[2]-.23,.07),(centre[2]-.13,.22),(centre[2]+.12,.22),(centre[2]+.23,.07)]
        b.lathe(centre[:2],profile,GLOW,8,f.label+'/paired opal lanterns')
        for k in range(8):
            a=math.tau*k/8
            points=[(centre[0]+rad*math.cos(a),centre[1]+rad*math.sin(a),z)
                    for z,rad in [(centre[2]-.27,.065),(centre[2]-.14,.244),(centre[2]+.14,.244),(centre[2]+.25,.065)]]
            b.tube(points,.016,BRASS,5,f.label+'/lantern cage')
        b.tube([f.point(x,4.23,-.78),f.point(x,4.74,-.78)],.026,FRAME,6,f.label+'/lantern suspension')
    return holes

def facet(f,region,top,lod):
    centre=region=='centre';paired=region=='pair';xs=[-2.04,0,2.04]if centre else [-1.13,1.13]if paired else [0]
    ground=entrance(f,lod)if centre else [sash(f,x,.63,1.58 if paired else 1.37,4.17,lod,'street shopfront',transom=.76)for x in xs]
    f.wall(0,5.55,ground,.39,DARK if centre else STONE)
    holes=[]
    for x in xs:
        holes.append(sash(f,x,5.84,1.54 if centre else 1.43,2.93,lod,'piano nobile',arch=.62 if centre else 0))
    count=10 if centre else 9 if paired else 8
    for row in range(count):
        for x in xs:holes.append(sash(f,x,10.12+3.69*row,1.40 if centre else 1.35,2.25,lod,'hotel room'))
    if centre or paired:
        base=48.16 if centre else 43.86;height=6.25 if centre else 2.77
        for x in xs:
            hole=opening(x,base,1.42 if centre else 1.37,height,.64,segments=9 if lod else 19);holes.append(hole)
            if centre:
                f.prism(hole.buffer(.012),-.6,-.57,'interior shadow','upper arched louvre back')
                for j in range(4 if lod else 9):panel(f,x,base+.25+j*((height-.95)/(3 if lod else 8)),1.34,.075,-.47,-.31,FRAME,'upper louvres')
            else:
                f.prism(hole.buffer(.01),-1.33,-1.30,'interior shadow','loggia setback')
                panel(f,x,base+.29,1.33,.44,-.13,-.015,STONE,'low gallery parapet')
    f.wall(5.55,top,holes,.39,BRICK)
    for z in [5.52,9.55]:sill_band(f,z)
    for x in xs[:-1]:
        mid=x+(xs[1]-xs[0])/2;panel(f,mid,(10.0+top-.48)/2,.18,top-10.48,-.035,.105,STONE,'vertical masonry fillet')
    for sign in [-1,1]:
        x=sign*(f.length/2-.22);panel(f,x,(9.63+top)/2,.42,top-9.63,-.035,.236,BRICK,'stepped end pier')
        if not lod:panel(f,x,top-.71,.24,1.05,.21,.267,STONE,'pier cap vertical ornament')
    sill_band(f,top-.17)

def street_wing(f,n,lod):
    xs=[(i-(n-1)/2)*f.length/n for i in range(n)];ground=[sash(f,x,.72,1.61,3.78,lod,'granite street bay',transom=.72)for x in xs]
    f.wall(0,5.55,ground,.40,STONE);holes=[]
    for x in xs:holes.append(sash(f,x,5.85,1.40,2.67,lod,'second storey'))
    for row in range(6):
        for x in xs:holes.append(sash(f,x,10.12+row*3.69,1.34,2.18,lod,'side wing room'))
    f.wall(5.55,LOWER_HEIGHT,holes,.39,BRICK)
    for z in [5.53,9.55,LOWER_HEIGHT-.14]:sill_band(f,z)
    if not lod:
        for i in range(n-1):panel(f,(xs[i]+xs[i+1])/2,19.78,.23,20.60,-.035,.09,BRICK,'side masonry strips')

def roof_and_returns(b,front,rear,bottom,top,label,lod,risers=False,above=None):
    ring=[*front,*rear];p=Polygon(ring)
    if not p.is_valid:raise ValueError(label+' has an invalid rooftop footprint')
    terrace=p.difference(Polygon(above))if above else p
    b.plan_prism(terrace,top-.22,top,ROOF,label+'/terrace roof')
    for i in range(len(front)-1,len(ring)):
        f=Facade(b,ring[i],ring[(i+1)%len(ring)],label+' return '+str(i))
        side=risers and i in (len(front)-1,len(ring)-1) and f.length>4.9
        holes=[]
        if side:
            n=max(1,min(3,int(f.length//3.1)));xs=[(j-(n-1)/2)*2.02 for j in range(n)]
            rows=[z for z in [34.28,37.97,41.66,45.35,49.06,52.75]if z>bottom+.56 and z+1.86<top-.45]
            for z in rows:
                for x in xs:holes.append(sash(f,x,z,1.02,1.86,lod,'upper exposed flank'))
        f.wall(bottom,top,holes,thickness=.28,material=BRICK if side else 'upper render')

def crown(b,lod):
    # The oblique survey shows a setback, the front has rounded/bevelled ends
    # and a rhythm of raised strips. The upper roof's hidden plant is omitted.
    poly=[(-3.40,.49),(3.40,.49),(4.40,1.51),(4.40,5.71),(3.40,6.77),(-3.40,6.77),(-4.40,5.71),(-4.40,1.51)]
    for i,(a,c)in enumerate(zip(poly,poly[1:]+poly[:1])):
        f=Facade(b,a,c,'lantern '+str(i));f.wall(55.99,63.96,material=STONE)
        if i in (0,1,2,6,7):
            n=7 if i==0 else 3 if f.length>2 else 1
            for j in range(n):
                x=(j-(n-1)/2)*f.length/(n+.45);panel(f,x,59.89,.16 if i==0 else .13,6.37,-.032,.17,BRICK,'crown fluting')
        panel(f,0,63.59,f.length+.007,.44,-.04,.087,FRAME,'upper coping fascia')
    p=Polygon(poly);b.plan_prism(p,63.90,64.07,ROOF,'lantern roof');b.plan_prism(p.buffer(-.26,join_style=2),64.05,64.88,FRAME,'setback rooftop parapet')
    b.plan_prism(p.buffer(-.39,join_style=2),64.86,65.0,ROOF,'lantern coping')

def add_hotel(b,lod):
    for i,(a,c)in enumerate(zip(ARC,ARC[1:])):
        facet(Facade(b,a,c,['west edge','west paired','entrance and tower','east paired','east edge'][i]),
              ['single','pair','centre','pair','single'][i],TOPS[i],lod)
    street_wing(Facade(b,WEST,ARC[0],'Jiangxi Middle Road wing'),5,lod)
    street_wing(Facade(b,ARC[-1],EAST,'Fuzhou Road wing'),3,lod)
    first=[(11.80,2.20),(4.50,10.61),(-8.72,9.10),(-12.28,4.46)]
    second=[(9.25,2.65),(3.84,8.01),(-6.50,7.65),(-9.30,3.12)]
    tower=[(4.95,2.78),(3.72,7.56),(-4.21,7.35),(-5.03,2.82)]
    roof_and_returns(b,[WEST,*ARC,EAST],[REAR],0,LOWER_HEIGHT,'eight storey base',lod,above=[*ARC,*first])
    roof_and_returns(b,ARC,first,LOWER_HEIGHT,TOPS[0],'lower setback',lod,True,[*ARC[1:-1],*second])
    roof_and_returns(b,ARC[1:-1],second,TOPS[0],TOPS[1],'paired shoulders',lod,True,[*ARC[2:4],*tower])
    roof_and_returns(b,ARC[2:4],tower,TOPS[1],TOPS[2],'upper three arch tower',lod,True)
    crown(b,lod)
