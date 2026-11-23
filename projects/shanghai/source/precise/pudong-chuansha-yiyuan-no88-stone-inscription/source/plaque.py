"""The four worn raised characters and moulded stone border photographed together at No. 88."""
from math import hypot, sin, pi

COLORS = {
    'buff limestone face': (0.72, 0.65, 0.52),
    'worn stone lettering': (0.75, 0.69, 0.58),
    'outer limestone lip': (0.72, 0.65, 0.52),
    'stone bevel': (0.67, 0.60, 0.49),
    'inner stone bead': (0.72, 0.66, 0.55),
    'stone cove': (0.63, 0.57, 0.47),
    'edge of backing slab': (0.59, 0.54, 0.45),
}
PALETTE = {name: {'color': list(rgb), 'roughness': .88} for name,rgb in COLORS.items()}

# Frontal inscription in reading order across the photograph. Each stroke has
# its own centreline and crest width, in the 600 by 192 reference drawing.
TRACES = {
    'hong': [
        (5.8, [(87,101),(90,92),(99,85),(110,82),(119,85),(124,90)]),
        (4.5, [(77,102),(83,105),(90,108),(94,112)]),
        (5.3, [(121,84),(133,82),(143,85),(150,89),(155,85),(159,79),(158,72)]),
        (9.5, [(148,100),(142,107),(132,110),(124,110),(118,113),(110,123),(99,135),(86,147),(76,153)]),
        (6.3, [(135,122),(128,130),(119,138),(110,145),(102,149),(106,152),(126,151),(139,149)]),
        (6.1, [(135,141),(139,146),(143,155),(149,157)]),
    ],
    'de': [
        (5.3, [(213,81),(219,76),(224,72),(228,68)]),
        (6.0, [(198,86),(203,88),(208,94)]),
        (7.2, [(187,118),(193,121),(201,118),(207,111)]),
        (7.5, [(215,101),(213,115),(211,128),(211,142),(215,152),(221,149),(224,141)]),
        (5.2, [(226,82),(231,85),(239,89),(243,93)]),
        (4.7, [(247,81),(255,83),(267,81),(273,77)]),
        (5.0, [(232,105),(238,110),(243,122)]),
        (5.9, [(248,110),(258,106),(269,106),(277,99)]),
        (5.0, [(244,121),(256,122),(265,120)]),
        (5.6, [(226,131),(232,128),(239,132),(245,132)]),
        (6.0, [(240,143),(245,151),(254,155),(264,157),(272,156),(279,151)]),
        (5.4, [(267,132),(276,135),(283,140),(289,138)]),
    ],
    'yi': [
        (8.5, [(352,89),(353,96),(357,99),(364,98),(369,94),(368,88)]),
        (6.8, [(369,111),(363,121),(354,130),(343,135),(332,139),(322,138)]),
        (6.4, [(350,140),(359,139),(369,134),(381,130),(390,130),(397,136),(402,140),(408,137)]),
    ],
    'dao': [
        (5.9, [(450,83),(458,89),(465,88),(470,83)]),
        (5.4, [(474,81),(479,76),(483,69)]),
        (5.5, [(498,82),(501,73),(506,70),(512,72),(516,80)]),
        (6.0, [(472,90),(485,92),(500,90),(514,88),(521,90)]),
        (6.6, [(473,103),(472,114),(470,129),(468,137)]),
        (6.6, [(477,101),(494,101),(511,99),(518,98),(518,109),(516,126),(514,139)]),
        (4.8, [(487,111),(497,110),(505,107)]),
        (5.0, [(486,122),(495,121),(505,118)]),
        (5.4, [(483,134),(498,134),(511,130)]),
        (5.7, [(454,108),(450,114),(452,122),(456,129),(454,136),(449,144)]),
        (8.1, [(444,144),(451,147),(463,147),(476,149),(495,151),(515,152),(530,151),(535,148)]),
    ],
}
SCALE = 0.0031  # display estimate from the repeated brick courses on the frontal 2021 photograph

def point(u,v,depth):
    return ((u-300)*SCALE, depth, (192-v)*SCALE)

