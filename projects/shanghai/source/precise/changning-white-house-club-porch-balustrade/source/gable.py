"""Freestanding balustrade and carved capital pair of the White House Club porch."""
from math import pi, cos, sin
from pathlib import Path
from shapely.geometry import Polygon, box, LineString
from profile_tools import BRICK, cb, slab, bricks_uv

STONE = 'Ivory dressed stone'
RECESS = 'Weathered limestone recess'
SHAFT = 'Pale column stone'
FACE = 'Carved relief'
SHADOW = 'Relief shadow'
WOOD = 'Dark window timber'
GLASS = 'Deep grey blue glass'
METAL = 'Patinated fanlight metal'
W = 1.98
AX = 1.48
FRONT = -.32
BALUSTERS = [(-1.65 + 3.30*i/11) for i in range(12)]
COLORS = {BRICK:(255,255,255), STONE:(223,221,210), RECESS:(190,189,181),
          SHAFT:(230,227,216), FACE:(206,201,185), SHADOW:(165,160,147),WOOD:(66,53,49),GLASS:(77,86,85),METAL:(125,122,105)}
PALETTE = {name:{'color':[(n/255)**2.2 for n in rgb],'roughness':.85} for name,rgb in COLORS.items()}
PALETTE[BRICK]['texture'] = str(Path(__file__).with_name('finish.png'))
def halfdisk(rx,spring,rz,res):
    return Polygon([(rx*cos(i*pi/res),spring+rz*sin(i*pi/res)) for i in range(res+1)])
def oval(b,x,z,rx,rz,y0,y1,material,label,segments):
    shape=Polygon([(x+rx*cos(i*2*pi/segments),z+rz*sin(i*2*pi/segments)) for i in range(segments)])
    slab(b,shape,y0,y1,material,label)
def fascia(b,half,y0,y1,z0,z1,material,label):
    cb(b,-half,half,y0,y1,z0,z1,material,label)
