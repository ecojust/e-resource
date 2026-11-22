"""Gallery steelwork, terracotta roof, lower elevations and the projecting terrace."""
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
import street_brick_arcade as arcade

ROOT=Path(__file__).resolve().parents[1]/'measurements'
OPENINGS=json.loads((ROOT/'gallery-opening-controls.json').read_text())['openings']
SPAN=26.537
STEEL='Gallery | weathered steel casements'
BEAD='Gallery | fine glazing bars'
DARK='Gallery | shaded interior'
MID='Gallery | steel-grey glass'
LIGHT='Gallery | pale reflected glass'
SHADE='Gallery | horizontal screen blades'
CHALK='Gallery | pale lintel and sill'
BELT='Gallery | russet cross course'
FASCIA='Main roof | dark eaves board'
EDGE='Main roof | pale gutter'
CREAM='Terrace | warm limestone'
TRIM='Terrace | weathered cap'
RED='Main roof | terracotta bed'
TILES=['Main roof | red tile '+str(i) for i in range(1,5)]
PALETTE={m:arcade.pigment(c,r,metal) for m,c,r,metal in (
 (STEEL,(75,72,69),.59,.23),(BEAD,(99,95,89),.61,.19),(DARK,(43,46,48),.44,.08),
 (MID,(105,110,111),.38,.13),(LIGHT,(175,177,169),.45,.09),(SHADE,(160,161,151),.65,.15),
 (CHALK,(191,184,163),.88,0),(BELT,(157,102,91),.91,0),(FASCIA,(91,70,62),.88,0),
 (EDGE,(171,165,151),.74,.08),(CREAM,(213,199,170),.87,0),(TRIM,(181,167,138),.91,0),
 (RED,(146,79,63),.90,0),*[(k,c,.90,0)for k,c in zip(TILES,[(169,92,72),(176,99,78),(185,104,81),(171,91,69)])])}

def cuboid(b,x0,x1,y0,y1,z0,z1,mat,name):
    b.box(((x0+x1)*.5,(y0+y1)*.5,(z0+z1)*.5),(x1-x0,y1-y0,z1-z0),mat,label=name)

def front(b,shape,y0,y1,mat,name):
    if not shape.is_empty:b.prism(shape,-y1,-y0,lambda x,z,t:(x,-t,z),mat,name)

def end(b,shape,x0,x1,mat,name):
    if not shape.is_empty:b.prism(shape,x0,x1,lambda y,z,t:(t,y,z),mat,name)

def gallery(b,lod):
    wall=box(0,8.59,SPAN,11.78)
    holes=[box(o['left'],o['bottom'],o['right'],o['top']) for o in OPENINGS]
    front(b,wall.difference(unary_union(holes)),0,.41,arcade.GREY,'Gallery | brick wall and inner window returns')
    for z0,z1 in [(8.78,8.91),(10.58,10.75),(11.55,11.61)]:
        front(b,box(.012,z0,SPAN-.012,z1).difference(unary_union(holes)),-.009,.001,BELT,'Gallery | horizontal brick belt')
    for o in OPENINGS:
        l,r,z,t=o['left'],o['right'],o['bottom'],o['top'];j=o['number'];n=4 if r-l>1.5 else 2
        name='Gallery window '+str(j).zfill(2)
        cuboid(b,l-.052,r+.052,-.102,.17,z-.061,z,CHALK,name+' | overhanging sill')
        cuboid(b,l-.044,r+.044,-.033,.17,t,t+.10,CHALK,name+' | pale head')
        glass=LIGHT if j in (3,4,5,14) else MID if j in (1,2,10,11) else DARK
        frame=.154
        pane=frame+.045
        w=.041
        # The 2026 frame shows four tall leaves in each wide opening and two
        # leaves in the narrow openings. Smaller bars continue behind the pale screens.
        for u in np.linspace(l+w/2,r-w/2,n+1):
            cuboid(b,u-w/2,u+w/2,frame,frame+.055,z,t,STEEL,name+' | full-height leaf stile')
        for h in (z+w/2,t-w/2,t-.32):
            cuboid(b,l+w,r-w,frame-.002,frame+.053,h-w/2,h+w/2,STEEL,name+' | perimeter and head rail')
        for k in range(n):
            u0=l+w+(r-l-2*w)*k/n;u1=l+w+(r-l-2*w)*(k+1)/n
            cuboid(b,u0,u1,pane,pane+.034,z+.031,t-.031,glass,name+' | inset glazing')
            if j in (3,4,5,10,14):
                # The lighter covering on no.4 stops above the lower dark lights.
                bottom=z+(t-z)*.38 if j in (4,10) else z+.038
                cuboid(b,u0+.012,u1-.012,pane-.008,pane,bottom,t-.36,LIGHT,name+' | pale backing')
            if j==11:
                for h in np.linspace(z+.13,t-.39,10):
                    cuboid(b,u0,u1,pane-.017,pane-.002,h,h+.035,SHADE,name+' | visible shutter slats')
            if not lod:
                u=(u0+u1)*.5
                cuboid(b,u-.008,u+.008,frame+.016,pane+.002,z+.046,t-.34,BEAD,name+' | slender vertical glazing bar')
        for h in [z+(t-z)*v for v in (.27,.53,.69)]:
            cuboid(b,l+w,r-w,frame+.012,pane,h-.010,h+.010,BEAD,name+' | thin horizontal glazing bar')
    for l,r in zip([0]+[o['right'] for o in OPENINGS],[o['left'] for o in OPENINGS]+[SPAN]):
        x=(l+r)*.5;wid=min(r-l-.035,.34)
        if wid>.08:
            cuboid(b,x-wid/2,x+wid/2,-.072,0,8.64,11.66,arcade.GREY,'Gallery | projecting brick mullion')
            cuboid(b,x-wid/2-.001,x+wid/2+.001,-.079,-.071,10.59,10.74,BELT,'Gallery pier | red cross course')

