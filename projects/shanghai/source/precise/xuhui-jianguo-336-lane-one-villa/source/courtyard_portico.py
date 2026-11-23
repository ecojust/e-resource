"""The photographically registered two-depth portico, curved stairs and two stone galleries."""
from pathlib import Path
import json
from math import sin,cos,pi,radians
import numpy as np
from shapely.geometry import Polygon,LineString
from shapely.geometry.polygon import orient

HERE=Path(__file__).absolute().parent.parent/'measurements'
GREY='Fudefang | grey terrazzo'
STEP='Fudefang | pale step stone'
PALETTE={GREY:dict(color=[.47,.46,.43],roughness=.87),STEP:dict(color=[.63,.61,.55],roughness=.93)}

def portico_layout():
    court=json.loads((HERE/'court-cameras.json').read_bytes())['measured_layout_m']
    bow=json.loads((HERE/'balcony-curves.json').read_bytes())['bowed_plan']
    return court,bow

def turned(b,x,y,profile,segments,material,name,phase=0.):
    """Closed lathe with a shared cap ring. On four sides it makes the square-necked balusters."""
    vertices=[];faces=[]
    for radius,z in profile:
        for j in range(segments):
            a=phase+2*pi*j/segments;vertices.append((x+radius*cos(a),y+radius*sin(a),z))
    faces.append(tuple(reversed(range(segments))))
    for level in range(len(profile)-1):
        for j in range(segments):
            a=level*segments+j;c=level*segments+(j+1)%segments
            faces.append((a,c,c+segments,a+segments))
    k=segments*(len(profile)-1);faces.append(tuple(range(k,k+segments)))
    b.add(vertices,faces,material,name)

def ellipse_sector(rx,ry,cy,a0,a1,n,back=None):
    t=np.linspace(a0,a1,n)
    arc=[(rx*sin(a),cy-ry*cos(a)) for a in t]
    if back is not None:
        return orient(Polygon([*arc,(arc[-1][0],back),(arc[0][0],back)]),sign=1)
    return arc

def bow_band(b,rx,ry,cy,thickness,z0,z1,n,name):
    outer=ellipse_sector(rx,ry,cy,-pi/2,pi/2,n)
    inner=ellipse_sector(rx-thickness,ry-thickness,cy,-pi/2,pi/2,n)
    b.plan_prism(Polygon([*outer,*reversed(inner)]),z0,z1,GREY,name)

def oriented_box(b,x,y,z,w,d,h,t,name):
    b.box((x,y,z),(w,d,h),GREY,label=name,basis=((cos(t),sin(t),0),(-sin(t),cos(t),0),(0,0,1)))

def scroll(b,x,y,z,r,sign,name,lod):
    # Front-facing spiral scroll of the Ionic capital. A short tail crosses the neck.
    t=np.linspace(-.45*pi,2.65*pi,25 if lod else 55)
    radii=np.linspace(r,r*.13,len(t))
    knots=[(x+sign*rad*cos(a),z+rad*sin(a))for a,rad in zip(t,radii)]
    rib=LineString(knots).buffer(r*.15,quad_segs=2 if lod else 3)
    b.prism(rib,-y-.012,-y+.013,lambda a,c,d:(a,-d,c),GREY,name)

def capital(b,x,y,z0,z1,r,lod,name):
    h=z1-z0;n=14 if lod else 28
    profile=[(r,z0),(r*1.12,z0+h*.09),(r*1.16,z0+h*.18),(r*1.06,z0+h*.25),
             (r*1.17,z0+h*.48),(r*1.30,z0+h*.59),(r*1.24,z0+h*.81),(r*1.29,z0+h*.87)]
    turned(b,x,y,profile,n,GREY,name+' | necking and echinus')
    cz=z0+.60*h;rs=.37*r
    for side in (-1,1):
        cx=x+side*.93*r
        b.tube([(cx,y-r*1.18,cz),(cx,y+r*1.0,cz)],rs,GREY,
               sides=12 if lod else 24,label=name+' | volute pulley')
        for end in ((-1,) if lod else (-1,1)):
            scroll(b,cx,y+end*(1.21 if end<0 else 1.03)*r,cz,rs,side,name+' | spiral face',lod)
    b.box((x,y,z0+h*.934),(2.64*r,2.54*r,h*.132),GREY,label=name+' | square abacus')

