"""Courtyard roof of the garden residence at 881 Middle Yan'an Road."""
import math


def surface(rgb,roughness):
    return {'color':[s/3294.6 if s<=10 else ((s/255+.055)/1.055)**2.4 for s in rgb],'roughness':roughness,'metallic':0}


PALETTE={name:surface(rgb,rough) for name,rgb,rough in [
    ('raked brick',(101,81,75),.91),('weathered joint',(128,113,100),.93),('projecting stone',(156,142,125),.89),
    ('earthenware',(117,100,90),.88),('flue interior',(57,48,46),.97),('roof clay',(117,68,58),.93),
    ('roof course',(141,83,67),.92),('white plaster',(215,205,184),.84),('bargeboard',(105,59,52),.80),
    ('sash',(74,64,58),.82),('pane',(93,107,109),.43),('sill',(161,151,133),.92)]}


def prism(b,outline,y0,y1,material,label):
    n=len(outline)
    vertices=[(x,y,z) for y in (y0,y1) for x,z in outline]
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    faces.extend((j,n+j,n+(j+1)%n,(j+1)%n) for j in range(n))
    b.add(vertices,faces,material,label)


def roof_panel(b,x0,x1,y0,y1,z0,z1,material,label,depth=.05):
    vertices=[(x,y,z+dz) for dz in (-depth,0.) for x,y,z in [(x0,y0,z0),(x1,y0,z0),(x1,y1,z1),(x0,y1,z1)]]
    b.add(vertices,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material,label)


def hollow_pot(b,x,y,base,lod,label):
    sides=10 if lod else 20
    vertices=[]
    for height,radius in [(0,.113),(.58,.096),(.58,.065),(.12,.066)]:
        for i in range(sides):
            a=2*math.pi*i/sides;vertices.append((x+radius*math.cos(a),y+radius*math.sin(a),base+height))
    for band,material in [(0,'earthenware'),(1,'earthenware'),(2,'flue interior')]:
        faces=[(band*sides+i,band*sides+(i+1)%sides,(band+1)*sides+(i+1)%sides,(band+1)*sides+i) for i in range(sides)]
        b.add(vertices,faces,material,label+' '+str(band))
    b.add(vertices,[tuple(3*sides+i for i in range(sides))],'flue interior',label+' inner bottom')


def stack(b,x,lod,label):
    y=4.74
    b.box((x,y,3.52),(.99,.82,2.86),'raked brick',label=label+' red masonry')
    for i in range(11):
        z=2.23+i*.249
        b.box((x,y,z),(1.000,.830,.014 if lod else .021),'weathered joint',label=label+' light bed '+str(i))
    for z,w,h in [(3.91,1.049,.079),(4.93,1.12,.115),(5.077,1.28,.18),(5.23,1.105,.126)]:
        b.box((x,y,z),(w,w*.87,h),'projecting stone',label=label+' projecting band '+str(z))
    for i,dx in enumerate((-.22,.22)):
        hollow_pot(b,x+dx,y,5.293,lod,label+' terminal '+str(i))


def add_building(b,lod=False):
    # Coordinates in metres, sill height is zero. Y increases from the dormer into the roof.
    for lo,hi in ((-2.35,-1.17),(1.17,5.28)):
        roof_panel(b,lo,hi,-.40,4.74,-.32,2.69,'roof clay','front clay slope')
    roof_panel(b,-1.17,1.17,.80,4.74,.382,2.69,'roof clay','slope behind the dormer')
    roof_panel(b,-2.35,5.28,4.74,5.57,2.69,2.20,'roof clay','rear ridge strip')
    for i in range(21):
        y=-.31+i*.244;z=-.32+(y+.40)*3.01/5.14
        segments=((-2.35,-1.17),(1.17,5.28)) if y<1.76 else ((-2.35,5.28),)
        for l,r in segments:
            roof_panel(b,l,r,y,y+.032,z+.018,z+.035,'roof course','tile lip '+str((i,l)),.014)
    for x in (-.27,4.12):stack(b,x,lod,'chimney '+str(x))
    # White plaster frames a single dark double casement and its low sill.
    for x in (-.91,.91):
        b.box((x,.32,.636),(.39,.64,1.352),'white plaster',label='dormer cheek '+str(x))
    b.box((0,.32,1.467),(2.21,.64,.313),'white plaster',label='flat window head')
    prism(b,[(-1.105,1.619),(1.105,1.619),(0,2.458)],0,.64,'white plaster','plastered triangle')
    b.box((0,.195,.64),(1.43,.085,1.28),'pane',label='two recessed panes')
    for x in (-.692,0,.692):b.box((x,.119,.635),(.06,.060,1.289),'sash',label='window stile '+str(x))
    for z in (.036,.448,1.267):b.box((0,.12,z),(1.43,.060,.063),'sash',label='window rail '+str(z))
    b.box((0,.078,-.02),(1.57,.27,.082),'sill',label='projecting window sill')
    for side in (-1,1):
        xs=sorted((0,side*1.32));zs=[2.503-.72*abs(x) for x in xs]
        shape=[(xs[0],zs[0]-.14),(xs[1],zs[1]-.14),(xs[1],zs[1]+.085),(xs[0],zs[0]+.085)]
        prism(b,shape,-.105,1.74,'roof clay','pitched dormer tile '+str(side))
        prism(b,shape,-.147,-.105,'bargeboard','front pitched fascia '+str(side))
    b.tube([(0,-.06,2.55),(0,-.06,2.81)],.024,'bargeboard',6 if lod else 12,'short ridge spike')
