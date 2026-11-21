"""Visible entrance elevation and southern return of 2 Beijing West Road Lane 1220."""
import math
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

# The facade drawing was proportioned in a local elevation frame. Its horizontal
# span is calibrated to the independently identified 12.55 m western source edge.
# Floor heights and the depth of the veranda remain photographic estimates.
DRAW_WIDTH = 20.768
WEST_FRONT_WIDTH = 12.5463
X_SCALE = WEST_FRONT_WIDTH / DRAW_WIDTH
Y_SCALE = .90
Z_SCALE = .89
HALF_WIDTH = DRAW_WIDTH / 2
BACK = 4.62
RETURN = 14.05
PALETTE = {
    'rough ivory render': {'color': [.70,.627,.509], 'roughness': .91},
    'relief mortar': {'color': [.51,.491,.442], 'roughness': .86},
    'pink beige porch stone': {'color': [.54,.436,.359], 'roughness': .78},
    'gray brown plinth': {'color': [.40,.351,.311], 'roughness': .89},
    'green window joinery': {'color': [.121,.171,.147], 'roughness': .64},
    'sage window glass': {'color': [.175,.255,.229], 'roughness': .29, 'metallic': .12},
    'blue fanlight glass': {'color': [.151,.237,.251], 'roughness': .32},
    'dark iron': {'color': [.102,.105,.098], 'roughness': .67, 'metallic': .28},
    'tile edge': {'color': [.435,.241,.165], 'roughness': .88},
    'baked roof tiles': {'color': [.441,.264,.189], 'roughness': .89},
    'neutral section': {'color': [.485,.474,.440], 'roughness': .93},
    'stair terrazzo': {'color': [.53,.499,.453], 'roughness': .84},
    'porch shade': {'color': [.232,.231,.211], 'roughness': .95},
}
WALL = 'rough ivory render'
STONE = 'relief mortar'
IRON = 'dark iron'

def circle(cx,z,r,lod):
    return Point(cx,z).buffer(r,quad_segs=8 if lod else 16)


def ring(face,shape,width,start,end,material,name):
    face.prism(shape.buffer(width,join_style='mitre').difference(shape),start,end,material,name)


def sash(face,shape,columns,rows,name,glass='sage window glass'):
    x0,z0,x1,z1=shape.bounds
    face.prism(shape.buffer(.01,join_style='mitre'),-.25,-.225,glass,name+'/glass')
    clear=shape.buffer(-.068,join_style='mitre')
    bars=[box(x0+(x1-x0)*i/columns-.022,z0,x0+(x1-x0)*i/columns+.022,z1) for i in range(1,columns)]
    bars += [box(x0,z0+(z1-z0)*j/rows-.024,x1,z0+(z1-z0)*j/rows+.024) for j in range(1,rows)]
    face.prism(shape.difference(clear.difference(unary_union(bars))),-.186,-.12,'green window joinery',name+'/frame')
    face.box((x0+x1)/2,z0-.045,x1-x0+.13,.09,.145,.024,STONE,name+'/sill')


def hood(face,x,top,span,lod):
    """Two rising curves and a central scallop above a rectangular opening."""
    hw=span/2+.115
    path=[(-hw,0),(-hw+.09,.12),(-.68*hw,.17),(-.40*hw,.38),(-.22*hw,.49),(0,.58),
          (.22*hw,.49),(.40*hw,.38),(.68*hw,.17),(hw-.09,.12),(hw,0)]
    shape=Polygon([(x-hw,top),(x+hw,top)]+[(x+u,top+.035+v) for u,v in reversed(path)])
    face.prism(shape,-.01,.095,STONE,'window hood/scalloped field')
    line=LineString([(x+u,top+.035+v) for u,v in path]).buffer(.044,cap_style='flat',join_style='round',quad_segs=3)
    face.prism(line,.089,.145,STONE,'window hood/curved drip')
    face.prism(circle(x,top+.36,.075,lod),.098,.141,STONE,'window hood/center boss')


def balustrade(face,x,width,floor,depth,lod):
    slab=face.point(x,floor-.09,depth/2-.015)
    face.builder.box(slab,(width+.12,depth+.14,.18),'stair terrazzo',[face.t,face.n,[0,0,1]],face.label+'/balcony slab')
    z=floor+1.02
    for h in (.1,.57,1.02):
        face.box(x,floor+h,width,.04,.045,depth,IRON,'gallery/horizontal rails')
    sections=max(2,round(width/.49))
    for i in range(sections+1):
        u=x-width/2+width*i/sections
        face.box(u,floor+.55,.042,1.02,.045,depth,IRON,'gallery/uprights')
        if i==sections or lod:continue
        wave=[face.point(u+width/sections*t,floor+.34+.14*math.sin(math.tau*t),depth) for t in (0,.125,.25,.375,.5,.625,.75,.875,1)]
        face.builder.tube(wave,.014,IRON,6,face.label+'/gallery/curved ironwork')
    for u in (x-width/2,x+width/2):
        for h in (.14,1.02):face.line((u,floor+h,.04),(u,floor+h,depth),.025,IRON,8,'gallery/end rails')
    for u in (x-width*.34,x+width*.34):
        face.line((u,floor-.47,.02),(u,floor-.17,depth-.13),.044,IRON,7,'gallery/knee brackets')


