"""Measured January 2015 gate, three ventilation slots and the barred window of No. 58."""
from math import cos, pi, sin
def material(rgb):
    return {'color':[(v/3294.6 if v<11 else ((v/255+.055)/1.055)**2.4) for v in rgb],'roughness':.81}
PALETTE={k:material(v) for k,v in {
    'warm grey render':(178,174,161),'cement cap':(151,148,137),'shadow fillet':(127,125,116),
    'charcoal plinth':(65,64,62),'wood 1':(99,48,39),'wood 2':(111,50,41),'wood 3':(105,47,39),
    'weathered timber':(112,80,57),'dark joint':(56,40,33),'mailbox red':(123,69,60),
    'old iron':(70,64,57),'dark glazing':(64,61,53),'dusty glass':(87,83,71),
    'stone sill':(164,157,142),'green enamel':(47,83,65),'white enamel':(223,222,199),
    'shadowed vent reveal':(79,73,62),'grey threshold':(128,118,105),'brass plate':(142,128,94)}.items()}
# Z uses the documented first camera's local pavement datum.
def block(b,label,mat,x0,x1,y0,y1,z0,z1):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)
def add_wall(b):
    holes=[(-1.61,-.735,1.57,2.78),(-.002,1.005,.421,2.383),(1.392,1.666,2.47,2.735),
           (1.914,2.038,1.95,2.343),(2.144,2.27,1.942,2.343),(2.377,2.498,1.938,2.34)]
    xmin,xmax=-1.865,2.695;bottom=.34;top=2.972
    edges=sorted({xmin,-.09,xmax,*[v for h in holes for v in h[:2]]})
    for j,(x0,x1) in enumerate(zip(edges,edges[1:])):
        top=2.895 if x1<=-.09 else 2.790
        aperture=next((q for q in holes if q[0]<=(x0+x1)/2<=q[1]),None)
        spans=[(bottom,top)] if aperture is None else [(bottom,aperture[2]),(aperture[3],top)]
        for a,z in spans:
            if a<.687:
                block(b,'charcoal base of rendered wall','charcoal plinth',x0,x1,0,.26,a,min(z,.687))
            if z>.687:
                block(b,'grey plaster and recessed reveals','warm grey render',x0,x1,0,.26,max(a,.687),z)
    # Dark inside returns are visible by oblique sight without closing the opening.
    for i,(x0,x1,z0,z1) in enumerate(holes[2:]):
        d=.005
        block(b,'aperture '+str(i+1)+' left inner cheek','shadowed vent reveal',x0,x0+d,.010,.26,z0,z1)
        block(b,'aperture '+str(i+1)+' right inner cheek','shadowed vent reveal',x1-d,x1,.010,.26,z0,z1)
        block(b,'aperture '+str(i+1)+' inside soffit','shadowed vent reveal',x0+d,x1-d,.01,.26,z1-d,z1)
        block(b,'aperture '+str(i+1)+' inner sill','shadowed vent reveal',x0+d,x1-d,.01,.26,z0,z0+d)
    block(b,'projecting cap above the gateway','cement cap',-.09,xmax,-.072,.274,2.790,2.972)
    block(b,'narrow drip at underside of cap','shadow fillet',-.09,xmax,-.046,.25,2.773,2.790)
    block(b,'left wall cap','cement cap',xmin,-.09,-.021,.265,2.895,2.970)
