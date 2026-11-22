"""Measured stair noses, the red newel, the four-door postbox and the address plate."""
import numpy as np
from shapely.geometry import Polygon,box
from photo_architecture import Facade
from registration import C,HERE,plane
from brick_entrance import FLOOR
import json
TREAD='Weathered brown stair tread'
RISER='Oxide brown stair riser'
BULL='Worn stone stair nosing'
RAIL='Oxide red stair rail'
WALL='Old limewashed plaster'
BOX='Dark mailbox enamel'
ZINC='Galvanised mailbox casing'
def stairs(b,lod):
    measure=json.loads((HERE.parent/'measurements/stair-noses.json').read_bytes())
    dy=measure['conditional_run_m'];dz=measure['conditional_rise_m'];count=len(measure['noses'])
    y0=.24;x0,x1=-.588,.074
    for i in range(count):
        y=y0+dy*i;z=FLOOR+dz*(i+1)
        # Each tread and its front edge remain separately editable in the native model.
        b.box(((x0+x1)/2,y+dy/2,z-.026),(x1-x0,dy+.012,.052),TREAD,label='Stair/tread '+str(i+1))
        b.box(((x0+x1)/2,y+.016,z-dz/2-.021),(x1-x0,.033,dz-.035),RISER,label='Stair/riser '+str(i+1))
        b.box(((x0+x1)/2,y-.001,z-.013),(x1-x0+.010,.032,.026),BULL,label='Stair/nosing '+str(i+1))
    end=y0+dy*count;landing=FLOOR+count*dz
    # The stringers close the sides of the flight and carry its painted handrail.
    for x,sgn in [(x0,-1),(x1,1)]:
        side=Facade(b,(x,-.5),(x,.5),'Stair structure')
        shape=Polygon([[y0,FLOOR+dz-.071],[end,landing-.055],[end,landing-.28],[y0,FLOOR-.17]])
        side.prism(shape,-.034,.034,WALL if sgn<0 else RAIL,'stringer '+str(sgn))
    b.box(((x0+x1)/2,end+.14,landing-.035),(x1-x0+.065,.28,.070),TREAD,label='Stair/upper landing')
    b.box((.339,end/2,FLOOR-.042),(.553,end+.28,.084),'Grey hall tile',label='Stair/side corridor pavement')
    px=x1+.044
    b.box((px,y0+.047,FLOOR+.355),(.072,.083,.71),RAIL,label='Stair/newel square shank')
    b.lathe((px,y0+.047),[(FLOOR+.685,.041),(FLOOR+.697,.050),(FLOOR+.718,.052),(FLOOR+.730,.041),
                             (FLOOR+.754,.030),(FLOOR+.768,.046),(FLOOR+.794,.053),(FLOOR+.822,.049),(FLOOR+.843,.027),(FLOOR+.850,.009)],
            'Red turned newel cap',segments=12 if lod else 26,label='Stair/fluted round newel head')
    for j in range(0,count,2):
        y=y0+dy*j+.12;z=FLOOR+(j+1)*dz
        b.box((px,y,z+.306),(.036,.041,.626),RAIL,label='Stair/slender guard post')
    a=np.array([px,y0+.07,FLOOR+.735]);c=np.array([px,end-.12,landing+.650])
    b.tube([a,c],.031,RAIL,8 if lod else 14,'Stair/sloping red handrail')
    # The painted walls are cut to reveal the flight. The pair of red doors is visible at the head.
    side=Facade(b,(x0-.061,-.5),(x0-.061,.5),'Stair enclosure')
    side.prism(Polygon([[-.03,FLOOR],[end+.28,landing-.12],[end+.28,landing+.69],[end-.33,landing+.69],[.4,.57],[-.03,.57]]),-.066,.012,WALL,'cut limewashed left cheek')
    f=Facade(b,(-.5,end+.28),(.5,end+.28),'Upper landing')
    for x in [-.424,-.111]:
        f.box(x,landing+.32,.305,.68,.035,-.013,'Red upper cupboard','red painted door')
        f.box(x+(.094 if x<-.22 else -.094),landing+.39,.016,.096,.019,.021,'Pale cabinet pull','vertical handle')
    # The dark panel door beside the foot of the staircase closes the passage in the gate photograph.
    xrear=.608;corridor=Facade(b,(-.5,2.12),(.5,2.12),'Side corridor')
    corridor.prism(box(.078,FLOOR,xrear,.64),-.105,-.022,'Inner hallway in shade','wall at end of passage')
    corridor.prism(box(.139,FLOOR+.018,.585,.42),-.018,.029,'Old oxblood door','closed corridor door')
    for low,high in [(FLOOR+.19,-.42),(-.33,.23)]:
        corridor.prism(box(.195,low,.53,high),.0295,.036,'Worn dark door panel','inset panel')
    right=Facade(b,(xrear,.5),(xrear,-.5),'Side corridor')
    right.prism(box(-2.18,FLOOR,.015,.65),-.103,.008,'Inner hallway in shade','right return')
    b.box((-.005,.109,FLOOR-.040),(1.209,.268,.08),'Grey hall tile',label='Stair/entrance floor')
    last=Facade(b,(-.5,end+.315),(.5,end+.315),'Upper landing')
    last.prism(box(x0-.04,FLOOR,.61,landing+.695),-.114,-.009,'Inner hallway in shade','closed back of stairs and landing')
    upper=Facade(b,(x1+.077,-.5),(x1+.077,.5),'Stair structure')
    upper.prism(Polygon([[.012,FLOOR-.01],[end+.27,FLOOR-.01],[end+.27,landing-.074],[y0,FLOOR+.06]]),
                -.066,.006,'Stair beneath flight','enclosed side under flight')
    # From the low entrance camera the photograph shows the interior, including under the hall ceiling.
    # The covered corridor ends before the exposed side of the staircase cutaway.
    b.box((.338,1.081,.817),(.588,2.154,.084),'Inner hallway in shade',label='Side corridor/ceiling above closed door')
    right.prism(box(-2.18,.635,-.003,.847),-.103,.008,'Inner hallway in shade','wall above the door head')
    b.box((.341,2.113,.725),(.60,.118,.206),'Inner hallway in shade',label='Side corridor/door head plaster')
    b.box((-.267,.441,.855),(.677,.630,.082),'Inner hallway in shade',label='Entrance/underside inside the timber arch')
    # The hidden back of the stair enclosure also closes the narrow oblique sightline beside the rail.
    b.box((.385,end+.355,-.030),(.755,.103,2.81),'Inner hallway in shade',label='Upper landing/return to right corridor')
    b.box((.644,(end+2.42)/2,-.030),(.090,end-1.69,2.81),'Inner hallway in shade',label='Upper landing/enclosed rear return')
    for j in range(10):
        b.box((.339,j*.36+.02,FLOOR+.001),(.538,.004,.003),'Tile bed',label='Stair/corridor transverse joint')
