"""The pair of seated stone guardians on the existing Hongde Church entrance plinths.

The source photo frame looks south. Local u increases to the viewer's right,
local depth increases towards the door, and z is measured above the plinth.
"""
from math import cos, pi, sin
from pathlib import Path
import json
import numpy as np

HERE = Path(__file__).resolve().parent
EDGE = json.loads((HERE/'baseline.json').read_bytes())['north_edge']
# The existing author's Facade runs westwards along the north edge.
WEST = -np.asarray(EDGE['tangent_east_north'])
INWARD = -np.asarray(EDGE['outward_normal_east_north'])
MID = np.asarray(EDGE['center_local_east_north_m'])
STONE = 'Hongde limestone carving'
CUT = 'Hongde incised stone'
PALETTE = {STONE: ([.54,.51,.45,1],.90), CUT: ([.29,.28,.25,1],.94)}


class Sculpture:
    def __init__(self, side, lod):
        self.side = side
        self.lod = lod
        self.parts = {}

    def solid(self, label, material, points, faces):
        points = np.asarray(points, dtype=float)
        world = MID + (1.95*self.side + points[:,0,None])*WEST + (-.48+points[:,1,None])*INWARD
        vertices = np.column_stack((world[:,0], .86+points[:,2], -world[:,1]))
        key = f'{self.side:+d}/{label}'
        pos, tris = self.parts.setdefault((key,material), ([],[]))
        offset = len(pos)
        pos.extend(vertices.tolist())
        tris.extend(tuple(i+offset for i in face) for face in faces)

    def loft(self, label, material, rings):
        """Close varying elliptical cross-sections with shared pole vertices."""
        n = 10 if self.lod else 20
        points = [(rings[0][0], rings[0][1], rings[0][2])]
        for x,y,z,rx,ry in rings[1:-1]:
            points.extend((x+rx*cos(2*pi*j/n), y+ry*sin(2*pi*j/n), z) for j in range(n))
        cap = len(points)
        points.append(tuple(rings[-1][:3]))
        faces = []
        for j in range(n):
            k = (j+1)%n
            faces.append((0,1+k,1+j))
            for i in range(len(rings)-3):
                l = 1+i*n
                faces.extend([(l+j,l+k,l+n+k), (l+j,l+n+k,l+n+j)])
            faces.append((cap, cap-n+j, cap-n+k))
        self.solid(label, material, points, faces)

    def ovoid(self, label, center, size, material=STONE):
        x,y,z=center; rx,ry,rz=size
        steps=6 if self.lod else 10
        rings=[]
        for j in range(steps+1):
            a=pi*j/steps-pi/2
            rings.append((x,y,z+rz*sin(a),rx*cos(a),ry*cos(a)))
        self.loft(label,material,rings)

    def strand(self,label,material,path,r):
        """Round carved cord or curl, with closed ends."""
        points=np.asarray(path,float)
        sides=5 if self.lod else 8
        verts=[]
        for i,pt in enumerate(points):
            axis=points[min(i+1,len(points)-1)]-points[max(0,i-1)]
            axis/=np.linalg.norm(axis)
            up=np.eye(3)[np.argmin(abs(axis))]
            first=np.cross(axis,up);first/=np.linalg.norm(first)
            second=np.cross(axis,first)
            for j in range(sides):
                a=2*pi*j/sides
                verts.append(pt+r*(cos(a)*first+sin(a)*second))
        lens=len(points);faces=[]
        for i in range(lens-1):
            for j in range(sides):
                k=(j+1)%sides;l=i*sides
                faces.extend([(l+j,l+k,l+sides+k),(l+j,l+sides+k,l+sides+j)])
        for j in range(1,sides-1):
            faces.extend([(0,j+1,j),((lens-1)*sides,(lens-1)*sides+j,(lens-1)*sides+j+1)])
        self.solid(label,material,verts,faces)

    def build(self):
        s=self.side
        # Compact haunches sit towards the door. The chest narrows under a
        # projecting jaw. Both front legs are visible from the street.
        self.loft('chest and rump',STONE,[(0,.07,.002,0,0),(0,.07,.018,.19,.17),
            (0,.092,.12,.213,.181),(0,.085,.25,.192,.175),(0,.015,.38,.203,.17),
            (0,-.018,.482,.208,.168),(0,-.035,.545,.14,.122),(0,-.02,.58,0,0)])
        self.ovoid('neck',(0,-.045,.53),(.152,.13,.156))
        for sign in [-1,1]:
            self.ovoid('folded haunches',(sign*.139,.104,.14),(.123,.17,.133))
            self.ovoid('back feet',(sign*.163,.068,.055),(.083,.14,.05))
            raised=sign==-s
            foot=.11 if raised else .012
            self.loft('bent foreleg' if raised else 'straight foreleg',STONE,[
                (sign*.14,-.135,.48,0,0),(sign*.138,-.10,.448,.074,.078),
                (sign*.149,-.105,.376,.085,.071),(sign*.178,-.137,.274,.073,.066),
                (sign*.163,-.181,.225 if raised else .19,.064,.073),
                (sign*.154,-.201,foot+.07,.057,.069),(sign*.152,-.214,foot+.035,0,0)][::-1])
            self.ovoid('forepaws',(sign*.153,-.214,foot+.048),(.074,.088,.047))
            for j in [-1,0,1]:
                self.ovoid('forepaw toes',(sign*.153+j*.039,-.264,foot+.03),(.026,.038,.027))
            if raised:
                self.ovoid('carved support beneath raised paw',(sign*.154,-.202,.074),(.099,.094,.077))
                if not self.lod:
                    # The east carving has clustered ornament, the west lion's
                    # support reads as a rounded ball in both dated views.
                    for a in np.linspace(0,2*pi,6,endpoint=False):
                        cx=sign*.154+.073*cos(a);cy=-.202+.064*sin(a)
                        if s<0:self.ovoid('support ornament',(cx,cy,.089),(.031,.032,.026))
        self.loft('head',STONE,[(0,-.088,.506,0,0),(0,-.088,.521,.09,.096),
            (0,-.085,.568,.158,.141),(0,-.085,.665,.19,.158),(0,-.073,.753,.177,.154),
            (0,-.055,.803,.111,.108),(0,-.057,.826,0,0)])
        for sign in [-1,1]:
            self.ovoid('ears',(sign*.149,-.005,.77),(.061,.067,.064))
            self.ovoid('ears inset',(sign*.175,-.04,.773),(.024,.033,.027),CUT)
            self.ovoid('cheek',(sign*.124,-.143,.638),(.078,.079,.083))
            self.ovoid('brow',(sign*.078,-.194,.722),(.08,.053,.038))
            self.ovoid('recessed eye',(sign*.084,-.232,.698),(.035,.022,.021),CUT)
            self.ovoid('muzzle',(sign*.057,-.213,.652),(.077,.081,.045))
        self.ovoid('carved mouth',(0,-.219,.60),(.108,.068,.033),CUT)
        self.ovoid('lower jaw',(0,-.197,.574),(.109,.079,.039))
        self.ovoid('short nose',(0,-.254,.678),(.057,.040,.034))
        for sign in [-1,1]:
            self.ovoid('teeth',(sign*.067,-.257,.625),(.016,.018,.021))
        # Coiled locks follow the back and sides of the head. Keep the face
        # open around the brow and taper the lower mane beside the neck.
        for band,(z,rx,ry,count) in enumerate([(.57,.147,.125,7),(.65,.172,.135,9),(.741,.162,.125,9),(.793,.094,.071,6)]):
            for a in np.linspace(-.54,pi+.54,count):
                x=rx*cos(a);y=-.05+ry*sin(a)
                self.ovoid('mane locks',(x,y,z),(.049,.052,.05))
                if not self.lod:
                    spiral=[]
                    for t in np.linspace(0,1,14):
                        phi=t*5.8+band*.37;radius=.031*(1-.64*t)
                        spiral.append((x+.043*cos(a)-sin(a)*radius*cos(phi),
                                       y+.043*sin(a)+cos(a)*radius*cos(phi), z+radius*sin(phi)))
                    self.strand('spiral mane carving',STONE,spiral,.008)
        self.strand('chest collar',STONE,[(-.17,-.077,.458),(-.128,-.147,.434),
            (0,-.203,.39),(.128,-.147,.434),(.17,-.077,.458)],.017)
        self.ovoid('hanging chest ornament',(0,-.178,.356),(.045,.035,.042))
        self.strand('tail against haunch',STONE,[(s*.13,.21,.052),(s*.199,.21,.102),
            (s*.211,.202,.169),(s*.198,.16,.223),(s*.158,.151,.23)],.036)
        return self.parts


def meshes(lod=False):
    """Four native edit groups per side, with unchanged glTF coordinates."""
    groups={}
    for side in [-1,1]:
        for (label,material),(p,f) in Sculpture(side,lod).build().items():
            prefix='West guardian' if side>0 else 'East guardian'
            name=label.split('/',1)[1]
            if 'mane' in name: group='curled mane'
            elif name in {'ears','ears inset','cheek','brow','recessed eye','muzzle','carved mouth','lower jaw','short nose','teeth','head'}: group='head and face'
            elif name in {'straight foreleg','bent foreleg','forepaws','forepaw toes','carved support beneath raised paw','support ornament'}:group='forelegs and paws'
            else:group='seated body'
            parts=groups.setdefault(prefix+' / '+group,{})
            vertices,indices=parts.setdefault(material,([],[]));offset=len(vertices)
            vertices.extend(p);indices.extend(tuple(v+offset for v in tri)for tri in f)
    return groups
