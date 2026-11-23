"""Garden elevation photographed by Fayhoo. Control points are native image pixels.

metric(u, v) supplies local X and Z. Y increases into the wall. The foliage
covering the first crest and the underside of the balcony limits their detail.
"""
from math import cos, sin, pi
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union

WOOD = 'Nanlin | oiled canopy timber'
IRON = 'Nanlin | dark balcony metal'
GLASS = 'Nanlin | blue-grey crown glass'
LEAD = 'Nanlin | crown glazing bars'
PALE = 'Nanlin | worn raised stone relief'
BROWN = 'Nanlin | weathered brick coping'
PALETTE = {
    WOOD: {'color':[.076,.049,.035], 'roughness':.76},
    IRON: {'color':[.045,.049,.045], 'roughness':.59, 'metallic':.24},
    GLASS: {'color':[.115,.161,.168], 'roughness':.26, 'metallic':.11},
    LEAD: {'color':[.067,.071,.066], 'roughness':.70},
    PALE: {'color':[.52,.436,.335], 'roughness':.92},
    BROWN: {'color':[.27,.089,.048], 'roughness':.91},
}
# At these surveyed joints the continuous projecting brick table passes
# to the wall model. Top and bottom of the rails have separate measured slopes.
WEST_BASE = [(234,451),(500,459),(700,465),(946,473)]
CENTRE_BASE = [(946,473),(1205,486),(1455,499)]
EAST_BASE = [(1658,513),(1800,521),(2074,538)]
BOTTLES = [
    [976,993,1009,1025,1041,1057,1073,1089,1104,1120,1136,1152,1167,1183],
    [1233,1248,1263,1278,1293,1309,1324,1339,1354,1369,1384,1399,1414,1429],
]

def at(points, x):
    for (xa,ya),(xb,yb) in zip(points,points[1:]):
        if x <= xb:
            return ya+(yb-ya)*(x-xa)/(xb-xa)
    return points[-1][1]

def quad(start, mid, end, n):
    out = []
    for i in range(n+1):
        t=i/n; s=1.-t
        out.append((s*s*start[0]+2*s*t*mid[0]+t*t*end[0],
                    s*s*start[1]+2*s*t*mid[1]+t*t*end[1]))
    return out

def band(points, depth):
    return Polygon(points+[(u,v+depth) for u,v in reversed(points)])

def stroke(points, radius):
    return LineString(points).buffer(radius, cap_style=2, join_style=2)

def flatten(metric, pixel_shape):
    """Convert each edge and each interior opening to the fitted facade plane."""
    for part in getattr(pixel_shape,'geoms',[pixel_shape]):
        if part.geom_type=='Polygon' and part.area>.001:
            def ring(vertices):
                return [metric(float(u),float(v)) for u,v in vertices.coords]
            yield Polygon(ring(part.exterior), [ring(r) for r in part.interiors])

def crown_profiles(lod=False):
    n=18 if lod else 38
    # The western arc is partly lost to leaves. Its right haunch, both bracket
    # drops, shadowed window and the slopes of the two shoulders remain readable.
    west_arc=[(602+81*cos(t*pi/n),365+3.9*cos(t*pi/n)-68*sin(t*pi/n))
              for t in range(n,-1,-1)]
    east_arc=[(1873+55*cos(t*pi/n),416+2.3*cos(t*pi/n)-59*sin(t*pi/n))
              for t in range(n,-1,-1)]
    return [
        ('West',WEST_BASE,[(234,401),(266,402),(286,401),(335,393),(406,379),
         (457,368),(474,364),(478,354),(506,354),(514,364),*west_arc,
         (695,370),(701,352),(721,353),(727,374),(755,382),(817,397),
         (876,414),(910,420),(946,423)],west_arc,[(489,402),(712,408)]),
        ('East',EAST_BASE,[(1658,456),(1693,458),(1725,437),(1749,420),
         (1755,410),(1772,412),(1772,386),(1803,389),(1802,411),
         *east_arc,(1930,420),(1931,395),(1961,397),(1960,425),(1975,427),
         (1980,437),(2025,471),(2046,482),(2074,484)],east_arc,[(1789,445),(1944,453)]),
    ]

