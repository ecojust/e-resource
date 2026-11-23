"""The stepped cornice and three egg-and-dart runs on the portal at 222 Shaanxi South Road, No. 20."""
from math import cos, pi, sin

import numpy as np

STONE = 'Shaanxi 222-20 | dark grey cornice stone'
RELIEF = 'Shaanxi 222-20 | projecting egg and tongue moulding'
EDGE = 'Shaanxi 222-20 | weathered cornice edge'
PLINTH = 'Shaanxi 222-20 | shaded moulding ground'


def finish(rgb, roughness):
    def linear(v):
        v=v/255
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return {'color':[linear(v) for v in rgb], 'roughness':roughness}


PALETTE={STONE:finish((77,80,85),.90),RELIEF:finish((83,85,88),.86),
         EDGE:finish((101,103,103),.88),
         PLINTH:finish((63,65,69),.93)}
DEFAULT={'center_x':.055,'cornice_width':3.87,'overhang':.32,
         'head_outer_x':1.635,'head_inner_x':.908,
         'outer_center_offset':-.015,'inner_center_offset':-.062,
         'head_projection':.24,'centre_projection':.13,'bottom_z':3.25,'top_z':4.00}
NAME='No. 20 entrance | '


def _profile(builder, centre, rings, material, label):
    """Loft the photographed changes of fascia width and front projection around the wall return."""
    vertices=[]
    for half,projection,z in rings:
        vertices.extend([(centre-half,-projection,z),(centre+half,-projection,z),
                         (centre+half,.016,z),(centre-half,.016,z)])
    faces=[(3,2,1,0)]
    for i in range(len(rings)-1):
        for j in range(4):
            k=(j+1)%4
            faces.append((4*i+j,4*i+k,4*i+4+k,4*i+4+j))
    faces.append(tuple(range(len(vertices)-4,len(vertices))))
    builder.add(vertices,faces,material,NAME+label)


def _closed(builder,vertices,faces,material,label):
    q=np.asarray(vertices)-vertices[0]
    volume=sum(q[f[0]]@np.cross(q[f[i]],q[f[i+1]]) for f in faces for i in range(1,len(f)-1))
    if volume<0:
        faces=[tuple(reversed(f)) for f in faces]
    builder.add(vertices,faces,material,NAME+label)


class Band:
    def __init__(self,b,begin,end,direction,normal,ground,top,bottom,lod,title):
        self.b=b
        self.begin,self.end=begin,end
        self.t=np.asarray(direction)
        self.n=np.asarray(normal)
        self.ground=np.asarray(ground)
        self.top,self.bottom=top,bottom
        self.height=top-bottom
        self.lod,self.title=lod,title

    def point(self,u,z,depth):
        q=self.ground+u*self.t+depth*self.n
        return (q[0],q[1],z)

    def egg(self, u, pitch, worn=False):
        # A softly rounded egg with its widest shoulder above the midpoint and a
        # narrow toe. Its back sits in the actual recessed moulding bed.
        n=9 if self.lod else 16
        h=self.height*(.74 if worn else .79)
        mid_z=self.bottom+self.height*.59
        rx=.300*pitch
        peak=.105*self.height if worn else .137*self.height
        vertices=[self.point(u,mid_z-h/2,-.001)]
        rings=5 if self.lod else 9
        for i in range(1,rings):
            phase=pi*i/rings
            z=mid_z-.5*h*cos(phase)
            shoulder=sin(phase)*(.84-.16*cos(phase))
            for j in range(n):
                angle=2*pi*j/n
                d=(.004+peak*shoulder*sin(angle)) if sin(angle)>0 else .004+.008*shoulder*sin(angle)
                vertices.append(self.point(u+rx*shoulder*cos(angle),z,d))
        vertices.append(self.point(u,mid_z+h/2,-.001))
        faces=[]
        for j in range(n):
            k=(j+1)%n
            faces.append((0,j+1,k+1))
            for i in range(rings-2):
                a=1+i*n
                faces.append((a+j,a+n+j,a+n+k,a+k))
            last=1+(rings-2)*n
            faces.append((last+j,len(vertices)-1,last+k))
        _closed(self.b,vertices,faces,RELIEF,self.title+' | raised eggs')

    def cup(self,u,pitch):
        # Each egg is held in an open U-shaped cup, with separate lips, visible
        # in the central dark band even where the egg face is in shadow.
        h=self.height
        path=[(-.385,.95),(-.380,.70),(-.369,.43),(-.336,.277),(-.270,.177),(-.153,.114),
              (0,.092),(.153,.114),(.270,.177),(.336,.277),(.369,.43),(.380,.70),(.385,.95)]
        if self.lod:
            path=path[::2]
        p=np.array([(u+x*pitch,self.bottom+h*y) for x,y in path])
        prev,after=np.roll(p,1,axis=0),np.roll(p,-1,axis=0)
        prev[0],after[-1]=p[0],p[-1]
        t=after-prev
        t/=np.linalg.norm(t,axis=1)[:,None]
        across=np.stack([-t[:,1],t[:,0]],axis=-1)
        vs=[]
        for centre,cross in zip(p,across):
            for width,depth in ((-1,-.001),(-1,.009),(0,.0145),(1,.009),(1,-.001)):
                x,z=centre+cross*width*pitch*.042
                vs.append(self.point(x,z,depth))
        n=5;faces=[tuple(reversed(range(n)))]
        for i in range(len(p)-1):
            for j in range(n):
                k=(j+1)%n
                faces.append((i*n+j,i*n+k,(i+1)*n+k,(i+1)*n+j))
        faces.append(tuple(range(len(vs)-n,len(vs))))
        _closed(self.b,vs,faces,RELIEF,self.title+' | rolled egg cups')

    def tongue(self,u,pitch):
        # The slender point separates neighbouring cups. Its two cast faces
        # meet at a small ridge instead of filling the gap with a rectangular dentil.
        h=self.height
        outline=[(-.058,.96),(.058,.96),(.043,.48),(.016,.23),(0,.15),(-.018,.23),(-.043,.48)]
        front=[self.point(u+x*pitch,self.bottom+y*h,.004)for x,y in outline]
        rear=[self.point(u+x*pitch,self.bottom+y*h,-.001)for x,y in outline]
        vertices=front+rear+[self.point(u,self.bottom+.62*h,.015)]
        n=len(outline);faces=[tuple(reversed(range(n,2*n)))]
        for j in range(n):
            k=(j+1)%n
            faces+= [(j,k,2*n),(j,j+n,k+n,k)]
        _closed(self.b,vertices,faces,RELIEF,self.title+' | separating tongues')

    def run(self,count,weathered_end=False):
        pitch=(self.end-self.begin)/count
        for i in range(count):
            u=self.begin+(i+.5)*pitch
            self.egg(u,pitch,weathered_end and i==0)
            self.cup(u,pitch)
            if i+1<count:
                self.tongue(u+pitch/2,pitch)


