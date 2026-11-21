"""Southern pediment and street portal of the east front, measured in metres."""

from math import cos, pi, sin
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, box
from shapely.affinity import scale as xy_scale
from photo_architecture import Facade, opening

BRICK = 'warm red running-bond brick'
LIME = 'pale limestone'
SHADE = 'recessed warm stone'
GLASS = 'deep blue-grey glass'
WOOD = 'brown painted casements'
IRON = 'dark bronze door'
ROOF = 'grey metal coping'
PALETTE = {name: {'color': rgb, 'roughness': rough} for name, rgb, rough in [
    (BRICK, [.88, .85, .82], .89), (LIME, [.80, .74, .65], .80),
    (SHADE, [.59, .53, .45], .88), (GLASS, [.13, .21, .22], .24),
    (WOOD, [.26, .13, .09], .65), (IRON, [.105, .115, .105], .55), (ROOF, [.31,.30,.28], .85),
    ('green enamel', [.025, .155, .095], .46), ('enamel lettering', [.91,.89,.77], .55)]}
WIDTH = 11.50
HALF = WIDTH/2
FACE = .94
BACK = 2.48
PAVILION = -1.33
PORTAL = 2.85


def pentagon(x, z, half_width, shoulder, crest):
    return Polygon([(x-half_width,z), (x+half_width,z), (x+half_width,z+shoulder),
                    (x,z+crest), (x-half_width,z+shoulder)])


def band(f, x, z, width, height, depth=.22, material=LIME, projection=.065, label='stone stringcourse'):
    f.box(x,z,width,height,depth,projection,material,label)


def frame(f, x, bottom, width, height, rise, lod, common, label):
    aperture = opening(x,bottom,width,height,rise,segments=9 if lod else 23)
    f.window(aperture,columns=1 if lod else 2,rows=2 if lod else 3,
             frame=WOOD,glass=GLASS,trim=False,label=label)
    f.builder.parts.pop()
    # The segmental heads are narrow at the sides and a separate moulding runs across the crown.
    outer=aperture.buffer(.094,join_style=2)
    band_shape=outer.difference(aperture).intersection(box(x-width,bottom+height-rise-.22,x+width,bottom+height+.2))
    f.prism(band_shape,.014,.153,LIME,label+' arched hood')
    band(f,x,bottom-.045,width+.15,.09,.26,SHADE,.04,label+' sill')
    if common:
        trim=aperture.buffer(.052,join_style=2).difference(aperture)
        f.prism(trim,-.045,.021,SHADE,label+' reveal')
    return aperture


def medallion(f,x,z,radius,lod):
    pts=[(x+radius*cos(t*2*pi/(12 if lod else 28)),z+radius*sin(t*2*pi/(12 if lod else 28)))
         for t in range(12 if lod else 28)]
    shp=Polygon(pts)
    f.prism(shp,.055,.101,SHADE,'stone roundel bed')
    f.prism(shp.difference(shp.buffer(-.035)),.096,.165,LIME,'raised roundel rim')


def pilaster(f,x,base,top,wide,lod):
    band(f,x,(base+top)/2,wide,top-base,.30,LIME,.09,'white pier')
    for z,w,h in [(base+.08,wide+.14,.16),(top-.30,wide+.08,.15),(top-.12,wide+.21,.13),(top,wide+.28,.10)]:
        band(f,x,z,w,h,.39,LIME,.12,'pier base or capital')
    if not lod:
        for n in range(3):
            band(f,x+(n-1)*wide*.235,(base+top)/2,wide*.05,top-base-.75,.035,SHADE,.255,'pier flute')


def carved_spandrel(f,x,z,width,lod):
    band(f,x,z,width,.38,.31,LIME,.11,'projecting carved spandrel')
    band(f,x,z,width-.18,.22,.034,SHADE,.282,'recessed spandrel panel')
    if lod:return
    for i in range(7):
        cx=x+(i-3)*(width-.60)/7
        for sign in (-1,1):
            shape=Polygon([(cx,z-.055),(cx+sign*.16,z-.01),(cx+sign*.22,z+.075),(cx+sign*.065,z+.05)])
            f.prism(shape,.301,.326,LIME,'paired leaf relief')


def brick_texture(builder,start):
    """Apply the original repeating mortar tile in physical wall coordinates."""
    for part in builder.parts[start:]:
        if part['material']!=BRICK:continue
        part['texcoords']=[((x+(2*y if abs(x)>HALF-.3 else 0))/1.32,z/.64)for x,y,z in part['vertices']]


