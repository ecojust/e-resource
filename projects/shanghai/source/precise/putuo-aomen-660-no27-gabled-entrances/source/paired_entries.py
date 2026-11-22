"""The two adjacent entrance bays in the numbered photograph of 27 Aomen Lane 660.

The measured silhouettes are original geometry. The reference photograph is not
distributed or used as a texture. Depths are nominal estimates from the oblique
view, especially inside the partly opened right doorway.
"""
from pathlib import Path
import json
import math

DATA = json.loads((Path(__file__).resolve().parents[1] / 'measurements' / 'paired-entries.json').read_text())
SCALE = .018
MORTAR = 'Aomen entry muted red pointing'
CLAY = ('Aomen entry russet facing brick', 'Aomen entry deep rust facing brick',
        'Aomen entry pale burnt brick', 'Aomen entry weathered red brick')
WHITE = 'Aomen fan weathered limestone'
BEVEL = 'Aomen fan lime bevel'
REVEAL = 'Aomen fan shaded reveal'
GLASS = 'Aomen smoky fan glazing'
SASH = 'Aomen fan dark timber'
LEDGE = 'Aomen entry cement ledge'
EDGE = 'Aomen entry grey drip edge'
DOOR = 'Aomen entry painted oxblood timber'
PANEL = 'Aomen entry worn oxblood panel'
RAIL = 'Aomen entry dark panel moulding'
NARROW = 'Aomen narrow door glass'
DARK = 'Aomen open passage shadow'
BRASS = 'Aomen entry brown metal latch'
PLATE = 'Aomen enamel number green'
LETTER = 'Aomen ivory enamel numerals'
STONE = 'Aomen worn stone doorstep'

def pigment(rgb, rough=.85):
    def linear(c):
        c /= 255
        return c/12.92 if c<.04045 else ((c+.055)/1.055)**2.4
    return dict(color=[linear(c) for c in rgb], roughness=rough)

PALETTE = {
    MORTAR:pigment((151,109,87)), WHITE:pigment((204,199,177)), BEVEL:pigment((179,173,149)),
    REVEAL:pigment((143,135,113)), GLASS:pigment((65,71,63),.43), SASH:pigment((50,47,39)),
    LEDGE:pigment((141,140,120)), EDGE:pigment((104,102,86)), DOOR:pigment((100,57,43)),
    PANEL:pigment((88,51,40)), RAIL:pigment((76,47,37)), NARROW:pigment((53,63,52),.45),
    DARK:pigment((33,32,26)), BRASS:pigment((126,107,67),.59), PLATE:pigment((38,87,68),.58),
    LETTER:pigment((220,217,190)), STONE:pigment((159,155,137))
}
for name,color in zip(CLAY, ((159,97,73),(145,85,65),(171,108,83),(151,93,73))):
    PALETTE[name] = pigment(color)

def vertex(uv,y):
    u,v=uv
    return ((u-267.)*SCALE,y,(358.-v)*SCALE)

def signed_area(uv):
    return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(uv,uv[1:]+uv[:1]))/2

def solid(b,uv,front,back,mat,name):
    """Extrude a convex face; low y is the face toward the lane."""
    assert back>front
    if signed_area(uv)>0:uv=uv[::-1]
    size=len(uv)
    vertices=[vertex(a,y) for y in (front,back) for a in uv]
    near=tuple(range(size));far=tuple(reversed(range(size,size*2)))
    sides=[(j+size,(j+1)%size+size,(j+1)%size,j) for j in range(size)]
    b.add(vertices,[near,far,*sides],mat,name)

def box(b,l,t,r,d,front,back,mat,name,slope=0):
    rise=slope*(r-l)
    solid(b,[(l,t),(r,t+rise),(r,d+rise),(l,d)],front,back,mat,name)

def ellipse(q,t):
    middle,base,w,h,slant=q
    u=middle+w*math.cos(t)
    return (u,base-h*math.sin(t)+slant*(u-middle))

def interp(a,b,k):
    return tuple((1-k)*x+k*y for x,y in zip(a,b))

def ring(b,start,end,front,back,steps,mat,name,front2=None,back2=None):
    """Build one continuous curved strip with shared vertices on each station."""
    front2=front if front2 is None else front2
    back2=back if back2 is None else back2
    stations=[]
    for j in range(steps+1):
        t=math.pi*j/steps; inner=ellipse(start,t);outer=ellipse(end,t)
        stations.append([vertex(inner,front),vertex(outer,front2),vertex(outer,back2),vertex(inner,back)])
    faces=[]
    for j in range(steps):
        for k in range(4):
            l=(k+1)%4
            faces.append((4*j+k,4*j+l,4*j+4+l,4*j+4+k))
    faces.extend([(3,2,1,0),(4*steps,4*steps+1,4*steps+2,4*steps+3)])
    b.add([v for station in stations for v in station],faces,mat,name)

