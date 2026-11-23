"""Seven-bay open veranda of the former Nanlin Normal School.

s follows the restored arcade from the photograph's left end. Positive d is
inward and z is up. The pier centres at both ends are included in the length.
"""
from math import cos, pi, sin
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from fabric import DARK, FRAME, GLASS, GRAY, MORTAR, RED, RED_STONE, STONE, paint, polygons

ASHLAR = 'Nanlin arcade | pale grey stone'
CLAY = 'Nanlin arcade | radial red brick'
CLAY_DARK = 'Nanlin arcade | dark fired face'
TIMBER = 'Nanlin arcade | dark timber'
CEILING = 'Nanlin arcade | corridor soffit'
PALETTE = {ASHLAR:paint((174,163,151)),CLAY:paint((156,74,54)),CLAY_DARK:paint((125,59,43)),
           TIMBER:paint((56,49,43),.77),CEILING:paint((154,148,134))}
AXES = (0., .94785244, 1.88057302, 2.88464823, 3.98514846, 5.05199365, 6.01729607, 7.)
# Counts of unobscured pale shafts on the restored elevation. The central
# ground opening is an entrance, its upper guard is the gabled masonry face.
UPPER = (8,8,9,0,9,9,9)
LOWER = (8,8,8,0,8,8,8)
ROOF = (0,10,10,0,10,10,0)


class Arcade:
    def __init__(self, builder, lod, layout, point):
        self.builder = builder
        self.lod = lod
        self.pitch = layout.get('arcade_length', 22.4) / 7.
        self.storey = layout.get('arcade_storey', self.pitch * 1.32)
        self.corridor = layout.get('arcade_depth', 1.72)
        self.point = point or layout.get('arcade_point') or (lambda s,d,z:(s,d,z))

    def world(self,s,d,z):
        return self.point(s*self.pitch,d,z*self.storey)

    def solid(self,shape,front,back,material,label):
        for part in polygons(shape):
            self.builder.prism(part,-back,-front,
                               lambda s,z,off:self.world(s,-off,z),material,'Arcade | '+label)

    def rect(self,left,bottom,right,top,front,back,material,label):
        if min(right-left,top-bottom,back-front)>1.e-6:
            self.solid(box(left,bottom,right,top),front,back,material,label)

    def bottle(self,x,foot,top,r,depth,label):
        # A squared foot, narrowed neck, swelling body and separate cap are visible.
        profile=((0,.68),(.075,.80),(.11,.85),(.16,.70),(.22,.54),(.36,.42),
                 (.51,.56),(.65,.79),(.765,.88),(.82,.84),(.87,.60),(.92,.59),(1,.64))
        n=6 if self.lod else 10
        if self.lod:profile=tuple(profile[j] for j in [0,1,3,5,6,8,10,12])
        verts=[self.world(x + r*cos(2*pi*i/n)*fac/self.pitch, depth+r*sin(2*pi*i/n)*fac,
                          foot+(top-foot)*z) for z,fac in profile for i in range(n)]
        faces=[tuple(reversed(range(n)))]
        for j in range(len(profile)-1):
            for i in range(n):
                a=j*n+i;q=j*n+(i+1)%n;faces.append((a,q,q+n,a+n))
        faces.append(tuple(range((len(profile)-1)*n,len(profile)*n)))
        self.builder.add(verts,faces,ASHLAR,'Arcade | '+label)

    def guard(self,i,left,right,z0,z1,count,kind):
        L=kind+' bay '+str(i+1)
        foot=z0+.035; head=z1-.024
        self.rect(left,z0,right,foot,-.112,.098,ASHLAR,L+' lower rail')
        self.rect(left,head,right,z1,-.118,.105,ASHLAR,L+' coping rail')
        dist=(right-left)/(count+.20)
        for k in range(count):
            self.bottle(left+(k+.6)*dist,foot,head,dist*self.pitch*.363,-.007,L+' baluster '+str(k+1))


