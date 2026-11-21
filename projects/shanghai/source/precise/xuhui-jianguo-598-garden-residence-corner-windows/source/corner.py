"""Measure visible divisions in Antigng's February 2018 street photograph."""
from pathlib import Path
from random import Random
from PIL import Image, ImageFilter
from shapely.geometry import Polygon, box
from photo_architecture import Facade

WALL = 'Warm grey roughcast'
EDGE = 'Grey formed concrete'
UNDER = 'Shadowed concrete soffit'
BRICK = 'Russet-brown facing brick'
BRICK_DARK = 'Darker russet facing brick'
JOINT = 'Recessed brick joint'
STEEL = 'Deep green painted steel'
BEAD = 'Green glazing bead'
GLASS = 'Muted green glazing'
GLASS_LIGHT = 'Paler reflected glazing'
PALETTE = {
    name: {'color': color, 'roughness': roughness, 'metallic': metal}
    for name, color, roughness, metal in [
        (WALL, [.69,.61,.46], .97, 0),
        (EDGE, [.34,.33,.29], .88, 0), (UNDER, [.26,.25,.23], .92, 0),
        (BRICK, [.29,.108,.069], .95, 0), (BRICK_DARK, [.255,.093,.062], .96, 0),
        (JOINT, [.135,.066,.043], .98, 0), (STEEL, [.054,.122,.087], .57, .18),
        (BEAD, [.088,.156,.112], .57, .12), (GLASS, [.112,.181,.160], .25, .24),
        (GLASS_LIGHT, [.174,.255,.231], .24, .2)]
}
LEFT, RIGHT, END = -2.04, 1.87, 1.68
GLAZING_START, PIER_START = -1.66, 1.19
SIDE_BEGIN, SIDE_END = .135, 1.22
LEVELS = (.24, 3.56)
WINDOW_HEIGHT = 1.72
ZTOP = 5.84

def make_texture(path):
    rng = Random(598)
    coarse = Image.new('L',(48,44))
    coarse.putdata([rng.randint(200,252) for _ in range(48*44)])
    smooth = coarse.resize((240,220),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(1.3))
    grain = Image.new('L',smooth.size)
    grain.putdata([max(110,min(255,p+rng.randint(-21,21))) for p in smooth.getdata()])
    grain.convert('RGB').save(path)

def wall_face(b, a, c, label, bounds):
    face = Facade(b, a, c, label)
    center = (bounds[0]+bounds[1])/2
    def u(value): return value-center
    return face, u

def casement(face, x0, x1, bot, label, majors, detailed):
    """Paired tall casement leaves below a wider top light in each street bay."""
    height = WINDOW_HEIGHT
    xmid=(x0+x1)/2
    width=x1-x0
    top=bot+height
    face.box(xmid, bot+height/2, width+.018, height+.018,.024,-.125,
             GLASS if label.startswith('Lower') else GLASS_LIGHT, label+' glazing')
    def strip(a,b,c,d,material,depth,label2):
        face.box((a+c)/2,(b+d)/2,c-a,d-b,.047,depth,material,label+' '+label2)
    trim=.041
    for index,x in enumerate((x0+trim/2,x1-trim/2)):
        strip(x-trim/2,bot,x+trim/2,top,STEEL,-.062,'outer jamb '+str(index+1))
    for idx,z in enumerate((bot+trim/2,top-trim/2)):
        strip(x0+trim,z-trim/2,x1-trim,z+trim/2,STEEL,-.062,('lower outer rail','upper outer rail')[idx])
    light=bot+height*.775
    for k in range(1,majors):
        x=x0+width*k/majors
        strip(x-.023,bot+trim,x+.023,top-trim,STEEL,-.060,'principal mullion '+str(k))
    strip(x0+trim,light-.020,x1-trim,light+.020,STEEL,-.067,'continuous top transom')
    for k in range(majors):
        a=x0+width*k/majors+.026
        c=x0+width*(k+1)/majors-.026
        middle=(a+c)/2
        strip(middle-.012,bot+trim,middle+.012,light-.020,STEEL,-.074,'meeting stile '+str(k+1))
        for fraction in (.265,.52):
            z=bot+height*fraction
            strip(a,z-.010,c,z+.010,STEEL,-.084,f'paired sash {k+1} glazing bar {fraction:.3f}')
        if detailed:
            for leaf,(start,end) in enumerate(((a,middle),(middle,c))):
                ring=box(start+.006,bot+.043,end-.006,light-.025)
                inside=ring.buffer(-.012,join_style=2)
                face.prism(ring.difference(inside),-.099,-.080,BEAD,f'{label} putty fillet {k+1}-{leaf+1}')

