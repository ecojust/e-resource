"""Surveyed-outline podium, bowed central salon and recessed south loggias."""
import math
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade,opening

LIME='cream limestone'; BASE='rusticated light stone'; PALE='pale cut cornice'; RECESS='warm plaster'; FRAME='dark bronze sash'
GLASS='smoky green glazing'; LEAF='carved limestone scrolls'; CANOPY='glazed entrance canopy'; IRON='canopy bronze ribs'
ROOF='warm grey roof'; GREEN='green ballroom metal roof'; DOOR='entrance bronze and glass'
PALETTE={LIME:{'color':[.73,.69,.59],'roughness':.84},BASE:{'color':[.67,.63,.53],'roughness':.88},PALE:{'color':[.84,.81,.71],'roughness':.78},RECESS:{'color':[.78,.71,.57],'roughness':.87},
 FRAME:{'color':[.14,.12,.098],'roughness':.49,'metallic':.32},GLASS:{'color':[.12,.185,.185],'roughness':.28,'metallic':.19},LEAF:{'color':[.76,.72,.61],'roughness':.83},CANOPY:{'color':[.34,.48,.43],'roughness':.33,'metallic':.27},IRON:{'color':[.23,.20,.15],'roughness':.55,'metallic':.48},ROOF:{'color':[.49,.47,.42],'roughness':.90},GREEN:{'color':[.34,.44,.39],'roughness':.65,'metallic':.21},DOOR:{'color':[.14,.16,.14],'roughness':.47,'metallic':.23}}

# The rear edge clears the decoded north tower’s projecting cornices by at least 0.3 m.
SERVICE=[(-58.50,-18.64),(-39.79,-18.12),(-39.66,-23.67)]
BACK=[(47.46,-24.00),(46.42,2.80),(47.74,10.90),(47.64,19.25),(45.93,25.43),(45.44,34.30),(12.39,34.34),(12.17,16.99),(-1.58,16.89),(-5.75,14.71),(-37.65,14.69),(-41.92,16.71),(-53.06,16.33),(-53.52,14.44),(-58.46,14.58)]
XC=2.80; XT=13.51; V=-23.91; BOW=4.80; CORNICE=12.83
def bow(t):return (XC+XT*math.sin(t),V-BOW*math.cos(t))
def arc(n):return [bow(t) for t in np.linspace(-math.pi/2,math.pi/2,n+1)]
def rect(f,u,z,w,h):return box(u-w/2,z,u+w/2,z+h)

def glass(f,p,lod,*,door=False,arch=False,depth=-.32):
    x0,z0,x1,z1=p.bounds;w=x1-x0;h=z1-z0;u=(x0+x1)/2
    f.prism(p.buffer(.012,join_style=2),depth-.025,depth,DOOR if door else GLASS,'recessed door' if door else 'recessed glass')
    bars=[box(u+w*t-.026,z0,u+w*t+.026,z1) for t in [-.25,0,.25]]
    for z in ([z0+h*.61] if lod else [z0+h*.31,z0+h*.68]):
        bars.append(box(x0,z-.031,x1,z+.031))
    if arch:
        spring=z1-w*.48;center=(u,spring)
        for theta in np.linspace(.13,math.pi-.13,5 if lod else 9):
            a,b=center[0]+w*.54*math.cos(theta),center[1]+w*.54*math.sin(theta)
            from shapely.geometry import LineString
            bars.append(LineString([(u,spring),(a,b)]).buffer(.033,cap_style=2))
        half=opening(u,spring-.05,w*.82,w*.39,w*.38,10 if lod else 24)
        bars.append(half.boundary.buffer(.047,cap_style=2))
    interior=p.buffer(-.087,join_style=2)
    f.prism(p.buffer(-.018,join_style=2).difference(interior.difference(unary_union(bars))),depth+.045,depth+.11,FRAME,'recessed sash')
    f.prism(p.buffer(.10,join_style=2).difference(p),-.04,.12,PALE,'dressed arch and jambs')
    f.box(u,z0-.063,w+.22,.127,.35,.015,LIME,'window ledge')

