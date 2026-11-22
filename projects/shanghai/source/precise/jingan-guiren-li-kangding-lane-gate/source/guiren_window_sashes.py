"""Five timber street windows flanking the Guiren Li covered passage.

X points southwest along the street (right in the frontal view), Y points
inside the building and Z is the height above the street. All inputs are metres.
"""
from collections import defaultdict
from pathlib import Path
from math import cos,radians,sin

WOOD='Guiren windows | red-brown painted joinery'
LIP='Guiren windows | slim painted glazing beads'
BLUE='Guiren windows | cool reflected glass'
DARK='Guiren windows | shaded glass'
FROST='Guiren windows | grey-green lower glass'
GUARD='Guiren windows | dark red grille'
LIGHT_GUARD='Guiren windows | pale inner guard'
RETURN='Guiren windows | shaded timber reveal'

def finish(rgb,roughness,metallic=0.):
    def linear(channel):
        c=channel/255.
        return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
    return dict(color=[linear(c) for c in rgb],roughness=roughness,metallic=metallic)

PALETTE={WOOD:finish((100,47,43),.64),LIP:finish((94,46,42),.71),
         DARK:finish((71,69,60),.26,.12),BLUE:finish((93,124,139),.22,.16),
         FROST:finish((90,96,81),.35,.08),GUARD:finish((101,64,57),.65,.16),
         LIGHT_GUARD:finish((163,165,144),.7,.16),RETURN:finish((65,43,38),.73)}
for material in (BLUE,DARK,FROST):
    PALETTE[material]['texture']=str(Path(__file__).with_name('guiren-window-glass.png'))

FACES=((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))


def fixed(x,y,z):return x,y,z


def swing(hinge,front,degrees):
    c,s=cos(radians(degrees)),sin(radians(degrees))
    def rotate(x,y,z):
        u,v=x-hinge,y-front
        return hinge+c*u+s*v,front-s*u+c*v,z
    return rotate