def horizontal(b, footprint, low, high, material, label):
    b.prism(footprint, low, high, lambda x,y,z:(x,y,z), material, label)

def ledge(b, rear_x, rear_y, width, z, thickness, label):
    outline=[(rear_x,-width),(RIGHT+width,-width),(RIGHT+width,rear_y),
             (RIGHT-.13,rear_y),(RIGHT-.13,.13),(rear_x,.13)]
    fp=Polygon(outline)
    horizontal(b,fp,z,z+thickness,EDGE,label+' flat cast edge')
    horizontal(b,fp.buffer(-.016,join_style=2),z-.017,z,UNDER,label+' underside')

def courses(b, bot, detailed, label):
    # The 2018 photograph shows horizontal bed joints continuing across a narrow return.
    front=Polygon([(PIER_START,-.014),(RIGHT+.018,-.014),(RIGHT+.018,SIDE_BEGIN),
                   (RIGHT-.09,SIDE_BEGIN),(RIGHT-.09,.070),(PIER_START,.070)])
    horizontal(b, front,bot,bot+WINDOW_HEIGHT,JOINT,label+' backing')
    step=WINDOW_HEIGHT/17
    for j in range(17):
        lo=bot+j*step+.006; hi=bot+(j+1)*step-.005
        material=BRICK_DARK if j%7 in (2,6) else BRICK
        fp=front.buffer(.010+(j%3)*.0008,join_style=2)
        horizontal(b,fp,lo+.003,hi-.003,material,label+' course '+str(j+1))
        if detailed:
            inset=fp.buffer(-.002,join_style=2)
            horizontal(b,inset,lo,lo+.003,material,label+' lower arris '+str(j+1))
            horizontal(b,inset,hi-.003,hi,material,label+' upper arris '+str(j+1))

def add_building(b,lod):
    front,fu=wall_face(b,(LEFT,0),(RIGHT,0),'Street face',(LEFT,RIGHT))
    side,su=wall_face(b,(RIGHT,0),(RIGHT,END),'Return face',(0,END))
    # Drop both wall faces clear of the corner infill over each whole window opening.
    for f,coordinate,start,end in ((front,fu,GLAZING_START,RIGHT+.0001),
                                   (side,su,-.0001,SIDE_END)):
        openings=[box(coordinate(start),bot,coordinate(end),bot+WINDOW_HEIGHT) for bot in LEVELS]
        outline=box(su(.17),0,su(END),ZTOP-.15) if f is side else None
        f.wall(0,ZTOP-.15,openings,thickness=.17,material=WALL,outline=outline)
    for index,bot in enumerate(LEVELS):
        label=('Lower','Upper')[index]
        casement(front,fu(GLAZING_START),fu(PIER_START),bot,label+' street',3,not lod)
        casement(side,su(SIDE_BEGIN),su(SIDE_END),bot,label+' return',1,not lod)
        courses(b,bot,not lod,label+' russet corner')
        ledge(b,GLAZING_START-.039,SIDE_END+.030,.061,bot-.052,.051,label+' sill')
    ledge(b,GLAZING_START-.22,SIDE_END+.27,.24,LEVELS[0]+WINDOW_HEIGHT+.014,.094,
          'Intermediate concrete hood')
    ledge(b,LEFT,END,.375,ZTOP-.151,.151,'Continuous roof cornice')
    for part in b.parts:
        if part['material'] == WALL:
            b.palette[WALL]['texture']=str(Path(__file__).with_name('roughcast.png'))
            v=part['vertices']
            sideward=abs(max(q[0] for q in v)-min(q[0] for q in v))<.5
            part['texcoords']=[[(.03+.94*y/END) if sideward else .03+.94*(x-LEFT)/(RIGHT-LEFT),
                               .02+.96*(1-z/ZTOP)] for x,y,z in v]
