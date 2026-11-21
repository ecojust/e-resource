"""Tanggu Road curved cornice, the row of modillions, small dentils and central scroll."""
from math import cos,sin,radians,ceil
RADIUS=7.4
ANGLE=.420
PAL={'warm limestone':(201,189,164),'top ledge':(190,181,164),'drip shadow':(148,139,121),
     'dentil face':(200,190,171),'shadowed stone':(172,159,134),
     'faded brick':(152,88,72),'darker brick':(134,75,65),'mortar':(159,117,101),
     'light render':(210,201,183)}
def linear(c):
    t=c/255
    return t/12.92 if t<.04045 else ((t+.055)/1.055)**2.4
PALETTE={k:{'color':[linear(c) for c in v],'roughness':.88} for k,v in PAL.items()}
def xyz(t,r,z):
    return ((RADIUS+r)*sin(t),RADIUS-(RADIUS+r)*cos(t),z)
def sweep(b,label,material,t0,t1,cross,n):
    # Counterclockwise section in radial/height coordinates; arc ends close the real section.
    profile=len(cross);verts=[xyz(t0+(t1-t0)*i/n,r,z) for i in range(n+1) for r,z in cross]
    faces=[tuple(range(profile-1,-1,-1)),tuple(n*profile+i for i in range(profile))]
    for j in range(n):
        for i in range(profile):
            k=(i+1)%profile;a=j*profile
            faces.append((a+i,a+k,a+profile+k,a+profile+i))
    b.add(verts,faces,material,label)
def ribbon(b,label,mat,lo,hi,inner,outer,z0,z1,n):
    sweep(b,label,mat,lo,hi,[(inner,z0),(outer,z0),(outer,z1),(inner,z1)],n)
def add_building(b,lod=False):
    n=28 if lod else 64
    ribbon(b,'Cut through curved backing wall','mortar',-ANGLE,ANGLE,-.22,-.027,0,1.55,n)
    # Four courses directly below the bottom string course, with staggered vertical joints.
    for i in range(4):
        z0=.003+i*.071;z1=.068+i*.071
        pitch=.032
        if lod:
            ribbon(b,'Brick course '+str(i+1),'faded brick',-ANGLE,ANGLE,-.030,0.,z0,z1,n)
        else:
            t=-ANGLE-(i%2)*pitch/2;k=0
            while t<ANGLE:
                a=max(t+.0005,-ANGLE);h=min(t+pitch-.0005,ANGLE)
                if h>a:ribbon(b,f'Brick course {i+1} header {k+1}','darker brick' if (i+2*k)%7==3 else 'faded brick',a,h,-.030,0,z0,z1,2)
                t+=pitch;k+=1
    ribbon(b,'Pale fascia above the cornice','light render',-ANGLE,ANGLE,-.04,.017,1.087,1.55,n)
    sweep(b,'Continuous lower moulded string','warm limestone',-ANGLE,ANGLE,
          [(-.055,.277),(.025,.277),(.041,.294),(.100,.304),(.107,.326),(.092,.352),(.080,.361),(.068,.398),(-.055,.398)],n)
    ribbon(b,'Shadow bed behind the small dentils','shadowed stone',-ANGLE,ANGLE,-.045,.048,.393,.511,n)
    for i in range(-27,28):
        t=i*.01515
        if abs(t)<.027:continue
        ribbon(b,f'Fine dentil {i+28}','dentil face',t-.0047,t+.0047,.044,.142,.395,.519,1 if lod else 2)
    sweep(b,'Overhanging bed mould','warm limestone',-ANGLE,ANGLE,
          [(-.05,.508),(.16,.508),(.162,.536),(.147,.552),(.194,.577),(.209,.602),(.208,.625),(-.05,.625)],n)
    ribbon(b,'Shadowed strip behind projecting brackets','shadowed stone',-ANGLE,ANGLE,-.045,.086,.624,.831,n)
    for i in (-5,-4,-3,-2,-1,1,2,3,4,5):
        t=i*.075;width=.0125
        sweep(b,f'Projecting modillion {i+6}','warm limestone',t-width,t+width,
              [(.070,.638),(.109,.638),(.178,.674),(.289,.697),(.307,.715),(.307,.829),(.070,.829)],1 if lod else 3)
    # The middle bracket drops across the finer course and has a curled, stepped underside.
    sweep(b,'Centre scroll bracket','shadowed stone',-.023,.023,
          [(.021,.329),(.068,.329),(.099,.347),(.108,.380),(.103,.422),(.130,.461),(.140,.517),(.155,.556),(.190,.601),(.243,.630),(.273,.682),(.330,.712),(.342,.753),(.326,.806),(.298,.825),(.021,.825)],3 if lod else 8)
    for side in (-1,1):
        a,bx=(-.026,-.019) if side<0 else (.019,.026)
        sweep(b,'Centre scroll side fillet '+str(side),'dentil face',a,bx,
              [(.101,.358),(.115,.358),(.126,.420),(.154,.460),(.166,.520),(.197,.585),(.260,.625),(.301,.684),(.353,.717),(.357,.758),(.333,.807),(.300,.825),(.280,.824),(.312,.778),(.322,.732),(.272,.697),(.231,.647),(.170,.611),(.134,.532),(.115,.461),(.102,.422)],1 if lod else 3)
    sweep(b,'Main cornice overhang and rounded lip','top ledge',-ANGLE,ANGLE,
          [(-.07,.826),(.289,.826),(.313,.805),(.341,.805),(.361,.825),(.360,.872),(.350,.892),(.304,.909),(.310,.935),(.302,.962),(.282,.974),(.25,1.015),(.22,1.036),(.205,1.09),(-.07,1.09)],n)
    ribbon(b,'Narrow recessed weather line','drip shadow',-ANGLE,ANGLE,.225,.268,1.016,1.035,n)