def rectangle(inset, depth):
    return [point(u,v,depth) for u,v in [(inset,192-inset),(600-inset,192-inset),(600-inset,inset),(inset,inset)]]

def ring(b, label, profile, material):
    verts = [p for inset,depth in profile for p in rectangle(inset,depth)]
    faces = []
    for j in range(len(profile)):
        for i in range(4):
            n=(i+1)%4
            a=j*4; c=((j+1)%len(profile))*4
            faces.extend([(a+i,a+n,c+n),(a+i,c+n,c+i)])
    # The contour moves outward from the face to the inner rim, then down and back.
    # Use signed volume to orient every closed loop consistently.
    add_closed(b, verts, faces, material, label)

def add_closed(b, vertices, faces, material, label):
    vol=0.
    for ai,bi,ci in faces:
        a,bb,c=(vertices[i]for i in (ai,bi,ci))
        vol += a[0]*(bb[1]*c[2]-bb[2]*c[1])+a[1]*(bb[2]*c[0]-bb[0]*c[2])+a[2]*(bb[0]*c[1]-bb[1]*c[0])
    b.add(vertices,faces if vol>0 else [(c,k,a) for a,k,c in faces],material,label)

def stroke(b, glyph, index, width, points, lod):
    # The historical strokes have softened edges and tapered ends.
    section=[(-1,.10),(-.76,.65),(-.30,.98),(.28,1),(.74,.67),(1,.10)] if not lod else [(-1,.10),(-.56,.83),(.45,.95),(1,.10)]
    verts=[]
    for i,(u,v) in enumerate(points):
        left=points[max(0,i-1)];right=points[min(len(points)-1,i+1)]
        dx,dy=right[0]-left[0],right[1]-left[1];mag=hypot(dx,dy);nx,ny=-dy/mag,dx/mag
        taper=.31 if i in (0,len(points)-1) else (.86+.14*sin(pi*i/(len(points)-1)))
        for t,h in section+[(1,-.04),(-1,-.04)]:
            verts.append(point(u+nx*width*t*taper/2,v+ny*width*t*taper/2,-.039-(.0063+.00033*width)*h*taper))
    n=len(section)+2
    faces=[(0,i+1,i) for i in range(1,n-1)]
    for j in range(len(points)-1):
        for k in range(n):
            t=(k+1)%n;offset=j*n
            faces.extend([(offset+k,offset+t,offset+n+t),(offset+k,offset+n+t,offset+n+k)])
    last=(len(points)-1)*n
    faces.extend([(last,last+i,last+i+1) for i in range(1,n-1)])
    add_closed(b,verts,faces,'worn stone lettering',f'{glyph} | carved stroke {index+1:02d}')

def add_building(b,lod=False):
    b.box((0,.038,192*SCALE/2),(600*SCALE,.088,192*SCALE),'edge of backing slab',label='No. 88 | intact backing stone')
    b.box((0,-.018,192*SCALE/2),(534*SCALE,.042,126*SCALE),'buff limestone face',label='No. 88 | recessed inscription field')
    ring(b,'No. 88 | proud outer lip',[(0,-.012),(2,-.069),(5,-.074),(11,-.073),(14,-.065),(14,.002),(0,.002)],'outer limestone lip')
    ring(b,'No. 88 | inclined outer bevel',[(11.9,-.068),(15,-.060),(19,-.053),(20,-.051),(20,.001),(11.9,.001)],'stone bevel')
    ring(b,'No. 88 | rounded inner bead',[(19,-.053),(20.3,-.058),(22.0,-.061),(24,-.059),(25.3,-.054),(26,-.050),(26,.001),(19,.001)],'inner stone bead')
    ring(b,'No. 88 | shallow inner hollow',[(25.9,-.050),(27,-.045),(29,-.041),(32,-.039),(34,-.039),(34,.001),(25.9,.001)],'stone cove')
    for glyph,strokes in TRACES.items():
        for i,(width,line) in enumerate(strokes):
            stroke(b,glyph,i,width,line,lod)
