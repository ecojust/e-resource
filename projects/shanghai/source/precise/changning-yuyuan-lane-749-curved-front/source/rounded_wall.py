"""Curved aggregate shell with open window reveals, concentric coping and brick dressings."""
import math
import numpy as np
from photo_architecture import Facade

CAST='Yuyuan grey washed aggregate'
COAT='Brown grey rendered coping'
SOOT='Weathered dark cap'
MORTAR='Cool grey brick mortar'
BRICKS=['Clinker brown','Dark umber brick','Plum brown brick','Old chestnut brick']
JOINT='Recessed ashlar joint'

def cylinder(radius,s,z,offset=0):
    angle=s/radius
    return np.array([(radius+offset)*math.sin(angle),radius-(radius+offset)*math.cos(angle),z])

def tangent(builder,radius,s,label,offset=0):
    origin=cylinder(radius,s,0,offset);theta=s/radius
    axis=np.array([math.cos(theta),math.sin(theta),0.])
    return Facade(builder,(origin-axis*.5)[:2],(origin+axis*.5)[:2],label)

def apertures(d):
    r=d['radius_m'];upper=(0,d['upper_window_top_m'])
    lower=(d['lower_window_top_m']-d['lower_window_height_m'],d['lower_window_top_m'])
    holes=[]
    for bay,(theta,width)in enumerate(zip(d['bay_angles_rad'],d['bay_widths_m'])):
        half=r*math.asin(width/(2*r));s=r*theta
        for storey,(lo,hi) in enumerate([upper,lower]):
            holes.append(dict(bay=bay,storey=storey,left=s-half,right=s+half,bottom=lo,top=hi))
    return holes

def strip(builder,r,xlist,low,high,back,face,material,label):
    """A complete watertight annular belt with end returns."""
    verts=[];faces=[]
    for x in xlist:
        verts += [cylinder(r,x,z,o)for z,o in [(low,face),(high,face),(low,back),(high,back)]]
    for i in range(len(xlist)-1):
        n=4*i;j=n+4
        faces.extend([(n,j,j+1,n+1),(n+2,n+3,j+3,j+2),(n+1,j+1,j+3,n+3),(n,n+2,j+2,j)])
    n=4*(len(xlist)-1)
    faces.extend([(0,1,3,2),(n,n+2,n+3,n+1)])
    builder.add(verts,faces,material,label)

def wall(builder,d,lod):
    r=d['radius_m'];a,b=[r*v for v in d['visible_arc_limits_rad']];hi=d['cap_top_m']-.045;lo=d['lower_cut_m']
    holes=apertures(d)
    xs=np.unique([*np.linspace(a,b,38 if lod else 79),*[x for h in holes for x in [h['left'],h['right']]]])
    zs=sorted(set([lo,hi,*[z for h in holes for z in [h['bottom'],h['top']]]]))
    cells=set()
    for i,(x0,x1)in enumerate(zip(xs,xs[1:])):
        for j,(z0,z1)in enumerate(zip(zs,zs[1:])):
            x=(x0+x1)/2;z=(z0+z1)/2
            if not any(h['left']<x<h['right'] and h['bottom']<z<h['top'] for h in holes):
                cells.add((i,j))
    geometry=[];quads=[];indices={}
    def index(i,j,side):
        ref=(i,j,side)
        if ref not in indices:
            indices[ref]=len(geometry);geometry.append(cylinder(r,xs[i],zs[j],-.21 if side else 0))
        return indices[ref]
    for i,j in sorted(cells):
        f=[index(u,v,0) for u,v in [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]]
        k=[index(u,v,1) for u,v in [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]]
        quads.extend([f,list(reversed(k))])
        for n,nb in enumerate([(i,j-1),(i+1,j),(i,j+1),(i-1,j)]):
            if nb not in cells:
                t=(n+1)%4;quads.append((f[t],f[n],k[n],k[t]))
    builder.add(geometry,quads,CAST,'Rounded frontage/aggregate wall and six window reveals')
    top=d['cap_top_m'];hl=d['coping_bottom_m'];small=np.linspace(a,b,47 if lod else 117)
    strip(builder,r,small,hl,top-.055,-.045,.048,COAT,'Rounded frontage/continuous cornice fascia')
    strip(builder,r,small,hl-.022,hl+.017,-.030,.062,'Coping lower drip','Rounded frontage/underside of cornice')
    strip(builder,r,small,top-.062,top,-.075,.083,SOOT,'Rounded frontage/dark stone coping')

def brick_ribbon(builder,r,s,low,high,width,measured,phase,name,lod):
    """Regular brick beds, with whole faces alternating with a central face and two cut ends."""
    if high-low<.02:return
    f=tangent(builder,r,s,name);p=measured['course_median_m']
    f.box(0,(low+high)/2,width,high-low,.027,.001,MORTAR,'joint bed')
    zref=measured['photographed_beds_z_m'][0]
    actual=measured['photographed_beds_z_m']
    kmin=math.floor((low-zref)/p)-2;kmax=math.ceil((high-zref)/p)+3
    # Extend minor variation observed along the source pier only beyond the observed region.
    def bed(i):
        if i<0:return actual[0]+i*p
        if i<len(actual):return actual[i]
        return actual[-1]+(i-len(actual)+1)*p
    for i in range(kmin,kmax):
        z0=max(low+.002,bed(i)+.004);z1=min(high-.002,bed(i+1)-.004)
        if z1<=z0:continue
        edges=[-width/2,width/2]if (i+phase)%2 else[-width/2,-.265*width,.265*width,width/2]
        for j,(a,b)in enumerate(zip(edges,edges[1:])):
            gap=.0045;size=b-a-2*gap
            if size<=0:continue
            color=BRICKS[(i*7+j*3+phase)%11%4]
            f.box((a+b)/2,(z0+z1)/2,size,z1-z0,.014,.020,color,'brick faces')
            if not lod and size>.11 and (i+j)%4==0:
                f.box((a+b)/2,z0+.004,size-.009,.005,.003,.028,'Fired lower brick edge','weathered brick arrises')

def dressings(builder,d,measure,lod):
    r=d['radius_m'];ang=d['bay_angles_rad'];p=measure['pier_width_m'];hi=d['coping_bottom_m']-.008;lo=d['lower_cut_m']+.01
    for n,t in enumerate([-.985,-.327,.345,.898]):
        brick_ribbon(builder,r,r*t,lo,hi,p,measure,(n+1)%2,'Pier '+str(n+1),lod)
    for i,(angle,width)in enumerate(zip(ang,d['bay_widths_m'])):
        for side in [-1,1]:
            s=r*angle+side*(width/2-.070)
            for j,(low,high)in enumerate([(hi-.345,hi),(-1.72,-.12),(lo,d['lower_window_top_m']-d['lower_window_height_m']-.13)]):
                brick_ribbon(builder,r,s,low,high,p*.92,measure,(i+j)%2,'Bay '+str(i+1)+' brick panel '+str(side)+' '+str(j),lod)
        f=tangent(builder,r,r*angle,'Bay '+str(i+1)+' render grooves')
        f.box(0,-.91,.012,1.51,.009,.004,JOINT,'vertical joint between panels')
        f.box(0,hi-.175,.009,.34,.009,.004,JOINT,'upper render joint')
