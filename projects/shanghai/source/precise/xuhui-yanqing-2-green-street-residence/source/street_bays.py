"""The measured steel windows, folded bays, pale apron panels and flat hoods of No. 2 Yanqing Road."""
from functools import lru_cache
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union

sys.path.append(str(Path(__file__).resolve().parents[1]/'measurements'))
from register_front import Camera
from stair_surface import at_surface
from photo_architecture import Facade

WALL = 'Yanqing 2 | pale celadon mineral render'
SOCK = 'Yanqing 2 | charcoal plinth'
CREAM = 'Yanqing 2 | ivory stone bay bands'
FRAME = 'Yanqing 2 | dark steel bay frames'
GLASS = 'Yanqing 2 | recessed blue grey glass'
REAR = 'Yanqing 2 | deep casement reveal'


def finish(rgb,roughness,metal=0):
    def linear(v):
        v=v/255.
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return {'color':[linear(v) for v in rgb],'roughness':roughness,'metallic':metal}


PALETTE = {WALL:finish((151,167,153),.95), SOCK:finish((68,65,67),.93),
           CREAM:finish((199,194,171),.88), FRAME:finish((38,42,41),.61,.21),
           GLASS:finish((53,60,58),.33,.12), REAR:finish((24,26,26),.93)}
# Each point is the measured source-image X near the middle of the ground
# storey paired with the provisional Y coordinate. All other dimensions are
# ray intersections with these vertical facets, not screen-space extrusions.
SURVEY_Y=1000
PROFILES={
    'west':[(138,2.24),(270,2.00),(348,2.00),(473,2.28)],
    'three-window bay':[(635,1.65),(753,1.31),(873,.71),(994,1.59)],
    'east shoulder':[(1579,1.39),(1613,1.27),(1715,2.49),(1734,2.40)],
    'below balcony':[(1386,1.51),(1579,1.39)],
    'stair west of balcony':[(1276,0.),(1363,0.)],
}
# native left/right pixel centres of the jambs at mid-height, top and bottom
# centre pixels, numbers of panes across, apron underneath, upper transom
ROWS={
 'west':[
   (0,'lower west',182,258,958,1100,4,True,True),(2,'lower east',358,430,957,1102,4,True,True),
   (0,'middle west',190,263,702,840,4,True,True),
   (2,'middle balcony door',364,433,703,882,3,False,True),
   (0,'upper west',211,271,455,574,4,False,True),(2,'upper balcony door',395,454,472,600,3,False,True)],
 'three-window bay':[
   (0,'lower west',698,742,956,1105,3,True,True),(1,'lower centre',773,850,952,1108,4,True,True),
   (2,'lower east',888,949,955,1109,4,True,True),(0,'middle west',703,750,687,818,3,True,True),
   (1,'middle centre',781,851,687,810,4,True,True),(2,'middle east',886,947,683,811,4,True,True),
   (0,'upper west',708,751,436,567,3,False,True),(1,'upper centre',780,850,434,566,4,False,True),
   (2,'upper east',892,950,435,568,4,False,True)],
 'east shoulder':[
   (1,'lower angled sash',1641,1680,978,1115,3,False,True),
   (1,'middle angled sash',1629,1677,702,843,3,True,True),
   (1,'upper angled sash',1616,1669,453,605,3,True,True)],
 'below balcony':[(0,'lower broad sash',1454,1545,965,1112,4,False,True)],
 'stair west of balcony':[(0,'stair ground sash',1284,1353,995,1098,2,False,False)],
}
LEVELS={'west':(0.,10.20),'three-window bay':(0.,9.94),'east shoulder':(0.,10.00),
        'below balcony':(.76,3.78),'stair west of balcony':None}


@lru_cache(maxsize=1)
def camera():
    return Camera()


def facet_edges(name,paths=None):
    if paths and name in paths:
        return np.array(paths[name],float)
    if name=='stair west of balcony':
        return np.array([at_surface((x,SURVEY_Y))[:2] for x,_ in PROFILES[name]])
    return np.array([camera().wall((x,SURVEY_Y),y)[:2] for x,y in PROFILES[name]])


def local_point(f,pixel):
    cam=camera()
    ray=cam.ray(pixel)
    distance=np.dot(f.center-cam.c,f.n)/np.dot(ray,f.n)
    point=cam.c+distance*ray-f.center
    return np.dot(point,f.t),point[2]


def measured(f,row):
    _,label,left,right,top,bottom,cols,apron,transom=row
    midx=(left+right)*.5
    midy=(top+bottom)*.5
    return (local_point(f,(left,midy))[0],local_point(f,(midx,bottom))[1],
            local_point(f,(right,midy))[0],local_point(f,(midx,top))[1])