def cornice(face,z,width,center=0):
    for dz,h,d in [(0,.09,.095),(.14,.12,.19),(.24,.075,.245)]:
        face.box(center,z+dz,width,h,d+.06,d/2-.016,STONE,'cornice/stepped lip')


def steps_and_portal(face,lod):
    """Semicircular opening with recessed soffit, dressed radial voussoirs and six risers."""
    b=face.builder;rise=1.43*X_SCALE/Z_SCALE
    opening_shape=opening(0,.995,2.86,4.17,rise,20 if lod else 46)
    surrounds=opening_shape.buffer(.31,join_style='mitre').difference(opening_shape)
    face.prism(surrounds,-.045,.153,'pink beige porch stone','central portal/cut surround')
    center_z=.995+4.17-rise
    for i in range(1,13):
        t=i*math.pi/13
        seam=LineString([(1.434*math.cos(t),center_z+1.434*X_SCALE/Z_SCALE*math.sin(t)),(1.747*math.cos(t),center_z+1.747*X_SCALE/Z_SCALE*math.sin(t))]).buffer(.008,cap_style='flat')
        face.prism(seam,.152,.156,'gray brown plinth','central portal/radial joints')
    for side in (-1,1):
        for k in range(1,6):face.box(side*1.589,.995+(center_z-.995)*k/6,.298,.016,.017,.154,'gray brown plinth','central portal/jamb joints')
    face.prism(opening_shape.buffer(.045).difference(opening_shape),-1.52,-.29,'pink beige porch stone','central portal/deep reveal')
    face.prism(opening_shape.buffer(.024),-1.60,-1.57,'porch shade','central portal/recess back')
    face.prism(box(-.78,1.025,.78,3.47),-1.556,-1.53,'green window joinery','central portal/entrance leaf in shadow')
    for j in range(6):
        edge=-1.81+j*.305
        b.box((0,edge+.155,(j+1)*.087),(3.045,.314,(j+1)*.174),'stair terrazzo',label='portal stairs/treads and risers')
    b.box((0,.78,.513),(3.02,1.59,1.026),'stair terrazzo',label='portal stairs/landing')
    for x in (-1.56,1.56):
        b.tube([(x,-1.67,.94),(x,-.02,1.89),(x,.69,1.89)],.036,IRON,8,'portal stairs/rails')
        for y,h in ((-1.47,1.04),(-.19,1.80),(.62,1.89)):b.box((x,y,h-.42),(.045,.045,.84),IRON,label='portal stairs/posts')
    panel=box(-1.63,5.40,1.63,6.33)
    face.prism(panel,-.036,.027,STONE,'central portal/moulded panel')
    ring(face,panel,.07,.025,.103,STONE,'central portal/panel frame')
    for u in (-.72,0,.72):
        face.prism(circle(u,5.86,.17,lod).buffer(.022).difference(circle(u,5.86,.15,lod)),.030,.059,'pink beige porch stone','central portal/panel bosses')
    return opening_shape


