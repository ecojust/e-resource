"""Raised seven-character institution board and the canopy's oval escutcheon and paired scrolls."""
from math import pi,sin,cos
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
HERE=Path(__file__).absolute().parent
M='patinated canopy relief'
WOOD='warm brown vertical board'
INK='black applied lettering'
def add(b,lod):
    b.palette[WOOD]=dict(color=[.401,.340,.243],roughness=.66,metallic=.11)
    b.palette[INK]=dict(color=[.061,.052,.045],roughness=.65)
    # The board fits the first pier. Flat glyphs are traced from the actual sign in 2015.
    b.box((2.11,.957,1.745),(.505,.050,2.47),WOOD,label='west porch pier/seven-character nameplate')
    data=json.loads((HERE/'vertical-board-outlines.json').read_bytes())
    def convert(p):
        u,v=p;t=(v-181)/396
        xleft=146+4*t;w=77+4*t
        return [1.8575+.505*(u-xleft)/w,2.98-2.47*t]
    for char in data['glyphs']:
        for i,(outer,*holes)in enumerate(char['rings']):
            outline=Polygon([convert(p)for p in outer],[[convert(p)for p in h]for h in holes])
            # Pixel corner contacts need a finite joint to survive Float32 welding.
            outline=outline.buffer(-.00041,join_style='mitre').simplify(.00029,preserve_topology=True)
            if lod:outline=outline.simplify(.002,preserve_topology=True)
            if outline.is_valid and outline.area>.0000020:b.prism(outline,.069,.080,lambda x,z,d:(x,1-d,z),INK,f"pier name/{char['character']} stroke {i+1}")
    # The observed crest has a central oval boss, beaded inner border, crown-like
    # upper leaves and two smaller curls above each group of three swept ribbons.
    xc,zc=5.70,4.066
    n=18 if lod else 34
    def stroke(label,pts,r=.018):
        b.tube([(xc+x,-.267-d,zc+z)for x,z,d in pts],r,M,6 if lod else 10,'canopy crest/'+label)
    for j,(rx,rz,d,r) in enumerate([(.203,.245,.028,.027),(.164,.195,.054,.014),(.118,.152,.07,.023)]):
        a=np.linspace(0,2*pi,n+1);pts=[(rx*cos(t),rz*sin(t),d)for t in a]
        # Sow the ring as one prism with a centred hole instead of coincident cylinder caps.
        outside=[(xc+(rx+r)*cos(t),zc+(rz+r)*sin(t))for t in a[:-1]]
        inside=[(xc+(rx-r)*cos(t),zc+(rz-r)*sin(t))for t in a[:-1]]
        b.prism(Polygon(outside,[inside]),.199+d,.250+d,lambda x,z,k:(x,-k,z),M,f'canopy crest/oval ring {j+1}')
    profile=[(-.017,.001),(-.010,.085),(.000,.112),(.028,.107),(.055,.081),(.075,.039),(.081,.002)]
    seg=12 if lod else 20
    vertices=[(xc+radius*cos(2*pi*i/seg),-.298-depth,zc+1.21*radius*sin(2*pi*i/seg)) for depth,radius in profile for i in range(seg)]
    faces=[tuple(reversed(range(seg))),tuple(range((len(profile)-1)*seg,len(profile)*seg))]
    for j in range(len(profile)-1):
        for i in range(seg):faces.append((j*seg+i,j*seg+(i+1)%seg,(j+1)*seg+(i+1)%seg,(j+1)*seg+i))
    b.add(vertices,faces,M,'canopy crest/convex oval boss')
    def curved(name,pts,r):
        # Piecewise cubic Bézier curve from labelled knots, each bend independent.
        k=np.array(pts,dtype=float);samples=[]
        for j in range(0,len(k)-1,3):
            for t in np.linspace(0,1,5 if lod else 9,endpoint=j+3==len(k)-1):
                a,b1,c,d=k[j:j+4];p=(1-t)**3*a+3*t*(1-t)**2*b1+3*t*t*(1-t)*c+t**3*d
                samples.append([p[0],p[1],.018+.015*sin(pi*t)])
        stroke(name,samples,r)
    for sg,side in [(-1,'west'),(1,'east')]:
        for i in range(3):
            dz=i*.044
            curved(f'{side} outward ribbon {i+1}',[(sg*x,z+dz)for x,z in [(.17,-.184),(.35,-.265),(.48,-.205),(.49,-.082),(.63,-.262),(.78,-.270),(.932,-.171),(1.002,-.159),(1.020,-.228),(1.095,-.245)]],.020 if i==0 else .017)
        curved(side+' scroll around small eye',[(sg*x,z)for x,z in [(.17,-.14),(.26,-.22),(.48,-.13),(.445,.015),(.43,.115),(.302,.131),(.269,.045),(.237,-.033),(.325,-.060),(.345,-.005)]],.024)
        for j in range(3):
            d=j*.039
            curved(f'{side} top leaf {j+1}',[(sg*x,z)for x,z in [(.040+d,.196),(.008+d,.247),(.063+d,.285),(.037+d,.321-j*.021)]],.014)
    return b