def add_gate(b,lod):
    block(b,'inset wooden gate panel','dark joint',.052,.966,.115,.178,.433,2.361)
    block(b,'left wooden jamb','dark joint',.001,.053,.052,.177,.422,2.382)
    block(b,'right wooden jamb','dark joint',.962,1.005,.052,.177,.422,2.382)
    block(b,'dark head of opening','dark joint',.05,.964,.056,.176,2.320,2.382)
    for i in range(10):
        x=.06+i*.09
        block(b,'red timber board '+str(i+1),['wood 1','wood 2','wood 3','wood 1','wood 2'][i%5],
              x,x+.089,.100,.116,.435,2.321)
    for i,(bottom,top) in enumerate([(1.086,1.242),(.561,.666)]):
        block(b,'weathered horizontal gate rail '+str(i+1),'weathered timber',.053,.96,.067,.103,bottom,top)
        if not lod:
            for x in (.09,.91):
                b.tube([(x,.064,(top+bottom)/2),(x,.059,(top+bottom)/2)],.009,'old iron',10,'rail fastener')
    block(b,'stone threshold below timber','grey threshold',-.012,1.012,-.115,.17,.332,.424)
    block(b,'painted mailbox case','mailbox red',.148,.455,-.043,.1,1.547,1.976)
    block(b,'mailbox letter slot','dark joint',.166,.441,-.054,-.043,1.892,1.932)
    block(b,'mailbox drop front','mailbox red',.162,.441,-.054,-.043,1.562,1.881)
    # The box lid pitches towards the street.
    x0,x1=.125,.478;y0,y1=-.091,.10
    v=[(x,y,z-d)for d in (0,.019)for x,y,z in ((x0,y0,1.992),(x1,y0,1.992),(x1,y1,2.044),(x0,y1,2.044))]
    b.add(v,[(0,1,2),(0,2,3),(4,6,5),(4,7,6),(0,4,5),(0,5,1),(1,5,6),(1,6,2),(2,6,7),(2,7,3),(3,7,4),(3,4,0)],
          'weathered timber','sloping lid on the letterbox')
    block(b,'rectangular metal plate on the gate','brass plate',.536,.725,.084,.10,1.378,1.574)
    if not lod:
        for x in (.548,.712):
            for z in (1.393,1.559):
                b.tube([(x,.083,z),(x,.079,z)],.004,'old iron',8,'metal plate screw')
def add_window(b,lod):
    x0,x1=-1.61,-.735;z0,z1=1.57,2.78
    block(b,'deep window backing','dark glazing',x0,x1,.159,.172,z0,z1)
    for i in range(4):
        for j in range(3):
            x=x0+(x1-x0)*i/4;z=z0+(z1-z0)*j/3
            block(b,'dark interior glass '+str(i+1)+' '+str(j+1),'dusty glass' if i==2 else 'dark glazing',
                  x+.016,x+(x1-x0)/4-.016,.141,.155,z+.013,z+(z1-z0)/3-.013)
    for i in range(4):
        x=x0+(x1-x0)*(.10+i*.267)
        block(b,'street window upright '+str(i+1),'old iron',x-.014,x+.014,.031,.060,z0,z1)
    for j in (1,2):
        z=z0+(z1-z0)*j/3
        block(b,'street window horizontal '+str(j),'old iron',x0,x1,.054,.082,z-.011,z+.011)
    block(b,'window sill with front lip','stone sill',-1.681,-.661,-.086,.22,1.491,1.57)
def add_number(b,lod):
    block(b,'number plate raised green enamel','green enamel',1.050,1.301,-.015,.005,2.232,2.408)
    # Two white digits are independently drawn as strokes from the clearly legible number.
    def stroke(points,label,width=.006):
        b.tube([(x,-.021,z)for x,z in points],width,'white enamel',5 if lod else 8,label)
    stroke([(1.151,2.386),(1.098,2.386),(1.094,2.348),(1.133,2.348),(1.151,2.336),
            (1.150,2.312),(1.139,2.299),(1.113,2.295),(1.092,2.306)],'digit five')
    for i,(cz,rx,rz) in enumerate([(2.365,.024,.022),(2.323,.028,.025)]):
        sides=12 if lod else 24
        stroke([(1.216+rx*cos(2*pi*k/sides),cz+rz*sin(2*pi*k/sides))for k in range(sides+1)],'digit eight loop '+str(i+1))
    for x in (1.060,1.290):
        for z in (2.243,2.397):
            b.tube([(x,-.015,z),(x,-.019,z)],.004,'old iron',6,'enamel plate fastening')
def add_building(builder,lod=False):
    add_wall(builder);add_gate(builder,lod);add_window(builder,lod);add_number(builder,lod)
