"""Red iron garden balcony of the former No. 3 residence, transcribed from two 2015 views."""
from shapely.geometry import Polygon

# Physical frame from the two native 2015 views in registered-courtyard-cameras.json.
# Only the front roofed house wall, its railing and the exposed ends of the brackets were measurable.
LEFT, RIGHT, FRONT, BASE, TOP = 1.12, 4.54, -.90, 4.02, 5.06
PANEL_CENTRES = (122., 274., 420., 565., 712., 855., 998.)
OXIDE = 'Garden balcony | red oxide iron'
CREST = 'Garden balcony | grey green handrail crown'
BAND = 'Garden balcony | aged red collars'
STONE = 'Garden balcony | pale cement under slab corbels'

def material(rgb, roughness, metallic=0.):
    def linear(v):
        v /= 255
        return v / 12.92 if v < .04045 else ((v + .055)/1.055)**2.4
    return dict(color=[linear(v) for v in rgb],roughness=roughness,metallic=metallic)

PALETTE={OXIDE:material((137,80,67),.64,.39),BAND:material((114,66,58),.65,.4),
         CREST:material((111,117,106),.63,.43),STONE:material((156,145,132),.9)}

def _cubic(start, controls, samples):
    result=[start]
    for cp1,cp2,end in controls:
        x0,y0=result[-1]
        for i in range(1,samples+1):
            t=i/samples;s=1.-t
            result.append((s**3*x0+3*s*s*t*cp1[0]+3*s*t*t*cp2[0]+t**3*end[0],
                           s**3*y0+3*s*s*t*cp1[1]+3*s*t*t*cp2[1]+t**3*end[1]))
    return result

def _bar(b,points,width,depth,point,mat,label):
    """Mitred rectangular flat bar with continuous paired edges, including both ends."""
    if len(points)<2:return
    vectors=[]
    for a,c in zip(points,points[1:]):
        dx,dy=c[0]-a[0],c[1]-a[1];length=(dx*dx+dy*dy)**.5
        if length<1e-10:raise ValueError('Repeated flat-bar centreline vertex')
        vectors.append((-dy/length,dx/length))
    verts=[]
    for i,(x,y) in enumerate(points):
        a=vectors[max(0,i-1)];c=vectors[min(len(vectors)-1,i)]
        # Intersect the two offset half-width lines. No coincident ends or internal cross sections.
        denom=1+a[0]*c[0]+a[1]*c[1]
        nx=(a[0]+c[0])*width/(2*denom);ny=(a[1]+c[1])*width/(2*denom)
        verts.extend([point(x-nx,y-ny,-depth/2),point(x+nx,y+ny,-depth/2),
                      point(x+nx,y+ny,depth/2),point(x-nx,y-ny,depth/2)])
    faces=[(3,2,1,0),tuple(4*(len(points)-1)+k for k in range(4))]
    for i in range(len(points)-1):
        for k in range(4):faces.append((4*i+k,4*i+(k+1)%4,4*i+4+(k+1)%4,4*i+4+k))
    b.add(verts,faces,mat,label)

def _flat(b,uv,width,depth,mapper,label,material=OXIDE):
    # All traced iron patterns use source pixels after rectifying the front of study2015-02.
    points=[((RIGHT-LEFT)*u/1120, (TOP-BASE)*(335-v)/335) for u,v in uv]
    _bar(b,points,width,depth,mapper,material,label)

def _design(b,center,mapper,tag,lod):
    """Seven repeated panels carry opposed S scrolls interrupted by short angled bends."""
    n=3 if lod else 6
    def trace(path,width,label,metal=OXIDE):
        _flat(b,path,width,.014,mapper,tag+' '+label,metal)
    # The central flat strip has a riveted junction at each end of the paired S shapes.
    trace([(center,73),(center,275)],.019,'centre standard')
    for side in (-1,1):
        for upper in (True,False):
            def mirror(path):
                return [(center+side*x, y if upper else 351-y) for x,y in path]
            tip=_cubic((0,77),[((7,67),(19,74),(16,81)),((14,86),(10,86),(9,82))],n)
            trace(mirror(tip),.008,'curled tip')
            shank=[(2,80),(15,102),(7,113)]
            shank+=_cubic(shank[-1],[((17,131),(26,154),(21,165)),((16,177),(4,174),(5,165)),((5,161),(11,160),(12,164))],n)[1:]
            trace(mirror(shank),.0105,'scrolled blade')
    for v in (78,171,180,272):
        trace([(center-2.1,v),(center+2.1,v)],.016,'binding strip',BAND)

