"""花雅堂实测三窗。X向照片右，Y向室内，墙外皮Y0，窗台上表面Z0。

按言衣草2016-11-02正立与右斜照片重建。2.40m轴距作为全模型的相对标尺。
玻璃后部、墙身、左右回转不在此模块。原创材质与模型依项目MIT许可。
"""
from pathlib import Path
from math import cos, sin, pi, sqrt
import numpy as np
from shapely.geometry import Polygon, LineString
from shapely.geometry import box as rectangle
from shapely.ops import unary_union

STONE = 'Huaya windows | warm grey cast stone'
EDGE = 'Huaya windows | carved pale relief'
BED = 'Huaya windows | recessed pediment field'
FRAME = 'Huaya windows | aged rose shutter rails'
BLADE = 'Huaya windows | faded red timber blades'
DARK = 'Huaya windows | deep shutter recess'
HINGE = 'Huaya windows | small hinge knuckles'
REVEAL = 'Huaya windows | shaded stone window reveals'

def finish(rgb, roughness):
    def linear(n):
        s=n/255.
        return s/12.92 if s<=.04045 else ((s+.055)/1.055)**2.4
    return dict(color=[linear(n) for n in rgb],roughness=roughness)

PALETTE = {STONE:finish((175,166,153),.89),EDGE:finish((190,182,169),.83),
           BED:finish((159,152,141),.92),FRAME:finish((121,76,77),.78),
           BLADE:finish((141,92,91),.73),DARK:finish((52,40,40),.94),
           HINGE:finish((83,58,54),.49),REVEAL:finish((135,120,110),.88)}
CENTRES=(-2.4,0.,2.4)
RANGE=(-.64,.64,.0,2.67)

def openings():
    return [(c+RANGE[0],c+RANGE[1],RANGE[2],RANGE[3]) for c in CENTRES]

def block(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)

def extrude(b,p,center,y_front,y_back,material,label):
    b.prism(p,-y_back,-y_front,lambda x,z,d:(center+x,-d,z),material,label)

def cubic_chain(start,cubics,steps):
    pts=[np.array(start,dtype=float)]
    for a,d,end in cubics:
        p=pts[-1]
        a,d,end=map(np.asarray,(a,d,end))
        for t in np.linspace(0.,1.,steps+1)[1:]:
            pts.append((1-t)**3*p+3*(1-t)**2*t*a+3*(1-t)*t*t*d+t**3*end)
    return np.array(pts)

def raised_stroke(b,center,uv,radii,y,mat,label,lod):
    """An open swept moulding with an elliptical crown and a flat bedding face."""
    uv=np.asarray(uv); radii=np.interp(np.linspace(0.,1.,len(uv)),
        np.linspace(0.,1.,len(radii)),radii)
    uv=uv.copy();uv[:,0]+=center
    sides=4 if lod else 8
    vertices=[]
    for i,(p,r) in enumerate(zip(uv,radii)):
        tangent=uv[min(i+1,len(uv)-1)]-uv[max(0,i-1)]
        normal=np.array([-tangent[1],tangent[0]])/np.linalg.norm(tangent)
        # Semicircular front with the underside just inside the parent relief.
        for a in np.linspace(0,pi,sides+1):
            u,z=p+normal*r*cos(a)
            vertices.append((u,y-r*.75*sin(a),z))
    stride=sides+1
    faces=[]
    for i in range(len(uv)-1):
        for j in range(stride):
            a=i*stride+j;d=i*stride+(j+1)%stride
            faces.append((a,d,d+stride,a+stride))
    faces.extend((tuple(reversed(range(stride))),
                  tuple(range(len(vertices)-stride,len(vertices)))))
    # Maintain the exterior orientation when the generating path reverses.
    volume=sum(np.dot(vertices[f[0]],np.cross(vertices[f[k]],vertices[f[k+1]]))
               for f in faces for k in range(1,len(f)-1))
    if volume<0:faces=[f[::-1] for f in faces]
    b.add(vertices,faces,mat,label)

