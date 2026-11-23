"""The No. 3 blue-lined terrace and its two visible iron faces, read on the 2016 photograph."""
from math import cos, pi, sin

import numpy as np

BLUE = 'Dafu Li 3 | blue terrace lining'
IRON = 'Dafu Li 3 | weathered black terrace iron'
SLAB = 'Dafu Li 3 | pale cement terrace beam'
DECK = 'Dafu Li 3 | grey terrace deck edge'
COVER = 'Dafu Li 3 | dark weathered liner hem'


def finish(rgb, roughness, metallic=0.):
    def linear(c):
        x = c / 255.
        return x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4
    return {'color': [linear(v) for v in rgb], 'roughness': roughness, 'metallic': metallic}


PALETTE = {BLUE: finish((38, 81, 106), .85), IRON: finish((50, 51, 52), .76, .23),
           SLAB: finish((203, 197, 189), .91), DECK: finish((147, 142, 137), .94),
           COVER: finish((78, 76, 77), .95)}
# Conditional coordinates at front Y=0, the plaque plane. The named bearing runs back
# to the dwelling. The far end is occluded where it meets the adjoining court.
EYE = np.array([4.906327644700017, -2.3040789044311376, 1.56])
LEFT, RIGHT, REAR = -1.30, .736, .553
BOTTOM, TOP = 3.337, 3.793
NAME = 'No. 3 terrace | '


def terrace_bounds(front_depth=.65, wall_depth=None):
    scale = (front_depth - EYE[1]) / -EYE[1]
    back = front_depth + scale * REAR if wall_depth is None else wall_depth
    return (EYE[0] + (LEFT - EYE[0]) * scale, EYE[0] + (RIGHT - EYE[0]) * scale,
            front_depth, back, EYE[2] + (3.155 - EYE[2]) * scale, EYE[2] + (3.91 - EYE[2]) * scale)