def column(b,x,y,foot,base,shaft_top,underside,r,lod,name):
    n=14 if lod else 32;h=base-foot
    b.box((x,y,foot+h*.21),(r*2.91,r*2.84,h*.42),GREY,label=name+' | square plinth')
    profile=[(r*1.33,foot+h*.42),(r*1.37,foot+h*.55),(r*1.32,foot+h*.68),
             (r*1.14,foot+h*.76),(r*1.18,foot+h*.86),(r*1.12,base)]
    turned(b,x,y,profile,n,GREY,name+' | stepped torus')
    shaft=[(r*1.035,base),(r*1.045,base+(shaft_top-base)*.27),(r*.98,shaft_top)]
    turned(b,x,y,shaft,n,GREY,name+' | tapered smooth shaft')
    capital(b,x,y,shaft_top,underside,r,lod,name+' | capital')

def baluster(b,x,y,h0,h1,turn,lod,name):
    h=h1-h0
    profile=[(.103,h0),(.103,h0+.09*h),(.073,h0+.13*h),(.108,h0+.25*h),(.107,h0+.32*h),
             (.058,h0+.77*h),(.055,h0+.83*h),(.083,h0+.88*h),(.095,h0+.92*h),(.095,h1)]
    if lod:profile=[profile[i]for i in (0,2,3,5,7,9)]
    turned(b,x,y,profile,4,GREY,name,pi/4+turn)

def add_stairs(b,p,a,lod):
    rx=a['upper_landing_radius_x'];ry=a['upper_landing_radius_y'];cy=a['rear_center_y']
    z=a['upper_landing_z'];n=24 if lod else 54;back=p['door_y']+.10
    # Four distinct curved risers are visible in 05, with the uppermost surface continuous to the door.
    for k in range(4):
        ext=(3-k)*.25;plan=ellipse_sector(rx+ext,ry+ext,cy,-pi/2,pi/2,n,back=back)
        b.plan_prism(plan,k*z/4,(k+1)*z/4,STEP,f'Portico | curved stair level {k+1}')
        if not lod:
            outside=ellipse_sector(rx+ext+.024,ry+ext+.024,cy,-pi/2,pi/2,n)
            inside=ellipse_sector(rx+ext-.02,ry+ext-.02,cy,-pi/2,pi/2,n)
            b.plan_prism(Polygon([*outside,*reversed(inside)]),(k+1)*z/4-.024,(k+1)*z/4,STEP,
                         f'Portico | rounded projecting stair lip {k+1}')

def add_bowed_balcony(b,p,a,lod):
    rx,ry,cy=a['radius_x'],a['radius_y'],a['rear_center_y']
    z=a['soffit_z'];top=a['balustrade_coping_z'];n=28 if lod else 66
    slab=ellipse_sector(rx,ry,cy,-pi/2,pi/2,n,back=p['door_y']+.08)
    b.plan_prism(slab,z,z+.235,GREY,'Bowed gallery | underside and floor')
    bow_band(b,rx+.023,ry+.023,cy,.11,z+.225,z+.290,n,'Bowed gallery | raised bead on fascia')
    bow_band(b,rx-.026,ry-.026,cy,.196,z+.278,z+.375,n,'Bowed gallery | stone sill')
    bow_band(b,rx-.018,ry-.018,cy,.196,top-.083,top,n,'Bowed gallery | curving stone handrail')
    bow_band(b,rx-.022,ry-.022,cy,.167,top-.135,top-.080,n,'Bowed gallery | coping neck')
    low=z+.372;high=top-.13
    # In 03 the two broad central baluster piers delimit eight tapered stems; five are spaced along each oblique return.
    rimx,rimy=rx-.118,ry-.118
    def position(t):
        return rimx*sin(t),cy-rimy*cos(t),np.arctan2(rimy*sin(t),rimx*cos(t))
    limits=np.radians([-90,-32.5,32.5,90])
    for i,t in enumerate(limits):
        x,y,turn=position(t);oriented_box(b,x,y,(low+high)/2,.255,.175,high-low,turn,f'Bowed gallery | division pier {i+1}')
    for section,num in enumerate((5,8,5)):
        for i in range(num):
            t=limits[section]+(limits[section+1]-limits[section])*(i+1)/(num+1)
            x,y,turn=position(t);baluster(b,x,y,low,high,turn,lod,f'Bowed gallery | span {section+1} stem {i+1}')
    if not lod:
        # Alternating upright and cross-cut tablets are visible on the soffit in the frontal photograph.
        for i,t in enumerate(np.linspace(-1.40,1.40,23)):
            x,y=rx*sin(t),cy-ry*cos(t);turn=np.arctan2(ry*sin(t),rx*cos(t))
            oriented_box(b,x,y,z+.116,.106,.018,.145,turn,f'Bowed gallery | fascia tablet {i+1}')
            if i%2==0:
                for j in (-1,0,1):
                    oriented_box(b,x-.009*sin(turn),y+.009*cos(turn),z+.116+j*.032,.086,.023,.012,turn,
                                 f'Bowed gallery | tablet courses {i+1}.{j+1}')

