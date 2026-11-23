"""The identified No. 3 enclosure and the green opening behind its balcony, 2016."""
from math import cos, hypot, pi, sin

BRICK = "Dafuli 3 | red face brick"
CAST = "Dafuli 3 | worn grey pink render"
CAP = "Dafuli 3 | weathered cap"
CHARCOAL = "Dafuli 3 | charcoal sheet metal"
SEAM = "Dafuli 3 | dark folded edge"
ENAMEL = "Dafuli 3 | green enamel"
LETTER = "Dafuli 3 | old ivory painted lettering"
CREAM = "Dafuli 3 | pale window surround"
GREEN = "Dafuli 3 | dark green painted sash"
GLASS = "Dafuli 3 | recessed grey glass"
SILL = "Dafuli 3 | dark window recess"

SRGB = {
    BRICK: (.52,.21,.15), CAST:(.62,.53,.49),CAP:(.29,.27,.26),
    CHARCOAL:(.105,.10,.107),SEAM:(.06,.057,.061),ENAMEL:(.15,.24,.21),
    LETTER:(.87,.81,.64),CREAM:(.79,.77,.69),GREEN:(.105,.195,.16),
    GLASS:(.30,.39,.40),SILL:(.125,.128,.12)
}

def linear(v):
    return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4

PALETTE = {name:{'color':[linear(c) for c in rgb],
    'roughness':.34 if name in (ENAMEL,GLASS) else .75,
    'metallic':.15 if name in (CHARCOAL,SEAM) else 0.} for name,rgb in SRGB.items()}

def box(b,x0,x1,y0,y1,z0,z1,mat,tag):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),
          (x1-x0,y1-y0,z1-z0),mat,label='No 3 | '+tag)

def frustum(b,base,top,material,tag):
    def ring(r):
        x0,x1,y0,y1,z=r
        return [(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)]
    b.add(ring(base)+ring(top),[(0,3,2,1),(4,5,6,7),(0,1,5,4),
          (1,2,6,5),(2,3,7,6),(3,0,4,7)],material,'No 3 | '+tag)

def line(b,coords,width,y,thick,mat,name):
    for i,((x,z),(xx,zz)) in enumerate(zip(coords,coords[1:])):
        d=hypot(xx-x,zz-z)
        if d<1e-7:
            continue
        side=(z-zz)*width/(2*d);up=(xx-x)*width/(2*d)
        Q=[(x+side,z+up),(x-side,z-up),(xx-side,zz-up),(xx+side,zz+up)]
        vertices=[(u,v,h)for v in (y,y+thick)for u,h in Q]
        b.add(vertices,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),
              (2,6,7,3),(3,7,4,0)],mat,'No 3 | '+name+' '+str(i+1))

# Linework for the seven small painted characters on the verified plate.
STROKES = {
 '延':[[(1,9),(3,7),(1.5,7),(3.2,4.5),(2,2.3),(0.8,1)],[(2,2.3),(4.4,.8),(9.4,.8)],[(8.7,9.2),(6.1,8.2),(4.4,8)],[(6.6,8.1),(6.6,3.3)],[(4.5,6),(4.5,3),(9.2,3)],[(6.7,6.1),(9.1,6.1)]],
 '庆':[[(4.6,9.5),(5.5,8.6)],[(9.3,8),(2.4,8),(2.2,4),(1.6,1.8),(.6,.6)],[(3.5,5.4),(9.1,5.4)],[(6.3,7.3),(6,4.2),(5.1,2.1),(3,0.7)],[(6.2,4.9),(7.3,2.6),(9.4,.8)]],
 '路':[[(.6,9),(4.1,9),(4.1,6.1),(.6,6.1),(.6,9)],[(2.5,6),(2.5,1.1)],[(2.5,4.1),(4.1,4.1)],[(.6,4.4),(.6,1.2),(4.2,2)],[(6.2,9.5),(4.7,7.4)],[(5.8,8.5),(9.2,8.5),(7.6,6.4),(5.1,4.9)],[(5.7,7.7),(7.7,6),(9.8,5)],[(5.3,4.1),(9.2,4.1),(9.2,.7),(5.3,.7),(5.3,4.1)]],
 '二':[[(1.6,7.4),(8.4,7.4)],[(.5,2.4),(9.5,2.4)]],
 '十':[[(.4,5.7),(9.6,5.7)],[(5,9.4),(5,.5)]],
 '九':[[(4.5,9.4),(4.1,6.2),(3.3,3.5),(.6,.6)],[(.8,7.1),(7.3,7.1),(6.6,2),(6.9,.8),(9,.8),(9.6,2.3)]],
 '弄':[[(1.1,9),(9,9)],[(2,7.15),(8,7.15)],[(4.9,8.9),(4.9,5.4)],[(.8,5.4),(9.3,5.4)],[(.5,3.5),(9.5,3.5)],[(3.2,4.9),(3,2),(1.5,.45)],[(6.9,4.9),(6.9,.45)]],
}

