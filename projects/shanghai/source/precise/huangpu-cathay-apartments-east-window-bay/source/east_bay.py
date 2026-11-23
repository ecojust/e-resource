"""Build the 4C003 southern row's upper eastern window bay, in metres."""
from pathlib import Path
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
from photo_architecture import Facade

W=5.5
EAST=W/2
BOTTOM=5.55
EAVE=15.56
# Projected left and right jambs on the front, position of the three stone-framed window sets.
LEFT,RIGHT=-2.04,1.24
SILLS=(5.84,9.04,12.40)
HEADS=(7.69,11.04,14.70)
GLAZING=('smoke blue glass','grey glass','muted green glass')
PALETTE={
    'brown facing brick':{'color':[1.,1.,1.],'roughness':.89,'texture':str(Path(__file__).with_name('brown-facing-brick.jpg'))},
    'brick edge':{'color':[.118,.063,.046],'roughness':.89},
    'buff stone':{'color':[.36,.30,.23],'roughness':.88},
    'stone shadow':{'color':[.275,.234,.193],'roughness':.91},
    'stone lip':{'color':[.46,.398,.310],'roughness':.84},
    'sealant':{'color':[.076,.076,.073],'roughness':.75},
    'dark window frame':{'color':[.079,.076,.067],'roughness':.66,'metallic':.20},
    'smoke blue glass':{'color':[.14,.183,.215],'roughness':.38,'metallic':.14},
    'grey glass':{'color':[.177,.183,.177],'roughness':.39,'metallic':.15},
    'muted green glass':{'color':[.144,.177,.159],'roughness':.40,'metallic':.15},
    'painted rack':{'color':[.095,.091,.077],'roughness':.59,'metallic':.25},
    'charcoal sill':{'color':[.075,.073,.067],'roughness':.71},
    'grey eave trim':{'color':[.163,.158,.144],'roughness':.83},
    'eave soffit':{'color':[.338,.312,.258],'roughness':.87},
    'weathered roof':{'color':[.208,.135,.105],'roughness':.95},
}

def pane(f,x,z,w,h,level,index,lod):
    label=f'L{level} light {index}'
    f.box(x,z,w,h,.066,-.164,'sealant',label+' reveal')
    f.box(x,z,w-.049,h-.058,.032,-.127,GLAZING[(level+index)%3],label+' glass')
    for side in (-1,1):
        f.box(x+side*(w-.043)*.5,z,.041,h,.057,-.080,'dark window frame',label+' jamb')
        f.box(x,z+side*(h-.041)*.5,w-.038,.041,.061,-.080,'dark window frame',label+' rail')
    for ratio in ((.39,.69) if level<4 else (.54,)):
        f.box(x,z+(ratio-.5)*h,w-.050,.045,.058,-.078,'dark window frame',label+' transom')
    if not lod:
        f.box(x,z+.055*(h if level<4 else .5),.023,h-.058,.038,-.090,'dark window frame',label+' fine upright')

def profiled_mullion(face,x,width,base,head,label,lod):
    if lod:
        face.box(x,(head+base)/2,width,head-base,.315,-.028,'buff stone',label)
        return
    # The February 2007 photograph and the close winter projection show splays
    # at the external edge of the dividing stone, exposing a narrow front land.
    half=width/2
    section=Polygon([(x-half,.186),(x-half,-.036),(x-half+.024,-.129),
                     (x+half-.024,-.129),(x+half,-.036),(x+half,.186)])
    face.builder.plan_prism(section,base,head,'buff stone',label)
    if head-base>1.9:
        face.box(x,head-.062,width+.033,.085,.258,-.005,'stone shadow',label+' capital shoulder')