def side_face(b,i,label):
    p=np.array(C['wall_corners_xy']);a,c=[(p[1],p[0]),(p[2],p[3])][i];return Facade(b,a,c,label)
def hardware(b,lod):
    right=side_face(b,1,'Postal boxes')
    # Project a source point to the actual splayed cheek, including its yaw.
    from registration import P
    eye=np.array(C['eye_enu_m'])
    def hit(face,uv):
        ray=np.linalg.solve(P[:,:3],[*uv,1]);t=((face.center-eye)@face.n)/(ray@face.n);q=eye+t*ray
        return (q-face.center)@face.t,q[2]
    u,z=hit(right,[557,442]);u=float(u);z=float(z)
    width=.49;height=.66;lo=z-height/2;hi=z+height/2
    right.prism(box(u-width/2,lo,u+width/2,hi),.006,.123,ZINC,'sheet metal body')
    # The pitched hood falls left and right across the width of the four-box stack.
    pts=[right.point(x,zz,d)for d in [.001,.139]for x,zz in [(u-width/2-.008,hi),(u,hi+.108),(u+width/2+.008,hi)]]
    b.add(pts,[(0,1,4,3),(1,2,5,4),(0,3,5,2),(0,2,1),(3,4,5)],ZINC,'Postal boxes/folded peaked hood')
    for i in range(4):
        zz=lo+(i+.5)*height/4
        right.box(u,zz,width-.011,height/4-.013,.018,.130,BOX,'stacked black door '+str(i+1))
        right.box(u,zz+.019,.014,.040,.012,.146,'Silver mailbox latch','white latch '+str(i+1))
        right.box(u+.15,zz-.043,.051,.027,.005,.143,'Ivory label','paper label '+str(i+1))
    left=side_face(b,0,'Address and meters');u,z=hit(left,[167,299])
    left.box(u,z,.176,.167,.017,.016,'Deep green enamel sign','public address plate')
    # Both block figures on the small green street plate are modeled in a restrained cream stroke.
    glyphs=[[(.00,.81),(.55,1),(.55,0)],[(.86,.95),(.55,1),(.17,.78),(.06,.32),(.15,.07),(.60,.00),(.88,.20),(.86,.43),(.62,.57),(.13,.51)]]
    for n,points in enumerate(glyphs):
        loc=[left.point(u-.057+n*.059+x*.039,z-.035+y*.081,.0275)for x,y in points]
        b.tube(loc,.0031,'Ivory label',6 if lod else 9,'Address and meters/house number '+str(n+1))
    for i,uv in enumerate([[208,293],[232,298],[252,306]]):
        u,z=hit(left,uv)
        left.box(u,z,.105,.175,.075,.058,['Aged aluminium meter','Blue enamel meter','Blue enamel meter'][i],'meter cabinet '+str(i+1))
        left.box(u,z+.030,.063,.048,.006,.099,'Grey meter window','inspection window')
    u,z=hit(left,[250,419])
    b.tube([left.point(u,FLOOR,.026),left.point(u,-.070,.026),left.point(u+.040,-.034,.026)],.012,'Ochre service pipe',7 if lod else 11,'Address and meters/vertical ochre pipe')