def arch(x,width,zbase,shoulder,peak):
    ts=np.linspace(0,math.pi,27)
    return Polygon([(x-width/2,zbase),(x+width/2,zbase),*[(x+width/2*math.cos(t),shoulder+(peak-shoulder)*math.sin(t)) for t in ts]])

def ground(b,lod):
    # Five crowns can be followed behind the boundary rail on the west in the
    # 2026 frame. The foliage obscures the rest of this storey's masonry.
    measured=[(1.05,.89),(2.85,1.70),(4.65,1.03),(6.47,1.72),(8.36,1.05)]
    shapes=[arch(x,w,.48,3.27,3.73) for x,w in measured]
    front(b,box(0,0,SPAN,4.61).difference(unary_union(shapes)),.015,.43,arcade.GREY,'Lower wall | visible arch openings')
    for i,((x,w),shape) in enumerate(zip(measured,shapes),1):
        name='Lower arch '+str(i)
        outer=arch(x,w+.22,.48,3.27,3.84);ring=outer.difference(shape).intersection(box(x-w,3.27,x+w,4.))
        front(b,ring,-.026,.015,arcade.TRIM,name+' | visible fired brick hood')
        front(b,shape,.24,.27,MID,name+' | recessed glass')
        for u in np.linspace(x-w*.37,x+w*.37,3 if w>1.4 else 2):
            front(b,shape.intersection(box(u-.017,.49,u+.017,3.75)),.20,.25,STEEL,name+' | principal steel bars')
        for h in (1.68,2.56,3.15):
            front(b,shape.intersection(box(x-w/2,h-.014,x+w/2,h+.014)),.20,.25,STEEL,name+' | cross bars')
    cuboid(b,0,SPAN,-.04,.43,4.45,4.57,BELT,'Lower storey | horizontal red course')

def tapered_baluster(b,x,y,z0,z1,mat,name,lod=False):
    ring=[(0,.073),(.055,.073),(.098,.056),(.20,.047),(.31,.065),(.45,.070),(.60,.039),(.77,.035),(.85,.053),(.94,.065),(1,.065)]
    vertices=[];faces=[];n=6 if lod else 10
    for f,r in ring:
        for i in range(n):
            a=i*2*math.pi/n;vertices.append((x+r*math.cos(a),y+r*math.sin(a),z0+f*(z1-z0)))
    for k in range(len(ring)-1):
        for i in range(n):
            j=(i+1)%n;faces.append((k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i))
    faces += [tuple(reversed(range(n))),tuple(range((len(ring)-1)*n,len(ring)*n))]
    b.add(vertices,faces,mat,name)