def draw_crowns(put, metric, grey, red, stone, lod):
    n=9 if lod else 18
    for name,base,outline,arc,brackets in crown_profiles(lod):
        body=Polygon(outline+list(reversed(base))).buffer(0)
        if name=='West':
            # Behind the branch: only the visible upper part of the rectangular
            # glazed opening is continued to the two jamb heads.
            glazing=Polygon([(572,365),(626,367),(627,435),(570,433)])
            body=body.difference(glazing)
        put(body,0,.285,grey,name+' shaped brick parapet')
        put(band(outline,6.1).buffer(0),-.057,.294,red,name+' red shoulder and arch')
        put(band(outline,2.1).buffer(0),-.083,.31,BROWN,name+' raised weather cap')
        put(band(arc,8.4),-.082,.302,red,name+' outer arch mould')
        put(band(arc,2.25),-.114,.314,stone,name+' arch drip')
        for j,(cx,top) in enumerate(brackets):
            # The tiny acanthus drops are pendants under red-stepped shoes.
            width=18 if name=='West' else 16
            put(Polygon([(cx-width,top-2),(cx+width,top),(cx+width-4,top+7),
                         (cx-width+3,top+5)]),-.106,.014,BROWN,f'{name} shoe {j+1}')
            sh=Polygon([(cx-width+3,top+5),(cx+width-3,top+7),(cx+8,top+15),
                        (cx+3,top+22),(cx-3,top+22),(cx-7,top+16)])
            put(sh,-.091,.016,stone,f'{name} hanging corbel {j+1}')
            for side in [-1,1]:
                pts=quad((cx,top+19),(cx+side*3,top+8),(cx+side*10,top+8),n)
                put(stroke(pts,1.25),-.111,-.088,PALE,f'{name} corbel leaf {j+1} {side}')
        if name=='West':
            outer=glazing.buffer(6.2,join_style=2)
            put(outer.difference(glazing),-.065,.147,red,'West window brick jambs')
            put(glazing,.071,.090,GLASS,'West recessed crown glazing')
            for j,f in enumerate((1/3,2/3)):
                x=571+55*f
                put(stroke([(x,365),(x-.7,434)],.98),.051,.076,LEAD,f'West crown mullion {j+1}')
            put(stroke([(571,398),(626,400)],1.45),.048,.075,LEAD,'West crown crossbar')
            put(Polygon([(553,435),(643,438),(644,447),(552,444)]),-.119,.12,stone,'West window sill')
            continue
        # A separately framed vertical foliate stone, with a low horizontal frieze.
        outer=Polygon([(1826,412),(1907,418),(1912,481),(1830,476)])
        inner=Polygon([(1843,425),(1893,429),(1897,469),(1845,468)])
        put(outer.difference(inner),-.115,.03,stone,'East carved panel frame')
        put(inner,-.047,.014,stone,'East recessed carved field')
        put(Polygon([(1824,475),(1914,480),(1916,489),(1824,484)]),-.159,.045,stone,'East carved panel sill')
        put(Polygon([(1828,485),(1912,489),(1912,518),(1830,512)]),-.041,.012,red,'East small plaque brick frame')
        put(Polygon([(1838,495),(1902,499),(1903,510),(1838,505)]),-.075,-.03,stone,'East frieze ground')
        # Paired upper fronds and two oppositely wound lower volutes. The stem
        # emerges from the fork at the centre of the source stone.
        for side in [-1,1]:
            x0,y0=1870.,448.
            def conv(points):return [(x0+side*x,y0+y+.054*side*x) for x,y in points]
            stem=quad((0,13),(1,-3),(4,-11),n)+quad((4,-11),(7,-20),(14,-20),n)[1:]
            top=quad((3,-7),(8,-10),(17,-8),n)+quad((17,-8),(15,-16),(10,-16),n)[1:]
            petal=quad((4,3),(13,-2),(19,1),n)+quad((19,1),(19,-3),(15,-5),n)[1:]
            curl=quad((1,2),(3,17),(13,16),n)+quad((13,16),(23,14),(18,6),n)[1:]+quad((18,6),(13,2),(11,9),n)[1:]
            for j,line in enumerate((stem,top,petal,curl)):
                put(stroke(conv(line),1.45 if j==2 else 1.8),-.099,-.045,PALE,f'East foliage {side} {j+1}')
        for j in range(5):
            x=1842+j*11.7; y=499+(x-1842)*.058
            line=quad((x,y+2),(x+4,y-3),(x+8,y),n)
            put(stroke(line,1.2),-.088,-.071,PALE,f'East frieze curl {j+1}')

