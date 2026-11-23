"""The two marked posts and photographed rear frontage of lane 310 in April 2015."""
from pathlib import Path
from math import cos, sin, pi
import json
import numpy as np
from shapely.geometry import LineString, Polygon, Point, box
import street314

HERE = Path(__file__).resolve().parent
RED, BRICK, GREY, DARK = street314.GABLE, street314.RED, street314.BASE, street314.CAP
SAND = '310 | pale dressed stone'
OXIDE = '310 | red mineral finish'
CAST = '310 | dark stone moulding'
DOOR = '310 | dark blue timber'
TIMBER = '310 | red window frames'
GLASS = '310 | weathered glass'
GREEN = '310 | enamel number plate'
WHITE = '310 | cream numerals'
TILE = '310 | brown clay roof tile'
EAVE = '310 | aged green gutter'
PALETTE = {**street314.PALETTE, **{m: street314.colour(c) for m,c in {
    SAND:(153,146,136), OXIDE:(141,61,46), CAST:(83,72,62), DOOR:(42,47,53),
    TIMBER:(104,50,40), GLASS:(113,131,134), GREEN:(36,108,66),
    WHITE:(229,228,205), TILE:(108,77,55), EAVE:(63,80,65)
}.items()}}
cal = json.loads((HERE.parent/'measurements/310-gate-and-gables-camera.json').read_bytes())
M = np.linalg.inv(np.array(cal['display_camera_P_reference'])[:,:3])
EYE = np.asarray(cal['display_camera_origin_m'])
REAR = cal['display_rear_y_m']

def cut(u,v,depth):
    ray=M@np.array([u,v,1.])
    return EYE + ray*((depth-EYE[1])/ray[1])

def dims(uv,y):
    return Polygon([(p[0],p[2]) for p in [cut(u,v,y) for u,v in uv]])

def quad(a,b,c,d):
    return [(a,b),(c,b),(c,d),(a,d)]

class Front:
    def __init__(self,b,lod):
        self.b=b
        self.lod=lod
    def panel(self,shape,y,thickness,mat,name):
        self.b.prism(shape,-y-thickness,-y,lambda x,z,d:(x,-d,z),mat,'310 '+name)
    def face(self,uv,y,thickness,mat,name):
        self.panel(dims(uv,y),y,thickness,mat,name)
    def rect(self,a,b,c,d,y,t,mat,name):
        self.face(quad(a,b,c,d),y,t,mat,name)
    def rim(self,curve,y,width,mat,name):
        line=LineString([(p[0],p[2]) for p in [cut(u,v,y) for u,v in curve]])
        self.panel(line.buffer(width/2,cap_style=2,join_style=2),y,.026,mat,name)
    def xzring(self,x,z,rx,rz,y,mat,name):
        n=20 if self.lod else 40
        shell=Polygon([(x+rx*cos(2*pi*i/n),z+rz*sin(2*pi*i/n)) for i in range(n)])
        self.panel(shell,y,.031,mat,name)

def crown(w,mid,label):
    # The changing square outline follows the curved, four-sided red cap.
    courses=[(235,34,-.13),(231,35,-.15),(226,37,-.16),(222,37,-.16),(219,31,-.11),
             (215,30,-.10),(211,27,-.09),(205,20,-.07),(199,14,-.04),
             (192,10,-.02),(187,9,-.01),(185,10,-.02),(182,10,-.02),(179,8,0.)]
    if label=='left':
        courses=[(235+(v-235)*.86,h*.91,y)for v,h,y in courses]
    def ring(v,half,y):
        a=cut(mid-half,v,y);c=cut(mid+half,v,y)
        front=(a[2]+c[2])/2
        depth=max(.075,c[0]-a[0])
        return [[a[0],y,front],[c[0],y,front],[c[0],y+depth,front],[a[0],y+depth,front]]
    for k,((v,h,y),(v2,h2,y2)) in enumerate(zip(courses,courses[1:])):
        pts=ring(v,h,y)+ring(v2,h2,y2)
        faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7)]
        for i in range(4):
            j=(i+1)%4
            faces.extend([(i,j,j+4),(i,j+4,i+4)])
        w.b.add(pts,faces,CAST if k<4 else OXIDE,label='310 '+label+' square cap course '+str(k+1))

