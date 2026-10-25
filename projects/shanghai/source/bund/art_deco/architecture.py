"""Reusable solid architectural components. Blender axes: east, north, up.

Window openings are gaps between actual masonry pieces, with recessed glazing
and four-sided reveals; no decal or uniform window-grid texture is used.
"""
import math, random
import bpy
from mathutils import Vector

class Builder:
    def __init__(self,name):self.name=name;self.v=[];self.f=[];self.m=[];self.sm=[]
    def geom(self,v,f,m,smooth=False):
        k=len(self.v);self.v.extend([tuple(p) for p in v]);self.f.extend([tuple(k+i for i in face) for face in f]);self.m.extend([m]*len(f));self.sm.extend([smooth]*len(f))
    def box(self,c,s,m,basis=None):
        c=Vector(c);axes=basis or [Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))]
        v=[c+axes[0]*a*s[0]/2+axes[1]*b*s[1]/2+axes[2]*d*s[2]/2 for a,b,d in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        self.geom(v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],m)
    def rod(self,a,b,r,m,n=10):
        a=Vector(a);b=Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)))
        if u.length<.01:u=Vector((1,0,0))
        u.normalize();w=d.cross(u);v=[p+r*(math.cos(math.tau*i/n)*u+math.sin(math.tau*i/n)*w) for p in [a,b] for i in range(n)]
        f=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        self.geom(v,f,m,True)
    def frustum(self,c,z0,z1,lower,upper,m):
        x,y=c;a,b=lower[0]/2,lower[1]/2;c,d=upper[0]/2,upper[1]/2
        self.geom([(x-a,y-b,z0),(x+a,y-b,z0),(x+a,y+b,z0),(x-a,y+b,z0),(x-c,y-d,z1),(x+c,y-d,z1),(x+c,y+d,z1),(x-c,y+d,z1)],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],m)
    def ellipsoid(self,c,r,m,n=16,rings=10):
        verts=[]
        for j in range(rings+1):
            phi=math.pi*j/rings
            for i in range(n):
                a=math.tau*i/n;verts.append((c[0]+r[0]*math.sin(phi)*math.cos(a),c[1]+r[1]*math.sin(phi)*math.sin(a),c[2]+r[2]*math.cos(phi)))
        self.geom(verts,[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(rings) for i in range(n)],m,True)
    def finish(self,materials):
        # Small joint strips at the first course are clipped to ground zero.
        self.v=[(x,y,max(0,z)) for x,y,z in self.v]
        mesh=bpy.data.meshes.new(self.name);mesh.from_pydata(self.v,[],self.f);mesh.materials.clear()
        for mat in materials:mesh.materials.append(mat)
        mesh.update()
        for p,m,s in zip(mesh.polygons,self.m,self.sm):p.material_index=m;p.use_smooth=s
        obj=bpy.data.objects.new(self.name,mesh);bpy.context.collection.objects.link(obj);return obj

