"""Unwrapped arc coordinates for the Art Deco entrance on the corner of Beijing and Guizhou roads."""
from math import ceil, cos, pi, radians, sin
from shapely import affinity


def linear_color(rgb):
    def component(c):
        c=c/255.
        return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
    return [component(c) for c in rgb]


def finish(rgb,roughness,metal=0.):
    return dict(color=linear_color(rgb),roughness=roughness,metallic=metal)


class Corner:
    """u runs along the street wall, depth is positive towards the pavement, Z is height."""
    def __init__(self,builder,radius,detail,center=(0.,0.),bearing_delta=0.):
        self.b=builder
        self.radius=radius
        self.center=center
        self.axis_angle=radians(bearing_delta)
        self.spacing=.21 if detail else .57
        self.detail=detail

    def point(self,u,depth,z):
        a=u/self.radius+self.axis_angle
        return (self.center[0]+(self.radius+depth)*sin(a),self.center[1]+(self.radius+depth)*cos(a),z)

    def tangent(self,u,x,depth,z):
        a=u/self.radius+self.axis_angle
        cx,cy,_=self.point(u,depth,z)
        return (cx+cos(a)*x,cy-sin(a)*x,z)

    def strip(self,name,material,a,b,inside,outside,lo,hi):
        """One closed curved solid with shared segments and a variable top or lower edge."""
        assert b>a,(name,a,b)
        count=max(1,ceil((b-a)/self.spacing))
        vertices=[];faces=[]
        for i in range(count+1):
            u=a+(b-a)*i/count
            low=lo(u) if callable(lo) else lo
            high=hi(u) if callable(hi) else hi
            back=inside(u) if callable(inside) else inside
            face=outside(u) if callable(outside) else outside
            assert high>low and face>back,(name,u,low,high,back,face)
            vertices.extend([self.point(u,back,low),self.point(u,face,low),
                             self.point(u,back,high),self.point(u,face,high)])
            if i:
                j=(i-1)*4
                faces.extend([(j,j+1,j+5,j+4),(j+2,j+6,j+7,j+3),
                              (j,j+4,j+6,j+2),(j+1,j+3,j+7,j+5)])
        j=4*count
        faces.extend([(0,2,3,1),(j,j+1,j+3,j+2)])
        self.b.add(vertices,faces,material,name)

    def flat(self,name,material,u,a,b,inside,outside,lo,hi):
        """A planar rectangular part tangent to the curved wall at u."""
        assert a<b and inside<outside and lo<hi,name
        vertices=[self.tangent(u,x,y,z) for z in (lo,hi) for x,y in
                  [(a,inside),(b,inside),(b,outside),(a,outside)]]
        self.b.add(vertices,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material,name)

    def post(self,name,material,u,depth,lower,upper,radius):
        x,y,_=self.point(u,depth,lower)
        sides=32 if self.detail else 14
        vertices=[(x+radius*cos(2*pi*i/sides),y+radius*sin(2*pi*i/sides),h)
                  for h in (lower,upper)for i in range(sides)]
        faces=[tuple(reversed(range(sides))),tuple(range(sides,2*sides))]
        faces += [(i,(i+1)%sides,(i+1)%sides+sides,i+sides)for i in range(sides)]
        self.b.add(vertices,faces,material,name)

    def glyph(self,name,material,u,depth,z,shape,thickness):
        # The observer stands at positive Y. Flip the font's reading axis and
        # keep the brass face slightly in front of its letter's mounting face.
        mapped=affinity.scale(shape,xfact=-1.,yfact=1.,origin=(0,0))
        def project(sx,sz,back):
            return self.tangent(u,sx,depth-back,z+sz)
        self.b.prism(mapped,-thickness,0.,project,material,name)


class StreetCorner(Corner):
    """Continue along each survey tangent beyond the rounded intersection."""
    def __init__(self,builder,radius,detail,tangents):
        super().__init__(builder,radius,detail)
        self.tangents=tangents

    def tangent(self,u,x,depth,z):
        start=max(self.tangents[0],min(self.tangents[1],u))
        a=start/self.radius
        bx,by,_=Corner.point(self,start,depth,z)
        return (bx+(x+u-start)*cos(a),by-(x+u-start)*sin(a),z)

    def point(self,u,depth,z):
        return self.tangent(u,0.,depth,z)


class Masonry(StreetCorner):
    """The two measured end corners and six observed foyer axes bound the upper wall."""
    def __init__(self,builder,d,detail):
        super().__init__(builder,d['radius_m'],detail,d['tangent_stations_m'])
        self.stations=d['masonry_street_offsets_m']

    def setback(self,u):
        for (a,inside),(b,outside) in zip(self.stations,self.stations[1:]):
            if u<=b:
                return inside+(outside-inside)*max(0.,(u-a)/(b-a))
        return self.stations[-1][1]

    def tangent(self,u,x,depth,z):
        return super().tangent(u,x,depth+self.setback(u),z)


class FlatFrame(Corner):
    """A separately surveyed plane such as the doorway chord or the side-mounted sign."""
    def __init__(self,builder,detail,center,bearing_delta):
        self.b=builder
        self.detail=detail
        self.center=center
        self.axis_angle=radians(bearing_delta)

    def tangent(self,u,x,depth,z):
        a=self.axis_angle
        return (self.center[0]+(u+x)*cos(a)+depth*sin(a),
                self.center[1]-(u+x)*sin(a)+depth*cos(a),z)

    def point(self,u,depth,z):
        return self.tangent(u,0.,depth,z)
