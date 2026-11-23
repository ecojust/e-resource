"""Fixed rain leaders, the red recess joinery and middle-bay wall ironwork."""
import numpy as np
from shapely.geometry import Polygon
from court_masonry import Camera,slab,layer,TRIM,STEEL,PIPE,PIER,HOOD,WALL,BACK,F67,F9,height
from courtyard_wall import COURT
def points(cam,readings):
    return [cam.wall(uv,y).tolist() for uv,y in readings]

def add_details(b,layout,lod):
    # The long No. 9 rainwater leader bends out before the hedge. The two bends,
    # the white soil pipe at No. 7 and its dark brackets recur in the registered photographs.
    for view,data,diameter,label in [
       (18,[((231,58),-.060),((226,64),-.109),((219,181),-.108),((213,194),-.105),((208,343),-.103),((212,367),-.10)],.071,'No 7 | pale rain leader'),
       (17,[((153,163),F67-.028),((149,171),F67-.079),((140,386),F67-.080)],.058,'No 6 | vertical leader by red loggia'),
       (20,[((298,7),F9-.040),((290,126),F9-.053),((287,259),F9-.068),((269,271),F9-.13),((259,273),F9-.19),((250,299),F9-.36)],.071,'No 9 | dogleg at divider'),
       (20,[((163,350),COURT-.13),((163,359),COURT-.17),((213,486),COURT-.25)],.058,'No 9 | lower diagonal drainage pipe')]:
        ps=points(Camera(view),data);b.tube(ps,diameter,PIPE,sides=8 if lod else 12,label=label)
        if not lod:
            for j in range(1,len(ps)-1,2):
                x,y,z=ps[j];slab(b,x-diameter-.01,x+diameter+.01,y-diameter,y+diameter,z-.018,z+.018,PIER,label+' | clamp')
    from no6_loggia import no6_rear_opening
    door=no6_rear_opening(Camera(17),F67,BACK)
    l,z,r,h=door.bounds
    for x in np.linspace(l+.065,r-.065,4):
        slab(b,x-.014,x+.014,BACK+.082,BACK+.11,z,h,STEEL,'No 6 | upper rear door mullion')
    for level in [z+.35*(h-z),z+.79*(h-z)]:
        slab(b,l,r,BACK+.065,BACK+.087,level-.014,level+.014,STEEL,'No 6 | upper rear door rail')
    c=Camera(19)
    # Short metal fence visible above the low wall in frame 19. The top slopes
    # in perspective and continues only between the two observed endpoints.
    a=c.wall((134,399),COURT+.05);e=c.wall((408,380),COURT+.05)
    za=c.wall((135,369),COURT+.05)[2];zb=c.wall((405,351),COURT+.05)[2]
    for i,x in enumerate(np.linspace(a[0],e[0],25 if lod else 33)):
        t=(x-a[0])/(e[0]-a[0]);base=a[2]*(1-t)+e[2]*t;top=za*(1-t)+zb*t
        slab(b,x-.009,x+.009,COURT+.032,COURT+.052,base,top,STEEL,'Middle court | narrow fence upright')
        if not lod:
            b.tube([(x,COURT+.042,top-.014),(x-.020,COURT+.042,top+.035)],.009,STEEL,sides=6,label='Middle court | bent finial')
    lower=[(a[0],COURT+.042,a[2]),(e[0],COURT+.042,e[2])]
    upper=[(a[0],COURT+.042,za-.046),(e[0],COURT+.042,zb-.046)]
    for line in [lower,upper]:b.tube(line,.011,STEEL,sides=6,label='Middle court | connecting fence rail')
