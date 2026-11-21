"""Four supports and the east curved entablature of the street portico, Fuxing Middle Road 1331."""
from math import cos, sin, pi, sqrt
from shapely.geometry import box, Polygon, LineString
from shapely.ops import unary_union

PALETTE = {
    'shaft aggregate': {'color':[.57,.55,.50], 'roughness':.91},
    'dressed grey stone': {'color':[.54,.51,.45], 'roughness':.88},
    'carved pale stone': {'color':[.65,.61,.53], 'roughness':.86},
    'shadowed stone moulding': {'color':[.47,.44,.38], 'roughness':.95},
    'pale parapet': {'color':[.66,.63,.56], 'roughness':.90},
    'soffit': {'color':[.48,.46,.42], 'roughness':.94},
}
SPAN=5.71
SOFFIT=3.79
RAIL_FOOT=4.48
RAIL_HEAD=5.19
RAIL_LEFT=.22
RAIL_RIGHT=5.38
PANELS=10
AXES=[(-.30,.12),(.30,.12),(SPAN-.34,.12),(SPAN+.34,.12)]

def front_y(x):
    # The cladding and handrail follow one continuous bowed side. X is the support chord.
    t=max(0.,min(1.,x/SPAN))
    return -.40*4*t*(1-t)

def plan(x,depth):
    return (x,front_y(x)+depth)

def strip(b,x0,x1,front,back,z0,z1,mat,lab,n):
    xs=[x0+(x1-x0)*i/n for i in range(n+1)]
    boundary=[plan(x,front) for x in xs]+[plan(x,back) for x in reversed(xs)]
    b.plan_prism(Polygon(boundary),z0,z1,mat,lab)

def leaf(b,x,y,a,base,height,radius,wide,low,label):
    n=4 if low else 7
    verts=[]
    for j in range(n+1):
        z=j/n
        half=wide*(.18+.82*sin(pi*z)**.78)
        radial=radius+.045*sin(z*pi*.78)+.043*z**3
        for t,extra in [(-1.,0.),(0.,.024*sin(pi*z)),(1.,0.)]:
            u,v=radial+extra,t*half
            verts.append((x+u*cos(a)-v*sin(a),y+u*sin(a)+v*cos(a),base+height*z))
    faces=[]
    for j in range(n):
        i=3*j
        faces.extend([(i,i+1,i+4,i+3),(i+1,i+2,i+5,i+4)])
    b.add(verts,faces,'carved pale stone',label)
    if not low:
        centers=[verts[j*3+1] for j in range(1,n)]
        b.tube(centers,.008,'dressed grey stone',sides=5,label=label+' leaf ribs')

def column(b,x,y,index,low):
    material='shaft aggregate'
    outer='carved pale stone';neck='shadowed stone moulding'
    n=14 if low else 36
    b.lathe((x,y),[(.00,.238),(.085,.245),(.145,.227),(.28,.224),(.90,.225),(2.76,.211),(3.28,.203)],
            material,n,f'Column {index} smooth tapered shaft')
    b.lathe((x,y),[(3.28,.203),(3.31,.216),(3.328,.231),(3.351,.232),(3.370,.214)],
            neck,n,f'Column {index} collar')
    b.lathe((x,y),[(3.370,.215),(3.43,.222),(3.55,.239),(3.65,.261),(3.704,.319)],
            'dressed grey stone',n,f'Column {index} bell')
    for row,(z,h,r,count) in enumerate([(3.367,.180,.215,10),(3.452,.209,.228,10)]):
        for k in range(count):
            a=2*pi*(k+.5*row)/count
            leaf(b,x,y,a,z,h,r,.066,low,f'Column {index} capital foliage course {row+1}')
    for k in range(4):
        a=pi/4+k*pi/2
        for turn in (-1,1):
            points=[]
            for j in range(10 if low else 18):
                v=j/(9 if low else 17)
                angle=1.36*pi-v*1.9*pi
                t=turn*(.087+.051*(1-.72*v)*cos(angle))
                z=3.647+.05*(1-.72*v)*sin(angle)
                d=.277
                points.append((x+d*cos(a)-t*sin(a),y+d*sin(a)+t*cos(a),z))
            b.tube(points,.015,'carved pale stone',sides=5 if low else 8,label=f'Column {index} corner scrolls')
    for z,h,width,mat in [(3.706,.035,.595,outer),(3.741,.049,.643,'dressed grey stone')]:
        b.box((x,y,z+h/2),(width,width,h),mat,label=f'Column {index} abacus')