def arch_points(mid,r,base,rise,n):
    # Three-centred appearance: the vault flattens across its crown.
    shape=2./2.6
    out=[]
    for i in range(n+1):
        t=i*pi/n;cc=cos(t)
        out.append((mid+r*(1 if cc>=0 else -1)*abs(cc)**shape,
                    base+rise*sin(t)**shape))
    return out


def upper_bay(c,i,a,b):
    mid=(a+b)/2;span=b-a
    rad=span/2-.123
    spring=1.492; inner=arch_points(mid,rad,spring,.189,16 if c.lod else 32)
    outer=arch_points(mid,rad+.074,spring,.285,len(inner)-1)
    # The visible tympanum is the grey brick between the extrados and the dentil course.
    arch_field=Polygon([(a,1.871),(b,1.871),(b,spring)]+outer+[(a,spring)])
    c.solid(arch_field,0,.335,GRAY,f'bay {i+1} brick spandrel')
    ring=Polygon(inner + list(reversed(outer)))
    c.solid(ring,.001,.33,MORTAR,f'bay {i+1} voussoir mortar backing')
    m=len(inner)-1
    for j in range(m):
        def between(p,q,t):return tuple(v+(w-v)*t for v,w in zip(p,q))
        f=.025 if c.lod else .043
        wedge=Polygon([between(inner[j],inner[j+1],f),between(inner[j],inner[j+1],1-f),
                       between(outer[j],outer[j+1],1-f),between(outer[j],outer[j+1],f)])
        c.solid(wedge,-.039,.001,CLAY_DARK if j%5==1 else CLAY,
                f'bay {i+1} radial facing brick {j+1:02d}')
    keystone=Polygon([(mid-.034,1.680),(mid+.034,1.680),(mid+.047,1.783),(mid-.050,1.783)])
    c.solid(keystone,-.055,-.04,ASHLAR,f'bay {i+1} pale keystone')
    if UPPER[i]:c.guard(i,a+.122,b-.122,1.019,1.253,UPPER[i],'upper')
    else:
        # The oblique view exposes a short plain back guard above the triangular cover.
        c.rect(a+.122,1.018,b-.122,1.252,.020,.195,RED,'central solid balcony guard')
        c.rect(a+.122,1.245,b-.122,1.263,.008,.209,ASHLAR,'central guard top')


def brackets(c,x,w,spring,id_):
    cap=Polygon([(x-w*.57,spring-.090),(x+w*.57,spring-.090),
                 (x+w*.725,spring-.022),(x+w*.725,spring),
                 (x-w*.725,spring),(x-w*.725,spring-.022)])
    c.solid(cap,-.115,.40,ASHLAR,f'pier {id_} flared carved capital')
    c.rect(x-w*.77,spring-.012,x+w*.77,spring+.012,-.155,.426,STONE,f'pier {id_} abacus')
    c.rect(x-w*.59,spring-.10,x+w*.59,spring-.087,-.132,.396,RED_STONE,f'pier {id_} neck moulding')
    for side in (-1,1):
        # Paired curved leaves with a centre lobe survive on both close photographs.
        pts=[(x+side*w*u,spring-z) for u,z in [(.015,.059),(.14,.072),(.30,.064),(.45,.040),(.56,.036),(.48,.050),(.30,.078),(.14,.086),(.015,.068)]]
        c.solid(Polygon(pts),-.129,-.115,STONE,f'pier {id_} capital leaf '+('left' if side<0 else 'right'))
    c.solid(Polygon([(x-.018,spring-.053),(x,spring-.031),(x+.018,spring-.053),(x,spring-.064)]),
            -.13,-.115,STONE,f'pier {id_} capital centre')