def balustrade(b,put,metric,grey,red,stone,lod):
    tracks=([(968,403),(1199,415)],[(1226,418),(1444,429)])
    beds=([(967,454),(1198,467)],[(1227,468),(1445,480)])
    for j,(axis,top,bed) in enumerate(zip(BOTTLES,tracks,beds),1):
        put(band(top,6.9),-.099,.185,stone,f'Rail {j} stone handrail')
        put(band(top,2.1),-.114,.20,PALE,f'Rail {j} upper lip')
        put(band(bed,6.3),-.093,.186,stone,f'Rail {j} stone bed')
        zbase=[(bed[0][0],at(CENTRE_BASE,bed[0][0])),(bed[-1][0],at(CENTRE_BASE,bed[-1][0]))]
        put(Polygon([(x,y+6) for x,y in bed]+list(reversed(zbase))),-.008,.233,red,f'Rail {j} brick curb')
        # Lathe the surveyed profile. It has a square block at both ends and
        # a long taper under the central bulb. Top blocks follow the real incline.
        for k,cx in enumerate(axis,1):
            tv=at(top,cx)+6.9; bv=at(bed,cx)
            xc,zt=metric(cx,tv); _,zb=metric(cx,bv)
            xm,_=metric(cx-4.8,tv);xp,_=metric(cx+4.8,tv)
            r=(xp-xm)*.50; h=zt-zb; yc=.045
            profile=((0,.92),(.07,.92),(.105,.72),(.17,.70),(.235,.33),
                     (.32,.29),(.50,.61),(.62,.73),(.69,.59),(.73,.32),
                     (.79,.35),(.84,.83),(1.,.83))
            sides=8 if lod else 12
            vv=[]
            for f,rr in profile:
                for i in range(sides):
                    t=i*2*pi/sides; vv.append((xc+r*rr*cos(t),yc+r*rr*sin(t),zb+h*f))
            ff=[]
            for row in range(len(profile)-1):
                for i in range(sides):
                    a=row*sides+i;d=row*sides+(i+1)%sides
                    ff.extend(((a,d,d+sides),(a,d+sides,a+sides)))
            p0=len(vv);vv.extend(((xc,yc,zb),(xc,yc,zt)))
            last=(len(profile)-1)*sides
            for i in range(sides):
                nxt=(i+1)%sides
                ff.extend(((p0,nxt,i),(p0+1,last+i,last+nxt)))
            b.add(vv,ff,stone,f'Rail {j} turned baluster {k:02}')
    for j,(cx,top,half) in enumerate([(951,379,14),(1210,395,15)],1):
        base=at(CENTRE_BASE,cx)
        put(Polygon([(cx-half,top+4),(cx+half,top+5),(cx+half,base),(cx-half,base-1)]),-.019,.26,grey,f'Rail pier {j}')
        put(band([(cx-half-4,top-4),(cx+half+4,top-3)],7.8),-.096,.32,BROWN,f'Rail pier {j} cap')
        put(band([(cx-half,base-14),(cx+half,base-13)],12),-.041,.271,red,f'Rail pier {j} red foot')

def balcony(put,metric,stone,lod):
    # The railing plane lies under the dark fascia, in front of the recessed
    # wall. Depths are section estimates; the back windows belong to the wall.
    y=-.85
    beam=[(443,502),(885,517)]
    put(band(beam,9),y-.105,.085,WOOD,'Balcony timber fascia')
    put(band(beam,2.1),y-.143,.12,IRON,'Balcony hood drip')
    cols=[(455,511,658),(661,518,667),(867,525,674)]
    for j,(cx,head,rail) in enumerate(cols,1):
        bot=at([(455,755),(867,768)],cx)
        put(Polygon([(cx-3.8,head+12),(cx+4,head+12),(cx+4,bot),(cx-4,bot)]),y-.034,y+.063,IRON,f'Balcony post {j}')
        put(box(cx-5.5,head,cx+6,head+40),y-.066,y+.09,WOOD,f'Balcony timber block {j}')
        put(box(cx-5.7,head+39,cx+5.9,head+44),y-.065,y+.09,IRON,f'Balcony post collar {j}')
    for j in range(2):
        l,lt,_=cols[j];r,rt,_=cols[j+1];n=9 if lod else 20
        fl=quad((l+3,lt+41),(l+17,lt+9),(l+56,lt+11),n)
        fr=quad((r-55,rt+10),(r-15,rt+10),(r-4,rt+38),n)
        put(stroke(fl,3.5),y-.023,y+.106,WOOD,f'Balcony {j+1} left knee')
        put(stroke(fr,3.5),y-.023,y+.106,WOOD,f'Balcony {j+1} right knee')
        for idx,cx in enumerate([l+58,r-49]):
            h=lt+(rt-lt)*(cx-l)/(r-l)
            put(Polygon([(cx-3,h+8),(cx+3,h+8),(cx+2,h+14),(cx,h+17),(cx-2.5,h+14)]),y-.046,y+.054,WOOD,f'Balcony {j+1} turned drop {idx+1}')
        # The open fret is legible only under the centre, between the drops.
        for k in range(4):
            sx=l+66+k*19; hy=lt+10+(sx-l)*(rt-lt)/(r-l)
            curl=quad((sx,hy),(sx+4,hy+8),(sx+10,hy+5),n)+quad((sx+10,hy+5),(sx+15,hy+1),(sx+10,hy),n)[1:]
            put(stroke(curl,.82),y+.012,y+.043,IRON,f'Balcony {j+1} scroll {k+1}')
    rail=[(452,658),(867,673)]
    put(band(rail,3.8),y-.08,y+.083,WOOD,'Balcony continuous handrail')
    sill=[(449,755),(869,768)]
    put(band(sill,5),y-.095,.085,stone,'Balcony sill plate')
    # The intact panels east of the centre post give the spacing, also visible
    # immediately west of it. Foliage conceals individual feet near both ends.
    for k in range(1,30):
        x=453+14.1*k
        if abs(x-661)<7:continue
        v=at(rail,x)+3.; base=at(sill,x)
        put(Polygon([(x-1.7,v),(x+1.7,v),(x+1.5,base),(x-1.5,base)]),y-.027,y+.024,IRON,f'Balcony rail picket {k:02}')