def terrace(b,lod):
    data=json.loads((ROOT/'video-terrace-and-roof.json').read_text())
    ps=np.asarray(data['triangulated_terrace_cap_centres_xyz_m'])
    outline=[(ps[0,0]-.19,.17),(ps[0,0]-.19,ps[0,1]),*[(x,y-.14) for x,y,_ in ps],(ps[-1,0]+.18,ps[-1,1]),(ps[-1,0]+.18,.17)]
    deck=Polygon(outline)
    for lo,hi,extension,mat,label in [(4.61,4.82,.07,TRIM,'stepped lower fascia'),(4.82,4.96,.15,CREAM,'overhanging deck cap'),(4.96,5.01,0,TRIM,'floor')]:
        b.prism(deck.buffer(extension,join_style=2) if extension else deck,lo,hi,lambda x,y,z:(x,y,z),mat,'Terrace | '+label)
    for i,(x,y,z) in enumerate(ps,1):
        for width,lo,hi in [(.43,4.96,5.14),(.33,5.14,z-.13),(.40,z-.13,z-.078),(.46,z-.078,z)]:
            cuboid(b,x-width/2,x+width/2,y-width/2,y+width/2,lo,hi,CREAM,'Terrace pier '+str(i)+' | limestone course')
    for i,(p,q,count) in enumerate(zip(ps,ps[1:],(15,2,14)),1):
        xy=p[:2];d=q[:2]-xy;length=np.linalg.norm(d);u=d/length;v=np.array([-u[1],u[0]])
        def beam(z0,z1,width,mat,name):
            a=xy+u*.143;c=xy+d-u*.143
            poly=Polygon([a-v*width/2,c-v*width/2,c+v*width/2,a+v*width/2]);b.prism(poly,z0,z1,lambda x,y,z:(x,y,z),mat,name)
        h=float((p[2]+q[2])/2-.105)
        beam(5.012,5.14,.24,CREAM,'Terrace | balustrade plinth')
        beam(h-.072,h+.006,.26,CREAM,'Terrace | stone handrail')
        for k in range(count):
            x,y=xy+u*(.218+(length-.436)*(k+.5)/count)
            tapered_baluster(b,x,y,5.135,h-.067,CREAM,'Terrace span '+str(i)+' | turned balusters',lod)
    # The recessed support below the deck is visible through the fence. Keep
    # the central bay open and stop the returns at the actual projecting deck.
    for x,y,_ in [ps[0],ps[-1]]:
        cuboid(b,x-.20,x+.20,y-.14,.04,.10,4.63,arcade.GREY,'Terrace | side supporting wall')

def roof_height(y):
    return 13.997+(y-3.445)*.59

