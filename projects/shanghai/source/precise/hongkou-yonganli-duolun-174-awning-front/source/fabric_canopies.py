"""Build the cloth over the paired timber casements of the Duolun Road frontage."""
import math
import numpy as np

CANVAS='Weathered grey canvas'
STRIPE='Pale woven stripe'
LINING='Grey canvas underside'
PIPE='Pale sewn piping'
IRON='Painted ironwork'
CORD='Dark awning stays'


def bonnet(f,u,rim_z,width,reach,rise,lod):
    # A Dutch hood is cylindrical across its middle and rounds back towards
    # the wall at the two ends. Its cloth is divided by narrow woven stripes.
    bands=12 if width<1.8 else 19
    station=[-.5]
    for i in range(bands):
        middle=(i+.5)/bands-.5
        station.extend((middle-.046/bands,middle+.046/bands))
    station.append(.5)
    levels=np.linspace(0,math.pi/2,9 if lod else 17)

    def profile(s,theta):
        # In the two cheeks the radial sections meet the hinged side frame.
        q=abs(2*s);cap=min(1.,max(0.,(q-.62)/.38))
        taper=math.sqrt(max(.026,1-cap*cap))
        x=u+s*width
        z=rim_z+(rise*math.cos(theta))*taper-.028*cap
        depth=.061+reach*math.sin(theta)*taper
        return x,z,depth

    for j,(a,b)in enumerate(zip(station,station[1:])):
        mat=STRIPE if j%2 else CANVAS
        v=[];faces=[]
        for theta in levels:
            for s in (a,b):v.append(f.point(*profile(s,theta)))
        for k in range(len(levels)-1):
            i=2*k
            faces.extend(((i,i+3,i+1),(i,i+2,i+3)))
        # Both exteriors and undersides have their own physical surface.
        count=len(v);v.extend((np.asarray(pt)+np.array([.006,0.,-.009])) for pt in v[:count])
        faces+= [tuple(i+count for i in reversed(face))for face in faces[:]]
        f.builder.add(v,faces,mat,f.label+'/Striped awning cloth')

    # A continuous wavy valance hangs from the forward edge. Its bottom is
    # cut into shallow scallops, one per fabric gore.
    divisions=bands*(4 if lod else 9);v=[];faces=[]
    for i in range(divisions+1):
        s=i/divisions-.5;x,z,d=profile(s,math.pi/2)
        hem=.060+.045*(1-math.cos(2*math.pi*bands*i/divisions))/2
        v.extend((f.point(x,z+.007,d+.002),f.point(x,z-hem,d+.007),
                  f.point(x,z-hem,d-.004),f.point(x,z+.007,d-.007)))
    for i in range(divisions):
        k=4*i;faces.extend((k+j,k+j+4,k+4+(j+1)%4,k+(j+1)%4)for j in range(4))
    faces.extend(((3,2,1,0),tuple(range(4*divisions,4*divisions+4))))
    f.builder.add(v,faces,CANVAS,f.label+'/Scalloped cloth valance')
    if not lod:
        # The frontal hem and the end frames remain visible from below.
        f.builder.tube([f.point(*profile(s,math.pi/2))for s in np.linspace(-.5,.5,33)],.013,PIPE,6,f.label+'/Awning front piping')
        for s in np.linspace(-.42,.42,5):
            pts=[]
            for a in levels:
                x,z,d=profile(s,a);pts.append(f.point(x,z-.024,d-.014))
            f.builder.tube(pts,.012,IRON,6,f.label+'/Folding hood ribs')
    for side in (-1,1):
        x=u+side*width*.475
        f.builder.tube([f.point(x,rim_z-.17,.058),f.point(x,rim_z-.02,reach*.69)],.018,IRON,6,f.label+'/Hood hinge arms')


def slatted_box(f,u,bottom,width,depth,lod):
    h=.44*width;edge=.043
    # These open guard boxes sit below selected windows on individual brackets.
    # A clear gap separates the boxes of the neighbouring homes.
    for side in (-1,1):
        for d in (.08,depth):
            f.box(u+side*(width-edge)/2,bottom+h/2,edge,h,edge,d,IRON,'Guard box corner uprights')
        f.box(u+side*(width-edge)/2,bottom,edge,edge,depth,depth/2,IRON,'Guard box underside rails')
        f.builder.tube([f.point(u+side*(width-.12)/2,bottom-.20,.033),
                        f.point(u+side*(width-.12)/2,bottom-.011,depth*.76)],.017,IRON,6,f.label+'/Individual box brackets')
    for z in (bottom+.012,bottom+h-.012):
        f.box(u,z,width,.037,.044,depth,IRON,'Guard box binding')
    for z in np.linspace(bottom+.07,bottom+h-.07,5):
        f.box(u,z,width-.07,.036,.045,depth,PIPE,'Spaced horizontal slats')
        for sign in (-1,1):
            f.box(u+sign*(width-.035)/2,z,.032,.036,depth-.07,(depth+.08)/2,PIPE,'Guard box side slats')
