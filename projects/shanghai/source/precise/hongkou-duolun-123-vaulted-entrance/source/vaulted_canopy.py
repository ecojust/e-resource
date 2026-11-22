"""Barrel-vault entrance canopy and four columns at 123 Duolun Road."""
from math import cos, pi, sin


def finish(rgb, roughness=.88, metallic=0):
    return dict(color=[((v / 255 + .055) / 1.055) ** 2.4 for v in rgb],
                roughness=roughness, metallic=metallic)


PALETTE = {
    'pale dressed stone': finish((179, 170, 147)),
    'worn stone edge': finish((161, 153, 136)),
    'canopy metal': finish((99, 107, 102), .66, .25),
    'soffit ground': finish((149, 143, 124)), 'soffit frame': finish((111, 111, 96)),
    'soffit recess': finish((167, 159, 136)), 'recess boss': finish((137, 132, 112)),
    'plinth mortar': finish((142, 132, 118)), 'plinth stone': finish((152, 143, 125)),
}
SPRING = 2.51
FRONT = -.74
BACK = .74


def box(b, x, y, z, width, depth, height, material, name):
    b.box((x, y, z), (width, depth, height), material, label=name)


def curved_shell(b, inner, outer, y0, y1, a0, a1, count, material, name):
    """An elliptical arch sector. End faces retain the real thickness at each spring."""
    pts = []
    for i in range(count + 1):
        theta = a0 + (a1 - a0) * i / count
        for rx, rz, y in [(inner[0],inner[1],y0),(outer[0],outer[1],y0),
                          (outer[0],outer[1],y1),(inner[0],inner[1],y1)]:
            pts.append((rx*cos(theta), y, SPRING+rz*sin(theta)))
    faces = [(0, 3, 2, 1), (4*count,4*count+1,4*count+2,4*count+3)]
    for part in range(count):
        start = 4 * part
        for edge in range(4):
            nxt = (edge + 1) % 4
            faces.append((start+edge,start+nxt,start+4+nxt,start+4+edge))
    b.add(pts, faces, material, name)


def shaft(b, x, y, name, lod):
    course = .080
    box(b,x,y,.291,.355,.355,.582,'plinth mortar',name+' plinth bed')
    for i in range(7):
        box(b,x,y,.042+i*course,.365,.365,.074,'plinth stone',name+f' plinth course {i+1}')
    box(b,x,y,.591,.397,.397,.040,'worn stone edge',name+' plinth cap')
    profile=[(.605,.148),(.615,.165),(.635,.173),(.651,.177),(.675,.174),(.692,.162),
             (.719,.159),(.735,.164),(.772,.185),(.806,.194),(.838,.194),(.864,.184),
             (.893,.154),(.915,.140),(1.42,.139),(2.238,.128),(2.266,.134),
             (2.28,.148),(2.299,.151),(2.329,.159),(2.351,.168),(2.378,.170),(2.398,.180)]
    count=20 if lod else 40
    pts=[(x+r*cos(i*2*pi/count),y+r*sin(i*2*pi/count),z) for z,r in profile for i in range(count)]
    faces=[(j*count+i,j*count+(i+1)%count,(j+1)*count+(i+1)%count,(j+1)*count+i)
           for j in range(len(profile)-1) for i in range(count)]
    faces.extend([tuple(reversed(range(count))),tuple(range((len(profile)-1)*count,len(profile)*count))])
    b.add(pts,faces,'pale dressed stone',name+' turned base shaft and capital')
    box(b,x,y,2.427,.377,.377,.062,'worn stone edge',name+' square abacus')


def add_building(b,lod=False):
    segments=42 if lod else 96
    for side, x in [('left',-1.06),('right',1.06)]:
        for depth,y in [('front',FRONT+.09),('rear',BACK-.08)]:
            shaft(b,x,y,depth+' '+side,lod)
        for z,width,height,material in [(2.461,.355,.029,'pale dressed stone'),(2.503,.387,.055,'worn stone edge'),
                                          (2.539,.410,.030,'pale dressed stone')]:
            box(b,x,0,z,width,1.73,height,material,side+f' eaves course {z:.3f}')
    curved_shell(b,(.965,.788),(1.095,.917),FRONT,BACK,0,pi,segments,'soffit ground','barrel vault body')
    curved_shell(b,(1.091,.915),(1.108,.932),FRONT+.015,BACK+.02,0,pi,segments,'canopy metal','outer curved weathering surface')
    for j,(ri,ro,front,mat) in enumerate([(.933,.962,-.817,'worn stone edge'),(.960,.981,-.842,'pale dressed stone'),
                                           (.978,1.062,-.825,'pale dressed stone'),(1.061,1.082,-.842,'worn stone edge'),
                                           (1.081,1.108,-.852,'pale dressed stone')]):
        curved_shell(b,(ri,ri-.179),(ro,ro-.179),front,FRONT+.035,0,pi,segments,mat,'front arch moulding '+str(j+1))
    # Six bands in depth and six sectors around the curve reproduce the visible reflected ceiling.
    bays=6
    rows=6
    for section in range(bays):
        a0=pi*section/bays+.015; a1=pi*(section+1)/bays-.015
        for row in range(rows):
            y0=FRONT+(BACK-FRONT)*row/rows+.012
            y1=FRONT+(BACK-FRONT)*(row+1)/rows-.012
            label=f'soffit panel {section+1}-{row+1}'
            steps=4 if lod else 10
            for low,high,near,far,edge in [(a0,a1,y0,y0+.026,'front'),(a0,a1,y1-.026,y1,'back'),
                             (a0,a0+.043,y0+.026,y1-.026,'left'),(a1-.043,a1,y0+.026,y1-.026,'right')]:
                curved_shell(b,(.948,.771),(.969,.792),near,far,low,high,steps,'soffit frame',label+' '+edge)
            curved_shell(b,(.961,.784),(.969,.792),y0+.025,y1-.025,a0+.042,a1-.042,steps,'soffit recess',label+' inset')
            mid=(a0+a1)/2; ym=(y0+y1)/2
            curved_shell(b,(.954,.777),(.964,.787),ym-.026,ym+.026,mid-.038,mid+.038,
                         3 if lod else 6,'recess boss',label+' centre')
    for i in range(1,bays):
        angle=pi*i/bays
        curved_shell(b,(.938,.761),(.968,.791),FRONT+.01,BACK-.008,angle-.012,angle+.012,3,
                     'pale dressed stone',f'longitudinal rib {i}')
