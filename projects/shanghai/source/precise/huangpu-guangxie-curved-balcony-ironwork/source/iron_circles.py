"""Balcony ironwork facing the rounded corner of the Guangxie building.

The 2015 photograph shows repeated circles, concave diamond-shaped fillets and
central squares. The chosen six panels form a section of the long street rail.
"""
from math import sin,cos,pi,ceil

RADIUS=4.8
SPACING=.46
BAYS=6
HALF=SPACING*BAYS/2
CENTRE=.50
RING=.201

def paint(rgb,metal=0):
    s=[v/255 for v in rgb]
    return dict(color=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in s],roughness=.61 if metal else .88,metallic=metal)

PALETTE={name:paint(col,metal)for name,col,metal in [
    ('cast stone coping',(151,144,127),0),('dark drip ledge',(104,101,91),0),
    ('edge of balcony slab',(141,138,124),0),('stone joint',(106,102,95),0),
    ('painted iron frame',(42,47,45),.24),('outer rolled iron',(53,58,54),.32),
    ('concave iron ornament',(61,64,58),.28),('cross ties',(51,54,48),.26),
    ('iron top edge',(75,76,67),.25)]}

def xyz(s,depth,z):
    a=s/RADIUS
    return (sin(a)*(RADIUS-depth),RADIUS-cos(a)*(RADIUS-depth),z)

def band(b,name,lo,hi,profile,material,lod):
    n=max(1,ceil((hi-lo)/(.20 if lod else .09)))
    v=[xyz(lo+(hi-lo)*i/n,d,z)for i in range(n+1)for d,z in profile];p=len(profile)
    faces=[tuple(range(p-1,-1,-1)),tuple(range(n*p,n*p+p))]
    faces.extend((p*i+j,p*i+(j+1)%p,p*(i+1)+(j+1)%p,p*(i+1)+j)for i in range(n)for j in range(p))
    b.add(v,faces,material,name)

def strap(b,name,centreline,width,material,depth=0,thick=.017):
    # A bent flat strip carries its own front, back and two edge faces.
    v=[]
    for i,(s,z) in enumerate(centreline):
        prev=centreline[max(0,i-1)];nxt=centreline[min(i+1,len(centreline)-1)]
        x,y=nxt[0]-prev[0],nxt[1]-prev[1];length=(x*x+y*y)**.5
        dx,dz=-y/length*width/2,x/length*width/2
        v.extend(xyz(s+a*dx,d,z+a*dz)for d,a in [(depth,-1),(depth,1),(depth+thick,1),(depth+thick,-1)])
    f=[(3,2,1,0)];end=len(v)-4;f.append((end,end+1,end+2,end+3))
    f.extend((i+j,i+(j+1)%4,i+4+(j+1)%4,i+4+j)for i in range(0,end,4)for j in range(4))
    b.add(v,f,material,name)

def add_building(b,lod=False):
    band(b,'cast balcony slab',-HALF-.045,HALF+.045,[(-.055,0),(.24,0),(.24,.155),(-.055,.155)],'edge of balcony slab',lod)
    band(b,'shadow beneath coping',-HALF-.048,HALF+.048,[(-.065,.136),(.25,.136),(.25,.169),(-.065,.169)],'dark drip ledge',lod)
    for i in range(3):
        st=-HALF-.054+i*(HALF+.054)*2/3
        band(b,'coping block '+str(i),st,st+(HALF+.054)*2/3-.003,[(-.076,.168),(.252,.168),(.252,.228),(-.076,.218)],'cast stone coping',lod)
    for nr,(height,width)in enumerate([(.263,.018),(.294,.017),(.717,.022),(.831,.026)]):
        depth=-.004 if nr<3 else -.014
        band(b,'continuous curved rail '+str(nr),-HALF-.019,HALF+.019,[(depth,height),(depth+.027,height),(depth+.027,height+width),(depth,height+width)],'painted iron frame',lod)
    band(b,'upper face of curved handrail',-HALF-.020,HALF+.020,[(-.017,.853),(.020,.853),(.020,.861),(-.017,.861)],'iron top edge',lod)
    for i in range(BAYS+1):
        s=-HALF+i*SPACING
        band(b,'structural upright '+str(i),s-.015,s+.015,[(-.006,.216),(.028,.216),(.028,.854),(-.006,.854)],'painted iron frame',lod)
    for i in range(BAYS):
        c=-HALF+(i+.5)*SPACING
        profile=lambda t:(c+RING*cos(t),CENTRE+RING*sin(t))
        count=24 if lod else 48
        strap(b,'round ring '+str(i),[profile(2*pi*k/count)for k in range(count+1)],.0125,'outer rolled iron',-.003)
        # Each quarter joins the tips of a concave-sided diamond within its ring.
        for q in range(4):
            arc=[];subdiv=5 if lod else 12
            for j in range(subdiv+1):
                t=j/subdiv
                u=(1-t)**2*RING+2*t*(1-t)*.038
                v=t*t*RING+2*t*(1-t)*.038
                a=q*pi/2;arc.append((c+u*cos(a)-v*sin(a),CENTRE+u*sin(a)+v*cos(a)))
            strap(b,f'concave leaf {i}-{q}',arc,.011,'concave iron ornament',-.007)
        rad=.049
        for k,(s0,z0,s1,z1)in enumerate([(-rad,-rad,rad,-rad),(rad,-rad,rad,rad),(rad,rad,-rad,rad),(-rad,rad,-rad,-rad)]):
            strap(b,f'central square {i}-{k}',[(c+s0,CENTRE+z0),(c+s1,CENTRE+z1)],.009,'cross ties',-.006)
        for j,(axis,t)in enumerate([(True,-1),(True,1),(False,-1),(False,1)]):
            a=.052*t;d=RING*t
            line=[(c+a,CENTRE),(c+d,CENTRE)]if axis else[(c,CENTRE+a),(c,CENTRE+d)]
            strap(b,f'four ties {i}-{j}',line,.008,'cross ties',.003)
