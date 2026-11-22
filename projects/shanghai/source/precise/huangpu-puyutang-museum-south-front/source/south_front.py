"""South elevation measured in the register's two 16 August 2014 photographs."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
from photo_plane import position
from material_names import MATERIAL

DATA=Path(__file__).resolve().parents[1]/'measurements'
STONE='Grey dressed entrance stone'
EDGE='Light stone cornice and sills'
BASE='Granite plinth'
WOOD='Oxide red painted sash'
GLASS='Grey blue courtyard glazing'
PAR='Recessed door panels'
TILE='Weathered clay plain tiles'
TILE2='Raised tile edges'
METAL='Painted downpipe'
BRASS='Entrance latch brass'

def pigment(rgb,rough=.85,metal=0.):
    a=np.asarray(rgb,dtype=float)/255
    return dict(color=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={STONE:pigment([150,145,137]),EDGE:pigment([165,159,150]),BASE:pigment([127,127,122]),WOOD:pigment([113,56,48],.65),
         GLASS:pigment([102,130,139],.31,.14),PAR:pigment([121,68,60]),TILE:pigment([151,82,62]),
         TILE2:pigment([165,95,73]),METAL:pigment([95,88,76],.63,.28),BRASS:pigment([150,123,74],.54,.38)}

def projected(coords,y=0.,view='close'):
    return Polygon([position(*p,y,view)[[0,2]] for p in coords])

def opening_rect(coords,y=0.,view='close'):
    corners=np.array([position(*p,y,view)[[0,2]] for p in coords])
    left=np.mean(corners[[0,3],0]);right=np.mean(corners[[1,2],0])
    top=np.mean(corners[:2,1]);bottom=np.mean(corners[2:,1])
    return box(left,bottom,right,top)

def grid(f,shape,label,columns,rows,frame_y,glass_y,outer=.065,door=False):
    x0,z0,x1,z1=shape.bounds
    w=x1-x0;h=z1-z0
    # Keep the pane edges seated behind the outer frame throughout its thickness.
    inner=shape.buffer(-outer,join_style=2)
    cuts=[]
    for i in range(1,columns):
        x=x0+w*i/columns
        half=.029 if i*2==columns or door else .018
        cuts.append(box(x-half,z0,x+half,z1))
    for i,t in enumerate(rows):
        z=z0+t*h
        half=.035 if door or i==len(rows)-1 else .021
        cuts.append(box(x0,z-half,x1,z+half))
    frame=shape.buffer(.013,join_style=2).difference(inner.difference(unary_union(cuts)))
    f.prism(shape.buffer(.026,join_style=2),-glass_y-.018,-glass_y,GLASS,label+' glass')
    f.prism(frame,-glass_y+.001,-frame_y,WOOD,label+' frame and glazing bars')
    if door:
        for i in range(columns):
            x=x0+i*w/columns+.052;r=x0+(i+1)*w/columns-.052
            panel=box(x,z0+.051,r,z0+h*rows[0]-.025)
            f.prism(panel,-glass_y+.003,-frame_y-.002,PAR,label+f' kick panel {i+1}')
            inside=panel.buffer(-.042,join_style=2)
            if not inside.is_empty:
                f.prism(panel.difference(inside),-frame_y-.004,-frame_y+.011,WOOD,label+' panel bead')
    return shape.bounds

def specimen_rectangle(f,coords,back,front,material,label):
    f.prism(projected(coords,front),-back,-front,material,label)

def entrance(f,b):
    # The independent relief module requires these two supporting faces at y=-.24 m.
    portal=[(147,235),(216,237),(273,244),(273,208),(386,78),(506,240),(505,281),(558,284),(607,302),(625,1011),(151,1064)]
    upper=opening_rect([(345,393),(439,405),(444,572),(352,565)],-.12)
    door=opening_rect([(267,780),(510,779),(522,1062),(272,1083)],-.09)
    body=projected(portal,-.12).difference(unary_union([upper,door.buffer(.018)]))
    f.prism(body,-.22,.12,STONE,'portal ashlar wall with openings')
    grid(f,upper,'central upper sash',4,[.239,.51,.785],-.125,-.065)
    specimen_rectangle(f,[(333,561),(454,572),(453,586),(333,576)],-.05,-.276,EDGE,'upper sash sill')
    # The stepped returns sit on a separate plane in front of the brickwork.
    for what,points in [
        ('date backing',[(327,585),(461,598),(463,658),(327,648)]),
        ('fruit and ribbon backing',[(296,241),(488,265),(490,378),(298,357)])]:
        specimen_rectangle(f,points,-.112,-.24,STONE,what)
    for label,outer,peak in [('west',[(147,225),(213,235),(224,1040),(153,1060)],[(141,224),(186,139),(220,228)]),
                              ('east',[(550,295),(610,305),(629,1008),(563,1018)],[(548,294),(576,218),(611,300)])]:
        pier=projected(outer,-.31);f.prism(pier,.09,.31,EDGE,label+' stone pier')
        x0,z0,x1,z1=pier.bounds
        for i,z in enumerate(np.arange(z0+.45,z1-.15,.53)):
            course=pier.intersection(box(x0-.1,z,x1+.1,z+.010))
            f.prism(course,.309,.315,STONE,label+' block joints')
        ridge=projected(peak,-.245)
        f.prism(ridge,-.13,.245,EDGE,label+' pyramidal pinnacle')
        a,tip,c=[position(*p,-.25) for p in peak];m=(a+c)/2;m[1]=-.43
        # Thin triangular wedge forms the projecting central arris of the cap.
        b.add([a,tip,c,m],[(0,1,2),(0,3,1),(1,3,2),(2,3,0)],STONE,label+' cap folded arris')
    tri=projected([(265,213),(384,77),(510,248)],-.25)
    f.prism(tri,-.058,.251,EDGE,'pediment triangular stone')
    inside=tri.buffer(-.078,join_style=2)
    f.prism(tri.difference(inside),.249,.337,STONE,'pediment raised rake')
    arch=projected([(350,213),(349,182),(354,166),(367,155),(385,153),(400,160),(409,174),(411,227)],-.27)
    f.prism(arch,.245,.263,BASE,'recessed tympanum blind head')
    f.prism(arch.buffer(.042,join_style=2).difference(arch),.249,.295,STONE,'blind head stone band')
    for label,a,c,d,width,thickness in [('pediment base',(263,209),(510,246),.33,.29,.063),
                                         ('portal sill course',(201,641),(568,672),.325,.23,.062),
                                         ('entrance hood',(250,752),(540,763),.326,.21,.053)]:
        v=position(*a,-d);e=position(*c,-d);xx0,xx1=sorted((v[0],e[0]));z=(v[2]+e[2])/2
        for off,depth,high in [(-.067,d-.035,.06),(0,d,thickness),(.045,d+.037,.05)]:
            f.prism(box(xx0,z+off,xx1,z+off+high),.085,depth,EDGE,label+' stepped profile')
        n=max(2,int((xx1-xx0)/.145))
        for ni,x in enumerate(np.linspace(xx0+.05,xx1-.05,n)):
            f.prism(box(x-.028,z-.115,x+.028,z-.066),.141,d-.056,STONE,label+' dentils')
    grid(f,door,'four entrance leaves',4,[.275,.456,.628,.793],-.102,-.016,.076,True)
    x0,z0,x1,z1=door.bounds
    for t in [.472,.526]:
        x=x0+t*(x1-x0)
        f.prism(box(x-.009,z0+1.0,x+.009,z0+1.19),.101,.148,BRASS,'centre door pulls')
    f.prism(box(x0-.12,z0-.092,x1+.12,z0+.013),-.24,.442,BASE,'door threshold')
    f.prism(box(-2.84,-.12,3.06,.38).difference(door),-.24,.126,BASE,'portal footing')
    return upper,door

def south_wall(builder):
    f=Facade(builder,(-23.8155,0),(23.8155,0),'Museum south')
    obs=json.loads((DATA/'observed-frontage.json').read_bytes())
    rows=[(r,opening_rect(r['outline_px'],0.,'wide')) for r in obs['openings']]
    entrance(f,builder)
    portal_cut=box(-2.33,-.4,2.33,11.6)
    openings=unary_union([shape for _,shape in rows]+[portal_cut])
    f.prism(box(-23.8155,-.08,23.8155,8.45).difference(openings),-.31,0,MATERIAL,'running bond wall')
    for i,(r,a) in enumerate(rows):
        x0,z0,x1,z1=a.bounds; label=r['level']+' bay '+str(r['bay'])
        is_door=r['level']=='lower-door'
        grid(f,a,label,4 if r['level']!='upper' else 2,[.27,.55,.8] if is_door else [.29,.57,.81],.073,.139,door=is_door)
        if not is_door:
            f.prism(box(x0-.07,z0-.063,x1+.07,z0+.006),-.032,.093,EDGE,label+' external sill')
            for u in (x0+.09,x1-.09):
                f.prism(box(u-.066,z0-.139,u+.066,z0-.063),-.001,.054,STONE,label+' sill lug')
        f.prism(box(x0-.10,z1,x1+.10,z1+.10),-.018,.047,MATERIAL,label+' brick lintel')
    for label,z,h,d,mat in [('base',-.064,.32,.07,BASE),('string lower',4.33,.079,.087,STONE),
        ('string',4.409,.115,.138,EDGE),('eaves bed',8.29,.088,.116,MATERIAL),('eaves crown',8.378,.077,.218,WOOD)]:
        block=box(-23.8155,z,23.8155,z+h).difference(openings)
        f.prism(block,-.018,d,mat,label)
    # Short visible returns carry the front edge and depth, without inventing a northern elevation.
    for x in [-23.8155,23.8155]:
        b=builder
        b.box([x,1.38,4.16],[.24,2.76,8.48],MATERIAL,label='Brick gable return '+('west' if x<0 else 'east'))
    for i,x in enumerate([-18.2,8.2,21.9]):
        builder.tube([(x,-.135,8.35),(x,-.12,8.19),(x,-.079,7.96),(x,-.079,.43)],.045,METAL,10,'Rainwater pipe '+str(i+1))
    return rows

def roof(builder,lod):
    # Plan of the photographed front slope. The horizontal back edge is the roof ridge.
    front=-.36;back=3.25;run=back-front;eave=8.454;rise=1.965;length=23.98
    def point(x,t):return np.array([x,front+t*run,eave+t*rise])
    def clip(poly,axis,bound,sign):
        out=[]
        for a,c in zip(poly,poly[1:]+poly[:1]):
            aa=sign*(a[axis]-bound);cc=sign*(c[axis]-bound)
            if aa>=0:out.append(a)
            if aa*cc<0:out.append(a+(c-a)*aa/(aa-cc))
        return out

    def solid(points,mat,label,depth):
        poly=[np.asarray(v,dtype=float)for v in points]
        # Across the projecting portal the eaves finish at the back of the
        # stonework. Clip every tile lip and joint at the same wall junction.
        if min(v[1] for v in poly)<.18 and min(v[0] for v in poly)<3.14 and max(v[0] for v in poly)>-2.85:
            pieces=[clip(poly,0,-2.85,-1),clip(poly,0,3.14,1),
                    clip(clip(clip(poly,0,-2.85,1),0,3.14,-1),1,.18,1)]
        else:pieces=[poly]
        for top in pieces:
            n=len(top)
            if n<3:continue
            bottom=[q-np.array([0.,0.,depth])for q in top]
            fs=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
            fs.extend((i+n,(i+1)%n+n,(i+1)%n,i)for i in range(n))
            builder.add(top+bottom,fs,mat,label)
    def half(t):return length-t*3.1
    solid([point(-half(0),0),point(half(0),0),point(half(1),1),point(-half(1),1)],TILE,'Southern clay tile slope',.16)
    courses=17 if not lod else 12
    for i in range(courses):
        t=i/courses;u=min(1,t+.021)
        # Downturned lips and staggered side joints distinguish neighbouring rows.
        a=point(-half(t),t);c=point(half(t),t)
        a[2]+=.023;c[2]+=.023
        solid([a,c,point(half(u),u)+[0,0,.032],point(-half(u),u)+[0,0,.032]],TILE2,'Roof course '+str(i+1),.029)
        gap=.26 if not lod else .52
        xs=np.arange(-half(u)+.14+(i%2)*gap/2,half(u)-.09,gap)
        v=min(1,(i+1)/courses)
        for x in xs:
            if abs(x)>half(v)-.02:continue
            solid([point(x-.007,u)+[0,0,.021],point(x+.007,u)+[0,0,.021],point(x+.007,v)+[0,0,.025],point(x-.007,v)+[0,0,.025]],TILE2,'Overlapping tile side joints '+str(i+1),.016)
    for sign in [-1,1]:
        # Hip ends slope out toward both front and side eaves.
        verts=[point(sign*half(0),0),point(sign*half(1),1),[sign*length,back,eave]]
        if sign>0:verts=verts[::-1]
        solid(verts,TILE,'Side hip '+str(sign),.14)
        line=[point(sign*half(0),0),point(sign*half(1),1)]
        builder.tube(line,.074,TILE2,8 if lod else 14,'Hip roll '+str(sign))
    builder.tube([point(-half(1),1),point(half(1),1)],.082,TILE2,8 if lod else 16,'Continuous ridge cap')
    for i,(u,v) in enumerate([(578,218),(937,237)]):
        # Locate two rooflights by ray/roof-plane intersection in the courtyard view.
        from photo_plane import RECORD
        eye=np.array(RECORD['wide']['eye_m']);direction=position(u,v,0,'wide')-eye
        k=(eave+(eye[1]-front)*rise/run-eye[2])/(direction[2]-direction[1]*rise/run)
        c=eye+k*direction;t=(c[1]-front)/run
        panel=[point(c[0]+dx,t+dy/run)+[0,0,.066] for dx,dy in [(-.26,-.21),(.26,-.21),(.26,.21),(-.26,.21)]]
        solid(panel,METAL,'Rooflight curb '+str(i+1),.071)
        panel=[point(c[0]+dx,t+dy/run)+[0,0,.092] for dx,dy in [(-.225,-.18),(.225,-.18),(.225,.18),(-.225,.18)]]
        solid(panel,GLASS,'Rooflight glass '+str(i+1),.024)