def add_balcony_iron(b,lod=False):
    """Add the railing and the two photographed stepped supports; slab supplied by the facade."""
    b.palette.update(PALETTE)
    def front(u,z,d):return LEFT+u,FRONT-d,BASE+z
    def left(u,z,d):return LEFT+d,FRONT+u,BASE+z
    def right(u,z,d):return RIGHT+d,FRONT+u,BASE+z
    span=RIGHT-LEFT;rise=TOP-BASE;ret=-FRONT
    # The grey crown overhangs the narrower red fascia. Its shallow convex top has a flat bearing.
    profile=[(-.026,-.019),(.026,-.019),(.026,-.001),(.022,.005),(.012,.009),(-.012,.009),(-.022,.005),(-.026,-.001)]
    polygon=Polygon(profile)
    for face,length,tag in ((front,span,'front'),(left,ret,'left return'),(right,ret,'right return')):
        # Orient the mapper consistently for a right-handed prism including the two returns.
        if face is front:
            mapper=lambda x,z,u:front(u,rise+z,-x)
        else:
            mapper=lambda x,z,u,face=face:face(u,rise+z,-x)
        b.prism(polygon,0,length,mapper,CREST,tag+' shallow rounded handrail')
        for v,h,w in ((13,.028,.034),(34,.012,.019),(69,.023,.031),(277,.022,.029),
                      (295,.012,.020),(326,.014,.023)):
            z=rise*(1-v/335)
            _bar(b,[(0,z),(length,z)],h,w,face,OXIDE,tag+' horizontal rail')
    def frontpost(x,v0,v1,width,tag):
        _flat(b,[(x,v0),(x,v1)],width,.025,front,tag)
    for k,u in enumerate((6.,1114.)):
        frontpost(u,13,336,.030,'front corner standard '+str(k+1))
    boundaries=[(a+c)/2 for a,c in zip(PANEL_CENTRES,PANEL_CENTRES[1:])]
    for i,x in enumerate(boundaries):
        lab='joint '+str(i+1)
        frontpost(x,14,147,.021,lab+' upper')
        frontpost(x,177,335,.021,lab+' lower')
        for side in (-1,1):
            path=[(x,145),(x+side*4,149),(x+side*13,158),(x+side*6,168),(x,179)]
            _flat(b,path,.011,.021,front,lab+' open diamond')
            frontpost(x+side*10,68,155,.013,lab+' upper flanking pale')
            frontpost(x+side*10,168,279,.013,lab+' lower flanking pale')
    for i,x in enumerate(PANEL_CENTRES):
        tag='front panel '+str(i+1)
        _design(b,x,front,tag,lod)
        for side in (-1,1):
            # The uninterrupted intermediate pales are separately visible between a scroll and its joint.
            for offset in (36.,51.):
                frontpost(x+side*offset,69,277,.012,tag+' plain intermediate pale')
            a=x+side*62
            p=_cubic((x,39),[((side*8+x,23),(side*18+x,38),(side*13+x,40)),
                               ((side*7+x,48),(x+side*5,36),(x+side*11,35))],3 if lod else 6)
            _flat(b,p,.009,.014,front,tag+' crown curl')
            wing=_cubic((x,40),[((x+side*11,13),(x+side*43,57),(a,49)),
                                   ((a+side*6,47),(a+side*7,39),(a+side*1,39))],4 if lod else 8)
            _flat(b,wing,.009,.014,front,tag+' top scroll')
            # Two small compressed scrolls next to each front joint in the low band.
            x0=x+side*54
            curls=_cubic((x0,298),[((x0+side*9,298),(x0+side*10,309),(x0,309)),
                                    ((x0-side*5,309),(x0-side*5,303),(x0,304))],3 if lod else 5)
            _flat(b,curls,.008,.013,front,tag+' lower bow')
            _flat(b,[(u,622-v) for u,v in curls],.008,.013,front,tag+' paired lower bow')
    # Besides the end posts there are narrower straight members between the openwork and the corner.
    for u in (27.,44.,64.,1056.,1077.,1094.):
        frontpost(u,69,277,.014,'end bay plain upright')
    for face,tag in ((left,'left return'),(right,'right return')):
        for j,frac in enumerate((.30,.49,.70,.97)):
            _bar(b,[(frac*ret,.006),(frac*ret,rise-.024)],.018 if j in (1,3) else .013,.020,face,OXIDE,tag+' upright '+str(j+1))
        # At the outer corner the stair-shaped brace lies outside the first vertical plain pale.
        for high in (True,False):
            path=[(.015,.865),(.045,.865),(.060,.826),(.043,.800),(.080,.773),(.083,.742),(.111,.733)]
            uv=[(u*ret,z*rise if high else (1-z)*rise)for u,z in path]
            _bar(b,uv,.012,.017,face,OXIDE,tag+' stepped corner strap')
        if face is left:
            # A single visible body of scrollwork on the courtyard side, behind the seven front panels.
            # Its rear tip is interrupted by the front railing and vegetation.
            def returning(u,z,d):return face(ret*.53+u-span*.50,z,d)
            _design(b,560,returning,'left return visible curl',lod)
    # The brackets are cement, broad and stepped into the wall. Their undersides appear in both 2015 views.
    profile=Polygon([(-.85,3.79),(.018,3.79),(.018,3.46),(-.40,3.46),(-.48,3.49),
                     (-.58,3.56),(-.65,3.64),(-.74,3.64),(-.79,3.73),(-.85,3.73)])
    for x,label in ((LEFT+.035,'west'),(RIGHT-.06,'east')):
        b.prism(profile,x-.086,x+.086,lambda y,z,t:(t,y,z),STONE,label+' stepped cement support below slab')