def stroke(b,a,c,width,front,back,mat,name):
    dx,dy=c[0]-a[0],c[1]-a[1];factor=.5*width/math.hypot(dx,dy)
    x,y=-dy*factor,dx*factor
    solid(b,[(a[0]+x,a[1]+y),(c[0]+x,c[1]+y),(c[0]-x,c[1]-y),(a[0]-x,a[1]-y)],
          front,back,mat,name)

def fan(b,side,steps,label):
    q=DATA['arches'][side];inner=q['inside']['ellipse'];outer=q['outside']['ellipse']
    # The light surround has a narrow bevel and a recessed inner jamb; no
    # voussoir joints can be identified confidently at this photograph size.
    before=list(inner);before[2]-=.8;before[3]-=.8
    after=list(outer);after[2]-=1.;after[3]-=1.
    ring(b,inner,after,-.063,.019,steps,WHITE,label+' fan broad lime arch')
    ring(b,after,outer,-.063,.019,steps,BEVEL,label+' fan outer bevel',-.024,.019)
    ring(b,before,inner,.091,.120,steps,REVEAL,label+' fan underside',-.063,.020)
    glass_edge=list(before);glass_edge[2]-=1.45;glass_edge[3]-=1.45
    ring(b,glass_edge,before,.091,.139,steps,SASH,label+' fan inner wood rim')
    arc=[ellipse(glass_edge,math.pi*i/steps) for i in range(steps+1)]
    solid(b,arc,.139,.156,GLASS,label+' fan recessed dark panes')
    # Two sloping bars rise from opposite ends of the short horizontal base
    # bar. A clear arc is visible at the top, the centre has no upright mullion.
    l=(inner[0]-3.1,inner[1]-1.5);r=(inner[0]+2.9,inner[1]-1.5)
    frame=[(l,ellipse(glass_edge,math.radians(135))),
           (r,ellipse(glass_edge,math.radians(48))), (l,r)]
    for i,(a,c) in enumerate(frame):stroke(b,a,c,1.10,.107,.139,SASH,label+' fan sash '+str(i+1))

