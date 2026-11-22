"""Pebbledash reveals, staggered quoins and the two wrought-iron casement panels at 709 Julu Road."""
from math import cos, pi, sin
from random import Random


def material(rgb,roughness=.86,metallic=0):
    def linear(c):return c/3294.6 if c<=10 else ((c/255+.055)/1.055)**2.4
    return {'color':[linear(c) for c in rgb], 'roughness':roughness, 'metallic':metallic}

PALETTE={
    'dark aggregate':material((78,77,70)), 'joint':material((78,71,59)),
    'pale brown stone':material((153,139,118)), 'ochre stone':material((143,128,108)),
    'sill':material((164,150,128)), 'sash':material((64,58,52),.56),
    'wrought iron':material((50,51,46),.63,.17), 'lower glass':material((154,163,155),.41,.09),
    'top glass':material((122,134,132),.43,.1),
    'light pebbles':material((118,112,99)), 'olive pebbles':material((97,96,84)),
    'slate pebbles':material((67,74,73)),
}
HALF=.74
SILL=.14
HEAD=2.06
TRANSOM=1.49


def block(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)


def pebbles(b,lod):
    rng=Random(709); buckets={key:([],[])for key in ('light pebbles','olive pebbles','slate pebbles')}
    for j in range(5300 if not lod else 1460):
        x=rng.uniform(-1.12,1.12);z=rng.uniform(SILL+.003,2.235)
        if z < HEAD:
            course=int((z-SILL)/((HEAD-SILL)/8)); outer=HALF+(.122 if course%2 else .235)
            if abs(x) <= outer+.015:continue
        elif abs(x)<HALF+.01:continue
        verts,faces=buckets[rng.choice(list(buckets))];ix=len(verts);wide=rng.uniform(.004,.012)*(1.24 if lod else 1);height=wide*rng.uniform(.50,1.4)
        verts.extend([(x-wide,-.002,z),(x,-.002,z-height),(x+wide,-.002,z),(x,-.002,z+height),(x+wide*.2,-rng.uniform(.004,.009),z)])
        faces.extend([(ix+4,ix+t,ix+(t+1)%4)for t in range(4)])
    for key,(v,f) in buckets.items():b.add(v,f,key,'exposed aggregate / '+key)


def stroke(b,coords,r,tag,lod):
    b.tube(coords,r,'wrought iron',5 if lod else 8,tag)


def leaf(b,c,lod,label):
    # A bottom rail and a slim upright hold each separately forged frame.
    w=.315;bot=.215;top=1.445
    for side in (-1,1):
        x=c+side*w;stroke(b,[(x,.068,bot),(x,.068,top)],.010,label+' outer straight '+str(side),lod)
    for zz in [bot,top]:stroke(b,[(c-w,.068,zz),(c+w,.068,zz)],.010,label+' rail '+str(zz),lod)
    stroke(b,[(c,.065,bot),(c,.065,top)],.008,label+' centre stile',lod)
    for side in (-1,1):
        count=24 if lod else 52
        # Two bent lines flare into the lower leaves and open at the crest.
        knots=[(.012,.23),(.101,.34),(.175,.51),(.190,.64),(.133,.79),(.078,.86),(.145,.97),(.194,1.09),(.176,1.17),(.104,1.223),(.018,1.231)]
        coords=[]
        for i in range(len(knots)-1):
            a=knots[max(i-1,0)];b0=knots[i];b1=knots[i+1];d=knots[min(len(knots)-1,i+2)]
            for jj in range(2 if lod else 5):
                t=jj/(2 if lod else 5)
                p=[.5*((2*b0[k])+(-a[k]+b1[k])*t+(2*a[k]-5*b0[k]+4*b1[k]-d[k])*t*t+(-a[k]+3*b0[k]-3*b1[k]+d[k])*t*t*t)for k in range(2)]
                coords.append((c+side*p[0],.059,p[1]))
        coords.append((c+side*knots[-1][0],.059,knots[-1][1]));stroke(b,coords,.0075,label+' bent leaf '+str(side),lod)
        for tier,(origin,radius,zc) in enumerate(((.101,.108,1.323),(.107,.076,1.161))):
            coords=[]
            for j in range(count+1):
                q=j/count;angle=(-pi/2 if tier==0 else pi/2)+(-1 if tier==0 else 1)*1.76*pi*q
                radius_q=radius*(1-.82*q)
                coords.append((c+side*(origin+radius_q*cos(angle)),.055,zc+radius_q*sin(angle)))
            stroke(b,coords,.008,label+' head scroll '+str((side,tier)),lod)
        x=c+side*.22
        # In each lower corner the bar hooks back towards the short vertical foot.
        foot=[]
        for j in range(10 if lod else 21):
            t=j/(9 if lod else 20);angle=-pi/2+1.40*pi*t;rad=.036*(1-.70*t)
            foot.append((c+side*(.145+rad*cos(angle)),.059,bot+.037+rad*sin(angle)))
        stroke(b,foot,.006,label+' foot hook '+str(side),lod)
        stroke(b,[(x,.058,bot),(x,.058,.40)],.007,label+' short foot '+str(side),lod)


def add_building(b,lod=False):
    for side in (-1,1):
        x0,x1=(-1.12,-HALF)if side<0 else(HALF,1.12)
        block(b,x0,x1,0,.27,SILL,HEAD,'dark aggregate','wall reveal '+str(side))
        for j in range(8):
            z=SILL+(HEAD-SILL)*j/8;top=SILL+(HEAD-SILL)*(j+1)/8
            reach=.122 if j%2 else .235
            x0,x1=(-HALF-reach,-HALF) if side<0 else(HALF,HALF+reach)
            block(b,x0,x1,-.027,.13,z+.006,top-.006,'ochre stone' if (j+side)%3==0 else 'pale brown stone','quoin '+str((side,j+1)))
    block(b,-1.12,1.12,0,.27,HEAD,2.24,'dark aggregate','upper spandrel')
    block(b,-1.12,1.12,-.051,.27,0,SILL,'sill','continuous sill band')
    pebbles(b,lod)
    for side in (-1,1):
        c=side*(HALF-.023);block(b,c-.022,c+.022,.048,.155,SILL,HEAD,'sash','outside sash '+str(side))
    for z in [SILL+.035,TRANSOM,HEAD-.036]:
        block(b,-HALF,HALF,.048,.147,z-.035,z+.035,'sash','horizontal sash '+str(z))
    block(b,-.027,.027,.062,.14,SILL,TRANSOM,'sash','two casement meeting stiles')
    block(b,-HALF+.035,HALF-.035,.151,.158,TRANSOM+.032,HEAD-.035,'top glass','recessed top light')
    for side in (-1,1):
        c=side*.366;block(b,c-.331,c+.331,.151,.158,SILL+.036,TRANSOM-.035,'lower glass','glazed casement '+str(side));leaf(b,c,lod,'casement '+str(side))
    for x in (-.34,0.,.34):
        stroke(b,[(x,.084,TRANSOM+.04),(x,.084,HEAD-.04)],.009,'upright between top loops '+str(x),lod)
    for i in range(4):
        c=(i-1.5)*.34;bot=TRANSOM+.045;top=HEAD-.065
        for side in (-1,1):
            pts=[(c+side*.015,.071,bot),(c+side*.114,.071,bot+.15),(c+side*.125,.071,top-.18),(c+side*.049,.071,top-.07),(c+side*.035,.071,top)]
            stroke(b,pts,.007,'transom bent bar '+str((i,side)),lod)