def ornament(b,c,which,lod):
    """Centre is a recessed oval cartouche, reverse curls and a small trefoil foot.
    The right acanthus spray of the middle window was already absent in 2016.
    Outline points below are expressed relative to the pediment bed and its centre.
    """
    steps=3 if lod else 7
    base_z=2.865;bed_y=-.142
    def stroke(side,start,handles,radii,label,y=bed_y):
        pts=cubic_chain(start,handles,steps)
        pts[:,0]*=side;pts[:,1]+=base_z
        raised_stroke(b,c,pts,radii,y,EDGE,which+' | '+label,lod)
    for side in (-1,1):
        stroke(side,(0,.318),[
            ((.047,.322),(.107,.280),(.117,.227)),
            ((.144,.139),(.096,.092),(.063,.060)),
            ((.041,.036),(.057,.022),(.071,.013))],
            [.015,.020,.023,.017,.025,.016],'rolled foliate cartouche')
        stroke(side,(.109,.217),[
            ((.082,.208),(.091,.164),(.068,.169)),
            ((.035,.178),(.043,.208),(.060,.207))],
            [.020,.018,.022,.009],'inward rolled tip',bed_y-.009)
        stroke(side,(.065,.275),[
            ((.087,.323),(.045,.348),(.023,.341)),
            ((.015,.335),(.014,.320),(.020,.317))],[.008,.018,.015],
            'crest leaf')
        stroke(side,(.004,.043),[
            ((.026,.060),(.044,.035),(.067,.008)),
            ((.038,.004),(.027,.025),(.005,.023))],
            [.012,.025,.012,.007],'bifurcated foot')
        if which=='Middle window' and side==1:
            continue
        stroke(side,(.087,.046),[
            ((.127,.092),(.157,.117),(.203,.104)),
            ((.232,.098),(.226,.150),(.293,.144)),
            ((.365,.142),(.396,.050),(.333,.037)),
            ((.285,.022),(.277,.082),(.319,.087)),
            ((.341,.087),(.341,.058),(.328,.058))],
            [.011,.023,.019,.026,.020,.015,.007],'large springing volute',bed_y-.002)
        stroke(side,(.136,.064),[
            ((.154,.107),(.170,.158),(.208,.195)),
            ((.173,.178),(.143,.153),(.147,.118))],
            [.012,.025,.013,.004],'upswept jagged leaf')
        stroke(side,(.209,.092),[
            ((.234,.133),(.256,.171),(.294,.157)),
            ((.285,.175),(.243,.185),(.235,.158))],
            [.015,.025,.013,.004],'curled leaf apex')
        stroke(side,(.352,.071),[
            ((.392,.071),(.410,.102),(.433,.082)),
            ((.480,.033),(.499,.065),(.527,.044)),
            ((.548,.036),(.562,.055),(.577,.056))],
            [.018,.020,.013,.014,.007,.003],'outward leaf spray')
        stroke(side,(.418,.056),[
            ((.465,.050),(.435,.011),(.485,.014)),
            ((.497,.015),(.506,.030),(.518,.033))],
            [.016,.016,.009,.003],'lower acanthus lobe')
    # Shallow convex boss enclosed by, and below, the two raised curls.
    loop=np.linspace(0,2*pi,14 if lod else 30,endpoint=False)
    ring=[(c+.066*cos(a),bed_y-.004,base_z+.158+.092*sin(a)) for a in loop]
    crown=(c,bed_y-.028,base_z+.158)
    size=len(ring)
    backing=[(x,bed_y+.002,z) for x,_,z in ring]
    vertices=[*ring,*backing,crown]
    faces=[(i,(i+1)%size,2*size) for i in range(size)]
    faces.extend(((i+1)%size,i,size+i,size+(i+1)%size) for i in range(size))
    faces.append(tuple(reversed(range(size,2*size))))
    b.add(vertices,faces,BED,which+' | inset oval boss')