def masonry(b,side,info,label):
    l,r=info['inner_jamb_px'];lo,hi=info['jamb_outer_px'];top_l,top_r=info['top_v']
    cap_l,cap_r=info['soldier_top_v'];bottom=info['floor_v'];c=info['course_h_px']
    for j,(u1,u2,v) in enumerate(((lo,l,top_l),(r,hi,top_r))):
        box(b,u1,v,u2,bottom,-.033,.115,MORTAR,label+' jamb bed '+str(j+1))
        course=0
        while v<bottom-.4:
            stop=min(bottom,v+c);dl,dr=u1+.12,u2-.12
            cuts=[dl,dr] if course%2==0 else [dl,dl+(dr-dl)*.48,dr]
            for k,(a,z) in enumerate(zip(cuts,cuts[1:])):
                if stop-v>.48:
                    box(b,a+.10,v+.15,z-.10,stop-.16,-.042,.0005,CLAY[(course+2*j+k)%4],
                        label+(' left' if j==0 else ' right')+' jamb brick '+str(course+1))
            v=stop;course+=1
    slope=(cap_r-cap_l)/(hi-lo)
    solid(b,[(lo,cap_l),(hi,cap_r),(hi,top_r),(lo,top_l)],-.034,.120,MORTAR,label+' soldier pointing')
    n=round((hi-lo)/3.5)
    for j in range(n):
        a,z=(j+.05)/n,(j+.95)/n
        solid(b,[interp((lo,cap_l),(hi,cap_r),a),interp((lo,cap_l),(hi,cap_r),z),
                 interp((lo,top_l-.25),(hi,top_r-.25),z),interp((lo,top_l-.25),(hi,top_r-.25),a)],
              -.043,.004,CLAY[(j*3+j//4)%4],label+' upright brick '+str(j+1))
    # Three extrusions give the projecting flat lintel its drip and upper lip.
    for k,(oversail,upper,lower,y,mat) in enumerate(((4.0,-3.3,.0,-.145,EDGE),
            (6.2,-5.8,-3.3,-.208,LEDGE),(7.1,-7.8,-5.8,-.221,LEDGE))):
        box(b,lo-oversail,cap_l+upper-slope*oversail,hi+oversail,cap_l+lower-slope*oversail,
            y,.035,mat,label+' projecting lintel '+str(k+1),slope)

def recess(b,box_,mat,label,face=.076):
    l,t,r,d=box_;w=min(1.15,(r-l)*.12)
    for a,z,rr,bt in [(l,t,r,t+w),(l,d-w,r,d),(l,t+w,l+w,d-w),(r-w,t+w,r,d-w)]:
        box(b,a,z,rr,bt,face,.102,RAIL,label+' moulding')
    box(b,l+w,t+w,r-w,d-w,face+.009,.104,mat,label+' inset')

def doors(b,side,record,label):
    l,r=record['inner_jamb_px'];top1,top2=record['top_v'];fl=record['floor_v'];slope=(top2-top1)/(r-l)
    solid(b,[(l,top1),(r,top2),(r,top2+2),(l,top1+2)],.014,.125,RAIL,label+' timber head')
    for j,(a,c,t) in enumerate(((l,l+1.7,top1),(r-1.7,r,top2))):
        box(b,a,t+1,c,fl,.014,.149,RAIL,label+' timber reveal '+str(j+1))
    if side=='left':
        seam=record['seam_u'];stamp=[(l+1.7,seam-.25),(seam+.25,r-1.7)]
        for i,(a,c) in enumerate(stamp):
            box(b,a,top1+1.8+slope*(a-l),c,fl-.55,.105,.151,DOOR,label+' closed leaf '+str(i+1),slope)
        recess(b,[l+6.2,top1+5.1,seam-5.3,fl-45.0],NARROW,label+' narrow vertical light')
        recess(b,[seam+4.9,top1+5.3,r-6.0,fl-47.0],PANEL,label+' upper panel')
        for i,(a,c) in enumerate(((seam+4,r-17.5),(r-17.1,r-6.2))):
            recess(b,[a,fl-35.,c,fl-4.0],PANEL,label+' lower field '+str(i+1))
        box(b,seam-.95,fl-47.0,seam+.2,fl-44.0,.053,.083,BRASS,label+' latch')
    else:
        end=record['closed_leaf_start'];a,c=record['open_leaf_edges']
        box(b,end,top2+2.7,r-1.7,fl-.45,.105,.151,DOOR,label+' right closed leaf',slope)
        for i,(t,d) in enumerate(((top2+6.1,top2+27.6),(top2+34.8,fl-4.9))):
            recess(b,[end+3.6,t,r-5.1,d],PANEL,label+' right panel '+str(i+1))
        # Four photographed edge pixels are the exposed thickness and shallow
        # perspective of the left leaf. Give it the physical width of a leaf
        # receding into the opening, rather than closing the dark gap.
        front,back=.099,.700
        uvs=[(a,top1+2),(c,top1+4),(c,fl-1),(a,fl-.4)]
        points=[vertex(q, y) for q,y in zip(uvs,(front,back,back,front))]
        b.add(points+[(x+.036,y,z) for x,y,z in points],
              [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],
              DOOR,label+' left leaf open inward')
        box(b,c-.2,fl-45,c+1.25,fl-42,.303,.342,BRASS,label+' exposed latch')
        # One shadowed background plane is visible. Its depth is an estimate;
        # keep the remainder of the passage empty.
        box(b,l,top1,r,fl,.78,.81,DARK,label+' shaded passage')
        for j,(a,c) in enumerate(((l+1.3,l+2.2),(end-1.3,end))):
            box(b,a,top1+1.5,c,fl,.108,.78,RAIL,label+' passage jamb '+str(j+1))
    box(b,l-.5,fl-.25,r+.55,fl+1.2,-.141,.78,STONE,label+' threshold face')

def plaque(b):
    q=DATA['plaque']['corners']
    for inset,front,mat,label in [(0,-.043,LETTER,'enamel bevel'),(.045,-.047,PLATE,'green enamel')]:
        corners=[interp(a,q[(i+2)%4],inset) for i,a in enumerate(q)]
        solid(b,corners,front,-.010,mat,'Number 27 '+label)
    digits=[[(.21,.38),(.27,.25),(.40,.24),(.47,.34),(.45,.45),(.22,.73),(.48,.72)],
            [(.56,.28),(.79,.27),(.63,.72)]]
    def uv(p):
        a,v=p
        return interp(interp(q[0],q[1],a),interp(q[3],q[2],a),v)
    for i,chain in enumerate(digits):
        for j,(a,r) in enumerate(zip(chain,chain[1:])):
            stroke(b,uv(a),uv(r),.46,-.052,-.046,LETTER,'Number 27 digit '+str(2 if i==0 else 7)+' stroke '+str(j+1))

def add_entries(builder,lod):
    for side in ('left','right'):
        info=DATA['doorways'][side];label='Left entrance' if side=='left' else 'Number 27 entrance'
        masonry(builder,side,info,label);fan(builder,side,20 if lod else 42,label)
        doors(builder,side,info,label)
    plaque(builder)