def balcony_eye(metric):
    """Estimate the oblique viewing ray from the Nikon D90 27-mm equivalent lens.

    A local plane homography is fitted to the front elevation chart. Its third
    independent direction follows the cross product of the two in-plane rays.
    The estimate sets perspective for short returns and does not survey depth.
    """
    import numpy as np
    pairs=[]
    for u in np.linspace(385,944,8):
        for v in np.linspace(480,790,5):
            x,z=metric(u,v);p=np.array([x,z,1.])
            pairs.extend([np.r_[p,np.zeros(3),-u*p],np.r_[np.zeros(3),p,-v*p]])
    _,_,vectors=np.linalg.svd(np.asarray(pairs),full_matrices=False)
    h=vectors[-1].reshape(3,3);h/=h[2,2]
    k=np.array([[1608.,0,1072.],[0,1608.,712.],[0,0,1.]])
    normalized=np.linalg.solve(k,h)
    rx,rz=normalized[:,0],normalized[:,1]
    ry=np.cross(rz,rx)
    ry*=np.sqrt(np.linalg.norm(rx)*np.linalg.norm(rz))/np.linalg.norm(ry)
    eye=-np.linalg.solve(np.column_stack((rx,ry,rz)),normalized[:,2])
    if eye[1]>0:eye[1]*=-1
    return eye

def balcony_returns(b,metric,eye,stone):
    """Short returns rigidly join the handrail, floor and two wall abutments."""
    import numpy as np
    def rig(u,v,y):
        x,z=metric(u,v);p=np.array((x,0.,z));return p+(eye-p)*(y/eye[1])
    def block(cx,xsize,y0,y1,zc,zsize,material,label):
        b.box((cx,(y0+y1)/2,zc),(xsize,y1-y0,zsize),material,label=label)
    for side,top,floor in [('W',(455,659),(455,755)),('E',(867,673),(867,767))]:
        x,y,zt=rig(*top,-.87);_,_,zb=rig(*floor,-.87)
        block(x,.067,-.87,.033,zt-.013,.054,WOOD,'Balcony '+side+' return handrail')
        block(x,.053,-.87,.018,zb+.038,.05,IRON,'Balcony '+side+' return base tie')
        for k,depth in enumerate([-.66,-.44,-.22],1):
            block(x,.026,depth-.015,depth+.015,(zt+zb)/2,zt-zb-.045,IRON,f'Balcony {side} return bar {k}')
        block(x,.092,-.055,.019,zt-.01,.092,IRON,'Balcony '+side+' wall socket')

def add_ornaments(b,lod,metric):
    """Add two distinct brick crests, central stone runs and the balcony front."""
    import fabric
    for k,v in PALETTE.items(): b.palette.setdefault(k,v)
    grey=fabric.GRAY; red=fabric.RED; stone=fabric.STONE
    def put(shape,front,back,material,label):
        for part in flatten(metric,shape):
            if part.area>1e-8:
                fabric.face(b,part,front,back,material,label)
    draw_crowns(put,metric,grey,red,stone,lod)
    balustrade(b,put,metric,grey,red,stone,lod)
    eye=balcony_eye(metric)
    def put_balcony(shape,front,back,material,label):
        def relocated(u,v):
            x,z=metric(u,v);ratio=front/eye[1]
            return x+(eye[0]-x)*ratio,z+(eye[2]-z)*ratio
        for part in flatten(relocated,shape):
            fabric.face(b,part,front,back,material,label)
    balcony(put_balcony,metric,stone,lod)
    balcony_returns(b,metric,eye,stone)