def add_building(b,lod):
    f=Facade(b,(-HALF,FACE),(HALF,FACE),'East front')
    wall_start=len(b.parts)
    holes=[]
    for tier,bottom,height,width,centers in [
        (1,.62,2.95,1.11,[PAVILION-.72,PAVILION+.72]),
        (2,4.53,2.74,1.15,[PAVILION-.73,PAVILION+.73]),
        (3,8.12,2.32,.83,[PAVILION-1.02,PAVILION,PAVILION+1.02])]:
        for x in centers:
            holes.append(frame(f,x,bottom,width,height,.22 if tier==3 else .18,lod,True,'pavilion tier '+str(tier)))
    # The narrow attic windows are independent of the pediment, which rises between the sashes.
    for x in [PAVILION-.64,PAVILION+.64,PORTAL]:
        holes.append(frame(f,x,12.02,.68,.91,0,lod,False,'attic sash'))
    for z in [4.53,8.10]:
        holes.append(frame(f,PORTAL,z,1.25,2.45,.24,lod,False,'upper portal window'))
    door=box(PORTAL-1.01,.12,PORTAL+1.01,3.17)
    holes.append(door)
    f.wall(.12,13.52,holes,thickness=.56,material=BRICK)
    f.prism(door,-.52,-.46,IRON,'recessed door leaves')
    for side in (-1,1):
        band(f,PORTAL+side*.51,1.56,.82,2.52,.042,IRON,-.42,'recessed leaf panel')
        pilaster(f,PORTAL+side*1.20,.15,3.37,.33,lod)
    band(f,PORTAL,3.43,3.17,.21,.64,LIME,.23,'portal lintel')
    band(f,PORTAL,3.61,3.31,.15,.63,LIME,.24,'portal cornice')
    f.prism(pentagon(PORTAL,3.68,1.60,.18,.38),.035,.30,LIME,'low crowned doorway crest')
    # The green plaque on the actual door jamb reads 181 in the full 2013 photograph.
    sign_x,sign_z=PORTAL+1.55,1.63
    band(f,sign_x,sign_z,.29,.20,.045,'green enamel',.065,'door number plaque')
    for sx in (sign_x-.071,sign_x+.071):
        one=LineString([(sx-.016,sign_z+.020),(sx,sign_z+.043),(sx,sign_z-.038)]).buffer(.007,cap_style=2,join_style=2)
        f.prism(one,.091,.100,'enamel lettering','number 1')
    for dz in [-.019,.023]:
        ell=xy_scale(Point(sign_x,sign_z+dz).buffer(.022,quad_segs=4 if lod else 8),.85,1,origin='center')
        f.prism(ell.difference(ell.buffer(-.007)),.091,.100,'enamel lettering','two loops of number 8')
    # Paired ground bays have three stone pilasters and a shallow encompassing brick arch.
    for x in [PAVILION-1.43,PAVILION,PAVILION+1.43]:
        pilaster(f,x,.20,3.27,.30,lod)
    outer=opening(PAVILION,.36,3.36,3.72,.58,segments=12 if lod else 30)
    fine=outer.buffer(.043,join_style=2).difference(outer)
    f.prism(fine.intersection(box(PAVILION-1.8,3.18,PAVILION+1.8,4.21)),.014,.079,LIME,'encompassing panel arch')
    for level in [3.77,7.53]:
        for sign in (-1,1):medallion(f,PAVILION+sign*1.58,level,.113,lod)
    for x in [PAVILION-1.45,PAVILION,PAVILION+1.45]:
        pilaster(f,x,4.46,6.89,.29,lod)
    for x in [PAVILION-1.55,PAVILION-.51,PAVILION+.51,PAVILION+1.55]:
        pilaster(f,x,8.04,10.13,.22,lod)
    for z in [4.08,7.70]:
        carved_spandrel(f,PAVILION,z,3.64,lod)
    pediment=pentagon(PAVILION,10.58,1.96,.22,1.28)
    inner=Polygon([(PAVILION-1.49,10.89),(PAVILION+1.49,10.89),(PAVILION,11.67)])
    f.prism(pediment,.02,.20,SHADE,'red-gable stone tympanum')
    f.prism(pediment.difference(inner),.195,.34,LIME,'triangular pediment moulding')
    band(f,PAVILION,10.64,4.12,.14,.56,LIME,.18,'pediment base cornice')
    for z in [.18,4.32,7.86,10.86,13.33,13.54]:
        band(f,0,z,WIDTH+.014,.13 if z<13 else .18,.31 if z<13 else .40,LIME,.07,'continuous facade course')
    for n in range(25):
        z=.53+n*.50
        width=.66 if n%2==0 else .43
        band(f,-HALF+width/2+.02,z,width,.37,.28,LIME,.095,'alternating south corner quoin')
    if not lod:
        for n in range(30):band(f,-HALF+.25+n*(WIDTH-.50)/29,13.33,.115,.17,.31,LIME,.235,'cornice dentil')
        for n in range(12):
            medallion(f,-HALF+.45+n*(WIDTH-.9)/11,13.09,.057,False)
    b.box((0,(FACE+BACK)/2,.12),(WIDTH,BACK-FACE,.22),SHADE,label='continuous stone foundation under street section')
    b.box((0,(FACE+BACK)/2,13.58),(WIDTH,BACK-FACE,.17),ROOF,label='roof section behind stone parapet')
    b.box((0,BACK-.075,6.78),(WIDTH,.15,13.40),BRICK,label='rear section')
    for x in (-HALF+.07,HALF-.07):
        b.box((x,(FACE+BACK)/2,6.78),(.14,BACK-FACE,13.40),BRICK,label='short return of studied front')
    brick_texture(b,wall_start)


PALETTE[BRICK]['texture']=str(Path(__file__).with_name('running-bond.png'))