def stepped_gable(face,lod,entry):
    w=face.length;z=11.76;cx=0
    profile=[(-.50,0),(-.50,.13),(-.444,.17),(-.423,.33),(-.355,.38),(-.33,.68),
             (-.255,.76),(-.235,1.03),(-.167,1.09),(-.122,1.26),(-.065,1.36),
             (0,1.4),(.065,1.36),(.122,1.26),(.167,1.09),(.235,1.03),(.255,.76),
             (.33,.68),(.355,.38),(.423,.33),(.444,.17),(.50,.13),(.50,0)]
    contour=[(u*w,z+h) for u,h in profile]
    wall=Polygon([(-w/2,8.31),(w/2,8.31)]+list(reversed(contour)))
    from shapely.affinity import scale
    face_scale=X_SCALE if entry else Y_SCALE
    eye=scale(circle(cx,11.91,.38,lod),xfact=Z_SCALE/face_scale,yfact=1,origin=(cx,11.91))
    holes=[eye]
    if entry:holes.append(opening(0,8.64,1.26,2.01,.11,12 if lod else 24))
    else:
        # The 2021 road panoramas show three separate upper arches below the return gable's oculus.
        holes += [opening(0,9.36,.83,1.61,.415*Y_SCALE/Z_SCALE,14 if lod else 28),
                  opening(-1.20,9.38,.49,.79,.245*Y_SCALE/Z_SCALE,10 if lod else 22),
                  opening(1.20,9.38,.49,.79,.245*Y_SCALE/Z_SCALE,10 if lod else 22)]
    face.prism(wall.difference(unary_union(holes)),-.24,0,WALL,'upper gable/visible wall')
    rim=LineString(contour).buffer(.065,join_style='round',cap_style='flat',quad_segs=3 if lod else 6)
    face.prism(rim,-.18,.088,STONE,'upper gable/stepped raking cap')
    ring(face,eye,.105,-.05,.071,STONE,'upper gable/oculus ring')
    ring(face,eye,.041,.07,.107,STONE,'upper gable/outer bead')
    face.prism(eye.buffer(.005),-.25,-.23,'porch shade','upper gable/oculus recess')
    for u in (-.15,0,.15):
        z0,z1=11.91-.30,11.91+.30
        face.box(u,(z0+z1)/2,.019,z1-z0,.032,-.13,IRON,'upper gable/oculus ironwork')
    if entry:
        sash(face,holes[1],2,4,'upper gable/French window')
        balustrade(face,0,2.83,8.64,1.22,lod)
    else:
        for aperture in holes[1:]:
            sash(face,aperture,2,2,'arched upper gable lights')
            ring(face,aperture,.076,-.02,.046,STONE,'arched upper gable window edge')


