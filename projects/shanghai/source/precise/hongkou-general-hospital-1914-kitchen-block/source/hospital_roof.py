"""Measured roof cornice, pierced parapets and exposed raised brickwork.

Local X runs from the corner west along Tiantong Road, Y into the courtyard.
eaves is the top of the continuous projecting stone lip. All dimensions are m.
"""
import math

LIP = 'Hospital | pale cornice stone'
SOFFIT = 'Hospital | weathered cornice soffit'
TURNED = 'Hospital | turned parapet stone'
BRICK = '1914 block | kiln-fired red brick'
MORTAR = 'Hospital | rooftop lime bed'
COVER = 'Hospital | dark weathered roof cover'
VENT = 'Hospital | shaded rooftop opening'

def colour(rgb):
    return [((k / 255 + .055) / 1.055) ** 2.4 for k in rgb]

PALETTE = {key: dict(color=colour(rgb), roughness=rough)
           for key,rgb,rough in [(LIP,(170,150,128),.92),(SOFFIT,(136,115,95),.95),
             (TURNED,(155,139,120),.91),(BRICK,(151,89,68),.95),
             (MORTAR,(148,119,99),.97),(COVER,(106,99,92),.97),(VENT,(58,56,51),.88)]}

# Position of the centres of the stone divisions on the straightened street photo.
STREET_PIERS = (0., .141, .207, .283, .359, .452, .550, .656, .743, .838, .932, 1.)


def block(b, spans, material, name):
    mids = tuple((lo + hi) / 2 for lo,hi in spans)
    sizes = tuple(hi - lo for lo,hi in spans)
    b.box(mids,sizes,material,label=name)


def strip(b, footprint, side, inner, outer, low, high, mat, name):
    """Closed straight moulding, its ends mitred onto the next segment."""
    normals=[]
    for index,p in enumerate(footprint):
        q=footprint[(index+1)%len(footprint)]
        dx,dy=q[0]-p[0],q[1]-p[1]
        length=math.hypot(dx,dy)
        normals.append((dy/length,-dx/length))
    def point(index, distance, z):
        p=footprint[index]
        prev,cur=normals[index-1],normals[index]
        denom=1+prev[0]*cur[0]+prev[1]*cur[1]
        return (p[0]+distance*(prev[0]+cur[0])/denom,
                p[1]+distance*(prev[1]+cur[1])/denom,z)
    end=(side+1)%len(footprint)
    base=[point(side,outer,low),point(end,outer,low),point(end,inner,low),point(side,inner,low)]
    top=[(x,y,high) for x,y,z in base]
    b.add(base+top,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,name)


def bracket(b, edge, s, z, mat, name, lod):
    """One cornice modillion, including the sloping stone below its head."""
    start,along,out=edge
    # (distance from street wall, height relative to lip)
    section=[(-.035,-1.18),(.14,-1.18),(.18,-1.05),(.248,-.991),
             (.245,-.90),(.324,-.81),(.414,-.81),(.43,-.70),(-.035,-.70)]
    if lod:
        section=[section[i] for i in (0,1,2,5,6,7,8)]
    points=[]
    for width in (-.128,.128):
        points += [(start[0]+along[0]*(s+width)+out[0]*r,
                    start[1]+along[1]*(s+width)+out[1]*r,z+h) for r,h in section]
    # Both end caps are triangulated as a fan about the upper rear corner:
    # each of the steps along the exposed edge is visible from that corner.
    n=len(section)
    faces=[(n-1,i+1,i) for i in range(n-2)]
    faces += [(2*n-1,n+i,n+i+1) for i in range(n-2)]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    # section is CCW in the outward-distance/elevation plane; its normal is
    # opposite to the edge tangent for this building's CCW outline.
    b.add(points,[tuple(reversed(f)) for f in faces],mat,name)


def balusters(b, edge, a, c, z, count, lod, name):
    """A pierced bay of individually closed, revolved and capped spindles."""
    start,t,norm=edge
    rings=[(0.,.093),(.057,.093),(.083,.075),(.112,.057),(.175,.055),(.268,.086),
           (.332,.093),(.386,.077),(.428,.053),(.474,.051),(.507,.074),(.555,.081),(.585,.081)]
    if lod:
        rings=[rings[i] for i in (0,1,3,4,6,8,9,11,12)]
    segs=6 if lod else 10
    points=[]
    faces=[]
    for slot in range(count):
        s=a+(c-a)*(slot+.5)/count
        cx=start[0]+s*t[0]-.14*norm[0]
        cy=start[1]+s*t[1]-.14*norm[1]
        first=len(points)
        for h,r in rings:
            for k in range(segs):
                angle=k*2*math.pi/segs
                points.append((cx+r*math.cos(angle),cy+r*math.sin(angle),z+h))
        for j in range(len(rings)-1):
            for k in range(segs):
                u=first+j*segs+k
                v=first+j*segs+(k+1)%segs
                faces.append((u,v,v+segs,u+segs))
        faces.append(tuple(first+k for k in reversed(range(segs))))
        last=first+(len(rings)-1)*segs
        faces.append(tuple(last+k for k in range(segs)))
    b.add(points,faces,TURNED,name)