class Terrace:
    def __init__(self, builder, front_depth, wall_depth, lod):
        self.b = builder
        self.front = front_depth
        self.scale = (front_depth - EYE[1]) / -EYE[1]
        self.back = front_depth + self.scale * REAR if wall_depth is None else wall_depth
        self.lod = lod

    def point(self, x, y, z):
        return (EYE[0] + self.scale * (x - EYE[0]), self.front + y * (self.back-self.front) / REAR,
                EYE[2] + self.scale * (z - EYE[2]))

    def box(self, x0, y0, z0, x1, y1, z1, material, label):
        a, b = np.array(self.point(x0, y0, z0)), np.array(self.point(x1, y1, z1))
        self.b.box((a+b)/2, b-a, material, label=NAME + label)

    def strap(self, face, path, label, width=.0085, thickness=.0048, shift=0., loop=False):
        """Sweep a rectangular iron flat on its own planar bend; the closed rings have welded ends."""
        p = np.asarray(path, dtype=float)
        prev, after = np.roll(p, 1, axis=0), np.roll(p, -1, axis=0)
        if not loop:
            prev[0], after[-1] = p[0], p[-1]
        tangents = after - prev
        tangents /= np.linalg.norm(tangents, axis=1)[:, None]
        across = np.column_stack((-tangents[:, 1], tangents[:, 0]))
        vertices = []
        for mid, cross in zip(p, across):
            for w, d in ((-1,-1), (1,-1), (1,1), (-1,1)):
                u,z = mid + cross * w * width/2
                offset = shift + d * thickness/2
                vertices.append(self.point(u, -offset, z) if face == 'front' else self.point(RIGHT+offset, u, z))
        faces = []
        for i in range(len(p) if loop else len(p)-1):
            j = (i+1) % len(p)
            for k in range(4):
                n=(k+1)%4
                faces.append([4*i+k, 4*i+n, 4*j+n, 4*j+k])
        if not loop:
            last=4*(len(p)-1)
            faces.extend([(3,2,1,0), (last,last+1,last+2,last+3)])
        # Wind the rectangular section consistently on both orthogonal rail faces.
        q = np.asarray(vertices) - vertices[0]
        volume = sum(q[f[0]] @ np.cross(q[f[k]], q[f[k+1]]) for f in faces for k in range(1,len(f)-1))
        if volume < 0:
            faces=[tuple(reversed(f)) for f in faces]
        self.b.add(vertices,faces,IRON,NAME + face + ' | ' + label)

    def ring(self, face, u, z, rx, rz, label):
        count = 10 if self.lod else 20
        points=[(u+rx*cos(2*pi*i/count),z+rz*sin(2*pi*i/count)) for i in range(count)]
        self.strap(face, points, label, width=.0070, thickness=.0045, shift=.002, loop=True)

    def curl(self, face, u, z, ru, rz, direction, start, label):
        # The end of each short C strap spirals inwards around its tangent.
        count = 10 if self.lod else 20
        arc=[]
        for i in range(count+1):
            t=i/count
            a=start + direction * 1.64*pi*t
            radius=1-.61*t
            arc.append((u+ru*radius*cos(a),z+rz*radius*sin(a)))
        self.strap(face, arc, label, width=.0081, thickness=.0045, shift=.001)

    def double_ears(self, face, lo, hi, label):
        middle=(lo+hi)/2
        for side,s in [(lo,1),(hi,-1)]:
            self.strap(face, [(side,BOTTOM),(side,TOP)], label+' upright')
            at=side+s*(hi-lo)*(.27 if s>0 else .38)
            for z,sign in [(TOP-.038,1),(BOTTOM+.038,-1)]:
                self.curl(face,at,z,(hi-lo)*.235,.028,sign*s,pi if s>0 else 0,label+' rolled ear')
                self.strap(face,[(side,z+sign*.010),(at,z-sign*.032),(at,3.56)],label+' slender stem',width=.0068)
        self.ring(face,middle,3.56,.013,.023,label+' central oval')
        self.strap(face,[(lo,3.56),(middle-.013,3.56)],label+' central bar',width=.0062)
        self.strap(face,[(middle+.013,3.56),(hi,3.56)],label+' central bar',width=.0062)

    def diamond(self, face, lo, hi, label):
        centre=(lo+hi)/2
        for u in (lo,hi):
            self.strap(face,[(u,BOTTOM),(u,TOP)],label+' upright')
        for a,b in [(lo,hi),(hi,lo)]:
            self.strap(face,[(a,TOP-.014),(b,3.56),(a,BOTTOM+.014)],label+' diagonal',width=.009)
        for z,orientation in [(TOP-.016,-1),(BOTTOM+.015,1)]:
            for sign in (-1,1):
                self.curl(face,centre+sign*.011,z,.012,.009,orientation*sign,pi/2*orientation,label+' narrow tip')

    def central_panel(self, offset, title):
        # These vertices are traced on the registered 850 by 490 near-panel
        # enlargement. The second panel is displaced along its common front plane.
        def rail(path, name, width=.0083, rounded=False):
            points = np.asarray(path, float)
            if rounded:
                for _ in range(1 if self.lod else 2):
                    a,b = points[:-1],points[1:]
                    pairs = np.stack([.75*a+.25*b,.25*a+.75*b],axis=1).reshape(-1,2)
                    points = np.vstack([points[0],pairs,points[-1]])
            coords=[(-.25 + x*.995/849 + offset, 3.83-y*.53/489) for x,y in points]
            self.strap('front', coords, title+' '+name, width=width)
        # Opposed, rising quarter-curves. Small hooked ends turn back along
        # the horizontal flat at the foot of the opposite inner stem.
        quarter=[(213,301),(213,248),(238,249),(269,239),(299,219),(321,194),(334,168),
                 (470,168),(468,158),(476,148),(490,147),(502,154),(504,170),(497,186),(481,203)]
        for reverse in (False,True):
            path=quarter if not reverse else [(696-x,505-y) for x,y in quarter]
            rail(path,'curved quarter and hook',rounded=True)
        # Three separately rolled C ends on each cheek. Their mouths face one
        # another. The thin vertical stiles remain visible between the curls.
        cheek=[(581,141),(558,141),(538,148),(528,162),(529,181),(543,197),
               (557,196),(561,184),(555,176),(545,176),(544,183)]
        for row in range(3):
            for mirror in (False,True):
                path=[(708-x if mirror else x,y+75*row) for x,y in cheek]
                rail(path,'three cheek scrolls',rounded=True)
        for x in (121,199,515,582):
            rail([(x,143),(x,366)],'inset stile',width=.0073)
        rail([(102,366),(602,366)],'bottom channel')
        rail([(116,143),(197,143),(213,133),(522,133),(542,142),(590,142)],'stepped upper edge')
        # Distinct tiers of bent horizontal strap above and below the inset.
        for y in (72,103):
            rail([(108,y),(155,y),(167,y-6),(526,y-6),(539,y-15),(560,y-15),
                  (578,y-9),(581,y+3),(568,y+12),(557,y+8),(557,y)],'upper rolled flat',width=.0068,rounded=True)
        rail([(122,401),(168,401),(181,395),(336,395),(348,404),(357,420)],
             'lower rolled flat',width=.0067,rounded=True)