class Facade:
    def __init__(self,b,a,c,outward=None):
        self.b=b;self.a=Vector((*a,0));d=Vector((c[0]-a[0],c[1]-a[1],0));self.length=d.length;self.u=d.normalized();self.n=Vector(outward) if outward else Vector((self.u.y,-self.u.x,0));self.up=Vector((0,0,1))
    def p(self,u,z,d=0):return self.a+self.u*u+self.up*z+self.n*d
    def box(self,u,z,w,h,depth,m,d=0):
        # Five exposed faces; the back is embedded in the masonry or frame.
        v=[self.p(u+a*w/2,z+c*h/2,d-depth/2+n*depth/2) for a,n,c in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        faces=[(0,3,2,1),(4,5,6,7),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        if self.u.cross(self.n).dot(self.up)<0:faces=[tuple(reversed(f)) for f in faces]
        self.b.geom(v,faces,m)
    def flat(self,u,z,w,h,m,d=.006):
        v=[self.p(u-w/2,z-h/2,d),self.p(u+w/2,z-h/2,d),self.p(u+w/2,z+h/2,d),self.p(u-w/2,z+h/2,d)]
        face=(0,1,2,3) if self.u.cross(self.up).dot(self.n)>0 else (3,2,1,0)
        self.b.geom(v,[face],m)
    def panel(self,u0,u1,z0,z1,m,depth=.48,joints=False):
        if u1-u0<.001 or z1-z0<.001:return
        self.box((u0+u1)/2,(z0+z1)/2,u1-u0,z1-z0,depth,m)
        if joints and u1-u0>.4 and z1-z0>.4:
            # Mortar joints are geometry, restrained to masonry (never on glass).
            start=math.ceil(z0/.62)*.62
            for k in range(int((z1-start)/.62)+1):
                z=start+k*.62
                if z<z1-.02:self.flat((u0+u1)/2,z,u1-u0,.012,2,.004)
            for row in range(math.floor(z0/.62),math.ceil(z1/.62)):
                za=max(z0,row*.62);zb=min(z1,(row+1)*.62)
                for k in range(math.floor(u0/1.4)-1,math.ceil(u1/1.4)+1):
                    u=k*1.4+(row%2)*.7
                    if u0+.02<u<u1-.02:self.flat(u,(za+zb)/2,.012,zb-za,2,.004)
    def window(self,u,z,w,h,stone=0,frame=4,glass=5,trim=.12,mullions=1,deep=.34,sill=True):
        # Glass is behind the wall and surrounded by solid jamb/reveal pieces.
        self.flat(u,z,w,h,glass,-deep)
        for x in [u-w/2,u+w/2]:
            self.flat(x,z,trim,h+.12,stone,.04)
            self.b.geom([self.p(x,z-h/2,.04),self.p(x,z+h/2,.04),self.p(x,z+h/2,-deep),self.p(x,z-h/2,-deep)],[(0,1,2,3)],stone)
        for zz in [z-h/2,z+h/2]:
            self.flat(u,zz,w+.12,trim,stone,.04)
            self.b.geom([self.p(u-w/2,zz,.04),self.p(u+w/2,zz,.04),self.p(u+w/2,zz,-deep),self.p(u-w/2,zz,-deep)],[(0,1,2,3)],stone)
        for x in [u-w/2+.07,u+w/2-.07]:self.flat(x,z,.065,h,frame,-deep+.10)
        for zz in [z-h/2+.05,z+h/2-.05]:self.flat(u,zz,w,.065,frame,-deep+.10)
        for i in range(1,mullions+1):self.box(u-w/2+w*i/(mullions+1),z,.055,h,.065,frame,-deep+.1)
        self.box(u,z+h*.28,w,.055,.065,frame,-deep+.10)
        if sill:self.box(u,z-h/2-.12,w+.24,.13,.55,1,.22)
    def cell(self,u0,u1,z0,z1,ww,wh,m=0,window_m=5,center=None,joints=False,spandrel=None):
        u=(u0+u1)/2;z=(z0+z1)/2 if center is None else center
        self.panel(u0,u-ww/2,z0,z1,m,joints=joints);self.panel(u+ww/2,u1,z0,z1,m,joints=joints)
        self.panel(u-ww/2,u+ww/2,z0,z-wh/2,m,joints=joints);self.panel(u-ww/2,u+ww/2,z+wh/2,z1,m,joints=joints)
        self.window(u,z,ww,wh,m,glass=window_m)
        if spandrel is not None:
            self.flat(u,(z0+z-wh/2)/2,ww-.1,max(.1,z-wh/2-z0-.2),spandrel,.06)
    def arch(self,u,zbase,spring,r,top,cell0,cell1,m=0,glass=5,joints=True):
        self.panel(cell0,u-r,zbase,top,m,joints=joints);self.panel(u+r,cell1,zbase,top,m,joints=joints)
        self.panel(u-r,u+r,spring+r,top,m,joints=joints)
        # Curved masonry spandrel and deep inner arch reveal.
        seg=24
        for i in range(seg):
            x0=-r+2*r*i/seg;x1=-r+2*r*(i+1)/seg
            y0=math.sqrt(max(0,r*r-x0*x0));y1=math.sqrt(max(0,r*r-x1*x1))
            v=[self.p(u+x0,spring+y0),self.p(u+x1,spring+y1),self.p(u+x1,spring+r),self.p(u+x0,spring+r)]
            self.b.geom(v,[(0,1,2,3)],m)
            self.b.geom([self.p(u+x0,spring+y0,d) for d in [0,-.65]]+[self.p(u+x1,spring+y1,d) for d in [-.65,0]],[(0,1,2,3)],1)
        poly=[self.p(u-r,zbase,-.66),self.p(u+r,zbase,-.66)]+[self.p(u+r*math.cos(math.pi*i/24),spring+r*math.sin(math.pi*i/24),-.66) for i in range(25)]
        self.b.geom(poly,[tuple(range(len(poly)))],glass)
        for rr in [r-.05,r-.27]:
            for i in range(24):
                a=math.pi*i/24;b=math.pi*(i+1)/24
                v=[self.p(u+rad*math.cos(angle),spring+rad*math.sin(angle),depth) for depth in [-.40,-.46] for angle,rad in [(a,rr-.055),(b,rr-.055),(b,rr+.055),(a,rr+.055)]]
                self.b.geom(v,[(0,1,2,3),(0,4,5,1),(3,2,6,7)],4)
        for x in [-r*.65,-r*.3,0,r*.3,r*.65]:self.box(u+x,(zbase+spring)/2,.065,spring-zbase,.09,4,-.43)
        for zz in [zbase+.3,spring*.52,spring]:self.box(u,zz,2*r,.08,.09,4,-.43)
        for a in [math.pi*i/8 for i in range(1,8)]:self.b.rod(self.p(u,spring,-.42),self.p(u+(r-.3)*math.cos(a),spring+(r-.3)*math.sin(a),-.42),.035,4,6)
    def cornice(self,z,width=None,m=1):
        w=width or self.length
        for dz,h,d in [(-.25,.16,.18),(0,.24,.45),(.21,.13,.65)]:self.box(self.length/2,z+dz,w,h,d+.45,m,d)
    def oculus(self,u,z,r,cell0,cell1,z0,z1,m=9):
        self.panel(cell0,u-r,z0,z1,m);self.panel(u+r,cell1,z0,z1,m)
        self.panel(u-r,u+r,z0,z-r,m);self.panel(u-r,u+r,z+r,z1,m)
        for i in range(24):
            x0=-r+2*r*i/24;x1=-r+2*r*(i+1)/24
            a=math.sqrt(max(0,r*r-x0*x0));c=math.sqrt(max(0,r*r-x1*x1))
            for sign in [-1,1]:
                self.b.geom([self.p(u+x0,z+sign*a),self.p(u+x1,z+sign*c),self.p(u+x1,z+sign*r),self.p(u+x0,z+sign*r)],[(0,1,2,3)],m)
        self.b.geom([self.p(u+r*math.cos(math.tau*i/48),z+r*math.sin(math.tau*i/48),-.4) for i in range(48)],[tuple(range(48))],5)
        for i in range(48):
            a=math.tau*i/48;c=math.tau*(i+1)/48
            v=[self.p(u+rad*math.cos(t),z+rad*math.sin(t),depth) for depth in [.12,-.4] for t,rad in [(a,r-.08),(c,r-.08),(c,r+.16),(a,r+.16)]]
            self.b.geom(v,[(0,1,2,3),(0,4,5,1)],1)
        self.box(u,z,.055,r*2,.06,4,-.3)
    def railing(self,z,start=0,end=None,m=4):
        end=self.length if end is None else end
        for zz in [z+.15,z+.95]:self.b.rod(self.p(start,zz,.12),self.p(end,zz,.12),.04,m,6)
        for i in range(int((end-start)/.50)+1):
            u=start+i*.50;self.b.rod(self.p(u,z,.12),self.p(u,z+1,.12),.026,m,6)
    def pediment(self,u,z,w,h,m=7):
        self.b.geom([self.p(u-w/2,z,.28),self.p(u+w/2,z,.28),self.p(u,z+h,.28)],[(0,1,2)],m)
        for a,b in [((u-w/2,z),(u,z+h)),((u,z+h),(u+w/2,z))]:self.b.rod(self.p(*a,.35),self.p(*b,.35),.10,1,8)
        self.box(u,z,w+.2,.14,.36,1,.35)
    def crest(self,u,z,w=1.3,h=1.8):
        points=[(-.5,.5),(.5,.5),(.45,-.25),(0,-.5),(-.45,-.25)]
        self.b.geom([self.p(u+x*w,z+y*h,.32) for x,y in points],[tuple(range(5))],1)
        for sign in [-1,1]:
            prev=None
            for i in range(35):
                a=i/34*math.pi*3;r=.48*(1-i/45)
                p=self.p(u+sign*(w*.68+r*math.cos(a)),z+r*math.sin(a),.22)
                if prev is not None:self.b.rod(prev,p,.055,1,6)
                prev=p

def perimeter(b,poly):
    area=sum(a[0]*c[1]-c[0]*a[1] for a,c in zip(poly,poly[1:]+poly[:1]))
    result=[]
    for a,c in zip(poly,poly[1:]+poly[:1]):
        f=Facade(b,a,c)
        if area<0:f.n=-f.n
        result.append(f)
    return result

def roof(b,triangles,z,m=8):
    for t in triangles:b.geom([(x,y,z) for x,y in t],[(0,1,2)],m)

def flag(b,c,height=4,m=10):
    x,y,z=c;b.rod(c,(x,y,z+height),.045,4,12)
    def cloth(u,v,offset=0):return (x+.08+u,y+.16*math.sin(u*2.6)+.055*u+offset,z+height-.1-v-.08*u)
    verts=[cloth(2.25*i/8,1.5*j/4) for i in range(9) for j in range(5)]
    b.geom(verts,[(i*5+j,(i+1)*5+j,(i+1)*5+j+1,i*5+j+1) for i in range(8) for j in range(4)],m)
    for u,v,r in [(.38,.38,.20),(.77,.16,.067),(.91,.33,.067),(.91,.55,.067),(.76,.74,.067)]:
        star=[cloth(u+math.sin(math.pi*k/5)*(r if k%2==0 else r*.40),v-math.cos(math.pi*k/5)*(r if k%2==0 else r*.40),-.012) for k in range(10)]
        b.geom(star,[tuple(range(10))],13)

def make_materials():
    specs=[('Warm granite masonry',(.54,.455,.335),0,.83),('Carved pale stone',(.66,.58,.44),0,.74),('Fine stone joints',(.36,.31,.245),0,.95),('Dark interior recess',(.033,.041,.038),0,.97),('Aged bronze frames',(.13,.145,.13),.62,.34),('Blue grey recessed glass',(.13,.23,.265),.36,.20),('Patinated copper',(.12,.24,.19),.55,.54),('Warm red terracotta',(.43,.22,.16),0,.78),('Roof gravel',(.28,.29,.275),0,.96),('Pale brick infill',(.66,.635,.54),0,.90),('Flag red',(.64,.025,.035),0,.8),('Brick joint',(.43,.38,.32),0,.95),('Bank bronze spandrel',(.16,.19,.16),.4,.55),('Warm metal lettering',(.65,.48,.17),.58,.34),('Recessed Art Deco stone panels',(.40,.295,.18),0,.85)]
    mats=[]
    for name,color,metal,rough in specs:
        mat=bpy.data.materials.new(name);mat.diffuse_color=(*color,1);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough;mats.append(mat)
    return mats