def roof(b,lod):
    x0,x1=-.22,SPAN+.24;y0,yr,y1=-.39,7.54,14.66
    rz=roof_height(yr)
    def face_y(y):return roof_height(y) if y<=yr else rz-(y-yr)*.55
    front_shape=box(x0,y0,x1,yr).difference(box(5.30,3.443,13.40,6.44))
    eave=face_y(y0)
    hip_run=(rz-eave)/.77
    xl=x0+hip_run;xr=x1-hip_run
    # The west photograph shows a level eaves line across the end wall.
    # The east end of the ridge descends toward the corner in the 2026 view.
    front_plan=Polygon([(x0,y0),(x1,y0),(xr,yr),(xl,yr)])
    back_plan=Polygon([(xl,yr),(xr,yr),(x1,y1),(x0,y1)])
    west_plan=Polygon([(x0,y0),(xl,yr),(x0,y1)])
    east_plan=Polygon([(x1,y0),(x1,y1),(xr,yr)])
    hole=box(5.30,3.30,13.40,6.44)
    planes=[(front_plan.difference(hole),lambda x,y:face_y(y),False,False),
            (back_plan,lambda x,y:rz-(y-yr)*(rz-eave)/(y1-yr),False,True),
            (west_plan,lambda x,y:eave+.77*(x-x0),True,False),
            (east_plan,lambda x,y:eave+.77*(x1-x),True,True)]
    for poly,height,across,invert in planes:
        b.prism(poly,-.105,0.,lambda x,y,z:(x,y,height(x,y)+z),RED,'Main roof | hip and pitch beds')
        # Each full-size tile has a raised side roll and a low drip lip. At the
        # hips, the tile is trimmed to the actual oblique intersection.
        pitch=.31 if not lod else .44
        left,bottom,right,top=poly.bounds
        aa,bb=(left,right) if across else (bottom,top)
        ss,tt=(bottom,top) if across else (left,right)
        course_bounds=np.linspace(aa,bb,max(2,round((bb-aa)/pitch)+1))
        for k,(a,c) in enumerate(zip(course_bounds,course_bounds[1:])):
            strip=box(a,ss,c,tt) if across else box(ss,a,tt,c)
            geom=poly.intersection(strip)
            polygons=[geom] if geom.geom_type=='Polygon' else [part for part in geom.geoms if part.geom_type=='Polygon']
            for shape in polygons:
                if shape.area<1e-4:continue
                lip=a if not invert else c
                def mapper(x,y,z):
                    f=1.-abs((x if across else y)-lip)/(c-a)
                    return (x,y,height(x,y)+z+.024*f)
                b.prism(shape,.001,.022,mapper,TILES[k%4],'Main roof | overlapping tile courses')
        # The longitudinal rolls are separate real sections. Clip each at the
        # eaves and hips and taper it onto the bedding.
        from shapely.geometry import LineString
        lateral=np.arange(ss+.12,tt,.24 if not lod else .40)
        for u in lateral:
            line=LineString([(aa,u),(bb,u)]) if across else LineString([(u,aa),(u,bb)])
            cut=poly.intersection(line)
            lines=[cut] if cut.geom_type=='LineString' else [part for part in getattr(cut,'geoms',[]) if part.geom_type=='LineString']
            for line in lines:
                if line.length<.10:continue
                q=[]
                for x,y in (line.coords[0],line.coords[-1]):
                    q.append((x,y,height(x,y)+.041))
                b.tube(q,.021 if not lod else .025,TILES[1],8 if not lod else 6,'Main roof | rounded tile ribs')
    for x,y in [(x0,y0),(x0,y1),(x1,y0),(x1,y1)]:
        bx=xl if x==x0 else xr
        b.tube([(x,y,eave+.035),(bx,yr,rz+.045)],.064,TILES[3],8 if lod else 12,'Main roof | diagonal hip tile')
    for y in (y0,y1):
        cuboid(b,x0,x1,y-.035,y+.035,face_y(y)-.17,face_y(y)-.074,FASCIA,'Main roof | eaves fascia')
        cuboid(b,x0-.015,x1+.015,y-.069,y+.058,face_y(y)-.104,face_y(y)-.012,EDGE,'Main roof | gutter lip')
    b.tube([(xl,yr,rz+.035),(xr,yr,rz+.035)],.091,TILES[3],10 if lod else 16,'Main roof | raised tiled ridge')
    # Margin below the roof is a brick gable. The opposite and rear sides use
    # a simple closure wherever the street photographs do not show openings.
    yz=[(0,0),(14.41,0),(14.41,eave-.05),(0,eave-.05)]
    end(b,Polygon(yz),SPAN-.32,SPAN,arcade.GREY,'East end | estimated closure')
    cuboid(b,.29,SPAN-.31,14.08,14.41,.03,face_y(14.41)-.10,arcade.GREY,'Rear | estimated structural closure')
    cuboid(b,0,SPAN,0,.38,11.77,face_y(0)-.08,arcade.GREY,'Gallery | roof bearing wall')
    west_end(b,Polygon(yz))

def west_end(b,wall):
    apertures=[(.56,9.34,1.74,11.04),(4.74,9.41,6.01,11.09),(10.19,9.35,11.46,11.10),
               (.60,5.47,1.78,7.23)]
    end(b,wall.difference(unary_union([box(*rect) for rect in apertures])),0,.31,arcade.GREY,'West end | brick masonry and deep window jambs')
    for i,(l,z,r,t) in enumerate(apertures):
        name='West return '+str(i+1)
        cuboid(b,.165,.194,l,r,z,t,MID,name+' | dark glass')
        for u in (l+.023,(l+r)*.5,r-.023):
            cuboid(b,.122,.173,u-.021,u+.021,z,t,STEEL,name+' | casement')
        for h in (z+.024,z+(t-z)*.53,t-.026):
            cuboid(b,.123,.176,l,r,h-.022,h+.022,STEEL,name+' | rails')
        cuboid(b,-.071,.16,l-.054,r+.054,z-.08,z,CHALK,name+' | stone sill')
    for h in (4.52,8.49,9.13,10.53,11.60):
        cuboid(b,-.051,.06,0,14.41,h,h+.093,BELT,'West end | masonry course')

