"""Four-level brick teaching wings and the grass court's three-arch auditorium entrance."""
from math import pi
import numpy as np
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
from photo_architecture import Facade,opening
from roofs import STONE,DARK,GLASS,PIGMENT,BLUE,TILE,ROLL,TIMBER

BRICK='warm red face brick'
BASE='grey masonry plinth'
TRIM='light dressed granite'
GOLD='old gold paint'
FIELD='dull ochre spandrel'
ASPHALT='grey flat roof'
RED='red brown window panels'
PALETTE={
    BRICK:(.452,.149,.102),BASE:(.42,.405,.372),STONE:(.77,.757,.69),TRIM:(.63,.629,.59),
    DARK:(.105,.112,.104),GLASS:(.19,.275,.306),PIGMENT:(.53,.093,.058),BLUE:(.070,.239,.232),
    TILE:(.685,.36,.094),ROLL:(.804,.48,.151),TIMBER:(.26,.163,.087),GOLD:(.69,.49,.20),
    FIELD:(.47,.214,.14),ASPHALT:(.40,.404,.382),RED:(.45,.187,.139)}
PALETTE={k:{'color':list(v),'roughness':.31 if k in (TILE,ROLL,GLASS) else .76}for k,v in PALETTE.items()}


def light(f,u,z,w,h,lod,columns=2,rows=3,trim=False):
    q=box(u-w/2,z,u+w/2,z+h)
    f.prism(q.buffer(.009,join_style=2),-.27,-.24,GLASS,'glazing')
    inset=q.buffer(-.058,join_style=2)
    bars=[box(u-w/2+w*i/columns-.021,z,u-w/2+w*i/columns+.021,z+h)for i in range(1,columns)]
    if not lod:bars +=[box(u-w/2,z+h*i/rows-.022,u+w/2,z+h*i/rows+.022) for i in range(1,rows)]
    panes=inset.difference(unary_union(bars)) if bars else inset
    f.prism(q.difference(panes),-.19,-.10,DARK,'window frames')
    if trim:f.prism(q.buffer(.09,join_style=2).difference(q),-.035,.065,TRIM,'window jambs')
    return q


def painted(f,u,z,w,h,lod):
    f.box(u,z,w,h,.18,.12,BLUE,'painted frieze')
    f.box(u,z+h*.35,w,.055,.20,.14,GOLD,'ochre fillets')
    if not lod:
        inset=min(.22,w*.10)
        for x in np.linspace(u-w/2+inset,u+w/2-inset,max(2,round(w/.85))):
            q=Polygon([(x-.120,z),(x,z-.113),(x+.12,z),(x,z+.113)])
            f.prism(q,.207,.233,GOLD,'frieze lozenges')
    # In the close frontal photograph three short painted timber layers project below the canopy.
    # Their colour bands and bracket profile are interpreted, not traced as individual motifs.
    count=max(1,round(w/3.5))
    for x in np.linspace(u-w/2+w/count*.5,u+w/2-w/count*.5,count):
        f.box(x,z-h*.63,.31,.14,.27,.12,TIMBER,'painted bracket blocks')
        f.box(x,z-h*.41,.50,.105,.34,.16,PIGMENT,'painted bracket arms')
        if not lod:
            f.box(x,z-h*.25,.66,.088,.41,.19,BLUE,'bracket caps')


def rail(f,u,z,width,lod,material=STONE):
    n=max(1,round(width/2.3))
    for i in range(n):
        center=u-width/2+(i+.5)*width/n;w=width/n-.18
        # Recessed lozenge openings read through the photographed pale stone balustrades.
        holes=[]
        for dx in (-.23,.23):
            xx=center+dx*w*.90
            holes.append(Polygon([(xx-.115,z+.46),(xx,z+.34),(xx+.115,z+.46),(xx,z+.58)]))
        slab=box(center-w/2,z+.14,center+w/2,z+.74)
        f.prism(slab.difference(unary_union(holes)),-.17,.045,material,'cut stone balustrade')
    for k in range(n+1):
        x=u-width/2+k*width/n
        f.box(x,z+.46,.175,.92,.32,-.01,material,'balustrade piers')
        if not lod:f.box(x,z+.94,.214,.065,.356,-.01,material,'pier cap')
    f.box(u,z+.74,width+.02,.085,.315,-.012,material,'balustrade rail')


def brick_face(f,lo,hi,holes,lod):
    skin=f.wall(lo,hi,holes,.33,BRICK)
    if not lod:
        bars=[]
        for h in np.arange(lo+.32,hi,.49):
            band=box(-f.length/2,h-.007,f.length/2,h+.007);bars.append(band)
        joints=skin.intersection(unary_union(bars))
        if not joints.is_empty:f.prism(joints,.001,.004,FIELD,'brick bed joints')
    f.box(0,.23,f.length,.46,.39,-.04,BASE,'stone skirting')
    f.box(0,hi-.16,f.length+.03,.24,.46,-.015,TRIM,'roof cornice')