def edge_box(b, edge, a, c, out0, out1, z0,z1, mat, name):
    start,t,n=edge
    rect=[(start[0]+s*t[0]+r*n[0],start[1]+s*t[1]+r*n[1])
          for s,r in [(a,out0),(a,out1),(c,out0),(c,out1)]]
    block(b,[(min(x for x,y in rect),max(x for x,y in rect)),
             (min(y for x,y in rect),max(y for x,y in rect)),(z0,z1)],mat,name)


def pier_and_rail(b,edge,stations,z,lod,tag,solid,raised_base=0.):
    for i,(a,c) in enumerate(zip(stations,stations[1:])):
        left=.38 if i else .245
        right=.38 if i+2<len(stations) else .245
        start=a+left
        finish=c-right
        name=f'Roof {tag} bay {i+1:02d}'
        edge_box(b,edge,a,c,-.335,.06,z+.045,z+.26+raised_base,SOFFIT,name+' base')
        z0=z+raised_base
        edge_box(b,edge,a,c,-.36,.07,z0+.26,z0+.32,LIP,name+' seat')
        edge_box(b,edge,a,c,-.37,.08,z0+.905,z0+1.035,LIP,name+' coping')
        edge_box(b,edge,a,c,-.365,.075,z0+1.035,z0+1.085,SOFFIT,name+' drip')
        if i in solid or finish-start < .36:
            edge_box(b,edge,a,c,-.31,.04,z0+.32,z0+.905,LIP,name+' solid')
            continue
        edge_box(b,edge,a,start,-.32,.045,z0+.32,z0+.905,LIP,name+' left pier')
        edge_box(b,edge,finish,c,-.32,.045,z0+.32,z0+.905,LIP,name+' right pier')
        count=max(2,round((finish-start)/.233))
        balusters(b,edge,start,finish,z0+.32,count,lod,name+' spindles')


def raised_block(b,x0,x1,y0,y1,bottom,top,label,lod,window=False):
    """Unpierced front brickwork; only the courtyard photo supplies a vent."""
    if window:
        dx=x1-x0
        lo,hi=x0+.47*dx,x0+.59*dx
        sill,head=bottom+(top-bottom)*.46,bottom+(top-bottom)*.80
        end=y1-.20
        block(b,[(x0,x1),(y0,end),(bottom,top)],BRICK,label+' core')
        for xa,xb,za,zb,tag in [(x0,lo,bottom,top,'west jamb'),(hi,x1,bottom,top,'east jamb'),
                                (lo,hi,bottom,sill,'sill'),(lo,hi,head,top,'head')]:
            block(b,[(xa,xb),(end,y1),(za,zb)],BRICK,label+' '+tag)
        block(b,[(lo,hi),(end,end+.012),(sill,head)],VENT,label+' vent inset')
    else:
        block(b,[(x0,x1),(y0,y1),(bottom,top)],BRICK,label+' masonry')
    for d,h0,h1,mat,tag in [(.055,top-.14,top-.082,SOFFIT,'neck'),
                               (.125,top-.082,top+.018,LIP,'coping'),
                               (.168,top+.018,top+.071,SOFFIT,'weathering')]:
        block(b,[(x0-d,x1+d),(y0-d,y1+d),(h0,h1)],mat,label+' '+tag)


class MeasuredScale:
    """Transfer all section lengths from the first scale to the surveyed span."""
    def __init__(self, builder, scale):
        self.builder=builder
        self.scale=scale
        self.palette=builder.palette

    def box(self, centre, size, material, label):
        self.builder.box(tuple(x*self.scale for x in centre),tuple(x*self.scale for x in size),
                         material,label=label)

    def add(self, verts, faces, material, label):
        self.builder.add([tuple(x*self.scale for x in pt) for pt in verts],faces,material,label)