def windows(f,story,sill,head,lod):
    width=RIGHT-LEFT
    c=(LEFT+RIGHT)/2
    h=head-sill
    jamb=.121
    mull=.132
    f.box(c,sill-.085,width+.37,.17,.36,.028,'stone lip',f'L{story} projecting sill')
    f.box(c,head+.11,width+.34,.22,.29,-.004,'buff stone',f'L{story} stone head')
    for xx in (LEFT-jamb/2,RIGHT+jamb/2):
        f.box(xx,(sill+head)/2,jamb,h+.044,.29,-.030,'buff stone',f'L{story} outer jamb')
    for k in range(4):
        x=LEFT+(k+.5)*width/4
        pane(f,x,sill+h/2,width/4-mull*.90,h,story,k+1,lod)
        if k<3:
            profiled_mullion(f,LEFT+(k+1)*width/4,mull,sill-.032,head+.032,f'L{story} mullion {k+1}',lod)
    if not lod:
        f.box(c,sill-.147,width+.40,.052,.405,.032,'stone shadow',f'L{story} sill drip')
        for xx in (LEFT-.12,RIGHT+.12):
            f.box(xx,(sill+head)/2,.045,h+.046,.21,.021,'stone shadow',f'L{story} jamb rebate')
        for xx in (LEFT+.28*width,LEFT+.72*width):
            f.box(xx,head+.105,.018,.199,.017,.147,'stone shadow',f'L{story} lintel joint')

def guard(f,x,z,width,projection,height,lod,label):
    # Three separate horizontal blades and the end returns can be seen in both street dates.
    f.box(x,z+.035,width, .07,projection,.5*projection,'charcoal sill',label+' floor')
    for k in range(3):
        h=z+.145+k*(height-.17)/2
        f.box(x,h,width,.074,.043,projection-.004,'painted rack',label+' horizontal band')
        for side in (-1,1):
            f.box(x+side*(width-.040)/2,h,.042,.074,projection,.5*projection,'painted rack',label+' end return')
    for side in (-1,1):
        xx=x+side*(width-.077)/2
        f.box(xx,z+height/2,.043,height,.046,projection-.024,'painted rack',label+' post')
        if not lod:
            f.builder.tube([f.point(xx,z-.19,.044),f.point(xx,z+.015,projection-.045)],.029,'painted rack',6,label+' lower bracket')

def add_bay(b,lod=False):
    front=Facade(b,(-EAST,0),(EAST,0),'street')
    end=Facade(b,(EAST,0),(EAST,.86),'east return')
    cutouts=[box(LEFT-.119,z-.06,RIGHT+.119,h+.06)for z,h in zip(SILLS,HEADS)]
    wall=box(-EAST,BOTTOM,EAST,EAVE).difference(unary_union(cutouts))
    for face,shape in ((front,wall),(end,box(-.43,BOTTOM,.43,EAVE))):
        idx=len(b.parts)
        face.prism(shape,-.245,0,'brown facing brick','running-bond wall')
        for part in b.parts[idx:]:
            part['texcoords']=[[max(0.,min(1.,((v[0]+2.79) if face is front else (v[1]+2.78))/5.6)),
                                max(0.,min(1.,1-(v[2]-5.50)/11.30))]for v in part['vertices']]
    for layer,(sill,head)in enumerate(zip(SILLS,HEADS),2):
        windows(front,layer,sill,head,lod)
    for i in range(24):
        z=BOTTOM+.20+i*.418
        if z+.208>EAVE:break
        w=.43 if i%2 else .71
        front.box(EAST-w/2,z,w,.404,.105,.012,'buff stone','corner quoin face')
        d=.31 if i%2 else .54
        end.box(-.43+d/2,z,d,.404,.107,.011,'buff stone','corner quoin return')
    # Upper racks at the inner pair, plus the narrower rack on the end pier.
    for z,span,s in ((8.94,1.53,'third storey'),(12.29,1.52,'fourth storey')):
        guard(front,-.52,z,span,.47,.43,lod,s+' centre rail')
    guard(front,2.28,12.28,.85,.36,.41,lod,'fourth storey corner rail')
    # Only the east bay's real fascia, soffit and short return are supplied.
    b.box((0,.15,15.64),(W+.11,.95,.16),'eave soffit',label='slightly projecting soffit')
    b.box((0,.13,15.78),(W+.22,1.14,.13),'grey eave trim',label='eave fascia')
    b.box((0,.11,15.91),(W+.29,1.23,.095),'eave soffit',label='upper cornice lip')
    b.box((0,.105,16.00),(W+.32,1.27,.09),'grey eave trim',label='outer drip')
    # Clip the roof behind the short strip supported by this measured facade.
    profile=box(-W*.5,0,W*.5,.96)
    def tilted(x,y,v):return (x,y-.24,16.035+.345*y+v)
    b.prism(profile,0,.048,tilted,'weathered roof','short roof return')