def add_terrace(b, lod=False, front_depth=.65, wall_depth=None):
    t=Terrace(b,front_depth,wall_depth,lod)
    t.box(LEFT,0,3.155,RIGHT,REAR,3.325,SLAB,'pale concrete edge beam')
    t.box(LEFT,.003,3.325,RIGHT,REAR,3.343,DECK,'thin terrace deck')
    # A blue sheet is visible directly behind the iron in 2016. The second road
    # view shows the open parapet in the same place with the boards and dark hem changed.
    t.box(LEFT+.006,.024,3.341,RIGHT-.024,.032,3.844,BLUE,'blue lining behind the street rail')
    t.box(RIGHT-.032,.026,3.341,RIGHT-.023,REAR,3.869,BLUE,'blue lining on the short return')
    t.box(RIGHT+.0001,.014,3.288,RIGHT+.003,REAR,3.342,BLUE,'blue apron below the return bottom flat')
    t.box(LEFT+.003,.002,3.342,LEFT+.010,.031,3.862,BLUE,'short turned edge of lining')
    # The sheet's gently uneven folded top follows the visible 2016 silhouette.
    top=[(LEFT+.006,3.875),(-1.15,3.870),(-.79,3.861),(-.51,3.852),(-.26,3.862),
         (.08,3.885),(.28,3.895),(.53,3.905),(RIGHT-.024,3.880)]
    for i,((a,za),(c,zc)) in enumerate(zip(top,top[1:])):
        front=.024; back=.034
        vertices=[t.point(x,y,z) for y in (front,back) for x,z in ((a,3.842),(c,3.842),(c,zc),(a,za))]
        faces=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
        t.b.add(vertices,faces,COVER,NAME+'rolled upper lining edge')
    t.box(RIGHT-.041,.031,3.842,RIGHT-.022,REAR,3.889,COVER,'return liner upper hem')
    for face,lo,hi in [('front',LEFT,RIGHT),('return',0.,REAR)]:
        t.strap(face,[(lo,BOTTOM),(hi,BOTTOM)],'bottom flat',width=.012,thickness=.017)
        t.strap(face,[(lo,TOP),(hi,TOP)],'top handrail',width=.0145,thickness=.022)
        for u in (lo,hi):
            t.strap(face,[(u,BOTTOM-.003),(u,TOP+.003)],'end post',width=.013,thickness=.015)
    t.central_panel(-.883,'far panel')
    t.central_panel(0.,'near panel')
    t.diamond('front',-1.288,-1.202,'far diamond')
    t.double_ears('front',-1.198,-1.083,'far ear pair')
    t.double_ears('front',-.414,-.299,'central ear pair')
    t.diamond('front',-.296,-.204,'central diamond')
    t.double_ears('front',-.201,-.089,'central ear pair at nearer panel')
    t.double_ears('front',.465,.566,'near ear pair')
    t.diamond('front',.568,.681,'near diamond')
    t.ring('front',.707,3.56,.025,.014,'corner link')
    t.diamond('return',.057,.163,'outer return diamond')
    t.double_ears('return',.163,.274,'outer return ear pair')
    t.curl('return',.302,3.559,.024,.019,1,pi,'return centre link')
    t.double_ears('return',.332,.452,'inner return ear pair')
    t.diamond('return',.463,.550,'inner return diamond')