def pilaster(b,c,which,side,lod):
    x=c+side*.859;w=.147;tag=which+(' | left pilaster' if side<0 else ' | right pilaster')
    for half,y,z0,z1 in ((.198,-.204,.005,.214),(.181,-.190,.214,.249),
                          (.158,-.176,.249,.287),(w,-.139,.287,2.494),
                          (.164,-.182,2.494,2.525),(.18,-.205,2.525,2.573),
                          (.15,-.161,2.573,2.711),(.195,-.216,2.711,2.743),
                          (.221,-.240,2.743,2.782),(.246,-.267,2.782,2.826),
                          (.272,-.290,2.877,2.917),(.304,-.315,2.917,2.961)):
        block(b,x-half,x+half,y,.015,z0,z1,STONE,tag)
    block(b,x-.233,x+.233,-.239,.01,2.825,2.878,BED,tag)
    for u in np.linspace(-.19,.19,6):
        block(b,x+u-.020,x+u+.02,-.270,-.226,2.823,2.882,EDGE,tag+' dentils')
    # Recessed long shaft and traced diamond, V and double step incisions.
    field=rectangle(-.086,.327,.086,2.454)
    for j,(fade,width) in enumerate(((0.,.010),(.012,.006))):
        ring=field.buffer(-fade,join_style=2).difference(field.buffer(-fade-width,join_style=2))
        extrude(b,ring,x,-.153-.005*j,-.138,EDGE,tag+' shaft margins')
    for coords in ([(-.077,1.39),(0,1.19),(.077,1.39),(0,1.60),(-.077,1.39)],
                   [(-.066,1.20),(0,1.095),(.066,1.20)]):
        strip=LineString(coords).buffer(.0065,cap_style=2,join_style=2)
        extrude(b,strip,x,-.154,-.14,BED,tag+' diamond and chevron')
    for row in range(2):
        block(b,x-.061+row*.013,x+.061-row*.013,-.157,-.139,2.421-row*.022,2.429-row*.022,BED,tag+' stepped head')

def pediment(b,c,which,lod):
    for z0,z1,half,y in ((2.665,2.709,.865,-.171),(2.709,2.810,.955,-.190),
                          (2.810,2.831,1.031,-.242),(2.831,2.856,.962,-.201)):
        block(b,c-half,c+half,y,.012,z0,z1,STONE,which+' | lintel and drip')
    tri=Polygon([(-1.135,2.858),(1.135,2.858),(0,3.504)])
    extrude(b,tri,c,-.132,.015,BED,which+' | triangular tympanum')
    # Concave / convex section stepped in depth on both raking sides.
    for rise,half,thick,front in [(3.55,1.166,.056,-.233),(3.506,1.124,.045,-.211),
                                  (3.470,1.070,.037,-.178),(3.443,1.03,.033,-.205),
                                  (3.418,1.00,.021,-.174),(3.325,.876,.026,-.160)]:
        fall=.564
        p=Polygon([(-half,rise-half*fall),(0,rise),(half,rise-half*fall),
                   (half,rise-half*fall-thick),(0,rise-thick),(-half,rise-half*fall-thick)])
        extrude(b,p,c,front,-.125,EDGE if thick<.04 else STONE,which+' | stepped raking cornice')
    for side in (-1,1):
        for i in range(15):
            x=side*(.027+i*.057)
            z=3.388-.564*abs(x)
            slope=-side*.564; half=.016
            p=Polygon([(x-half,z-slope*half-.034),(x+half,z+slope*half-.034),
                       (x+half,z+slope*half+.018),(x-half,z-slope*half+.018)])
            extrude(b,p,c,-.196,-.128,EDGE,which+' | raking dentils')
    ornament(b,c,which,lod)