def standard(f,lod,n,upper=False,towers=False):
    ztop=13.04 if not upper else 15.55
    spacing=f.length/n
    q=[]
    for k in range(n):
        u=(k+.5)*spacing-f.length/2
        for level,(zz,hh)in enumerate(((.92,2.30),(5.02,2.10),(8.63,2.18))):
            q.append(light(f,u,zz,min(1.55,spacing*.47),hh,lod,2,3,trim=(level==0 and towers)))
        if upper:q.append(light(f,u,13.21,min(2.68,spacing*.80),1.44,lod,3,2))
    brick_face(f,.12,ztop,q,lod)
    f.box(0,12.26,f.length,.19,.45,.011,TRIM,'parapet sill')
    if not upper:rail(f,0,12.33,f.length-.15,lod,TRIM)


def upper_galleries(f,lod):
    q=[];half=f.length/2
    # The history identifies eleven bays. The middle three are the entrance section, framed on either side.
    for u in np.linspace(-19.2,19.2,11):
        if abs(u)<5.85:continue
        q.append(light(f,u,13.22,2.66,1.22,lod,3,2))
    f.wall(12.74,15.55,q,.24,BRICK)
    for u in np.linspace(-21.1,21.1,12):
        p=f.point(u,0,.115)
        f.builder.lathe(p[:2],[(12.69,.14),(12.83,.22),(13.08,.161),(15.08,.147),(15.19,.233)],PIGMENT,10 if lod else 18,'Upper gallery / lacquered columns')
    painted(f,0,15.24,f.length,.45,lod)


def court_elevation(b,lod,xcenter,y):
    f=Facade(b,(xcenter+21.75,y),(xcenter-21.75,y),'North lawn/auditorium')
    holes=[]
    # Two rows of tall windows in the red-brick walls flank the three arched entry bays.
    for sign in (-1,1):
        for xx in (10.36,12.65,15.00,17.38,19.78):
            for zz,hh in ((.91,2.17),(5.10,1.94),(8.91,2.21)):
                holes.append(light(f,sign*xx,zz,1.42,hh,lod))
    center_cut=box(-9.24,.10,9.24,15.55)
    brick_face(f,.12,12.78,[*holes,center_cut],lod)
    upper_galleries(f,lod)
    for x in (-7.04,7.04):
        left=x-2.05;right=x+2.05
        ff=Facade(b,f.point(left,0,.45)[:2],f.point(right,0,.45)[:2],'North lawn/stone pylons')
        q=[light(ff,.0,zz,ww,hh,lod,1,2)for zz,ww,hh in [(1.04,.73,2.12),(6.10,.63,1.57),(10.18,.64,1.72),(13.87,.55,.63)]]
        ff.wall(.09,15.40,q,.66,STONE)
        ff.beam(15.49,.17,.17,STONE)
    # Three open arch reveals terminate on recessed timber/glass doors.
    port=Facade(b,f.point(-5.03,0,.55)[:2],f.point(5.03,0,.55)[:2],'North lawn/three arched doors')
    arches=[]
    for xx in (-3.30,0,3.30):
        sh=opening(xx,.21,1.94,2.90,.97,14 if lod else 24);arches.append(sh)
        port.prism(sh.buffer(.011),-.85,-.82,TIMBER,'recessed doors')
        port.prism(sh.intersection(box(xx-.94,1.34,xx+.94,3.22)),-.813,-.80,GLASS,'arched top lights')
        port.box(xx,1.69,.06,2.65,.12,-.74,DARK,'door mullions')
        port.prism(sh.buffer(.13).difference(sh).intersection(box(xx-1.2,.22,xx+1.2,3.37)),-.025,.096,TRIM,'architrave')
    port.wall(.10,4.84,arches,.69,STONE)
    port.beam(4.73,.19,.31,TRIM)
    rail(port,0,4.89,10.08,lod)
    for zz,hh in ((5.51,2.15),(9.12,2.33)):
        q=[light(f,xx,zz,2.25,hh,lod,3,3)for xx in (-3.19,0,3.19)]
        lo=5.07 if zz<8 else 8.43;hi=8.42 if zz<8 else 12.48
        f.prism(box(-4.96,lo,4.96,hi).difference(unary_union(q)),-.32,-.02,RED,'hall spandrels')
    for xx in (-4.80,-1.61,1.61,4.80):
        p=f.point(xx,0,.36)
        b.lathe(p[:2],[(5.20,.23),(5.35,.25),(5.48,.17),(11.98,.149),(12.16,.247)],PIGMENT,12 if lod else 20,'North lawn/red hall columns')
    painted(f,0,12.42,10.10,.52,lod)
    # The canopy is below the main roof and visibly projects between the two white pylons.
    b.box((xcenter,y+.41,12.86),(10.10,1.34,.14),TIMBER,label='North lawn/canopy soffit')
    for k in range(4):
        a=k/4;c=(k+1)/4
        v=[(xcenter-5.06,y-.17+a*1.34,13.45-.52*a),(xcenter+5.06,y-.17+a*1.34,13.45-.52*a),
           (xcenter+5.06,y-.17+c*1.34,13.45-.52*c),(xcenter-5.06,y-.17+c*1.34,13.45-.52*c)]
        b.add(v,[(0,1,2,3)],TILE,'North lawn/short eave')
    for x in np.arange(-4.95,5.0,.34 if not lod else .8):
        b.tube([(x+xcenter,y-.17,13.49),(x+xcenter,y+1.17,12.98)],.044,ROLL,6,'North lawn/canopy tile')
    for k in range(4):
        step=(4-k)*.25
        b.box((xcenter,y+.56+step/2,(k+1)*.034),(9.96,step,.068*(k+1)),BASE,label='North lawn/steps')
