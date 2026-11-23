"""The curved parapets over the corner and lane windows, the recessed stair bay and the numbered gate."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union

DATA=json.loads((Path(__file__).parent/'lane-and-crown-readings.json').read_bytes())

def add(house,m,lod):
    def front(u,z,d):return (u,-.11-d,z)
    def lane(u,z,d):return (-1.32-d,-u,z)
    def readings(points,axis,val):
        qs=[m.on_plane(p,axis,val) for p in points]
        return [(q[0] if axis==1 else -q[1],q[2])for q in qs]
    def wall(mapper,outline,openings,label):
        def face(shape,back,out,mat,name):
            house.prism(shape,back,out,mapper,mat,label+'/'+name)
        field=outline.difference(unary_union(list(openings.values())))
        face(field,-.35,0,m.WALL,'perforated lime wall')
        face(field.intersection(box(-60,0,60,4.25)),0,.044,m.BELT,'grey base')
        for key,op in openings.items():
            m.joinery(face,op,key,lod)
        for i,(z,height,depth) in enumerate([(3.56,.048,.092),(3.90,.06,.096),(4.16,.096,.14)]):
            face(field.intersection(box(-60,z,60,z+height)),.034,depth,m.BELT,f'horizontal plinth band {i+1}')
        return face
    def capped_curve(face,line,thick):
        for j,(thickness,offset,depth,material) in enumerate([(thick,0,.16,m.LINTEL),(.061,-.093,.12,m.BELT),(.077,.064,.204,m.LINTEL)]):
            edge=LineString([(x,z+offset)for x,z in line])
            face(edge.buffer(thickness/2,cap_style='flat',join_style='round',quad_segs=2),-.22,depth,material,f'curved parapet course {j+1}')
    def straight(face,lo,hi,z):
        if hi<=lo:return
        for k,(a,b,d) in enumerate([(-.30,-.18,.090),(-.18,-.11,.158),(-.11,.020,.226),(.020,.075,.272)]):
            face(box(lo,z+a,hi,z+b),-.25,d,m.LINTEL if k!=1 else m.BELT,f'straight eave {lo:.2f}/{k+1}')

    curve=readings(DATA['lane_curve'],0,-1.32)
    passage={key:Polygon(readings(p,0,-1.32))for key,p in DATA['lane_openings'].items()}
    street_end=-.56; far_end=-13.67
    outer=Polygon([(far_end,0),(street_end,0),(street_end,11.16),(curve[-1][0],curve[-1][1]),*reversed(curve[:-1]),(far_end,10.88)])
    face=wall(lane,outer,passage,'lane elevation')
    capped_curve(face,curve,.158)
    straight(face,far_end,curve[0][0],curve[0][1])
    straight(face,curve[-1][0],-3.33,curve[-1][1])
    straight(face,-2.32,street_end,11.16)
    def raised_lintel(mapper,op,label):
        x0,z0,x1,z1=op.bounds
        for j,(xa,xb,low,high) in enumerate([(x0-.10,x1+.10,z1+.012,z1+.158),
                (x0+(x1-x0)*.34,x0+(x1-x0)*.66,z1+.145,z1+.27)]):
            outline=Polygon([(xa,low),(xb,low),(xb+.04,high),(xa-.04,high)])
            house.prism(outline,-.03,.077,mapper,m.LINTEL,label+f'/header {j+1}')
    for key in ('far-upper-landing','outer-upper','arc-upper','near-upper','near-middle'):
        raised_lintel(lane,passage[key],'lane elevation/'+key)
    drain=readings(DATA['lane_rain_pipe_rectified_2011'],0,-1.32)
    house.tube([lane(u,z,.13) for u,z in drain],.057,m.LIGHT,8 if lod else 14,'lane elevation/downpipe at curved bay')
    # The district photograph contains the complete cap missing from the top of the 2011 frame.
    corr=DATA['district_2011_window_correspondence']
    H=m.homography(corr['district'],readings(corr['2011'],1,-.11))
    raw=[]
    for p in DATA['corner_upper_cornice_district']:
        v=H@[*p,1.];raw.append(v[:2]/v[2])
    xmin,xmax=-.13,3.29
    curve=[]
    for x,z in raw:
        t=(x-raw[0][0])/(raw[-1][0]-raw[0][0])
        # The two ends spring from the same horizontal cornice. Detrend the four-window-corner planar fit.
        curve.append((xmin+t*(xmax-xmin),11.24+z-(raw[0][1]*(1-t)+raw[-1][1]*t)))
    outline=Polygon([(xmin,0),(xmax,0),*reversed(curve)])
    corner={k:Polygon(readings(DATA[k],1,-.11))for k in ('corner_upper_window','corner_mid_window')}
    face=wall(front,outline,corner,'front corner with segmental parapet')
    capped_curve(face,curve,.151)
    raised_lintel(front,corner['corner_upper_window'],'front corner/upper opening')
    # The blue cloth awning is visible in both archive and street photos. Its framing stays separate.
    op=corner['corner_mid_window'];left,low,right,top=op.bounds
    end=Polygon([(-.04,top+.018),(.068,top+.32),(.58,top+.30),(.66,top+.12),(.64,top-.075),(.55,top-.04),(.53,top+.095),(.07,top+.13)])
    house.prism(end,-right-.17,-left+.17,lambda d,z,u:(-u,-.11-d,z),'indigo awning cloth','front corner/hood above 4-number gate')
    for x in (left+.08,right-.08):
        house.tube([front(x,top-.18,.012),front(x,top+.15,.54)],.023,m.DARK,8,'front corner/awning diagonal support')
    # Two short steps in plan link the lane wall to the front parapet.
    wall(lambda u,z,d:(u,.57-d,z),box(-1.32,0,-.13,11.15),{},'short plaster return')
    wall(lambda u,z,d:(-.13-d,-u,z),box(-.57,0,.11,11.16),{},'corner wall shoulder')
    pipe=readings(DATA['front_corner_pilaster_drain_2011'],0,-1.32)
    house.tube([lane(u,z,.125)for u,z in pipe],.065,m.LIGHT,8 if lod else 14,'lane elevation/full-height corner rain pipe')
    return house