def shutter(b,c,tag,index,lod):
    # Two paired leaves on either side: the middle pair is slightly folded.
    width=.286;half=width/2
    centre=c+(index-1.5)*width
    depths=[.195,.225,.183,.207,.190]
    left,right=depths[index:index+2]
    start=len(b.parts)
    for x0,x1,z0,z1 in ((-half,-half+.042,.040,2.368),(half-.042,half,.040,2.368),
          (-half+.042,half-.042,.040,.202),(-half+.042,half-.042,1.663,1.747),
          (-half+.042,half-.042,2.270,2.368)):
        block(b,x0,x1,0,.048,z0,z1,FRAME,tag+' frames')
    for lower,upper,count in ((.202,1.663,30),(1.747,2.270,11)):
        pitch=(upper-lower)/count
        for i in range(count):
            # The bevel catches daylight. The underside slopes into the room.
            z=lower+(i+.5)*pitch
            y=np.array([.000,.004,.039,.039,.004])
            heights=np.array([z-.32*pitch,z-.39*pitch,z+.29*pitch,z+.42*pitch,z-.20*pitch])
            if lod:
                y=y[[0,2,3,4]];heights=heights[[0,2,3,4]]
            n=len(y);vertices=[(x,a,d) for x in (-half+.041,half-.041) for a,d in zip(y,heights)]
            # Profile winds CCW in Y,Z looking from positive X.
            faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
            faces+=[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
            b.add(vertices,faces,BLADE,tag+(' upper blades' if lower>1 else ' lower blades'))
    if not lod:
        for z in (.307,2.174):
            x=half-.009
            block(b,x-.006,x+.005,-.011,.003,z-.032,z+.032,HINGE,tag+' hinge knuckles')
    for part in b.parts[start:]:
        part['vertices']=[(centre+x,left+(x+half)/width*(right-left)+y,.071+1.088*z)for x,y,z in part['vertices']]

def add_windows(b,lod):
    initial=len(b.parts)
    for c,which in zip(CENTRES,('Left window','Middle window','Right window')):
        block(b,c-.64,c+.64,.276,.302,.008,2.664,DARK,which+' | recessed backing')
        for x0,x1 in ((-.64,-.572),(.572,.64)):
            block(b,c+x0,c+x1,.038,.271,.018,2.664,REVEAL,which+' | rebated jamb')
        # The dark surface above the leaves is the intrados of the deep reveal.
        # Its front and back edges can be distinguished in both pictures.
        yz=[(-.062,2.664),(.225,2.641),(.28,2.641),(.28,2.675),(-.062,2.675)]
        verts=[(c+x,y,z)for x in (-.64,.64)for y,z in yz]
        faces=[(4,3,2,1,0),(5,6,7,8,9)]+[(j,(j+1)%5,(j+1)%5+5,j+5)for j in range(5)]
        b.add(verts,faces,REVEAL,which+' | splayed stone soffit')
        for i in range(4):shutter(b,c,which+' | shutter '+str(i+1),i,lod)
        for side in (-1,1):pilaster(b,c,which,side,lod)
        pediment(b,c,which,lod)
    for part in b.parts[initial:]:
        points=np.array(part['vertices'])
        heights=points[:,2]
        # Correct the moulding profile using the two photographed cap heights.
        heights+=np.interp(heights,[0.,.3,1.6,2.525,2.856,2.961,3.55],[0.,0.,0.,-.080,.060,.035,.105])
        part['vertices']=points.tolist()
        if PALETTE[part["material"]].get("texture"):face_uv(part)

def register_textures():
    source=Path(__file__).parent
    for material,fname,factor in [(STONE,'huaya-cast-stone.jpg',.84),(BED,'huaya-cast-stone.jpg',.67),
                                  (EDGE,'huaya-cast-stone.jpg',1.),(BLADE,'huaya-painted-timber.jpg',1.),
                                  (FRAME,'huaya-painted-timber.jpg',.74)]:
        PALETTE[material].update(texture=str(source/fname),color=[factor]*3)

def face_uv(part):
    """Orient each solid face in its own plane; wood fibres follow rails and blades."""
    vertices=np.array(part['vertices'])
    output=[]; triangles=[]; uv=[]
    span=np.ptp(vertices,axis=0); vertical=part['material']==FRAME and span[2]>span[0]
    for tri in part['triangles']:
        p=vertices[list(tri)]
        n=np.abs(np.cross(p[1]-p[0],p[2]-p[0]))
        axes=((1,2),(0,2),(0,1))[int(np.argmax(n))]
        if vertical and 2 in axes:axes=axes[::-1]
        # Choose one continuous projection per planar surface. Clamped sampling
        # requires each part to remain within the original, portable swatch.
        low=vertices[:,axes].min(axis=0)
        scale=np.maximum(np.ptp(vertices[:,axes],axis=0),(.12,.12))
        tex=.02+.96*(p[:,axes]-low)/scale
        i=len(output);output.extend(map(tuple,p))
        uv.extend((float(a),float(1-b))for a,b in tex);triangles.append((i,i+1,i+2))
    part.update(vertices=output,texcoords=uv,triangles=triangles)

register_textures()