def ground_bay(c,i,a,b):
    left=a+.125;right=b-.125;step=.039
    # The light lintel has stepped shoulders. Both lower side reveals stay open.
    sill=.807
    under=[(left,.767),(left+step,.767),(left+step,.783),(left+.069,.783),
           (left+.094,sill),(right-.094,sill),(right-.069,.783),
           (right-step,.783),(right-step,.767),(right,.767)]
    c.solid(Polygon(under+[(right,.956),(left,.956)]),0,.34,ASHLAR,f'bay {i+1} stepped lower lintel')
    if LOWER[i]:c.guard(i,left,right,.028,.227,LOWER[i],'lower')


def pediment(c):
    mid=(AXES[3]+AXES[4])/2;left=AXES[3]-.16;right=AXES[4]+.16
    tri=Polygon([(left,1.005),(right,1.005),(mid,1.29)])
    inner=Polygon([(left+.142,1.027),(right-.142,1.027),(mid,1.236)])
    c.solid(tri,-.20,.205,CLAY_DARK,'central projecting triangular door head')
    c.solid(inner,-.224,-.20,ASHLAR,'central pale relief field')
    cap=Polygon([(left-.025,1.006),(mid,1.302),(right+.025,1.006),
                 (right-.004,.997),(mid,1.274),(left+.004,.997)])
    c.solid(cap,-.258,.219,STONE,'paired slopes of pediment coping')
    # Two mirrored branching reliefs and the central medallion follow the photograph.
    from shapely.geometry import LineString, Point
    for side in (-1,1):
        for j in range(3):
            pts=[(mid+side*x,1.029+z) for x,z in [
                (.045+.092*j,.022),(.095+.095*j,.030),(.120+.103*j,.059-.009*j),
                (.112+.104*j,.081-.014*j),(.089+.100*j,.083-.014*j),
                (.080+.095*j,.068-.011*j)]]
            line=LineString(pts).buffer(.009,quad_segs=2).intersection(inner)
            c.solid(line,-.239,-.224,STONE,f'central relief foliate scroll {side} {j+1}')
    oval=Point(mid,1.124).buffer(.047,quad_segs=8)
    from shapely.affinity import scale
    oval=scale(oval,1,1.20)
    c.solid(oval.difference(oval.buffer(-.010)),-.243,-.224,STONE,'central oval relief surround')


