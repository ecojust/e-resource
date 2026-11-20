"""Historic offices of Caldbeck, Macgregor & Co., Shanghai, photographed in 2014."""
from math import ceil, floor
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union
from photo_architecture import Facade, pieces

HALF = 15.84
BACK = 8.45
FLOOR = 3.90
EAVE = 7.32
RIDGE = 11.38
GABLE_TOP = 11.25
GABLES = (-11.24, 11.12)
GABLE_HALF = 3.05
RIDGE_Y = 4.2
EAVE_Y = -.22
GABLE_Y = -.58
PALETTE = {k:{'color':rgb,'roughness':r} for k,rgb,r in [
    ('sand render',[.774,.655,.485],.93),('warm mortar',[.468,.395,.332],.95),
    ('dark kiln brick',[.333,.241,.208],.94),('rose brick',[.37,.248,.213],.95),
    ('umber brick',[.327,.221,.199],.94),('washed brick',[.371,.273,.231],.96),
    ('oxblood timber',[.322,.109,.061],.80),('rebated wood',[.229,.082,.049],.84),
    ('historic glass',[.103,.139,.144],.39),('window shadow',[.083,.091,.09],.95),
    ('slate plinth',[.27,.29,.285],.91),('brick rust tile',[.411,.203,.129],.92),
    ('weathered red tile',[.383,.196,.139],.93),('russet tile',[.449,.225,.150],.94),
    ('ridge roll',[.397,.202,.139],.9),('aged lead',[.22,.243,.245],.83),
    ('neutral section',[.529,.499,.455],.98),('inner dark reveal',[.16,.137,.115],.97)]}

def plank(f, u, z, width, height, label, depth=.13, material='oxblood timber'):
    f.box(u,z,width,height,depth,depth/2,material,label)

def sash(f, rect, lod, label, columns=2, rows=3):
    x0,z0,x1,z1=rect.bounds
    f.prism(rect.buffer(.012,join_style=2),-.33,-.30,'historic glass',label+'/glass')
    clear=rect.buffer(-.062,join_style=2)
    shape=rect.difference(clear)
    for i in range(1,columns):
        u=x0+(x1-x0)*i/columns
        shape=shape.union(box(u-.029,z0,u+.029,z1))
    for i in range(1,rows):
        h=z0+(z1-z0)*i/rows
        shape=shape.union(box(x0,h-.024,x1,h+.024))
    f.prism(shape,-.22,-.15,'rebated wood',label+'/frame')
    if not lod:
        f.box((x0+x1)/2,z0-.045,x1-x0+.09,.09,.22,.05,'rebated wood',label+'/drip sill')