def draw_elevation(b,lod):
    hw=HALF_WIDTH;front=Facade(b,(-hw,0),(hw,0),'entrance front')
    ground_centers=(-8.05,-4.32,4.32,8.05)
    ground=[opening(x,1.14,1.33,2.66) for x in ground_centers]
    portal=steps_and_portal(front,lod)
    upper_centers=(-8.38,-5.26,-2.20,1.10,3.73)
    upper=[opening(x,6.54,1.25,1.44) if x==1.10 else opening(x,5.39,1.34,2.47) for x in upper_centers]
    ext=box(-hw,0,hw,8.40)
    corner=box(5.08,5.66,hw+.06,8.53)
    front.prism(ext.difference(unary_union([portal,corner,*ground,*upper])),-.295,0,WALL,'street wall/continuous exterior')
    plinth=box(-hw,.035,hw,.73).difference(box(-1.84,0,1.84,1.1))
    front.prism(plinth,-.006,.042,'gray brown plinth','street wall/plinth')
    for x,shape in zip(ground_centers,ground):
        sash(front,shape,2,4,'lower casements');hood(front,x,3.8,1.33,lod)
    for x,shape in zip(upper_centers,upper):
        sash(front,shape,2,4,'upper casements')
        for sign in (-1,1):front.box(x+sign*.77,7.26,.10,1.66,.15,.055,STONE,'upper casements/stone jambs')
    cornice(front,8.39,15.44,-2.65)
    # The plaque sill rests above the dressed arch and leaves the semicircular opening clear.
    cornice(front,5.48,3.42,0)
    for x in [i*.54-10.21 for i in range(29)]:
        front.box(x,8.26,.135,.255,.25,.075,STONE,'upper eaves/modillions')
    balustrade(front,-8.15,4.15,5.34,1.02,lod)
    for x in (5.15,hw-.10):
        front.box(x,6.90,.11,2.54,.12,-.14,'green window joinery','southwest loggia/slender uprights')
    south_wall=Facade(b,(hw,.17),(hw,RETURN),'south return')
    side_u=lambda y:y-(.17+RETURN)/2
    fan_u=side_u(1.805)
    big=opening(fan_u,.45,2.27,4.42,1.135,22 if lod else 45)
    arched=[opening(x,5.45,1.07,2.40,.535,13 if lod else 26) for x in (side_u(4.695),side_u(6.105))]
    south_windows=[opening(side_u(y),5.34,1.24,2.46) for y in (8.49,10.82,13.06)]
    end_house=box(-south_wall.length/2,0,south_wall.length/2,8.43)
    south_wall.prism(end_house.difference(unary_union([big,*arched,*south_windows])),-.275,-.008,WALL,'wall/fanlight and double arch')
    sash(south_wall,big,2,3,'south return lower/fanlight','blue fanlight glass')
    spring=.45+4.42-1.135
    for t in (math.pi/4,math.pi/2,3*math.pi/4):
        south_wall.line((fan_u,spring,-.113),(fan_u+.99*math.cos(t),spring+.99*math.sin(t),-.113),.024,'green window joinery',8,'south return lower/fanlight rays')
    for shape in arched:
        sash(south_wall,shape,2,3,'south return upper/arched casement')
        ring(south_wall,shape,.12,-.045,.08,STONE,'south return upper/arch border')
    for hole in south_windows:
        sash(south_wall,hole,2,3,'road-facing regular upper casements')
    balustrade(south_wall,side_u(5.385),3.41,5.43,.77,lod)
    clerestory=Facade(b,(hw-.68,7.15),(hw-.68,13.87),'southern roof/wall below tiled eaves')
    high_windows=[opening(x,8.72,.89,1.15) for x in (-2.17,0,2.17)]
    clerestory.wall(8.42,10.15,high_windows,thickness=.19,material=WALL)
    for hole in high_windows:sash(clerestory,hole,2,2,'attic casements')
    cornice(clerestory,10.12,clerestory.length+.16)
    x0,x1=hw-2.22,hw-.49
    v=[(x0,7.03,10.77),(x1,7.03,10.41),(x1,14.00,10.41),(x0,14.00,10.77)]
    b.add(v+[tuple((x,y,z-.10)) for x,y,z in v],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'baked roof tiles','south roof/roadside eave strip')
    cornice(south_wall,8.43,south_wall.length-.06)
    inner=Facade(b,(5.08,1.45),(hw-.21,1.45),'upper loggia')
    glazed=opening(0,5.65,2.86,2.17)
    inner.wall(5.33,8.38,[glazed],thickness=.18,material=WALL);sash(inner,glazed,3,2,'recessed loggia glazing')
    front.box(7.68,5.36,5.23,.18,1.43,-.71,'stair terrazzo','southwest loggia/floor')
    front.box(7.68,5.61,5.23,.46,.16,-.025,WALL,'southwest loggia/solid parapet')
    cornice(front,5.83,5.35,7.68)
    for x in (5.32,7.62,10.12):front.box(x,7.16,.045,2.23,.045,-.18,IRON,'southwest loggia/canopy supports')
    front.box(7.68,8.27,5.48,.078,1.72,-.69,'tile edge','southwest loggia/shallow cover')
    # The visible upper walls turn around the two curved gables above the entrance and terrace.
    raised=Facade(b,(-2.98,.75),(2.98,.75),'upper/west gable')
    stepped_gable(raised,lod,True)
    side=Facade(b,(5.62,.93),(5.62,5.72),'upper/south gable')
    stepped_gable(side,lod,False)
    link=Facade(b,(3.00,.90),(5.55,.90),'upper link')
    northlight=opening(0,9.21,1.05,1.66)
    link.wall(8.37,11.78,[northlight],thickness=.20,material=WALL)
    sash(link,northlight,2,3,'upper linking casement')
    # Inclined roof strips close the measured near portion. The rear is a plain model section.
    for xa,xb in ((-hw,-2.98),(5.78,hw-.18)):
        v=[(xa,.04,8.64),(xb,.04,8.64),(xb,BACK,9.75),(xa,BACK,9.75)]
        b.add(v+[tuple((x,y,z-.12)) for x,y,z in v],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'baked roof tiles','side eaves/photographed roof portion')
    for x0,x1,y0,y1,z in ((-2.96,5.58,.98,BACK,11.68),(-hw,hw-1.2,.34,BACK,8.33),(hw-1.12,hw-.285,.35,RETURN,8.40)):
        b.box(((x0+x1)/2,(y0+y1)/2,z),(x1-x0,y1-y0,.117),'neutral section',label='neutral building section/top closure')
    for x,w,y in ((0,2*hw,BACK),(hw-.66,1.32,RETURN)):
        b.box((x,y,4.13),(w,.12,8.26),'neutral section',label='neutral building section/rear cut')
    b.box((-hw+.088,BACK/2,4.15),(.13,BACK-.04,8.30),'neutral section',label='neutral building section/north cut')
    b.box((hw-1.34,(BACK+RETURN)/2,4.15),(.12,RETURN-BACK,8.30),'neutral section',label='neutral building section/south turn cut')
    b.box((1.31,BACK-.10,9.94),(8.60,.14,3.16),'neutral section',label='neutral building section/high return')


def frontage(builder,lod):
    """Calibrate the photographed surfaces to the actual west wall and its southern return."""
    first=len(builder.parts)
    draw_elevation(builder,lod)
    for part in builder.parts[first:]:
        part['vertices']=[(x*X_SCALE,y*Y_SCALE,z*Z_SCALE) for x,y,z in part['vertices']]