def column(f,u,low,high,r,d,lod,engaged=False):
    x,y,_=f.point(u,0,d)
    stem=[(low,r*1.43),(low+.14,r*1.43),(low+.22,r*1.12),(low+.31,r*1.21),(low+.42,r),
          (high-.80,r*.86),(high-.66,r*1.00),(high-.53,r*1.13),(high-.35,r*1.04),(high-.20,r*1.20)]
    f.builder.lathe((x,y),stem,LIME,12 if lod else 22,f.label+'/column shaft and torus base')
    f.box(u,high-.13,3.03*r,.25,2.68*r,d,PALE,'capital abacus')
    # Four distinct Ionic scrolls around the capital, with leaf ridges below the volutes.
    for side in [-1,1]:
        for handed in [-1,1]:
            uc=u+handed*r*.80;zp=high-.42;pts=[]
            for a in np.linspace(-.45,math.pi*2.15,9 if lod else 22):
                radius=r*(.32-.17*(a+.45)/(math.pi*2.15+.45))
                pts.append(f.point(uc+handed*radius*math.cos(a),zp+radius*math.sin(a),d+side*r*.88))
            f.builder.tube(pts,.043 if not lod else .05,LEAF,5,f.label+'/capital volutes')
        if not lod:
            for du in [-.58,-.20,.20,.58]:
                f.line((u+du*r,high-.72,d+side*r*.79),(u+du*r*1.19,high-.45,d+side*r),.037,LEAF,6)

def rail(f,u,width,z,d,lod):
    f.box(u,z+.05,width,.13,.36,d,PALE,'balustrade base')
    f.box(u,z+.84,width+.08,.15,.39,d,PALE,'balustrade cap')
    n=max(3,round(width/(.53 if lod else .38)))
    for k in range(n):
        q=u+(k+.5-n/2)*width/n;px,py,_=f.point(q,0,d);r=.082
        f.builder.lathe((px,py),[(z+.11,r*1.44),(z+.19,r*1.29),(z+.30,r*.68),(z+.43,r*1.28),(z+.54,r*1.12),(z+.69,r*.62),(z+.77,r*1.13)],LIME,6 if lod else 9,f.label+'/turned stone balusters')

def tooling(f,cut,zmax,lod):
    # Rusticated joints stop at the actual arched openings and vanish around the corner.
    rows=[box(-f.length/2,z,f.length/2,z+.035) for z in np.arange(.39,zmax,.47)]
    f.prism(cut.intersection(unary_union(rows)),.008,.022,RECESS,'horizontal rustication')
    if not lod:
        blocks=[]
        for j,z in enumerate(np.arange(.40,zmax-.39,.48)):
            for x in np.arange(-f.length/2+(j%2)*.60,f.length/2,1.25):blocks.append(box(x,z,x+.017,z+.44))
        f.prism(cut.intersection(unary_union(blocks)),.008,.019,RECESS,'staggered vertical joints')

def cornice(f,lod):
    for z,h,d in [(5.28,.21,.23),(5.53,.16,.32),(11.96,.17,.14),(12.31,.24,.34),(12.62,.16,.47),(12.84,.11,.52)]:
        f.beam(z,h,d,PALE)
    if not lod:
        n=max(2,round(f.length/.48))
        for i in range(n):
            u=(i+.5-n/2)*f.length/n
            f.box(u,12.55,.175,.13,.25,.29,LIME,'cornice dentils')

