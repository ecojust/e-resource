"""Trace the two stone panels and the exposed undersides in the 2015 street photograph."""
import math
import numpy as np
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from photo_architecture import Facade
from photo_plane import trace,level
from material_names import MATERIAL

LIP='Pale dressed mouldings'
RETURN='Weathered stone returns'
SCROLL='Rounded scroll bead'
NARROW='Chiselled inner arris'
KEY='Broad central keystone'
FLOOR='Terrace soffit'
DISC='Soffit roundel face'
EDGE='Roundel turned bevel'
BAR='Dark horizontal guard'
PILASTER='Square stone uprights'

def curve(points,n):
    p=np.array(points)
    t=np.linspace(0.,1.,n+1)[:,None]
    return (1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3]

def continuous(segments,res):
    out=[segments[0][0]]
    for controls in segments:
        out.extend(curve(controls,res)[1:])
    return np.asarray(out,float)

def companion(points,right):
    p=np.asarray(points,dtype=float).copy()
    if right:
        # Register the second panel separately at the top and foot.
        dx=p[:,0]-756.; dy=p[:,1]-289.
        p[:,0]=1457.+.927*dx+.012*dy
        p[:,1]=299.+.994*dy+.0084*dx
    return p

def coords(points,y=0):
    return np.array([trace(u,v,y)for u,v in points])
def shape(points,y=0):
    return Polygon(coords(points,y))
def project_path(points,right,y):
    return coords(companion(points,right),y)
def surface(points,right,y):
    return Polygon(project_path(points,right,y))

def half_opening(cx,base,rx,h,right,n):
    a=np.linspace(math.pi,0,n+1)
    height=base-h*np.sin(a)
    if h>20:
        # Fit the shoulders separately on each arch, keeping the observed chord
        # and springing points fixed. Coefficients are in rectified photo pixels.
        flat,skew,shoulder=(4.26,1.86,8.18) if right else (2.03,3.14,7.23)
        height+=np.sin(a)*(flat+skew*np.cos(a)+shoulder*np.cos(a)**2)
    return surface(np.column_stack((cx+rx*np.cos(a),height)),right,0)

def profile_outline(n):
    # Rectified photo pixels, from the near side to the far side of the first panel.
    seg=[
        [(582,293),(583,252),(598,222),(626,203)],
        [(626,203),(647,187),(693,162),(698,143)],
        [(698,143),(682,148),(663,133),(665,116)],
        [(665,116),(667,95),(698,90),(721,111)],
        [(721,111),(724,105),(726,105),(730,104)],
        [(730,104),(749,104),(774,104),(789,106)],
        [(789,106),(795,105),(799,108),(799,112)],
        [(799,112),(825,95),(848,97),(854,112)],
        [(854,112),(860,135),(841,150),(827,144)],
        [(827,144),(830,161),(872,186),(892,205)],
        [(892,205),(913,229),(922,252),(924,294)]]
    outline=continuous(seg,n)
    return np.vstack([outline,[924,340],[582,339]])

def curl_points(side,right,n):
    # A shallow relief ribbon joins the shoulder to the rolled eye at the crest.
    seg=[[(592,266),(604,231),(635,207),(669,192)],
         [(669,192),(698,178),(721,160),(714,130)],
         [(714,130),(709,111),(697,102),(683,105)],
         [(683,105),(668,109),(666,131),(679,136)],
         [(679,136),(691,142),(703,131),(697,121)],
         [(697,121),(692,114),(683,117),(685,124)]]
    p=continuous(seg,n)
    if side:
        p[:,0]=1517.-p[:,0]
        p[:,1]+=1.2
    return companion(p,right)

def pyramid(builder,points,right,depths,label):
    pix=companion(points,right)
    v=[]
    for (u,z),y in zip(pix,depths):
        x,h=trace(u,z,y);v.append([x,y,h])
    # A solid, faceted keystone inclines toward the central ridge.
    faces=[(0,3,4),(0,4,1),(1,4,2),(2,4,3)]
    for face in faces:
        a,b,c=np.asarray([v[i] for i in face])
        if np.cross(b-a,c-a)[1]>0:face=tuple(reversed(face))
        builder.add(v,[face],KEY,label)

def roundel(builder,x,y,r,top,label,lod):
    sides=20 if lod else 44
    # Revolve the measured shallow circular boss with a broad flat underside.
    rings=[(r*.76,top-.042),(r*.91,top-.039),(r*.99,top-.029),(r,top-.008),(r*.94,top)]
    if lod:rings=[rings[i] for i in [0,2,4]]
    verts=[]
    for radius,z in rings:
        for a in np.linspace(0.,2*math.pi,sides,endpoint=False):
            verts.append([x+radius*math.cos(a),y+radius*math.sin(a),z])
    for k in range(len(rings)-1):
        faces=[(k*sides+i,k*sides+(i+1)%sides,(k+1)*sides+(i+1)%sides,(k+1)*sides+i)for i in range(sides)]
        builder.add(verts,faces,EDGE,label+' bevel')
    builder.add(verts,[tuple(range(sides-1,-1,-1)),tuple(range((len(rings)-1)*sides,len(verts)))],DISC,label+' flat')

