"""Editable north window wall, ashlar porch and street doors of the former Chung Foo Union Bank."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade
from photo_plane import position
from material_names import MATERIAL

DATA=Path(__file__).resolve().parents[1]/'measurements'
LIMESTONE='Light projecting limestone mouldings'
COURSE='Recessed ashlar joints'
GRANITE='Grey stone porch plinths'
IRON='Blackened steel framing'
GLASS='Green grey bank glazing'
DARKGLASS='Recessed smoked entrance glazing'
BRONZE='Dark bronze lattice'
SERVICE='Weathered condensers'
VENT='Slatted condenser grille'
TRIM='Pale metal case edging'

def colour(rgb,rough=.8,metal=0):
    a=np.array(rgb)/255.
    return dict(color=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)

PALETTE={LIMESTONE:colour([202,198,189]),COURSE:colour([175,172,165]),GRANITE:colour([149,146,141]),
    IRON:colour([68,66,61],.54,.32),GLASS:colour([139,160,165],.32,.26),
    DARKGLASS:colour([58,54,50],.33,.18),BRONZE:colour([85,75,59],.5,.37),
    SERVICE:colour([143,143,134],.62,.18),VENT:colour([88,89,84],.69,.22),TRIM:colour([191,190,176],.69,.20)}

def observe(q,y=0.,view='close'):
    pts=np.array([position(*p,y,view) for p in q])
    return box(np.mean(pts[[0,3],0]),np.mean(pts[[2,3],2]),
               np.mean(pts[[1,2],0]),np.mean(pts[[0,1],2]))

def windows():
    seen=json.loads((DATA/'north-wall-openings.json').read_bytes())
    rows={(v['level'],v['bay']):observe(v['outer_frame']) for v in seen['sash'] if 'outer_frame' in v}
    # These two openings retain the axis of the visible third-storey eastern window.
    x=rows[3,1].centroid.x
    for level in [1,2]:
        a,b,c,d=rows[level,2].bounds
        rows[level,1]=box(x-(c-a)/2,b,x+(c-a)/2,d)
    return rows

def sash(f,hole,label,verticals,transom,front=.062,entry=False):
    a,b,c,d=hole.bounds
    cuts=[]
    for fraction in verticals:
        x=a+fraction*(c-a)
        cuts.append(box(x-.026,b,x+.026,d))
    for fraction in transom:
        z=b+fraction*(d-b)
        cuts.append(box(a,z-.028,c,z+.028))
    inner=hole.buffer(-.049,join_style=2)
    frame=hole.buffer(.012,join_style=2).difference(inner.difference(unary_union(cuts)))
    f.prism(hole.buffer(.018,join_style=2),-front-.083,-front-.066,DARKGLASS if entry else GLASS,label+' glass')
    f.prism(frame,-front-.067,-front,BRONZE if entry else IRON,label+' glazing bars')

def belt(f,left,right,z,bands,label):
    for index,(dz,h,projection,material) in enumerate(bands,1):
        f.prism(box(left,z+dz,right,z+dz+h),-.02,projection,material,label+' '+str(index))

def north_wall(builder):
    f=Facade(builder,(-1,0),(1,0),'Bank')
    rows=windows()
    all_holes=unary_union(list(rows.values()))
    upper=box(-14.123,7.15,14.123,26.57).difference(all_holes)
    f.prism(upper,-.38,0,MATERIAL,'upper north ashlar with 36 openings')
    for i,u in enumerate([109,175,627,706],1):
        x,_,z=position(u*2041/860,104*1363/574,-.12)
        body=box(x-.29,7.36,x+.29,z).intersection(upper)
        f.prism(body,-.036,.096,MATERIAL,'flanking shallow pilaster '+str(i))
        for dz,w,depth in [(-.10,.36,.12),(.025,.39,.16),(.17,.42,.23),(.27,.41,.19)]:
            f.prism(box(x-w,z+dz,x+w,z+dz+.096),.085,depth,LIMESTONE,'pier capital '+str(i))
        for side in [-1.,1.]:
            for step in range(3):
                where=x+side*(.29+step*.027)
                f.prism(box(where-.02,z-.38+step*.115,where+.02,z+.246),.091,.129,LIMESTONE,'pilaster edging '+str(i))
    for (level,bay),hole in rows.items():
        a,b,c,d=hole.bounds
        label=f'L{level} bay {bay}'
        verticals=[.5] if level==1 or bay in {1,2,8,9} else [.34,.68]
        sash(f,hole,label,verticals,[.72 if level<4 else .62])
        # Openings have separate projecting sill and raised rectangular head.
        belt(f,a-.075,c+.075,b,[(-.095,.115,.096,LIMESTONE),(-.124,.038,.057,COURSE)],label+' sill')
        if level!=4:
            belt(f,a-.06,c+.06,d,[(0,.096,.066,LIMESTONE),(.096,.032,.089,LIMESTONE)],label+' lintel')
    # Joint courses pass behind jambs and are clipped at each sash.
    for n,z in enumerate(np.arange(7.60,26.36,.75),1):
        strip=box(-14.12,z,14.12,z+.010).intersection(upper)
        f.prism(strip,-.001,.0035,COURSE,'ashlar bed '+str(n))
    for course,z in enumerate(np.arange(7.61,26.36,.75),1):
        for x in np.arange(-14.+.83*(course%2),14.,1.74):
            seam=box(x,z,x+.008,z+.725).intersection(upper)
            f.prism(seam,-.003,.0035,COURSE,'ashlar upright joints '+str(course))
    for j,x in enumerate([-12.83,-9.46,-7.94,7.72,9.22,11.91,13.12],1):
        pier=box(x-.084,7.22,x+.084,24.28).intersection(upper)
        f.prism(pier,-.006,.069,LIMESTONE,'applied pier strip '+str(j))
    attic_bottom=np.median([rows[4,b].bounds[1] for b in range(1,10)])
    cap=np.median([rows[4,b].bounds[3] for b in range(1,10)])+.79
    belt(f,-14.16,14.16,attic_bottom-.34,[(-.14,.13,.14,LIMESTONE),(-.02,.14,.24,LIMESTONE),
        (.12,.075,.32,LIMESTONE),(.194,.065,.35,LIMESTONE)],'principal upper cornice')
    belt(f,-14.22,14.22,cap,[(-.19,.10,.11,LIMESTONE),(-.09,.10,.22,LIMESTONE),
        (.01,.12,.39,LIMESTONE),(.13,.09,.47,LIMESTONE)],'attic crown')
    # Short coping end blocks can be read against the skyline between the two roof projections.
    for j,x in enumerate([-7.36,-4.70,-1.89,.85,3.62,6.62,9.37],1):
        f.prism(box(x-.27,cap+.16,x+.27,cap+.33),-.146,.22,LIMESTONE,'parapet cap '+str(j))
    builder.box((0,.62,cap+.04),(28.22,1.24,.29),LIMESTONE,label='Front coping return')
    for side,x in [('east',-14.03),('west',14.03)]:
        builder.box((x,.55,cap/2),(.18,1.10,cap),MATERIAL,label=side+' wall return')
    return rows

def condenser_units(builder,lod):
    obs=json.loads((DATA/'north-wall-openings.json').read_bytes())
    f=Facade(builder,(-1,0),(1,0),'Equipment')
    for n,(u,v) in enumerate(obs['condensers'],1):
        x,_,z=position(u,v,-.31)
        lab='external unit '+str(n)
        face=box(x-.335,z-.22,x+.335,z+.22)
        f.prism(face,.091,.317,SERVICE,lab+' housing')
        fan=Point(x-.065,z).buffer(.160,quad_segs=6 if lod else 12)
        f.prism(fan,.317,.325,VENT,lab+' fan')
        f.prism(fan.buffer(.014).difference(fan),.318,.339,TRIM,lab+' rolled rim')
        for off in [-.10,-.05,0,.05,.10][::2 if lod else 1]:
            strip=box(x-.25,z+off-.007,x+.12,z+off+.007).intersection(fan)
            f.prism(strip,.326,.337,SERVICE,lab+' fan guard')
        for off in [-.24,.24]:
            builder.box((x+off,-.16,z-.269),(.044,.36,.045),IRON,label=lab+' mounting bracket')

def side_portal(builder):
    # West low wing meets the porch at the street. The photographed right
    # gate and the small gridded light belong to this plane.
    y=-4.50
    f=Facade(builder,(-1,y),(1,y),'West wing')
    data=json.loads((DATA/'north-wall-openings.json').read_bytes())['west_side']
    opening=observe(data['door'],y,'wide');light=observe(data['transom'],y,'wide')
    a,b,c,d=opening.bounds
    opening=box(a,.027,c,d)
    centre=(a+c)*.5
    edge=max(9.66,min(a-.82,10.80))
    wall=box(edge,0.,max(14.126,c+.52),8.48)
    holes=unary_union([opening,light])
    f.prism(wall.difference(holes),-.37,0,MATERIAL,'outer portal block')
    # The pair of gate leaves and glazed high transom are set back from the street stone.
    sash(f,opening,'tall street door',[.5],[.20,.76],.18,True)
    sash(f,light,'over-door light',[.16,.26,.74,.84],[.5],.12,True)
    inner=box(a-.26,d+.13,c+.26,d+.65)
    f.prism(inner,-.02,.097,LIMESTONE,'flat entablature frame')
    f.prism(inner.buffer(-.068,join_style=2),.096,.103,GRANITE,'inset tablet')
    for no,key in enumerate(['lower_hood','upper_hood']):
        outer=observe(data[key],y-.30,'wide')
        left,low,right,top=outer.bounds
        width=right-left
        cut=low+.24*(top-low)
        belt(f,left+.07,right-.07,cut,[(0,.09,.19,LIMESTONE),(.09,.08,.28,LIMESTONE),(.17,.085,.35,LIMESTONE),(.255,.052,.405,LIMESTONE)],'portal hood '+str(no+1))
        for side,x in enumerate([left+.14,right-.14]):
            f.prism(box(x-.088,low-.22,x+.088,cut+.04),.015,.17,LIMESTONE,'hood bracket '+str(no+1))
            f.prism(box(x-.047,low-.17,x+.047,cut-.06),.169,.183,GRANITE,'hood bracket face')
    for z in np.arange(.65,8.28,.62):
        f.prism(wall.intersection(box(edge,z,max(14.126,c+.52),z+.011)).difference(holes),-.001,.003,COURSE,'portal ashlar joint')
    builder.box((edge-.085,(y+.25)/2,4.24),(.17,abs(y)+.25,8.48),MATERIAL,label='West wing inside return')
    return opening,light

def grille(f,shape,label):
    a,b,c,d=shape.bounds; h=d-b;w=c-a
    f.prism(shape.buffer(.020,join_style=2),-.24,-.22,DARKGLASS,label+' shadow glass')
    inner=shape.buffer(-.070,join_style=2)
    grid=[box((a+c)/2-.034,b,(a+c)/2+.034,d)]
    for frac in [.18,.83]:
        z=b+h*frac;grid.append(box(a,z-.024,c,z+.024))
    for x in np.arange(a+.17,c-.06,.13):
        grid.append(box(x-.009,b+.10,x+.009,d-.075))
    frame=shape.buffer(.015,join_style=2).difference(inner.difference(unary_union(grid)))
    f.prism(frame,-.215,-.125,BRONZE,label+' upright bars and stiles')
    return shape

def rear_doors(builder,wall_y):
    f=Facade(builder,(-1,wall_y),(1,wall_y),'Vestibule')
    # Read the three image-supported central openings in the 2017 archival
    # exposure. The rightmost return and chair/steps obscure the lowest rails.
    observed=json.loads((DATA/'rear-porch-openings.json').read_bytes())['openings']
    dark=[]
    for n,entry in enumerate(observed,1):
        hole=observe(entry['portal'],wall_y,'wide');a,b,c,d=hole.bounds
        dark.append(hole)
        trans=observe(entry['high_light'],wall_y,'wide')
        for stroke in entry['relief_strokes']:
            points=[position(*uv,wall_y-.084,'wide') for uv in stroke]
            builder.tube(points,.037,LIMESTONE,6,'Raised overdoor leaf '+str(n))
        dark.append(trans)
        grille(f,hole,'entrance '+str(n))
        sash(f,trans,'grilled upper light '+str(n),[.25,.50,.75],[.51],.082,True)
        a,b,c,d=trans.bounds
        # The upper lights have additional diagonal grille bars in the near view.
        width=c-a;height=d-b
        diag=[]
        for x in np.arange(a-width,c+width,.26):
            for sign in [1,-1]:
                line=LineString([(x,b),(x+sign*height,d)]).buffer(.011,cap_style=2)
                diag.append(line.intersection(trans.buffer(-.058,join_style=2)))
        f.prism(unary_union(diag),-.075,-.056,BRONZE,'crossed transom grille '+str(n))
        f.prism(box(a-.12,hole.bounds[3]+.045,c+.12,hole.bounds[3]+.136),-.008,.136,LIMESTONE,'overdoor ledge '+str(n))
    wall=box(-14.11,0.,10.46,8.28).difference(unary_union(dark))
    f.prism(wall,-.326,.005,MATERIAL,'recessed porch wall')
    return dark

def base_and_steps(builder,axes,axis_y,bases):
    # The paired middle shafts stand on common oblong plinths. The two
    # outer shafts each have a smaller square pedestal.
    for index,pair in enumerate([(0,),(1,2),(3,4),(5,)],1):
        base_z=min(bases[i] for i in pair)
        xmin=axes[pair[0]]-.415;xmax=axes[pair[-1]]+.415
        mid=(xmin+xmax)/2;width=xmax-xmin
        lab='column plinth '+str(index)
        for z,h,extr,depth,material in [(0,.21,.145,1.13,GRANITE),(.21,.14,.09,1.06,GRANITE),
                (.35,base_z-.58,0.,.92,MATERIAL),(base_z-.23,.105,.042,.99,LIMESTONE),
                (base_z-.125,.125,.09,1.08,LIMESTONE)]:
            builder.box((mid,axis_y,z+h/2),(width+extr*2,depth,h),material,label=lab+' course '+str(round(100*z)))
        for i in pair:
            h=bases[i]-base_z+.032
            builder.box((axes[i],axis_y,bases[i]-h/2),(.71,.71,h),LIMESTONE,label=lab+' square column pad '+str(i+1))
    for n in range(6):
        # Six visible risers lead from the kerb to the recessed lobby.
        y=axis_y-.17+n*.272;z=.15*(n+1)
        builder.box((2.70,y+.137,z/2),(6.32,.276,z),GRANITE,label='granite stair '+str(n+1))
        builder.box((2.70,y+.021,z-.019),(6.34,.07,.041),LIMESTONE,label='rounded nosing '+str(n+1))
    builder.box((2.70,axis_y+2.39,.425),(6.33,1.91,.85),GRANITE,label='Entrance landing')

def porch_beam(builder,x0,x1,y_front,z0):
    # The ashlar beam spans the full porch including the paired columns.
    f=Facade(builder,(-1,y_front),(1,y_front),'Entablature')
    depth=abs(y_front)+.34
    # The underside of the street face is lower than the two sheltered
    # coffer rows. Six points on the close photograph and a separate edge
    # on the register view locate this exposed arris at about 6.33 m.
    # The edge over the street curves down over the centre bay. The
    # photographed front edge at the fourth shaft rises above the central
    # soffit edge and the bearing returns up towards the sheltered porch.
    stations=[(x0,6.325),(.09,6.311),(2.40,6.309),(3.09,6.310),
              (4.39,6.328),(5.47,6.353),(6.30,6.375),(x1,6.375)]
    vertices=[]
    for x,z in stations:
        vertices.extend([(x,y_front-.054,z),(x,y_front+.165,6.555),
                         (x,y_front+.165,z0),(x,y_front-.054,z0)])
    faces=[(3,2,1,0)]
    for start in range(0,len(vertices)-4,4):
        for k in range(4):
            a=start+k
            b=start+(k+1)%4
            faces.append((a,b,b+4,a+4))
    faces.append(tuple(range(len(vertices)-4,len(vertices))))
    builder.add(vertices,faces,LIMESTONE,'Entablature street-facing stone apron')
    for name,z,h,d,mat in [('architrave bed',z0,.17,.054,LIMESTONE),
            ('first fascia',z0+.17,.18,.105,LIMESTONE),('second fascia',z0+.35,.13,.146,LIMESTONE),
            ('narrow bead',z0+.48,.066,.195,LIMESTONE),('plain frieze',z0+.546,.54,.102,MATERIAL),
            ('crown fillet',z0+1.086,.118,.164,LIMESTONE),('projecting cornice',z0+1.204,.121,.249,LIMESTONE)]:
        soffit_clearance=z0+.60
        front_only=min(z+h,soffit_clearance)
        if z<front_only:
            f.prism(box(x0,z,x1,front_only),-.166,d,mat,name+' street return')
        if z+h>soffit_clearance:
            f.prism(box(x0,max(z,soffit_clearance),x1,z+h),-depth,d,mat,name)
    for j,(lo,hi) in enumerate([(x0+.9,x0+3.35),(x1-3.23,x1-.77)],1):
        f.prism(box(lo,z0+.64,hi,z0+.93),.102,.119,LIMESTONE,'frieze rectangular panel '+str(j))
    # Low horizontal balustrade shows short pierced slots between square stones.
    z=z0+1.326
    f.prism(box(x0,z,x1,z+.115),-depth,.18,GRANITE,'parapet bottom course')
    f.prism(box(x0,z+.49,x1,z+.595),-.27,.177,LIMESTONE,'parapet top rail')
    for i,x in enumerate(np.linspace(x0+.23,x1-.23,13)):
        f.prism(box(x-.13,z+.105,x+.13,z+.497),-.24,.14,LIMESTONE,'parapet block '+str(i+1))

def eastern_side_door(builder):
    y=-4.65
    f=Facade(builder,(-1,y),(1,y),'East wing')
    hole=observe([(21,917),(43,915),(43,991),(21,992)],y,'wide')
    a,b,c,d=hole.bounds
    hole=box(a,.045,c,d)
    body=box(-14.124,0.,-5.37,8.04).difference(hole)
    f.prism(body,-.38,0,MATERIAL,'street wing with east door')
    sash(f,hole,'east entry',[.52],[.22,.79],.135,True)
    for z in np.arange(.62,8.,.62):
        f.prism(body.intersection(box(-14.124,z,-5.37,z+.011)),-.001,.004,COURSE,'east lower bed joints')
    for x in np.arange(-13.63,-5.37,1.11):
        f.prism(body.intersection(box(x,0,x+.009,8.04)),-.001,.003,COURSE,'east lower block joints')
    belt(f,a-.33,c+.33,d+.26,[(0,.14,.13,LIMESTONE),(.14,.21,.20,MATERIAL),(.35,.10,.26,LIMESTONE),(.45,.065,.32,LIMESTONE)],'east door hood')
    for x in [a-.12,c+.12]:
        f.prism(box(x-.085,d-.13,x+.085,d+.33),-.005,.12,LIMESTONE,'east door hood brackets')
    builder.box((-5.46,-2.43,3.99),(.18,4.44,7.98),MATERIAL,label='East wing inner return')
    return hole