def panel_shape():
    width=(RAIL_RIGHT-RAIL_LEFT)/PANELS
    height=RAIL_HEAD-RAIL_FOOT
    bounds=box(0,0,width,height)
    arms=[LineString(ends).buffer(.044,cap_style=2,join_style=2)for ends in (
        [(0,0),(width,height)],[(0,height),(width,0)])]
    return unary_union([box(0,0,.038,height),box(width-.038,0,width,height),*arms]).intersection(bounds)

def panel(b,index):
    width=(RAIL_RIGHT-RAIL_LEFT)/PANELS
    x0=RAIL_LEFT+index*width;x1=x0+width
    slope=(front_y(x1)-front_y(x0))/width
    b.prism(panel_shape(),-.13,.015,
        lambda u,z,d:(x0+u,front_y(x0)+slope*u-d,z+RAIL_FOOT),
        'pale parapet',f'Open saltire railing {index+1}')

def parapet_pier(b,x,width,small,label):
    y=front_y(x)+.057
    courses=[(4.42,4.50,width+.07),(4.50,4.54,width+.026),(4.54,5.23,width),(5.23,5.265,width+.055),
             (5.265,5.325,width+.083),(5.325,5.360,width+.027)]
    for z0,z1,size in courses:
        b.box((x,y,(z0+z1)/2),(size,.337+(size-width),z1-z0),'dressed grey stone',label=label+' rectangular plinth and cap')
    z0,z1=4.628,5.145;ww=width-.106
    b.box((x,y-.177,(z0+z1)/2),(ww,.026,z1-z0),'carved pale stone',label=label+' shallow recessed panel surround')
    b.box((x,y-.193,(z0+z1)/2),(ww-.062,.012,z1-z0-.072),'pale parapet',label=label+' panel field')
    b.lathe((x,y),[(5.360,.073),(5.382,.077),(5.421,.046),(5.439,.018)],
            'carved pale stone',8 if small else 16,label+' stone cap button')

def add_portico(b,lod=False):
    for i,(x,y) in enumerate(AXES):
        column(b,x,y,i+1,lod)
    n=12 if lod else 36
    # The model ends with the two first-front standards and the soffit directly above their columns.
    courses=[(3.79,3.82,-.274,.532,'soffit'),(3.82,3.867,-.288,.532,'shadowed stone moulding'),
        (3.867,3.962,-.242,.532,'dressed grey stone'),(3.962,4.078,-.255,.532,'carved pale stone'),
        (4.078,4.105,-.292,.532,'shadowed stone moulding'),(4.105,4.217,-.241,.532,'dressed grey stone'),
        (4.217,4.249,-.266,.532,'carved pale stone'),(4.249,4.292,-.326,.532,'shadowed stone moulding'),
        (4.292,4.347,-.351,.532,'carved pale stone'),(4.347,4.404,-.303,.532,'dressed grey stone')]
    for i,(lo,hi,f,r,m) in enumerate(courses):
        strip(b,-.64,SPAN+.69,f,r,lo,hi,m,f'Curved architrave section {i+1}',n)
    for j in range(49):
        x=-.59+j*(SPAN+1.24)/48
        slope=front_y(x+.01)-front_y(x-.01)
        axis=(1.,slope/.02,0.);side=(-axis[1],1.,0.)
        b.box((x,front_y(x)-.262,4.174),(.073,.082,.077),'carved pale stone',
            basis=(axis,side,(0.,0.,1.)),label='Dentils below the portico parapet')
    for i in range(PANELS):
        panel(b,i)
    for lo,hi,f,r,name in [(4.404,4.445,-.052,.176,'lower sill'),(4.445,RAIL_FOOT,-.031,.155,'lower fillet'),
        (RAIL_HEAD,5.229,-.045,.163,'handrail fillet'),(5.229,5.29,-.069,.186,'bowed cap rail')]:
        strip(b,RAIL_LEFT,RAIL_RIGHT,f,r,lo,hi,'pale parapet',name,n)
    for x,w,name in [(0.,.388,'East terminal standard'),(5.593,.416,'First front standard'),(6.236,.454,'Paired front standard')]:
        parapet_pier(b,x,w,lod,name)
    strip(b,5.79,6.01,-.024,.155,4.53,5.075,'dressed grey stone','Short solid infill between the paired standards',2)