def add_gate(b,lod=False):
    """Gate and address stone. Plane y=0 is the face of the address plate pier."""
    box(b,-.255,.248,0,.44,0,2.475,CAST,'enclosure pier')
    frustum(b,(-.26,.25,-.006,.445,2.47),(-.296,.29,-.035,.48,2.515),CAP,'cap lower splay')
    box(b,-.311,.308,-.048,.493,2.51,2.546,CAP,'cap fillet')
    frustum(b,(-.311,.308,-.048,.493,2.545),(-.357,.35,-.095,.535,2.58),CAP,'cap bed bevel')
    box(b,-.355,.35,-.095,.535,2.58,2.679,CAP,'square overhanging cap')
    frustum(b,(-.349,.346,-.09,.53,2.678),(-.05,.048,.142,.25,2.779),CAP,'four sloping cap faces')
    box(b,-.125,.155,-.009,-.001,2.250,2.451,ENAMEL,'enamel lane and number plate')
    # Digit traced from the photograph after rectifying the oblique enamel sign.
    # Livelikerw (2016), File:Dafu_Li_Shanghai.JPG, CC BY-SA 4.0.
    outline = [(0.0088, 2.3405), (0.0113, 2.347), (0.0244, 2.347), (0.0283, 2.3379), (0.0347, 2.3367), (0.0413, 2.3445), (0.0413, 2.3535), (0.0269, 2.3626), (0.0283, 2.3769), (0.0386, 2.3847), (0.0386, 2.399), (0.0283, 2.4003), (0.0256, 2.3912), (0.0113, 2.3952), (0.0113, 2.4003), (0.0217, 2.4133), (0.0295, 2.4173), (0.0399, 2.416), (0.0491, 2.4082), (0.0542, 2.3964), (0.0491, 2.3691), (0.0568, 2.3626), (0.0607, 2.351), (0.0582, 2.3314), (0.0464, 2.3197), (0.0256, 2.3184), (0.0152, 2.3249)]
    from shapely.geometry import Polygon
    from shapely.geometry.polygon import orient
    from shapely.ops import triangulate
    poly=orient(Polygon(outline),1)
    ring=list(poly.exterior.coords)[:-1];n=len(ring)
    vertices=[(x,y,z) for y in (-.0102,-.0086)for x,z in ring]
    index={pt:k for k,pt in enumerate(ring)}
    faces=[]
    for tri in triangulate(poly):
        if not poly.covers(tri.representative_point()):
            continue
        a,c,d=[index[pt] for pt in list(orient(tri,1).exterior.coords)[:3]]
        faces.extend([(a,c,d),(a+n,d+n,c+n)])
    for k in range(n):
        nxt=(k+1)%n
        faces.append((k,k+n,nxt+n,nxt))
    b.add(vertices,faces,LETTER,'No 3 | enamel plate | photographed numeral 3')
    for j,c in enumerate('' if lod else '延庆路二十九弄'):
        for i,stroke in enumerate(STROKES[c]):
            coords=[(-.085+j*.028+x*.0025,2.267+z*.0026)for x,z in stroke]
            line(b,coords,.00185,-.0102,.00135,LETTER,'painted address '+c+' '+str(i+1))
    box(b,.252,1.68,.085,.131,.025,2.302,CHARCOAL,'recorded extent of dark sheet gate')
    box(b,.251,1.68,.071,.137,2.281,2.305,SEAM,'folded gate head')
    box(b,.910,.925,.075,.132,.027,2.279,SEAM,'vertical fold in gate')
    # Short pull, partly shadowed; right-hand leaf continues past the edge of the photograph.
    line(b,[(.461,1.24),(.438,1.23),(.424,1.204),(.424,1.125),(.439,1.11)],
         .014,.046,.040,SEAM,'gate pull')
    box(b,-.187,-.169,-.025,0,1.09,2.152,CAP,'narrow strip below number')