def trim_and_sash(f,row,opening,lod):
    _,name,_,_,_,_,columns,apron,transom=row
    x0,z0,x1,z1=opening
    width,height=x1-x0,z1-z0
    x=(x0+x1)/2
    shape=box(x0,z0,x1,z1)
    glass=shape.buffer(-.032,join_style=2)
    strips=[shape.difference(glass)]
    low=z0+height*.665
    if transom:
        strips.append(box(x0,low-.025,x1,low+.025))
    for i in range(1,columns):
        u=x0+width*i/columns
        weight=.011 if columns%2 or i!=columns//2 else .018
        strips.append(box(u-weight,z0,u+weight,z1))
    # The larger lower casement and smaller upper ventilator have their own
    # pane spacing. The narrow stair sash has a single, continuous 2-by-3 grid.
    levels=([z0+(low-z0)*i/4 for i in (1,2,3)]+[(low+z1)*.5]
            if transom else [z0+height*i/3 for i in (1,2)])
    for z in levels:
        strips.append(box(x0,z-.009,x1,z+.009))
    frame=unary_union(strips)
    if 'balcony door' in name:
        # The 2015 and 2020 street views show a real narrow balcony above
        # the two-window ground bay. Its side rails turn back to the wall.
        half=width*.70
        depth=.40
        f.box(x,z0-.075,2*half,.14,depth+.036,depth/2-.03,CREAM,name+' / projecting balcony slab')
        front=depth-.045
        for track in (z0+.09,z0+.46,z0+.59):
            f.box(x,track,2*half,.022,.025,front,FRAME,name+' / front rail')
            for sign in (-1,1):
                f.box(x+sign*half,track,.025,.022,front,front*.5,FRAME,name+' / short return rail')
        for d in (front,front*.54):
            for sign in (-1,1):
                f.box(x+sign*half,z0+.292,.025,.586,.025,d,FRAME,name+' / side baluster')
        for u in np.linspace(-half,half,9)[1:-1]:
            f.box(x+u,z0+.292,.015,.586,.019,front,FRAME,name+' / vertical baluster')
    f.prism(shape,-.185,-.166,REAR,name+' / dark window back')
    f.prism(glass,-.147,-.136,GLASS,name+' / recessed glazing')
    f.prism(frame,-.135,-.101,FRAME,name+' / joined steel grille')
    if not lod and columns>=3:
        f.box(x,low-.009,.042,.068,.021,-.092,FRAME,name+' / central sash catch')
    f.box(x,z0-.048,width+.13,.096,.177,.010,CREAM,name+' / projecting sill')
    f.box(x,z1+.041,width+.12,.082,.143,.006,CREAM,name+' / shallow flat hood')
    if apron:
        drop=.51 if name.startswith('lower') else .39
        outside=box(x0+.009,z0-.091-drop,x1-.009,z0-.091)
        inset=box(x0+.105,z0-.091-drop+.083,x1-.105,z0-.191)
        f.prism(outside.difference(inset),-.004,.02,CREAM,name+' / ivory apron around rendered field')


def project_plan(builder,polygon,z0,z1,material,label):
    from shapely.geometry import Polygon
    shape=Polygon(polygon)
    if shape.area>1e-6:
        builder.prism(shape,z0,z1,lambda x,y,z:(x,y,z),material,label)


def bay_layout(paths=None):
    result={}
    for group,rows in ROWS.items():
        points=facet_edges(group,paths)
        faces=[Facade(None,a,b,group) for a,b in zip(points,points[1:])]
        boxes=[]
        for row in rows:
            f=faces[row[0]]
            x0,z0,x1,z1=measured(f,row)
            boxes.append({'name':row[1],'bounds':[float(f.point(x0,z0)[0]),z0,float(f.point(x1,z1)[0]),z1]})
        result[group]={'plan':points.tolist(),'z_limits':LEVELS[group],'openings':boxes}
    return result


def bay_wall_cutouts(paths=None):
    holes=[]
    for name,group in bay_layout(paths).items():
        if group['z_limits'] is None:
            for item in group['openings']:
                x0,z0,x1,z1=item['bounds']
                holes.append(box(x0-.028,z0-.012,x1+.028,z1+.012))
        else:
            pts=group['plan']
            low,high=group['z_limits']
            holes.append(box(pts[0][0],low,pts[-1][0],high))
    return holes


def add_bays(builder,lod=False,paths=None):
    for group,rows in ROWS.items():
        pts=facet_edges(group,paths)
        levels=LEVELS[group]
        footing=.82 if group=='west' else .80
        if levels and group in ('west','three-window bay'):
            # The projecting feet and flat heads continue over the corner joints.
            back=max(pts[:,1])+.16
            polygon=[*pts.tolist(),(pts[-1][0],back),(pts[0][0],back)]
            project_plan(builder,polygon,0,footing-.07,SOCK,group+' | continuous charcoal plinth')
            project_plan(builder,polygon,footing-.07,footing,CREAM,group+' | continuous pale footing course')
            project_plan(builder,polygon,levels[1]-.075,levels[1],CREAM,group+' | flat terminal course')
        for i,(a,b) in enumerate(zip(pts,pts[1:])):
            f=Facade(builder,a,b,group+' | facet '+str(i+1))
            windows=[(r,measured(f,r)) for r in rows if r[0]==i]
            if levels:
                bottom=(footing if group in ('west','three-window bay') else levels[0])
                holes=[box(*opening) for _,opening in windows]
                f.wall(bottom,levels[1],holes,.145,material=WALL)
                if group in ('west','three-window bay','east shoulder'):
                    f.box(0,3.74 if group=='west' else 3.75,f.length,.09,.081,.018,CREAM,'interstorey flat eave')
            for row,opening in windows:
                trim_and_sash(f,row,opening,lod)