def model(b,lod=False):
    sides=12 if lod else 24
    for sign in (-1,1):
        x=AX*sign
        cb(b,x-.245,x+.245,FRONT-.245,FRONT+.245,0,.13,STONE,'Square column foot')
        prof=[(.13,.205),(.16,.22),(.195,.224),(.23,.192),(.27,.181),(.34,.169),
              (2.70,.145),(2.73,.175),(2.77,.182),(2.82,.156),(2.86,.187)]
        b.lathe((x,FRONT),prof,SHAFT,sides,label='Tapered column and moulded neck')
        for z0,z1,width,material in [(2.86,2.90,.45,STONE),(2.90,3.22,.409,STONE),(3.22,3.27,.47,STONE)]:
            cb(b,x-width/2,x+width/2,FRONT-width/2,FRONT+width/2,z0,z1,material,'Square carved capital')
        fy=FRONT-.409/2
        oval(b,x,3.062,.099,.112,fy-.019,fy+.008,FACE,'Central relief of the capital',sides)
        for sx in (-1,1):
            for row in range(3):
                arc=[(x+sx*(.054+.081*j/8),fy-.016,2.99+.052*row+.025*sin(pi*j/8)-.019*j/8) for j in range(9)]
                b.tube(arc,.010 if row!=2 else .013,FACE,5 if lod else 7,label='Flanking carved leaf scroll')
            oval(b,x+sx*.042,3.085,.017,.012,fy-.032,fy-.016,SHADOW,'Paired relief eyes',sides)
        oval(b,x,3.049,.023,.036,fy-.039,fy-.017,FACE,'Raised center of relief',sides)
    # The rear arch behind the columns is recessed, as in the frontal photograph.
    opening=box(-.75,-.01,.75,2.28).union(halfdisk(.75,2.28,.60,sides*2))
    slab(b,box(-1.82,0,1.82,3.27).difference(opening),.59,.87,BRICK,'Rendered wall behind the porch')
    for sign in (-1,1):
        for j in range(8):
            xa,xb=sorted((sign*.75,sign*1.12));cb(b,xa,xb,.545,.625,j*.284,j*.284+.269,STONE,'Jointed jamb stones')
    for j in range(9):
        a=(j+.018)*pi/9;c=(j+.982)*pi/9
        pts=[(.75*cos(a),2.28+.60*sin(a)),(1.12*cos(a),2.28+.89*sin(a)),
             (1.12*cos(c),2.28+.89*sin(c)),(.75*cos(c),2.28+.60*sin(c))]
        slab(b,Polygon(pts),.525 if j!=4 else .48,.64,STONE,'Radial arch stones')
    # A central semicircle sends five rays to a second hoop. Six scrolled
    # panels follow the glazing over the rectangular dark timber door.
    slab(b,halfdisk(.744,2.28,.592,sides*2),.772,.79,GLASS,'Glass behind the fanlight')
    for radius in [.115,.406,.704]:
        edge=[(radius*cos(i*pi/(sides*2)),.720,2.28+.795*radius*sin(i*pi/(sides*2))) for i in range(sides*2+1)]
        b.tube(edge,.011 if radius<.5 else .016,METAL,6 if lod else 8,label='Concentric fanlight hoop')
    for j in range(1,6):
        a=j*pi/6
        b.tube([(r*cos(a),.719,2.28+.795*r*sin(a)) for r in (.115,.406)],.009,METAL,6 if lod else 8,label='Straight fanlight spoke')
    for j in range(6):
        a=(j+.5)*pi/6; ux,uz=cos(a),sin(a);vx,vz=-uz,ux
        for flip in (-1,1):
            coords=[]
            for i in range(14 if not lod else 9):
                u=i/(13 if not lod else 8);theta=u*1.70*pi;decay=1-.65*u
                v=flip*(.076+.070*cos(theta)*decay)
                r=.53+.080*sin(theta)*decay
                coords.append((r*ux+v*vx,.716,2.28+.795*(r*uz+v*vz)))
            stem=(.40*ux,.716,2.28+.795*.40*uz)
            b.tube([stem,*coords],.009,METAL,5 if lod else 8,label='Paired scroll in the outer fan')
    fascia(b,.753,.675,.812,2.217,2.283,WOOD,'Horizontal transom')
    panel=box(-.524,.22,.524,1.99)
    slab(b,box(-.746,.014,.746,2.218).difference(panel),.710,.808,WOOD,'Door rails and stiles')
    slab(b,panel,.778,.80,GLASS,'Dark glazed door panel')
    for sign in (-1,1):
        for j in range(-11,12):
            c=j*.326
            line=LineString([(c+sign*(z-1.10)*.45,z)for z in (-.10,2.25)]).intersection(panel)
            if line.geom_type!='LineString' or line.length<.045:continue
            b.tube([(x,.746,z)for x,z in line.coords],.009,METAL,5 if lod else 8,label='Diamond glazing bars')
    # The upper rail has a projecting front and two short returns.
    for z0,z1,x,y,material in [(3.27,3.33,1.85,-.565,STONE),(3.33,3.40,1.93,-.61,RECESS),(3.40,3.45,1.98,-.665,STONE),(3.45,3.49,1.94,-.62,STONE)]:
        fascia(b,x,y,.94,z0,z1,material,'Layer of the porch entablature')
    for i in range(38):
        x=-1.83+i*3.66/37;cb(b,x-.024,x+.024,-.635,-.604,3.336,3.373,STONE,'Projecting tooth beneath drip')
    for i in range(2):
        x=(-1 if i==0 else 1)*1.75
        for cy in (.04,.37,.70): 
            base=(3.49,.068);prof=[base,(3.54,.072),(3.57,.049),(3.64,.042),(3.77,.072),(3.87,.074),(3.94,.041),(4.02,.052),(4.044,.070),(4.07,.070)]
            b.lathe((x,cy),prof,STONE,sides,label='Baluster on the short return')
        cb(b,x-.10,x+.10,-.43,.83,4.07,4.15,STONE,'Side handrail')
    for x in BALUSTERS:
        b.lathe((x,-.444),[(3.49,.071),(3.535,.074),(3.564,.052),(3.631,.044),(3.765,.075),(3.865,.079),(3.925,.052),(4.0,.044),(4.03,.068),(4.07,.073)],STONE,sides,label='Front row of twelve turned balusters')
    fascia(b,1.85,-.55,-.334,4.07,4.14,STONE,'Front handrail')
    fascia(b,1.88,-.575,-.315,4.14,4.184,RECESS,'Weathered lip of the handrail')
    bricks_uv(b)