def add_roof(b,lod=False,layout=None):
    layout=layout or {}
    span=float(layout.get('width',44.62))
    scale=span/46.5
    b=MeasuredScale(b,scale)
    w=span/scale
    d=float(layout.get('depth',11.33))/scale
    z=float(layout.get('eaves',23.69))/scale
    step_y=float(layout.get('short_return_depth',4.95))/scale
    step_x=float(layout.get('short_return_x',1.14))/scale
    foot=[(0.,0.),(w,0.),(w,d),(step_x,d),(step_x,step_y),(0.,step_y)]
    names=['street','west','court','court return','east jog','east end']
    for material, specification in PALETTE.items():
        b.palette.setdefault(material,specification)
    # Two masses support the horizontal cover; the eastern end really steps back.
    block(b,[(0.,w),(0.,step_y),(z-.16,z+.044)],COVER,'Roof eastern deck')
    block(b,[(step_x,w),(step_y,d),(z-.16,z+.044)],COVER,'Roof courtyard deck')
    courses=[(-.09,.115,-1.52,-1.40,SOFFIT,'bed'),(-.085,.168,-1.40,-1.30,LIP,'lower drip'),
             (-.09,.093,-1.30,-1.19,SOFFIT,'neck'),(-.08,.185,-1.19,-1.12,LIP,'seat'),
             (-.08,.115,-1.12,-.73,SOFFIT,'frieze'),(-.08,.445,-.73,-.58,SOFFIT,'soffit'),
             (-.08,.465,-.58,-.48,LIP,'lower fillet'),(-.08,.455,-.48,-.36,SOFFIT,'fascia'),
             (-.08,.535,-.36,-.18,LIP,'upper fascia'),(-.08,.61,-.18,-.105,SOFFIT,'throat'),
             (-.08,.64,-.105,.045,LIP,'lip')]
    for side,p in enumerate(foot):
        q=foot[(side+1)%len(foot)]
        length=math.dist(p,q)
        t=((q[0]-p[0])/length,(q[1]-p[1])/length)
        edge=(p,t,(t[1],-t[0]))
        tag=names[side]
        if side==1:  # Wall adjoining the neighbouring building is a section limit.
            strip(b,foot,side,-.08,.04,z-.20,z+.045,SOFFIT,'Roof west section closure')
            continue
        # The surveyed eave elevation refers to the wall plane. At the actual
        # projecting mitre, the stone lip falls 0.40 m below that sightline.
        def level(h):
            return z+h-.395*max(0.,min(1.,(h+.73)/.775))
        for inside,outside,lo,hi,mat,kind in courses:
            strip(b,foot,side,inside,outside,level(lo),level(hi),mat,'Roof '+tag+' '+kind)
        strip(b,foot,side,-.09,.035,level(.045),z+.046,SOFFIT,'Roof '+tag+' parapet foot')
        count=max(2,round(length/.58))
        for i in range(count):
            bracket(b,edge,(i+.5)*length/count,z,LIP,f'Roof {tag} bracket {i+1:02d}',lod)
        if side==0:
            stations=[f*w for f in STREET_PIERS]
            solid={0}
        elif side==2:
            # The rear and street piers are not opposite. The unobstructed
            # courtyard photograph shows five longer panels before the roof room.
            south_piers=(1.14,6.97,12.22,17.45,22.73,28.16,32.68,39.32,44.62)
            stations=[length*(44.62-x)/(44.62-1.14) for x in reversed(south_piers)]
            solid={1}
        else:
            n=max(1,round(length/3.5))
            stations=[i*length/n for i in range(n+1)]
            solid=set(range(n)) if side in (4,5) else set()
        pier_and_rail(b,edge,stations,z,lod,tag,solid,.39 if side==2 else 0.)
    # Corner mass's two exposed façades share one photographed upper lip.
    raised_block(b,.10,6.47*w/46.5,.10,step_y-.10,z+1.065,z+2.81,'Roof street corner block',lod)
    # The west face and the north face of the brick shaft meet at the photograph's
    # forward arris. The dark metal grid above it belongs to the background roof.
    shaft_a,shaft_b=.4533*w,.4910*w
    front,back=.354,1.762
    block(b,[(shaft_a-.10,shaft_b+.10),(front-.10,back+.10),(z+.045,z+2.54)],
          BRICK,'Roof flue lower drum')
    for spread,h0,h1 in [(.16,2.54,2.61),(.22,2.61,2.72),(.275,2.72,2.815)]:
        block(b,[(shaft_a-spread,shaft_b+spread),(front-spread,back+spread),(z+h0,z+h1)],
              LIP,'Roof flue collar '+str(round(h0*100)))
    raised_block(b,shaft_a,shaft_b,front,back,z+2.815,z+6.34,'Roof flue upper shaft',lod)
    # The separate courtyard photograph establishes the rectangular block and
    # a single square shadow; its screened return depth is an estimate.
    raised_block(b,w*.734,w*.890,d-2.66,d-.20,z+.045,z+3.31,'Roof rear raised block',lod,True)