def pier(w,mid,ss,label):
    stem=quad(mid-24*ss,290,mid+24*ss,562)
    w.face(stem,0,.48*ss,SAND,label+' pier shaft')
    w.rect(mid-27*ss,518,mid+27*ss,568,0.002,.55*ss,SAND,label+' square foot')
    w.rect(mid-13.7*ss,300,mid+13.7*ss,516,-.016,.030,OXIDE,label+' long red panel')
    w.rect(mid-15*ss,516,mid+15*ss,520,-.025,.037,CAST,label+' panel foot')
    for v,c,h,m in [(289,26,5,CAST),(285,27,4,OXIDE),(245,25,41,SAND),(241,27.5,5,CAST),
                    (238,29,3,SAND),(234,31,4,CAST)]:
        w.rect(mid-c*ss,v,mid+c*ss,v+h,-.045,.54*ss,m,label+' capital '+str(v))
    a=cut(mid-16*ss,266,-.086);b=cut(mid+16*ss,266,-.086);o=cut(mid,266,-.086)
    rx=(b[0]-a[0])/2
    w.xzring(o[0],o[2],rx,rx,-.086,OXIDE,label+' round red medallion')
    crown(w,mid,label)

def number_plate(w):
    # Hand-drawn digits follow the visible 310; the tiny lower inscription is omitted.
    w.rect(265,322,290,341,-.034,.018,GREEN,'green enamel number sign')
    digit_paths=[
        [(270,326),(272,325),(274,326),(273.7,328),(271.7,329),(274,330),(274,332),(272.5,333),(270.5,332.5)],
        [(277,326),(278.5,325),(278.5,333)],[(276.8,333),(280,333)],
        [(284,325),(285.7,326),(286.2,330.5),(285.2,332.8),(283.5,333),(282.5,331.6),(282.3,327),(284,325)]]
    for i,path in enumerate(digit_paths):
        w.rim(path,-.046,.012,WHITE,'enamel number stroke '+str(i))

def window(w,area,y,name,cols=2,rows=3):
    a,b,c,d=area
    w.rect(a,b,c,d,y+.1,.038,GLASS,name+' glass')
    sw=.055
    grid=[]
    for i in range(cols+1):
        x=a+(c-a)*i/cols
        grid.append([(x,b),(x,d)])
    for j in range(rows+1):
        v=b+(d-b)*j/rows
        grid.append([(a,v),(c,v)])
    for n,line in enumerate(grid):
        w.rim(line,y+.042,sw,TIMBER,name+' window frame '+str(n+1))

def gables(w):
    # The silhouette of the far left crown is hidden by a utility pole.
    # The exposed slopes and left brick border establish its estimated central length.
    for tag,ridge,wall,inner,outline,win in [
        ('west',259,(143,377),[(163,151),(163,105),(236,65),(236,49),(276,49),(276,65),(338,106),(338,153)],
         [(143,99),(152,97),(223,58),(226,32),(281,32),(284,61),(368,95),(377,96)],None),
        ('east',618,(500,727),[(543,151),(543,105),(601,71),(601,53),(637,53),(637,72),(704,108),(704,153)],
         [(500,96),(514,94),(584,52),(582,31),(654,31),(652,53),(719,87),(732,89)],(586,128,661,234))]:
        a,b=wall
        envelope=outline+[(b,240),(a,240)]
        shell=dims(envelope,REAR)
        if win: shell=shell.difference(dims(quad(*win),REAR))
        w.panel(shell,REAR,.38,RED,tag+' red gable')
        pale=dims(outline+[(b,164),(a,164)],REAR-.021).difference(dims(inner,REAR-.021))
        if win:pale=pale.difference(dims(quad(*win),REAR-.021))
        w.panel(pale,REAR-.021,.045,SAND,tag+' pale gable border')
        w.rim(outline,REAR-.093,.120,CAST,tag+' gable coping')
        w.rim([(a,163),(b,163)],REAR-.034,.15,SAND,tag+' belt')
        if win:
            window(w,win,REAR,tag+' upper sash',2,3)
            w.rect(582,124,663,128,REAR-.11,.14,CAST,tag+' upper window head')
        w.rect(ridge-12,83,ridge+13,88,REAR-.08,.10,CAST,tag+' gable tablet')

