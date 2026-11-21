"""Stone mouldings and hung ornament visible around the bank windows and stair tower."""
from math import sin,cos,pi
from shapely.geometry import Polygon,LineString,box
from finish import GRANITE,TRIM,BED

def foliage(face,x,z,width,height,angle,lod,depth=.22):
    outline=[(0,0),(-.27,.13),(-.18,.28),(-.49,.35),(-.32,.51),(-.47,.64),(-.18,.76),
             (0,1),(.10,.79),(.35,.70),(.28,.55),(.50,.44),(.20,.33),(.27,.19)]
    cs,sn=cos(angle),sin(angle)
    shape=[(x+width*u*cs+height*v*sn,z-width*u*sn+height*v*cs)for u,v in outline]
    face.prism(Polygon(shape),depth,depth+.065,TRIM,'stone leaf relief')
    if not lod:
        face.line((x,z,depth+.078),(x+.68*height*sn,z+.68*height*cs,depth+.082),.018,GRANITE,5,'leaf veins')

def hung_console(face,x,z,scale,lod):
    s=scale
    shield=Polygon([(x-.25*s,z+.11*s),(x+.25*s,z+.11*s),(x+.20*s,z-.57*s),
                    (x+.09*s,z-.86*s),(x,z-.98*s),(x-.09*s,z-.86*s),(x-.20*s,z-.57*s)])
    face.prism(shield,.08,.25,GRANITE,'tapering stone drop')
    face.box(x,z+.14*s,.62*s,.15*s,.39,.14,TRIM,'carved bracket head')
    for side in (-1,1):
        foliage(face,x+side*.08*s,z-.79*s,.23*s,.61*s,side*.19,lod,.25)
        face.line((x+side*.19*s,z-.15*s,.29),(x+side*.16*s,z-.51*s,.29),.022*s,TRIM,6,'console channels')
    face.box(x,z-.09*s,.11*s,.29*s,.08,.29,TRIM,'bracket relief')
    # The projecting toe at the bottom of the shelf is visible in the oblique 2026 image.
    face.box(x,z-.91*s,.23*s,.13*s,.29,.17,GRANITE,'bracket pendant')

def carved_band(face,start,end,z,lod):
    count=max(1,round((end-start)/.44))
    for i in range(count):
        u=start+(i+.5)*(end-start)/count
        face.box(u,z,.134,.23,.36,.27,GRANITE,'modillions below stone cornice')
        if not lod:face.box(u,z+.10,.18,.065,.43,.29,TRIM,'cornice tooth cap')

def raised_arch(face,x,z,w,rise,lod):
    coords=[(x+w*(i/20-.5),z+rise*sin(i*pi/20))for i in range(21)]
    for dy,thick,project in [(0,.154,.18),(.14,.104,.30)]:
        shape=LineString([(u,v+dy)for u,v in coords]).buffer(thick/2,cap_style='flat')
        face.prism(shape,.055,project,TRIM,'curved window hood')
    key=Polygon([(x-.075,z+rise+.05),(x+.075,z+rise+.05),(x+.13,z+rise+.42),(x-.13,z+rise+.42)])
    face.prism(key,.16,.31,GRANITE,'proud head keystones')

def stair_sculpture(face,lod):
    # Between the two landing windows and the roof lantern, carved consoles
    # carry a bowed cornice and a wreath encloses the circular ventilator.
    for side in (-1,1):
        hung_console(face,side*1.63,19.48,.99,lod)
        hung_console(face,side*1.69,28.29,.62,lod)
        for j in range(5):
            frac=j/4
            x=side*(.48+frac*.87)
            z=17.45+.52*frac**1.7
            foliage(face,x,z,.39,.43,side*(.89-.56*frac),lod,.22)
        for xx in (1.15,1.54):
            foliage(face,side*xx,23.48,.37,.59,side*.28,lod,.24)
        # Curved broken hoods on each side of the high arched window.
        path=[(side*(1.09+.64*t/12),25.91+.79*sin(pi*t/24))for t in range(13)]
        face.prism(LineString(path).buffer(.14,cap_style='flat'),.13,.39,GRANITE,'lantern broken scrolled hood')
        face.box(side*1.58,25.56,.97,.19,.48,.20,TRIM,'lantern half pediment spring')
    raised_arch(face,0,16.28,2.22,.28,lod)
    face.box(0,12.08,2.32,.15,.50,.20,TRIM,'landing window pedestal cornice')
    face.box(0,12.62,1.93,.60,.17,.077,GRANITE,'blind panel below landing')
    face.box(0,12.62,1.65,.40,.060,.172,TRIM,'recessed tablet field')
    for i in range(13):
        t=(i+.5)/13;x=(t-.5)*4.63;z=19.63+1.01*sin(t*pi)-.10
        face.box(x,z,.15,.18,.34,.30,GRANITE,'bowed modillions')
    key=Polygon([(-.17,19.98),(.17,19.98),(.29,20.64),(-.29,20.64)])
    face.prism(key,.22,.53,TRIM,'central bow keystone')