def gallery_frieze(b,rx,front,under,lod):
    """Two strips measured separately in 04: close running scrolls over broader triangular fields."""
    def relief(poly,plane,height,name):
        b.prism(poly,-plane,-plane+height,lambda x,z,d:(x,-d,z),GREY,'Upper gallery | '+name)
    x0=-rx+.025;x1=rx-.025;rise=.168;z0=under+.075
    # Eleven full-fold bays can be distinguished across the rectangular lower fascia.
    for i in range(11):
        l=x0+(x1-x0)*i/11;r=x0+(x1-x0)*(i+1)/11;c=(l+r)/2
        chevron=LineString([(l,z0+rise),(c,z0),(r,z0+rise)]).buffer(.014,cap_style=2,join_style=2)
        relief(chevron,front+.002,.022,f'chevron field {i+1}')
        if not lod:
            for j,(xx,zz) in enumerate(((c,z0+.101),((l+c)/2,z0+.034))):
                flower=[]
                for t in np.linspace(0,2*pi,28,endpoint=False):
                    radius=.024+.014*cos(4*t)
                    flower.append((xx+radius*cos(t),zz+radius*sin(t)))
                relief(Polygon(flower),front+.002,.014,f'chevron flower {i+1}.{j+1}')
    if lod:return
    # At a 900-pixel rectification the curl centres recur at about 20 pixels.
    # The last turns of the scroll at the two coping ends are obscured.
    for i in range(42):
        l=x0+(x1-x0)*i/42;w=(x1-x0)/42;z=under+.487
        knots=[(l,z-.016),(l+.12*w,z-.021),(l+.24*w,z-.011),(l+.39*w,z+.013),
               (l+.50*w,z+.028),(l+.64*w,z+.034),(l+.77*w,z+.027),
               (l+.82*w,z+.016),(l+.78*w,z+.005),(l+.67*w,z+.005),(l+.63*w,z+.013)]
        curl=LineString(knots).buffer(.007,quad_segs=2,cap_style=1,join_style=1)
        relief(curl,front-.044,.013,f'running scroll {i+1}')


def add_upper_gallery(b,p,lod):
    rx=p['rail_x'];cy=p['rail_y']+.058;top=p['rail_top'];under=p['rear_head']+.34;back=p['door_y']+.08
    front=cy-.080
    b.box((0,(front+back)/2,under+.18),(2*(rx+.085),back-front,.36),GREY,label='Upper gallery | loadbearing floor and soffit')
    b.box((0,front+.045,under+.35),(2*(rx+.105),.16,.090),GREY,label='Upper gallery | projecting lower cornice')
    b.box((0,front+.041,under+.485),(2*(rx+.093),.168,.186),GREY,label='Upper gallery | straight front fascia')
    low=under+.574;high=top-.108
    b.box((0,cy,(low+low+.052)/2),(2*rx,.19,.052),GREY,label='Upper gallery | balustrade base')
    b.box((0,cy,top-.054),(2*(rx+.06),.222,.108),GREY,label='Upper gallery | straight handrail')
    width=.222;centres=np.linspace(-2.18,2.18,4)
    for i,x in enumerate(centres):
        b.box((x,cy,(low+high)/2),(width,.142,high-low),GREY,label=f'Upper gallery | pier {i+1}')
        b.box((x,cy,top-.02),(width+.048,.245,.109),GREY,label=f'Upper gallery | raised pier cap {i+1}')
    for section in range(3):
        for i in range(5):
            x=centres[section]+(centres[section+1]-centres[section])*(i+1)/6
            baluster(b,x,cy+.048,low+.052,high,0,lod,f'Upper gallery | span {section+1} stem {i+1}')
    gallery_frieze(b,rx,front,under,lod)
    return under

def add_courtyard_portico(builder,lod=False):
    for n,mat in PALETTE.items():builder.palette.setdefault(n,mat)
    p,a=portico_layout();add_stairs(builder,p,a,lod);add_bowed_balcony(builder,p,a,lod)
    upper=add_upper_gallery(builder,p,lod)
    for s,side in [(-1,'west'),(1,'east')]:
        column(builder,s*p['front_x'],p['front_y'],a['upper_landing_z'],p['front_base'],p['front_head'],
               a['soffit_z'],.163,lod,'Portico | '+side+' forward Ionic column')
        # The tall pair has separate square plinths outside the curved landing and carries the upper floor.
        x=s*p['rear_x'];y=p['rear_y'];foot=a['upper_landing_z']
        builder.box((x,y,foot/2),(.72,.74,foot),STEP,label='Portico | '+side+' projecting landing under tall column')
        column(builder,x,y,foot,p['rear_base'],p['rear_head'],upper,.190,lod,'Portico | '+side+' tall rear Ionic column')