def loggia(b,lo,hi,v,lod,name):
    f=Facade(b,(lo,v),(hi,v),name);w=f.length;bay=w/5
    lower=[];upper=[]
    inner=Facade(b,(lo,v+1.67),(hi,v+1.67),name+'/recess')
    for i in range(5):
        u=(i-2)*bay
        p=opening(u,.28,bay*.67,4.05,.49,9 if lod else 18);lower.append(p);glass(f,p,lod)
        door=rect(inner,u,5.69,bay*.65,3.96);upper.append(door);glass(inner,door,lod)
        z=10.68;ww=bay*.55;hh=1.01
        vent=Polygon([(u-ww*.29,z-hh*.5),(u+ww*.29,z-hh*.5),(u+ww*.50,z-hh*.22),(u+ww*.50,z+hh*.22),(u+ww*.29,z+hh*.5),(u-ww*.29,z+hh*.5),(u-ww*.5,z+hh*.22),(u-ww*.5,z-hh*.22)])
        upper.append(vent);inner.prism(vent,-.24,-.21,FRAME,'octagonal fanlight');inner.prism(vent.buffer(.12,join_style=2).difference(vent),-.04,.12,PALE,'octagonal surround')
        rail(f,u,bay-.81,5.56,.01,lod)
    cut=f.wall(0,5.44,lower,.46,BASE);tooling(f,cut,5.20,lod)
    f.wall(11.95,12.77,[],.65,LIME);inner.wall(5.45,12.44,upper,.41,RECESS)
    for i in range(6):
        u=(i-2.5)*bay;f.box(u,5.99,.90,1.00,.85,-.01,PALE,'column pedestal');column(f,u,6.44,11.96,.47,-.055,lod)
    for u in [-w/2,w/2]:
        f.box(u,8.66,.31,6.45,1.84,-.85,LIME,'loggia end return')
    b.plan_prism(box(lo,v-.18,hi,v+1.81),5.34,5.54,LIME,name+'/loggia floor')
    b.plan_prism(box(lo,v-.20,hi,v+1.81),11.93,12.09,RECESS,name+'/loggia ceiling')
    cornice(f,lod)

def decorated_bay(f,lod,terminal=False,front_entrance=False):
    w=f.length
    holes=[]
    lower=opening(0,.20,min(2.56,w*.58),4.12,.45,9 if lod else 18);holes.append(lower);glass(f,lower,lod,door=front_entrance)
    upper=opening(0,5.93,min(2.71,w*.67),5.42,min(1.30,w*.31),12 if lod else 28);holes.append(upper);glass(f,upper,lod,arch=True)
    cut=f.wall(0,12.83,holes,.44,LIME);tooling(f,cut,5.18,lod)
    for sign in [-1,1]:
        pos=sign*(min(w*.40,2.24));column(f,pos,5.78,11.97,.32,.135,lod,True)
        f.box(pos,3.03,.58,4.42,.26,.055,BASE,'lower pier')
    rail(f,0,min(w*.60,2.57),5.50,.18,lod)
    cornice(f,lod)
    if terminal:
        body=box(-w*.34,12.87,w*.34,13.60)
        f.prism(body,-.54,.035,LIME,'terminal parapet')
        arc=opening(0,12.99,3.28,1.98,1.34,10 if lod else 23)
        f.prism(arc.buffer(.19,join_style=2).difference(arc).intersection(box(-1.95,13.31,1.95,15.39)),-.46,.06,PALE,'terminal arched pediment')
    else:
        rail(f,0,min(w*.75,4.0),12.90,-.07,lod)

def simple_side(f,lod,back_to_tower=False):
    holes=[]
    if not back_to_tower:
        n=max(1,round(f.length/5.8))
        for i in range(n):
            u=(i+.5-n/2)*f.length/n
            if f.length/n<2.9:continue
            for z,h in [(1.12,2.90),(6.74,3.63)]:
                q=opening(u,z,min(2.14,.57*f.length/n),h,.29 if z<2 else .0,8 if lod else 12)
                holes.append(q);glass(f,q,lod)
    f.wall(0,12.67,holes,.39,LIME);f.beam(5.46,.19,.18,PALE);f.beam(12.67,.21,.25,PALE)