def screen_wall(b,lod):
    """The three infilled arches at the garden edge, visible in the 2026 film."""
    d=json.loads((ROOT/'courtyard-screen.json').read_text());y=d['nominal_face_y']
    lo,_,wl=d['west_cap'];hi,_,wr=d['east_cap'];h=(wl+wr)/2-.095
    name='Garden screen | '
    openings=[arch((o['left']+o['right'])/2,o['right']-o['left'],.24,o['spring'],o['peak']) for o in d['arches']]
    rings=[a.buffer(.105,quad_segs=3).difference(a).intersection(box(lo,-1,hi,h-.12))for a in openings]
    face=box(lo,.29,hi,h-.10)
    front(b,face,y+.045,y+.30,CREAM,name+'brick backing')
    # Rows continue within the blind niches, at a slightly receded plane.
    row_height=.083;length=.237;allrings=unary_union(rings)
    for i in range(math.ceil((h-.40)/row_height)):
        z=.31+i*row_height
        if z>=h-.11:break
        a=lo-.19+(i%2)*.5*length;j=0
        while a<hi:
            left=max(lo+.004,a+.006);right=min(hi-.004,a+length-.006)
            if right>left+.01:
                block=box(left,z,right,min(h-.105,z+row_height-.009))
                if block.area>1e-5:
                    permitted=block.difference(allrings)
                    if permitted.area>.00006:
                        front(b,permitted,y+.026,y+.05,[TRIM,CHALK,CREAM,CHALK][(i*7+j*3)%4],name+'light facing bricks')
            a+=length;j+=1
    for i,(o,ring) in enumerate(zip(d['arches'],rings)):
        front(b,ring,y-.058,y+.046,arcade.TRIM,name+'raised blind arch '+str(i+1))
        half=(o['right']-o['left'])/2;mid=(o['left']+o['right'])*.5
        for t in np.linspace(.03,math.pi-.03,29 if not lod else 18):
            u=mid+half*math.cos(t);z=o['spring']+(o['peak']-o['spring'])*math.sin(t)
            b.tube([(u,y-.059,z),(u+.10*math.cos(t),y-.059,z+.10*math.sin(t))],.0055,arcade.BEAD,5,name+'radial joints')
    for loz,hiz,width in [(h-.10,h-.03,.03),(h-.03,h+.07,.064)]:
        cuboid(b,lo-.05,hi+.05,y-width,y+.33,loz,hiz,CREAM,name+'coping')
    from daren_photo_plane import on_wall
    posts=[on_wall(u,v,y) for u,v in d['foreground_columns_video_px']]
    for u,_,t in posts:
        for width,z0,z1,mat in [(.265,.25,t-.32,arcade.GREY),(.32,t-.32,t-.22,CREAM),(.35,t-.21,t-.13,TRIM),(.42,t-.12,t,CREAM)]:
            cuboid(b,u-width,u+width,y-width+.13,y+width+.13,z0,z1,mat,name+'square pilaster and cap')
    # Low railing in the two openings between the three western piers.
    for p,q in zip(posts[:2],posts[1:3]):
        a=p[0]+.28;c=q[0]-.28
        n=max(8,round((c-a)/.17))
        for x in np.linspace(a,c,n+1):
            hh=2.72+.07*math.cos((x-a)*2.2)
            cuboid(b,x-.013,x+.013,y+.105,y+.135,.47,hh,STEEL,name+'slender rail')
        for z in (.56,.77,1.30):cuboid(b,a,c,y+.10,y+.14,z-.018,z+.018,STEEL,name+'iron ties')
        size=(c-a)/4.
        for i in range(4):
            m=a+(i+.5)*size
            for radius in [.43,.31]:
                arc=[(m+radius*math.cos(ang),y+.098,2.62+radius*math.sin(ang)) for ang in np.linspace(0,math.pi,20 if not lod else 12)]
                b.tube(arc,.017,STEEL,6,name+'rounded iron crowns')

def add_school(b,lod=False):
    start=len(b.parts)
    gallery(b,lod);ground(b,lod);terrace(b,lod);screen_wall(b,lod);roof(b,lod)
    for part in b.parts[start:]:
        if part['material']==arcade.GREY:arcade.brick_uv(part)
