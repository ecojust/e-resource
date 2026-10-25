"""Batched geometry utilities; Blender coordinates are east/north/up."""
import bpy, math
from mathutils import Vector
class Builder:
    def __init__(self):
        self.vertices=[]; self.faces=[]; self.indices=[]; self.smooth=[]
    def geom(self, verts, faces, mat, smooth=False):
        n=len(self.vertices); self.vertices.extend([tuple(v) for v in verts])
        self.faces.extend([tuple(n+i for i in f) for f in faces])
        self.indices.extend([mat]*len(faces));self.smooth.extend([smooth]*len(faces))
    def box(self,center,size,mat,basis=None):
        c=Vector(center);axes=basis or [Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))]
        verts=[c+axes[0]*a*size[0]/2+axes[1]*b*size[1]/2+axes[2]*d*size[2]/2
               for a,b,d in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        self.geom(verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    def cylinder(self,center,radius,depth,mat,segments=48,axis=(0,0,1)):
        c=Vector(center);n=Vector(axis).normalized();u=n.cross(Vector((0,0,1)))
        if u.length<.01:u=Vector((1,0,0))
        u.normalize();v=n.cross(u);verts=[]
        for sign in [-1,1]:
            for i in range(segments):
                a=math.tau*i/segments;verts.append(c+n*depth*sign/2+radius*(u*math.cos(a)+v*math.sin(a)))
        faces=[tuple(reversed(range(segments))),tuple(segments+i for i in range(segments))]
        faces.extend((i,(i+1)%segments,(i+1)%segments+segments,i+segments) for i in range(segments))
        self.geom(verts,faces,mat,True)
        self.smooth[-len(faces)]=False
        self.smooth[-len(faces)+1]=False
    def ring(self,center,outer,inner,mat,normal=(1,0,0),segments=96):
        c=Vector(center);n=Vector(normal);u=Vector((-n.y,n.x,0));v=Vector((0,0,1));verts=[]
        for i in range(segments):
            a=math.tau*i/segments
            for radius in [inner,outer]:verts.append(c+(u*math.sin(a)+v*math.cos(a))*radius)
        self.geom(verts,[(2*i,2*((i+1)%segments),2*((i+1)%segments)+1,2*i+1) for i in range(segments)],mat)
    def frustum(self,center,z0,z1,lower,upper,mat):
        x,y=center;a,b=lower[0]/2,lower[1]/2;c,d=upper[0]/2,upper[1]/2
        self.geom([(x-a,y-b,z0),(x+a,y-b,z0),(x+a,y+b,z0),(x-a,y+b,z0),
                   (x-c,y-d,z1),(x+c,y-d,z1),(x+c,y+d,z1),(x-c,y+d,z1)],
                  [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    def outline(self,polygon,z0,z1,mat):
        n=len(polygon);verts=[(x,y,z) for z in [z0,z1] for x,y in polygon]
        faces=[tuple(reversed(range(n))),tuple(n+i for i in range(n))]
        faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
        self.geom(verts,faces,mat)
    def segment(self,a,b,width,depth,normal,mat):
        a,b=Vector(a),Vector(b);along=(b-a).normalized();n=Vector(normal);across=n.cross(along).normalized()
        self.box((a+b)/2,(width,depth,(b-a).length),mat,[across,n,along])
    def east_arch(self,x,y,spring,radius,height,mat):
        # Filled round-headed dark window, front-facing +X.
        poly=[(x,y-radius,spring-height),(x,y+radius,spring-height)]
        for j in range(21):
            a=math.pi*j/20;poly.append((x,y+radius*math.cos(a),spring+radius*math.sin(a)))
        self.geom(poly,[tuple(range(len(poly)))],mat)