def canopy(b,lod):
    # The photographs from 2013 to 2022 include this later low glass and bronze frame below the historic arch row.
    r0,r1=13.55,15.18;d0,d1=4.90,9.12
    angles=np.linspace(-math.pi*.51,math.pi*.51,12 if lod else 22)
    def p(a,r,d):return (XC+r*math.sin(a),V-d*math.cos(a))
    for a,c in zip(angles,angles[1:]):
        panel=Polygon([p(a,r0,d0),p(a,r1,d1),p(c,r1,d1),p(c,r0,d0)]);b.plan_prism(panel,5.03,5.13,CANOPY,'Canopy/glass panels')
        b.tube([(*p(a,r0,d0),5.02),(*p(a,r1,d1),5.02)],.075,IRON,6,'Canopy/radial bronze ribs')
    for r,d in [(r0,d0),(r1,d1)]:
        b.tube([(*p(a,r,d),5.06) for a in angles],.13,IRON,8,'Canopy/rim')
    for a in [-.89,0,.89]:
        x,y=p(a,14.4,7.43);b.box((x,y,2.49),(.42,.44,4.98),BASE,label='Canopy/current entrance posts')

def add_building(b,lod):
    points=arc(5)
    # Five front facets follow the five large radial windows in the historic photograph.
    for i,(a,c) in enumerate(zip(points,points[1:])):
        decorated_bay(Facade(b,a,c,'Garden bow/bay '+str(i+1)),lod,front_entrance=True)
    left0,left1=-39.65,-32.33;right0,right1=39.73,47.46
    decorated_bay(Facade(b,(left0,V),(left1,V),'West terminal pavilion'),lod,True)
    loggia(b,left1,points[0][0],V,lod,'West five-bay loggia')
    loggia(b,points[-1][0],right0,V,lod,'East five-bay loggia')
    decorated_bay(Facade(b,(right0,V),(right1,V),'East terminal pavilion'),lod,True)
    ring=[(-58.50,-18.64),(-39.79,-18.12),(left0,V),*points,(right1,V),*BACK[1:],(-58.50,-18.64)]
    plan=Polygon(ring)
    for i,(a,c) in enumerate(zip(ring,ring[1:])):
        if i in range(2,9):continue
        f=Facade(b,a,c,'Podium side/'+str(i));simple_side(f,lod,back_to_tower=(min(a[1],c[1])>15.0 and max(a[0],c[0])<12))
    b.plan_prism(plan,0,.13,BASE,'Podium/ground footprint')
    b.plan_prism(plan,12.48,12.68,ROOF,'Podium/main roof')
    # Roof shape of the northeast grand ballroom comes from the operator's 2F plan and 2024 orthophotography.
    ballroom=Polygon([(12.54,33.75),(44.78,33.75),(45.62,24.90),(47.02,19.20),(47.12,11.08),(45.83,4.29),(42.44,1.85),(36.92,.25),(20.06,.35),(16.31,2.22),(13.18,8.22)])
    b.plan_prism(ballroom,12.66,14.34,LIME,'Ballroom/curved enclosing walls')
    b.plan_prism(ballroom,14.32,14.50,GREEN,'Ballroom/green roof')
    for x in [20.1,25.14,30.18,35.22,40.26]:
        b.tube([(x,3.35,14.52),(x,33.51,14.52)],.041,GREEN,6,'Ballroom/roof seams')
    # Shallow discontinuities visible on the service roofs, with no detailed claim about hidden machinery.
    for x0,x1,y0,y1 in [(-56,-48,-13.7,12.5),(-34.5,-13.3,-13.0,-2.4),(-5.8,7.7,4.3,13.6)]:
        b.plan_prism(box(x0,y0,x1,y1),12.65,13.48,ROOF,'Roof/service bays')
    canopy(b,lod)