def add_frieze(builder,lod=False,layout=None):
    o=dict(DEFAULT)
    o.update(layout or {})
    # Elevations are interpolated inside the registered lower and upper lines.
    z=lambda t:o['bottom_z']+(o['top_z']-o['bottom_z'])*t
    outer,inner=o['head_outer_x'],o['head_inner_x']
    cx=o['center_x']
    outer_centre=cx+o['outer_center_offset']
    inner_centre=cx+o['inner_center_offset']
    left_outer,right_outer=outer_centre-outer,outer_centre+outer
    left_inner,right_inner=inner_centre-inner,inner_centre+inner
    lip=o['cornice_width']/2
    top=o['overhang']
    hp,cp=o['head_projection'],o['centre_projection']
    if not (0<inner<outer<lip and 0<cp<hp<top and z(1)>z(0)):
        raise ValueError('The centre must recess between the two projecting heads and the upper coping')
    # The full-width fascia and the three-piece underside read independently
    # in both Gao Can photographs. Width/projection changes carry round the ends.
    _profile(builder,cx,[(outer+.010,cp+.023,z(.486)),(outer+.017,hp+.012,z(.503)),
                        (outer+.023,hp+.020,z(.534)),(outer+.026,hp+.022,z(.572)),
                        (outer+.048,hp+.027,z(.593)),(outer+.050,hp+.030,z(.618)),
                        (outer+.063,hp+.050,z(.643)),(outer+.092,hp+.066,z(.679)),
                        (lip-.021,top-.020,z(.785)),(lip-.012,top-.013,z(.834)),
                        (lip-.011,top-.012,z(.924)),(lip-.006,top-.007,z(.936))],
             STONE,'broad continuous cornice fascia and cove')
    _profile(builder,cx,[(lip-.008,top-.009,z(.935)),(lip-.003,top-.004,z(.954)),
                        (lip,top,z(.975)),(lip,top,z(1.))],EDGE,'upper worn projecting rim')
    for label,left,right,projection,count in [('left head',left_outer,left_inner,hp,5),
                                               ('central recessed frieze',left_inner,right_inner,cp,13),
                                               ('right head',right_inner,right_outer,hp,6)]:
        # The far left of the wider 07 frame has a weathered half-visible egg;
        # a sixth extrapolated egg would lie outside the silhouette of its bed.
        central=label=='central recessed frieze'
        relief_low=z(.220 if central else .247)
        relief_high=z(.492 if central else .503)
        centre=(left+right)/2; half=(right-left)/2
        _profile(builder,centre,[(half-.011,projection-.012,z(.172)),(half,projection,z(.219)),
                                  (half,projection,relief_high)],PLINTH,label+' | bed of the relief')
        _profile(builder,centre,[(half-.038,projection-.058,z(0.)),(half-.036,projection-.054,z(.072)),
                                 (half-.019,projection-.031,z(.100)),(half-.012,projection-.023,z(.123)),
                                 (half-.008,projection-.016,z(.147)),(half+.004,projection+.005,z(.163)),
                                 (half+.004,projection+.005,z(.188)),(half,projection,z(.219))],
                 STONE,label+' | stepped lower moulding')
        band=Band(builder,left+(.062 if central else .008),right-.008,(1.,0.),(0.,-1.),(0.,-projection),relief_high,relief_low,lod,label)
        band.run(count,weathered_end=label=='left head')
    # The camera sees a narrow oblique continuation round both inner projecting
    # heads; an entire invented extra egg row would exceed these short faces.
    for sign,label in [(-1,'left head inner return'),(1,'right head inner return')]:
        inward=np.array([-sign,0.]); start=-hp; end=-cp
        turn=Band(builder,start,end,(0.,1.),inward,(inner_centre+sign*inner,0),relief_high,relief_low,lod,label)
        turn.run(1)