class Joinery:
    def __init__(self,builder,label):
        self.builder,self.label=builder,label
        self.parts=defaultdict(lambda:([],[],[]))

    def bar(self,part,mat,x0,x1,y0,y1,z0,z1,turn=fixed):
        if x1<=x0 or y1<=y0 or z1<=z0:
            raise ValueError(f'Collapsed Guiren Li joinery in {part}')
        verts,faces,uv=self.parts[part,mat];o=len(verts)
        for x,y,z in ((x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
                      (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)):
            verts.append(turn(x,y,z))
            uv.append((x-x0+.61*(y-y0),z-z0+.33*(y-y0)))
        faces.extend(tuple(o+k for k in f) for f in FACES)

    def frame(self,name,mat,l,r,z,t,y,depth,w,turn=fixed):
        self.bar(name,mat,l,l+w,y,y+depth,z,t,turn)
        self.bar(name,mat,r-w,r,y,y+depth,z,t,turn)
        self.bar(name,mat,l+w,r-w,y,y+depth,z,z+w,turn)
        self.bar(name,mat,l+w,r-w,y,y+depth,t-w,t,turn)

    def glazing(self,name,mat,l,r,z,t,y,nx,nz,coarse,turn=fixed):
        stile=min(.043,(r-l)*.075,(t-z)*.075)
        self.frame(name,WOOD,l,r,z,t,y,.045,stile,turn)
        x0,x1,z0,z1=l+stile,r-stile,z+stile,t-stile
        h=min(.011,(x1-x0)/nx*.070,(z1-z0)/nz*.070)
        xx=[x0+(x1-x0)*i/nx for i in range(nx+1)]
        zz=[z0+(z1-z0)*i/nz for i in range(nz+1)]
        for x in xx[1:-1]:self.bar(name,LIP,x-h,x+h,y+.009,y+.037,z0,z1,turn)
        for a,b in zip(xx,xx[1:]):
            a+=h if a!=x0 else 0;b-=h if b!=x1 else 0
            for v in zz[1:-1]:
                self.bar(name,LIP,a,b,y+.009,y+.037,v-h,v+h,turn)
        if coarse:
            self.bar(name+' glass',mat,x0,x1,y+.038,y+.045,z0,z1,turn)
        else:
            for j in range(nz):
                for i in range(nx):
                    a=xx[i]+(h if i else 0);b=xx[i+1]-(h if i<nx-1 else 0)
                    u=zz[j]+(h if j else 0);v=zz[j+1]-(h if j<nz-1 else 0)
                    self.bar(name+' glass',mat,a,b,y+.029,y+.035,u,v,turn)

    def emit(self):
        for (name,mat),(v,f,uv) in self.parts.items():
            self.builder.add(v,f,mat,self.label+' | '+name)
            self.builder.parts[-1]['texcoords']=uv


def add_window(builder,lod,kind,x0,x1,z0,z1,front_y=0.,*,transom_ends=None,transom_z=None):
    """Install joinery in one net opening. front_y denotes its front frame plane.

    For the projecting six-light window, transom_ends can span the two rendered
    side panels. In that case x0/x1 enclose the lower glazed part only and the
    top light crosses the side panels directly above it. The caller cuts wall holes.
    """
    if min(x1-x0,z1-z0)<.25:raise ValueError('Window below admissible clear size')
    g=Joinery(builder,'Guiren Li | '+kind)
    coarse=lod is True or lod=='lod'
    frame=min(.059,(x1-x0)*.052,(z1-z0)*.046)
    l,r=x0+frame,x1-frame;bottom,top=z0+frame,z1-frame
    y=front_y+.013;mid=(l+r)/2
    if kind=='right_upper':
        z=transom_z if transom_z is not None else z0+.804*(z1-z0)
        tx0,tx1=(x0,x1) if transom_ends is None else transom_ends
        if not tx0<=x0<x1<=tx1 or not z0+.18<z<z1-.12:raise ValueError('Transom is outside the projecting window')
        g.frame('lower fixed frame',WOOD,x0,x1,z0,z,front_y,.091,frame)
        g.frame('continuous upper light fixed frame',WOOD,tx0,tx1,z,z1,front_y,.091,frame)
        units=6
        # Lower parts are six tall, single-column sashes, each with three rails.
        for j in range(units):
            a=l+(r-l)*j/units;b=l+(r-l)*(j+1)/units
            g.glazing('projecting bay lower sash '+str(j+1),BLUE,a,b,bottom,z-frame,y,1,4,coarse)
        # Continue the upper dividers in register with the six long sashes.
        step=(r-l)/6
        outer_l,outer_r=tx0+frame,tx1-frame
        inner=[l+(r-l)*j/6 for j in range(7)]
        limits=[outer_l,*[x for x in inner if outer_l+.08<x<outer_r-.08],outer_r]
        if outer_l+.08<l:
            count=max(1,round((l-outer_l)/step))
            limits.extend(outer_l+(l-outer_l)*i/count for i in range(1,count))
        if r<outer_r-.08:
            count=max(1,round((outer_r-r)/step))
            limits.extend(r+(outer_r-r)*i/count for i in range(1,count))
        limits=sorted(set(limits))
        for j,(a,b) in enumerate(zip(limits,limits[1:])):
            g.glazing('upper band '+str(j+1),DARK,a,b,z+frame,top,y,1,1,coarse)
    elif kind=='gate_upper':
        g.frame('fixed outer frame',WOOD,x0,x1,z0,z1,front_y,.093,frame)
        # In the 2020 winter view the left leaf is outside the street plane.
        # The 2013 and Gao exposures record the same pair in the closed position.
        # The two timber leaves sit behind the street opening. Eight measured
        # corners in the 2020 photograph fix their proportions inside that opening.
        span,height=x1-x0,z1-z0
        hinge=x0+.140*span
        leaf_width=.381*span
        meeting=hinge+leaf_width
        right=meeting+leaf_width
        sill=z0+.064*height
        head=z1-.061*height
        back=front_y+.130
        # Return boards bridge the frame and the timber rebate; the centre is clear.
        g.bar('recessed left jamb',RETURN,l,hinge,front_y+.074,back,sill,head)
        g.bar('recessed right jamb',RETURN,right,r,front_y+.074,back,sill,head)
        g.bar('recessed sill lining',RETURN,l,r,front_y+.074,back,bottom,sill)
        g.bar('recessed head lining',RETURN,l,r,front_y+.074,back,head,top)
        g.glazing('left outward casement',DARK,hinge,meeting-.002,sill,head,back,
                  2,4,coarse,swing(hinge,back,124.))
        g.glazing('right closed casement',BLUE,meeting+.002,right,sill,head,back,2,4,coarse)
    elif kind in ('left_upper','left_lower'):
        g.frame('fixed outer frame',WOOD,x0,x1,z0,z1,front_y,.093,frame)
        z=z0+.344*(z1-z0);rail=min(.064,(z1-z0)*.042)
        glass=DARK if kind=='left_upper' else FROST
        inner_y=y if kind=='left_upper' else y+.057
        g.bar('fixed low cross rail',WOOD,l,r,inner_y,inner_y+.066,z-rail/2,z+rail/2)
        for j,(a,b) in enumerate(((l,mid),(mid,r))):
            g.glazing('upper sash '+str(j+1),glass,a,b,z+rail/2,top,inner_y+.008,
                      2 if kind=='left_upper' else 1,3 if kind=='left_upper' else 1,coarse)
            g.glazing('lower light '+str(j+1),glass,a,b,bottom,z-rail/2,inner_y+.008,
                      2 if kind=='left_upper' else 1,2 if kind=='left_upper' else 1,coarse)
        if kind=='left_lower':
            for j,t in enumerate((.109,.230,.462,.575,.681,.786,.891)):
                v=z0+(z1-z0)*t
                g.bar('horizontal grille '+str(j+1),GUARD,l,r,y-.022,y+.010,v-.014,v+.014)
    elif kind=='right_lower':
        g.frame('fixed outer frame',WOOD,x0,x1,z0,z1,front_y,.082,frame)
        for j,(f0,f1) in enumerate(zip((0,.18,.45,.725),(.18,.45,.725,1))):
            a=l+(r-l)*f0;b=l+(r-l)*f1
            g.glazing('lower street sash '+str(j+1),FROST,a,b,bottom,top,y,1,3,coarse)
            # Thin pale rods lie behind the dark horizontal timber rails.
            for k in (1,2):
                rod=a+(b-a)*k/3
                g.bar('inner pale rods '+str(j+1),LIGHT_GUARD,rod-.006,rod+.006,y+.022,y+.028,bottom+.043,top-.043)
    else:raise ValueError('Unrecognised Guiren Li window group: '+str(kind))
    g.emit()


# The figure above the third opening is part of the masonry model. Its
# two visible side panels are opaque beneath the continuous upper band.
STREET_OPENINGS={
    'left_lower':(-4.55,-3.41,1.12,2.82,0.),
    'left_upper':(-4.58,-3.45,4.66,6.29,0.),
    'gate_upper':(-.68,.79,5.13,6.84,0.),
    'right_upper':(3.13,5.57,4.90,6.99,-.89),
    'right_lower':(3.63,5.35,1.74,3.03,-.13),
}
BRIGHT_TRANSOM={'transom_ends':(2.45,6.35),'transom_z':6.48}


def add_windows(builder,lod):
    for kind,bounds in STREET_OPENINGS.items():
        options=BRIGHT_TRANSOM if kind=='right_upper' else {}
        add_window(builder,lod,kind,*bounds,**options)