def rear_entrance(w):
    y=REAR
    opening=quad(400,345,479,477)
    # The central gate wall is behind the gable piers. Its red face must not coincide
    # with the bottom corners of either larger gable.
    centre_face=y+.055
    w.panel(dims(quad(355,215,529,478),centre_face).difference(dims(opening,centre_face)),
            centre_face,.43,BRICK,'inner brick gate wall')
    for i,(left,right) in enumerate([(400,439.5),(440.5,479)]):
        w.rect(left,345,right,477,y+.18,.045,DOOR,'dark rear door '+str(i+1))
        if not w.lod:
            for j in range(1,5):
                u=left+(right-left)*j/5
                w.rim([(u,347),(u,476)],y+.169,.012,DOOR,'rear door board seam')
    w.rect(398,331,481,344,y-.12,.16,SAND,'inner doorway lintel')
    w.rect(398,327,480,332,y-.147,.18,CAST,'inner doorway shadow line')
    curve=[(376+126*i/44,264-26*sin(pi*i/44))for i in range(45)]
    w.face(curve+[(502,271),(376,271)],y-.067,.125,SAND,'segmental pediment')
    w.rim(curve,y-.15,.13,CAST,'pediment arch moulding')
    w.rect(381,266,499,272,y-.136,.18,CAST,'inner pediment cornice')
    w.rect(406,273,486,318,y-.085,.14,SAND,'rear gateway tablet surround')
    w.rect(411,281,479,314,y-.11,.14,GREY,'inset tablet field')
    cheek=[(483,275),(486,274),(490,273),(493,276),(493,280),(496,284),
           (505,287),(510,289),(513,294),(513,300),(509,305),(483,311)]
    w.face(cheek,y-.106,.14,SAND,'east tablet scrolled cheek')
    for i,(x,v,sz) in enumerate([(489.6,276.4,3.7),(502.8,294.2,7.7)]):
        spiral=[(x+(sz*(1.-.72*j/40))*cos(.65*pi+1.8*pi*j/40),v+(sz*(1.-.72*j/40))*sin(.65*pi+1.8*pi*j/40))for j in range(41)]
        w.rim(spiral,y-.15,.034,CAST,'east tablet scroll '+str(i+1))
    for i in range(4):
        window(w,(378+i*31.7,196,408+i*31.7,212),y,'clerestory '+str(i+1),1,2)
    w.rect(374,211,508,216,y-.094,.136,CAST,'clerestory sill')

def roof_corners():
    return [cut(378,179,REAR),cut(497,179,REAR),cut(506,143,REAR+2.60),cut(374,143,REAR+2.60)]

def roof(w):
    pts=np.array(roof_corners())
    pts[0,2]=pts[1,2]=(pts[0,2]+pts[1,2])/2
    pts[2,2]=pts[3,2]=(pts[2,2]+pts[3,2])/2
    vertices=np.vstack((pts-[0,0,.095],pts))
    faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7)]
    for i in range(4):
        j=(i+1)%4;faces.extend([(i,j,j+4),(i,j+4,i+4)])
    w.b.add(vertices.tolist(),faces,TILE,'310 short roof over central windows')
    intervals=20 if w.lod else 34
    for i in range(intervals+1):
        f=i/intervals
        a=pts[0]*(1-f)+pts[1]*f;c=pts[3]*(1-f)+pts[2]*f
        w.b.tube([a.tolist(),c.tolist()],.025 if w.lod else .030,TILE,5 if w.lod else 8,'310 pantile rolls')
    for j in range(1,9):
        f=j/9;a=pts[0]*(1-f)+pts[3]*f;c=pts[1]*(1-f)+pts[2]*f
        w.b.tube([a.tolist(),c.tolist()],.022,TILE,5,'310 tile nose courses')
    w.b.tube([pts[0].tolist(),pts[1].tolist()],.064,EAVE,8,'310 green eave edge')

def street_walls(w):
    for tag,a,r,top in [('west',34,251,342),('east',581,842,284)]:
        w.rect(a,top,r,548,.09,.29,GREY,tag+' front wall')
        w.rect(a,514,r,550,.067,.32,OXIDE,tag+' wall plinth')
        w.rect(a,top-14,r,top,.050,.37,SAND,tag+' wall neck')
        w.rect(a,top-23,r,top-12,.025,.42,CAST,tag+' wall coping')
    # Three recessed panels below the dated public noticeboard are visible at image right.
    for i,(a,r) in enumerate([(623,668),(680,730),(752,809)]):
        for n,line in enumerate([[(a,367),(a,322),(r,322),(r,367)]]):
            w.rim(line,.040,.032,CAST,'right wall recessed panel '+str(i+1))

def add_lane310(b,lod=False,layout=None):
    w=Front(b,lod)
    pier(w,279,.94,'left')
    pier(w,556,1.,'right')
    number_plate(w)
    street_walls(w)
    rear_entrance(w)
    gables(w)
    roof(w)
