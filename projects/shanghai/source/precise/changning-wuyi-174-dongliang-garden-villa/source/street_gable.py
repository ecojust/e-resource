"""North wall, half-timbered gable, casements and the shop awnings observed from Wuyi Road."""
from shapely.geometry import LineString,Polygon,box
from shapely.ops import unary_union
from wuyi_fabric import BRICK,DOOR,DARK,FABRIC,FRAME,IRON,SOFFIT,STONE,TIMBER,WALL,face,glazing,metric,rect

W=(400.-79.5)*2.60/116.
APEX=metric(238.7,155.7)
PLATE=metric(79.5,326.8)[1]  # Continue the visible north rake down to the wall corner.
FRONT_WINDOWS=[('east attic',rect(159.2,256.,203.4,307.),2,3),
               ('west attic',rect(275.,256.,319.5,307.),2,3),
               ('east middle',rect(133.2,378.,179.2,433.2),2,2),
               ('balcony doors',rect(251.2,376.5,343.2,484.),3,4)]

def strip(a,c,thickness):
    return LineString([a,c]).buffer(thickness/2,cap_style='flat',join_style='mitre')


def awning(b,opening,name,lod):
    l,lo,r,hi=opening.bounds;l-=.18;r+=.18;back=.045;tip=-.56
    # The two canvas shades hang from their individual wall plates. The
    # front hem masks the upper glazing in the September 2025 photograph.
    bracket=Polygon([(back,hi+.245),(back,hi+.29),(tip,hi-.54),(tip,hi-.585)])
    for poly in [bracket]:
        b.prism(poly,l,r,lambda y,z,x:(x,y,z),FABRIC,name+' sloped canvas')
    face(b,box(l,hi-.655,r,hi-.549),tip-.012,tip+.012,FABRIC,name+' front hem')
    wordmark(b,(l+r)/2,hi-.612,tip-.013,name)
    for n,x in enumerate((l+.06,r-.06)):
        b.tube([(x,back-.04,hi-.76),(x,tip+.008,hi-.565)],.012,IRON,5 if lod else 8,name+' awning stay '+str(n+1))


def wordmark(b,x,z,y,name):
    # Upright, dark capitals on each separate awning valance in the front view.
    outlines={
        'D':[[(0,0),(0,1),(.52,1),(.83,.77),(.88,.3),(.60,0),(0,0)]],
        'O':[[(.22,0),(0,.22),(0,.78),(.22,1),(.64,1),(.86,.77),(.86,.22),(.64,0),(.22,0)]],
        'N':[[(0,0),(0,1),(.82,0),(.82,1)]],
        'G':[[(.84,.82),(.65,1),(.24,1),(0,.77),(0,.22),(.22,0),(.82,0),(.82,.45),(.49,.45)]],
        'L':[[(0,1),(0,0),(.76,0)]],
        'I':[[(.35,0),(.35,1)]],
        'A':[[(0,0),(.43,1),(.86,0)],[(.18,.40),(.68,.40)]],
    }
    h=.062;advance=.078
    for i,char in enumerate('DONGLIANG'):
        paths=[LineString([(x+(i-4)*advance+(u-.43)*h,z+(v-.5)*h)for u,v in path]) for path in outlines[char]]
        face(b,unary_union(paths).buffer(.0054,join_style='round',cap_style='round',quad_segs=2),y-.006,y,FRAME,name+' DONGLIANG '+str(i+1))


def add_street_gable(b,lod):
    wall_shape=Polygon([(0,0),(W,0),(W,PLATE),(APEX[0],APEX[1]),(0,PLATE)])
    # Behind the projecting entrance and bay are a recessed real threshold
    # and the three lower lights. Keep the back wall clear of these volumes.
    access=unary_union([box(metric(156,616)[0]+.14,-.02,metric(224,616)[0]-.14,1.90),
                        box(metric(229,616)[0],.02,metric(372,616)[0],2.58)])
    face(b,wall_shape.difference(unary_union([access,*(f[1]for f in FRONT_WINDOWS)])),0,.22,WALL,'north roughcast gable with four openings')
    for name,hole,cols,rows in FRONT_WINDOWS:
        glazing(b,hole,(0,0),(1,0),.104,name,cols,rows)
        l,z,r,top=hole.bounds
        face(b,box(l-.07,top+.012,r+.07,top+.076),-.061,.035,STONE,name+' window head')
        if name!='balcony doors':face(b,box(l-.14,z-.095,r+.14,z),-.126,.032,STONE,name+' projecting sill')
        if name in ('east middle','balcony doors'):awning(b,hole,name,lod)
    # Five vertical timbers stand between the heavy triangular border
    # and its lower tie. Their positions are read from Wang's front view.
    a=metric(159.,242.1);c=metric(319.4,242.1);tip=APEX
    outer=Polygon([a,c,tip]);inset=outer.buffer(-.126,join_style='mitre')
    face(b,outer.difference(inset),-.063,.016,TIMBER,'north gable outer triangular timber')
    for i,u in enumerate((196.,218.,239.,261.,283.)):
        x,_=metric(u,240);p=inset.intersection(box(x-.054,0,x+.054,APEX[1]+.1));face(b,p,-.067,.015,TIMBER,'north gable upright '+str(i+1))
    # The east quoin alternates a long stretcher and a short brick end.
    for i in range(round(PLATE/.087)):
        z=.01+.087*i;span=.28 if i%2 else .13
        face(b,box(0,z,span,min(z+.077,PLATE)), -.017,.014,BRICK,'north staggered brick quoin')