def add_arcade(b,lod=False,layout=None,point=None):
    """Build the photographed front and its open corridor. See arcade-sources.json."""
    layout=layout or {}; c=Arcade(b,lod,layout,point)
    for i,(a,end) in enumerate(zip(AXES,AXES[1:])):
        ground_bay(c,i,a,end);upper_bay(c,i,a,end)
        if ROOF[i]:c.guard(i,a+.065,end-.065,1.895,2.104,ROOF[i],'roof')
        else:
            c.rect(a+.064,1.895,end-.064,2.08,.0,.233,GRAY,f'roof solid parapet {i+1}')
            c.rect(a+.064,2.076,end-.064,2.101,-.031,.263,ASHLAR,f'roof coping {i+1}')
    for i,x in enumerate(AXES):
        label=f'pier {i+1}'; terminal=i in (0,7);centre=i in (3,4)
        width=.245;h=width/2
        body=RED if (terminal or centre) else GRAY
        c.rect(x-h,0,x+h,.949,0,.39,body,label+' lower shaft')
        c.rect(x-h-.017,0,x+h+.017,.054,-.033,.418,CLAY_DARK,label+' lower plinth')
        if centre:
            for j in range(1,10):
                zz=.068+.088*j
                c.rect(x-h-.004,zz,x+h+.004,zz+.016,-.023,0,RED_STONE,label+f' rusticated face {j}')
        elif not terminal:
            c.rect(x-h,.502,x+h,.562,-.011,0,CLAY,label+' red lower belt')
            c.rect(x-h,.771,x+h,.790,-.012,0,CLAY,label+' spring belt')
        c.rect(x-h,1.015,x+h,1.495,0,.37,body,label+' upper shaft')
        c.rect(x-h-.009,1.015,x+h+.009,1.070,-.022,.389,CLAY,label+' upper foot')
        if not (centre or terminal):
            c.rect(x-h,1.231,x+h,1.257,-.012,0,CLAY,label+' upper red belt')
        brackets(c,x,width,1.522,i+1)
        c.rect(x-.066,1.892,x+.066,2.145,-.012,.25,GRAY,label+' roof parapet pier')
        c.rect(x-.076,2.138,x+.076,2.163,-.035,.27,CLAY_DARK,label+' parapet cap')
    for zz in (.970,1.858):
        c.rect(-.136,zz,7.136,zz+.032,-.124,.445,RED_STONE,'long brick coping '+str(zz))
        for j in range(94):
            x=-.113+(7.21/94)*j
            c.rect(x,zz-.026,x+.047,zz,-.078,.03,CLAY,'dentil '+str(zz)+f' {j+1:02d}')
    pediment(c)
    # Inner deck and soffit start behind the outer rail. A transverse timber and its
    # shadow are visible through each upper arch, with a separate plane behind.
    for base,top,mat,name in [(-.025,.0,ASHLAR,'open gallery pavement'),(.951,1.014,CEILING,'upper gallery slab'),
                              (1.837,1.895,CEILING,'upper gallery ceiling')]:
        c.rect(-.12,base,7.12,top,.0,c.corridor+.15,mat,name)
    for i,x in enumerate(AXES):
        c.rect(x-.052,1.797,x+.052,1.837,.22,c.corridor,TIMBER,'visible upper ceiling beam '+str(i+1))
    if layout.get('arcade_backing',True):
        add_visible_back(c)
    return b


def add_visible_back(c):
    """Model the lower rear glazing actually distinguishable in the restored obliques."""
    depth=c.corridor
    # Lower bays 5–7 show the dark double leaf and split rectangular lights under
    # a shallow arched head. Leftmost bay allows a side glimpse out to the garden.
    for i,(a,b) in enumerate(zip(AXES,AXES[1:])):
        if i==0:continue
        mid=(a+b)/2
        l=mid-.30;r=mid+.30
        lower = i in (4,5,6)
        foot=.153 if i in (5,6) else .007
        head=.784 if i in (5,6) else .78
        dark_open=Polygon([(l,foot),(r,foot),(r,head-.04),(mid+.16,head),(mid-.16,head),(l,head-.04)])
        surround=box(a,0,b,.951).difference(dark_open)
        c.solid(surround,depth,depth+.19,GRAY,f'rear bay {i+1} visible masonry')
        if lower or i in (1,2,3):
            c.solid(dark_open,depth+.079,depth+.088,GLASS if lower else DARK,f'rear bay {i+1} dark recess')
            rim=dark_open.difference(dark_open.buffer(-.016,join_style='mitre'))
            c.solid(rim,depth+.017,depth+.076,FRAME,f'rear bay {i+1} sash outer edge')
            if lower:
                rows=3 if i>=5 else 2
                for j in range(1,4):
                    xx=l+(r-l)*j/4
                    c.solid(box(xx-.010,foot,xx+.010,head).intersection(dark_open),
                            depth+.024,depth+.055,TIMBER,f'rear bay {i+1} upright {j}')
                for j in range(1,rows+1):
                    zz=foot+(head-foot)*j/(rows+1)
                    c.rect(l+.016,zz-.007,r-.016,zz+.007,depth+.054,depth+.078,TIMBER,f'rear bay {i+1} rail {j}')
        # Upper rear wall seen in shade. Narrow dark recesses are left beneath the beams.
        lower_band=box(a,1.014,b,1.24); cap=box(a,1.73,b,1.837)
        c.solid(unary_union([lower_band,cap]),depth,depth+.19,GRAY,f'rear bay {i+1} visible upper brick bands')