def rail(builder,lod):
    f=Facade(builder,(-2.5,0),(2.5,0),'Parapet')
    n=6 if lod else 15
    left_bound=272;right_bound=1703
    def line(u):return 440+(u-78)*.0103
    def top(u):return 31+(u-278)*.026
    u0,z0=trace(left_bound,line(left_bound))
    u1,z1=trace(right_bound,line(right_bound))
    full=shape([(left_bound,274),(right_bound,310),(right_bound,line(right_bound)),(left_bound,line(left_bound))])
    sculpted=[surface(profile_outline(n),right,0) for right in (False,True)]
    openings=[]
    for right in (False,True):
        openings.extend([half_opening(756,289.4,40,33,right,n*3),half_opening(762,369.0,19,16.2,right,n*3)])
    holes=unary_union(openings)
    f.prism(full.difference(holes),-.125,0,MATERIAL,'continuous pierced sill')
    for index,part in enumerate(sculpted):
        f.prism(part.difference(full).difference(holes),-.125,0,MATERIAL,'fret crest '+str(index+1))
    for right in (False,True):
        tag='Far' if right else 'Near'
        for ix in (0,1):
            q=curl_points(ix,right,n)
            ridge=LineString(coords(q,-.012)).buffer(.0107,quad_segs=4 if lod else 8)
            f.prism(ridge,.001,.0145,NARROW,tag+' engraved fillet '+str(ix+1))
            path=[[*x]for x in coords(q,-.020)]
            builder.tube([(x,-.019,z)for x,z in path],.0115,SCROLL,5 if lod else 10,tag+' scroll ridge '+str(ix+1))
        q=[(722,106),(793,108),(793,172),(718,173),(772,126)]
        pyramid(builder,q,right,[-.013,-.013,-.045,-.045,-.081],tag+' central folded keystone')
        q=[(718,173),(794,173),(791,184),(718,184)]
        f.prism(surface(q,right,-.045),.003,.047,LIP,tag+' keystone lower lip')
        # The rectangular T-ended piers frame the broad open shoulders.
    for name,l,r,start,end in [('Near',271,550,270,361),('Middle',1003,1267,289,375),('Far',1680,1704,308,380)]:
        cap=shape([(l,top(l)+39),(r,top(r)+38),(r,start),(l,start)])
        f.prism(cap,-.146,.013,PILASTER,name+' square pier')
        low=shape([(l,start-1),(r,start-1),(r,end),(l,end)])
        f.prism(low,.001,.014,PILASTER,name+' pier front below sill')
        for tag,side in [('left',l),('right',r)]:
            if side in (271,1704):continue
            sign=-1 if tag=='left' else 1
            tab=shape([(side-1*sign,top(side)+39),(side+38*sign,top(side)+40),(side+38*sign,top(side)+69),(side-1*sign,top(side)+69)])
            f.prism(tab,-.116,.008,RETURN,name+' inset collar '+tag)
    # Four open shoulders expose an iron bar set behind the pale panels.
    for label,l,r,base in [('left',550,1003,146),('right',1267,1680,168)]:
        a=trace(l,base,.084);b=trace(r,base+(r-l)*.020,.084)
        builder.tube([(a[0],.084,a[1]),(b[0],.084,b[1])],.014,BAR,8 if lod else 16,label+' cross bar')
    for i,(l,r) in enumerate([(left_bound,548),(548,1005),(1005,1264),(1264,right_bound)]):
        # Offsets at both square piers break the long coping in the source.
        lift=-6 if i in (0,2) else 0
        for k,(a,b,d,mat) in enumerate([(0,8,.061,LIP),(8,15,.044,NARROW),(15,35,.033,MATERIAL),(35,41,.055,LIP)]):
            q=[(l,top(l)+a+lift),(r,top(r)+a+lift),(r,top(r)+b+lift),(l,top(l)+b+lift)]
            f.prism(shape(q,-d),-.173,d,mat,'coping '+str(i+1)+' profile '+str(k+1))
    # The underside is exposed on the street side and runs back into the wall.
    floor_z=-.007
    builder.box([(u0+u1)/2,.46,floor_z+.064],[u1-u0,.923,.128],FLOOR,label='slab with two visible decorated brackets')
    for i,points in enumerate([[(314,294),(413,340),(299,383),(201,334)],[(578,419),(661,461),(554,506),(465,464)]]):
        underside=-.155; q=np.array([level(*pt,underside)[:2] for pt in points]); top=Polygon(q)
        tag=['Near','Far'][i]
        builder.plan_prism(top,.002+underside,.049+underside,LIP,tag+' lower rectangular plate')
        builder.plan_prism(top.buffer(-.018,join_style=2),underside+.049,underside+.067,RETURN,tag+' rebated joint')
        builder.plan_prism(top.buffer(-.005,join_style=2),underside+.067,-.006,FLOOR,tag+' bracket block')
        # Four corner bosses set the observed pitch and orientation. The other
        # five centres on each plate remain independent checks on the array.
        controls=[
            [(565,2678),(620,2703),(551,2728),(495,2702)],
            [(826,2804),(873,2826),(806,2848),(759,2828)]][i]
        centres=np.array([level(u-253,v-2350,underside-.040)[:2] for u,v in controls])
        for row,b in enumerate((0.,.5,1.)):
            for col,a in enumerate((0.,.5,1.)):
                xy=(1-b)*((1-a)*centres[0]+a*centres[1])+b*((1-a)*centres[3]+a*centres[2])
                radius=.073 if i==0 else .0725
                roundel(builder,*xy,radius,underside+.002,tag+' boss '+str(row+1)+'-'+str(col+1),lod)