def brickwork(f, face, lod, label):
    x0,z0,x1,z1=face.bounds
    width,height=(.72,.26) if lod else (.335,.155)
    for row in range(ceil((z1-z0)/height)):
        begin=x0-width*(row%2)/2
        for col in range(ceil((x1-begin)/width)):
            x=begin+col*width; z=z0+row*height
            tile=face.intersection(box(x+.009,z+.007,x+width-.006,min(z+height-.007,z1)))
            if tile.area<.001:continue
            mat=('dark kiln brick','rose brick','umber brick','washed brick')[(row*47+col*17+(row//3))%4]
            f.prism(tile,0,.018,mat,label)

def lower_storey(b,lod):
    f=Facade(b,(-HALF,0),(HALF,0),'Ground floor')
    middle=box(-2.50,-.01,2.50,3.74);cuts=[middle]
    left=box(-14.16,1.10,-9.04,3.17);right=box(9.00,1.03,14.13,3.24)
    cuts.extend([left,right])
    sash(f,right,lod,'east bank',5,3)
    f.prism(left,-.27,-.24,'window shadow','west shutter dark field')
    for j in range(12 if lod else 24):
        z=1.12+j*(2.00/(12 if lod else 24))
        f.box(-11.60,z,5.08,.025,.051,-.208,'rebated wood','west shutter horizontal blades')
    for side in (-1,1):
        for z0,z1 in [(.82,2.12),(2.62,3.38)]:
            center=side*3.76;ap=box(center-.43,z0,center+.43,z1)
            cuts.append(ap);sash(f,ap,lod,'brick jamb lights',1,2 if z1-z0>1 else 1)
    wall=f.wall(.18,FLOOR,cuts,.40,'warm mortar')
    brickwork(f,wall,lod,'brick face')
    for lo,hi in [(-HALF,-2.50),(2.50,HALF)]:
        f.box((lo+hi)/2,.095,hi-lo,.19,.49,-.15,'slate plinth','brickwork base')
    f.prism(box(-2.50,0,2.50,3.74),-1.25,-1.24,'inner dark reveal','unseen passage back')
    for side in (-1,1):
        b.box((side*2.53,.57,1.88),(.12,1.1,3.76),'rebated wood',label='Entrance/recessed timber side')
    b.box((0,.52,3.74),(5.10,1.04,.12),'rebated wood',label='Entrance/soffit')
    for side in (-1,1):
        d=side*7.1
        brace=LineString([(d,2.51),(d-side*.70,3.73)]).buffer(.09,cap_style=2)
        f.prism(brace,-.035,.20,'oxblood timber','curved support line')
    plank(f,0,FLOOR-.01,2*HALF+.10,.30,'principal continuous timber')
    
def upper_storey(b,lod):
    f=Facade(b,(-HALF,0),(HALF,0),'Upper timber frame')
    left,right=GABLES;centers=[-8.08,-7.13,-6.18,-4.82,-1.95,-.98,0,.98,1.94,2.93,5.42,6.37]
    central=[box(x-.325,5.44,x+.325,7.03) for x in centers]
    covers=[box(x-GABLE_HALF,FLOOR-.05,x+GABLE_HALF,EAVE+.04)for x in GABLES]
    f.wall(FLOOR+.13,EAVE,[*central,*covers],.32,'sand render')
    for aperture in central:sash(f,aperture,lod,'tall casements',1,3)
    for pos in [-15.15,-8.0,-6.61,-5.57,-4.12,-3.08,-2.45,-1.45,-.50,.51,1.46,2.46,3.45,4.32,4.89,5.91,6.88,7.65,14.76,15.62]:
        if any(abs(pos-c)<GABLE_HALF+.07 for c in GABLES):continue
        plank(f,pos,(EAVE+FLOOR)/2,.139,EAVE-FLOOR,'upper studs')
    for lo,hi in [(-HALF,left-GABLE_HALF),(left+GABLE_HALF,right-GABLE_HALF),(right+GABLE_HALF,HALF)]:
        for z,h in [(5.27,.16),(EAVE-.04,.19)]:
            plank(f,(lo+hi)/2,z,hi-lo,h,'mid rail and eave edge')
    for c in GABLES:
        g=Facade(b,(c-GABLE_HALF,GABLE_Y+.07),(c+GABLE_HALF,GABLE_Y+.07),'Jettied gable')
        outline=Polygon([(-GABLE_HALF,FLOOR+.1),(GABLE_HALF,FLOOR+.1),(GABLE_HALF,EAVE),(0,GABLE_TOP),(-GABLE_HALF,EAVE)])
        windows=[box(u-.339,5.45,u+.339,6.99)for u in [-1.42,-.47,.47,1.42]]
        g.wall(FLOOR,GABLE_TOP,windows,.31,'sand render',outline)
        for a in windows:sash(g,a,lod,'oriel four lights',1,3)
        for side in (-1,1):
            b.box((c+side*(GABLE_HALF-.10),-.19,5.63),(.22,.70,3.35),'sand render',label='Gables/short side returns')
        positions=[-GABLE_HALF+.13,-1.95,-.96,0,.96,1.95,GABLE_HALF-.13]
        for x in positions:
            z=GABLE_TOP-(GABLE_TOP-EAVE)*abs(x)/GABLE_HALF-.09
            plank(g,x,(z+FLOOR+.12)/2,.16,z-FLOOR-.12,'projecting gable studs')
        for z,h in [(FLOOR+.08,.28),(5.28,.17),(7.15,.20)]:
            plank(g,0,z,2*GABLE_HALF,h,'oriel rails',depth=.19)
        for side in (-1,1):
            rake=LineString([(side*(GABLE_HALF+.06),EAVE-.09),(0,GABLE_TOP+.06)]).buffer(.115,cap_style=2)
            g.prism(rake,.09,.27,'oxblood timber','sloping bargeboard')
            inset=LineString([(side*1.65,8.97),(0,10.50)]).buffer(.08,cap_style=2)
            g.prism(inset,0,.12,'rebated wood','upper braces')
        plank(g,0,10.55,.20,.90,'ridge pendant',.29)

def plane_tiles(b,plan,zfn,axis,lod,label):
    if plan.is_empty:return
    # Tile pieces terminate at the two real roof valleys. Narrow open joints
    # reveal the continuous red roof plane underneath.
    def plane(poly,lift,mat):
        for ring in pieces(poly):
            from shapely.ops import triangulate
            for tri in triangulate(ring):
                if not ring.covers(tri):continue
                q=list(tri.exterior.coords)[:3]
                b.add([(x,y,zfn(x,y)+lift) for x,y in q],[(0,1,2)],mat,label)
    plane(plan,0,'weathered red tile')
    x0,y0,x1,y1=plan.bounds
    across,rise=(.67,.47) if lod else (.355,.265)
    low,high=(y0,y1) if axis=='y' else (x0,x1)
    left,right=(x0,x1) if axis=='y' else (y0,y1)
    for row in range(ceil((high-low)/rise)):
        a=low+row*rise;start=left-(row%2)*across/2
        for col in range(ceil((right-start)/across)):
            t=start+col*across
            bounds=(t+.008,a+.009,t+across-.008,a+rise-.005) if axis=='y' else (a+.009,t+.008,a+rise-.005,t+across-.008)
            piece=plan.intersection(box(*bounds))
            if piece.area>.002:plane(piece,.024,('weathered red tile','brick rust tile','russet tile')[(col*7+row*13+(col//3)*(row//5)+row//4)%3])

def roof(b,lod):
    slope=(RIDGE-EAVE)/(RIDGE_Y-EAVE_Y)
    front_z=lambda x,y:EAVE+(y-EAVE_Y)*slope
    rear_z=lambda x,y:RIDGE-(y-RIDGE_Y)*(RIDGE-EAVE)/(BACK-RIDGE_Y)
    front=box(-HALF-.05,EAVE_Y,HALF+.05,RIDGE_Y)
    back=box(-HALF-.05,RIDGE_Y,HALF+.05,BACK)
    hips=[]
    for side in (-1,1):
        e=side*(HALF+.05);tip=side*(HALF-4.2)
        wedge=Polygon([(e,EAVE_Y),(e,BACK),(tip,RIDGE_Y)])
        hips.append((e,wedge))
        front=front.difference(wedge);back=back.difference(wedge)
    for c in GABLES:
        ypeak=EAVE_Y+(GABLE_TOP-EAVE)/slope
        pocket=Polygon([(c-GABLE_HALF,EAVE_Y),(c+GABLE_HALF,EAVE_Y),(c,ypeak)])
        front=front.difference(pocket)
        hips=[(e,region.difference(pocket))for e,region in hips]
        for sign in (-1,1):
            edge=c+sign*GABLE_HALF
            wing=Polygon([(c,GABLE_Y-.13),(edge,GABLE_Y-.13),(edge,EAVE_Y),(c,ypeak)])
            gable=lambda x,y:EAVE+(GABLE_TOP-EAVE)*(1-abs(x-c)/GABLE_HALF)
            plane_tiles(b,wing,gable,'x',lod,'Roof/cross gable tile slopes')
            b.tube([(edge,EAVE_Y,EAVE+.07),(c,ypeak,GABLE_TOP+.07)],.050,'aged lead',6,'Roof/valley flashings')
        b.tube([(c,GABLE_Y-.16,GABLE_TOP+.079),(c,ypeak,GABLE_TOP+.079)],.09,'ridge roll',8,'Roof/cross ridges')
    plane_tiles(b,front,front_z,'y',lod,'Roof/main street slope')
    plane_tiles(b,back,rear_z,'y',lod,'Roof/rear slope')
    for edge,region in hips:
        hip_z=lambda x,y:EAVE+(RIDGE-EAVE)*abs(edge-x)/4.25
        plane_tiles(b,region,hip_z,'x',lod,'Roof/end hip slopes')
        tip=(1 if edge>0 else -1)*(HALF-4.2)
        for a in (EAVE_Y,BACK):
            b.tube([(edge,a,EAVE+.05),(tip,RIDGE_Y,RIDGE+.05)],.063,'ridge roll',7,'Roof/hip rolls')
    b.tube([(-HALF+4.20,RIDGE_Y,RIDGE+.073),(HALF-4.20,RIDGE_Y,RIDGE+.073)],.094,'ridge roll',8,'Roof/long ridge')
    ridge_outline=box(0,.15,BACK,EAVE)
    for side in (-1,1):
        lo,hi=sorted((side*HALF,side*(HALF-.19)))
        b.prism(ridge_outline,lo,hi,lambda y,z,x:(x,y,z),'neutral section','Cut ends/plain gable returns')
    b.box((0,BACK-.11,EAVE/2),(2*HALF-.31,.22,EAVE),'neutral section',label='Section/plain rear')
    for u in (-7.18,6.58):
        b.box((u,4.87,11.71),(.72,.86,3.71),'dark kiln brick',label='Roof/bricks in paired skyline stacks')
        for j in range(11 if lod else 23):
            z=10.11+j*(3.23/(10 if lod else 22))
            b.box((u,4.87,z),(.733,.871,.022),'warm mortar',label='Chimneys/brick beds')
        for z,w,h in [(13.46,.86,.15),(13.62,.78,.12),(13.70,.81,.065)]:
            b.box((u,4.87,z),(w,w+.12,h),'umber brick',label='Chimneys/corbelled caps')
        b.box((u,4.87,13.737),(.46,.50,.014),'window shadow',label='Chimneys/shadow at crown')

def add_street_wing(b,lod):
    lower_storey(b,lod)
    upper_storey(b,lod)
    roof(b,lod)
    # Fit the street wing inside the measured shared west boundary, including
    # its projecting eave. The source lot frontage is slightly wider than the house.
    for part in b.parts:
        part['vertices'] = [(.965*x+.25,y,z) for x,y,z in part['vertices']]