def add_green_window(b,lod=False,wall_y=.70):
    """Window in the red wall at the near return of the photographed balcony.

    The frame is fixed to the original photograph when its plane is refined.
    Bring in the four source marks before expanding the surrounding wall crop.
    """
    cx,cy,cz=4.9063276447,-2.3040789044,1.56
    def elem(x0,x1,z0,z1,inset,depth,material,name):
        t=(wall_y+inset-cy)/(.70-cy)
        box(b,cx+(x0-cx)*t,cx+(x1-cx)*t,wall_y+inset,wall_y+inset+depth,
            cz+(z0-cz)*t,cz+(z1-cz)*t,material,name)
    left,right=-.398,.466
    lo,hi=3.79,5.183
    for x0,x1 in [(-.91,left),(right,.91)]:
        elem(x0,x1,3.58,5.68,0,.17,BRICK,'brickwork beside green sash')
    elem(left,right,hi,5.68,0,.17,BRICK,'brickwork above green sash')
    elem(left,right,3.58,lo,0,.17,BRICK,'brickwork under the showing opening')
    elem(left-.104,left,lo-.05,hi+.13,-.045,.055,CREAM,'pale left jamb')
    elem(right,right+.101,lo-.05,hi+.13,-.045,.055,CREAM,'pale right jamb')
    elem(left-.104,right+.101,hi,hi+.176,-.045,.060,CREAM,'pale flat lintel')
    elem(left-.118,right+.117,hi+.119,hi+.148,-.063,.033,CREAM,'fine head fillet')
    elem(left-.131,right+.130,hi+.205,hi+.257,-.091,.115,CREAM,'projecting head band')
    for n in range(19):
        x=left-.101+n*((right-left+.185)/19)
        elem(x,x+.023,hi+.169,hi+.216,-.075,.05,CREAM,'dentil '+str(n+1))
    elem(left,right,lo-.045,lo+.017,-.055,.073,CREAM,'window sill')
    elem(left,right,lo,hi,.046,.010,GLASS,'recessed glass')
    for l,r in ((left,-.196),(.050,.149),(.418,right)):
        elem(l,r,lo,hi,.028,.015,GREEN,'painted vertical sash')
    for z in (lo+.02,4.710,hi-.020):
        elem(left,right,z-.025,z+.025,.031,.013,GREEN,'painted horizontal sash')
    for x in (-.055,.332):
        elem(x-.008,x+.008,lo,4.680,.038,.007,GREEN,'slender lower glazing bar')
    elem(left,right,4.452,4.466,.037,.008,GREEN,'thin lower crossbar')

def add_no3(b,lod=False,layout=None):
    for k,v in PALETTE.items(): b.palette.setdefault(k,v)
    add_gate(b,lod)
    add_green_window(b,lod,(layout or {}).get('window_wall_y',.70))
