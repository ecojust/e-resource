"""Five-storey riverside elevation of the former Butterfield & Swire Shanghai office."""
from math import cos, pi, sin
from pathlib import Path
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from shapely import set_precision
from photo_architecture import Facade
from brick_mapping import BRICK,brick_uv

TERRA='Rust-red cut masonry'
TERRADARK='Shadowed red brick voussoirs'
STONE='Weathered ochre sandstone trim'
LIME='Pale limestone sill and capitals'
SHADOW='Brown moulding and coping'
GLASS='Blue grey restored window glass'
DARK='Deep green bronze door glazing'
SASH='Black painted metal sash'
IRON='Black balcony rail and door iron'
COPPER='Copper coloured flag socket'
PALETTE={
    BRICK:{'color':[1.,1.,1.],'roughness':.90,'texture':str(Path(__file__).with_name('swire-river-brick.png'))},
    TERRA:{'color':[.424,.126,.072],'roughness':.84},TERRADARK:{'color':[.332,.103,.066],'roughness':.89},
    STONE:{'color':[.60,.55,.43],'roughness':.83},LIME:{'color':[.735,.698,.599],'roughness':.80},
    SHADOW:{'color':[.325,.276,.237],'roughness':.85},GLASS:{'color':[.137,.207,.246],'roughness':.34,'metallic':.18},
    DARK:{'color':[.073,.111,.101],'roughness':.33,'metallic':.25},SASH:{'color':[.120,.144,.140],'roughness':.56,'metallic':.22},
    IRON:{'color':[.110,.126,.123],'roughness':.61,'metallic':.38},COPPER:{'color':[.536,.465,.358],'roughness':.66,'metallic':.52}
}
LENGTH=30.75953804425162
AXES=(3.22,7.11,10.88,15.34,19.67,23.76,27.65)
CENTRE=AXES[3]
# Masonry heads and sills from photographed levels, in metres above the pavement.
SILLS=(1.48,6.00,10.90,15.40,21.51)
HEADS=(4.87,9.55,14.50,18.47,23.72)
WIDTHS=(2.21,2.38,2.43,2.45,2.25)

def arch(x,w,sill,top,segments=24):
    radius=w/2;spring=top-radius
    points=[(x+radius*cos(i*pi/segments),spring+radius*sin(i*pi/segments)) for i in range(segments+1)]
    return Polygon([(x-radius,sill),(x+radius,sill),*points])

def voussoirs(face,x,spring,radius,outer,lod):
    count=11 if lod else 19
    for j in range(count):
        a=pi*j/count+.007;b=pi*(j+1)/count-.007
        poly=Polygon([(x+radius*cos(a),spring+radius*sin(a)),(x+outer*cos(a),spring+outer*sin(a)),(x+outer*cos(b),spring+outer*sin(b)),(x+radius*cos(b),spring+radius*sin(b))])
        face.prism(poly,.031,.090,TERRA if j%3 else TERRADARK,'Radial brick headers')
    face.prism(Polygon([(x-.12,spring+radius-.02),(x+.12,spring+radius-.02),(x+.17,spring+outer+.12),(x-.17,spring+outer+.12)]),.075,.182,LIME,'Stone window keystones')

def railing(face,x,width,sill,lod):
    a=x-width/2+.06;b=x+width/2-.06
    for h,r in ((.07,.027),(.66,.025),(.84,.039)):
        face.line((a,sill+h,.11),(b,sill+h,.11),r,IRON,5 if lod else 7,'Gallery horizontal rails')
    n=max(4,round((b-a)/(.29 if lod else .21)))
    for j in range(n+1):
        u=a+(b-a)*j/n
        face.line((u,sill+.07,.11),(u,sill+.82,.11),.019,IRON,5 if lod else 6,'Gallery iron uprights')
        if j<n and not lod:
            step=(b-a)/n
            ring=[face.point(u+step*.50+step*.41*cos(i*2*pi/12),sill+.43+.20*sin(i*2*pi/12),.11)for i in range(13)]
            face.builder.tube(ring,.012,IRON,5,face.label+'/Gallery loopwork')

def glazed(face,x,width,bottom,top,round_head,lod,door=False,depth=-.20):
    n=16 if lod else 28
    opening=arch(x,width,bottom,top,n) if round_head else box(x-width/2,bottom,x+width/2,top)
    face.prism(opening,depth-.082,depth-.063,DARK if door else GLASS,'Entrance glass' if door else 'Restored recessed glazing')
    outer=opening.difference(opening.buffer(-.07))
    parts=[outer]
    for offset in ([0.]if door else [-width*.24,0.,width*.24]):
        parts.append(box(x+offset-.026,bottom+.02,x+offset+.026,top).intersection(opening))
    spring=top-width/2
    rails=[spring] if round_head else [top-.64]
    rails.append(bottom+.80 if door else bottom+(top-bottom)*.44)
    for z in rails:parts.append(box(x-width/2,z-.032,x+width/2,z+.032).intersection(opening))
    if round_head:
        for ang in (pi/4,3*pi/4):
            ray=LineString([(x,spring),(x+width*.5*cos(ang),spring+width*.5*sin(ang))]).buffer(.019,cap_style=2)
            parts.append(ray.intersection(opening))
    face.prism(unary_union(parts),depth-.050,depth+.009,SASH,'Entrance double leaves and fan' if door else 'Muntins, transoms and fanlights')
    return opening

def scroll_capital(face,x,z,width,lod):
    face.box(x,z-.10,width*.90,.20,.17,.106,STONE,'Capital neck')
    face.box(x,z+.095,width*1.12,.10,.23,.155,LIME,'Capital abacus')
    for sign in (-1,1):
        cx=x+sign*width*.35
        pts=[]
        n=10 if lod else 20
        for i in range(n+1):
            t=i/n;ang=sign*(2.45*pi*t+pi*.14);rad=width*(.17-.129*t)
            pts.append(face.point(cx+rad*cos(ang),z+rad*sin(ang),.246))
        face.builder.tube(pts,.021,LIME,5 if lod else 7,face.label+'/Capital volutes')

def timberless_window(face,bay,level,lod):
    x=AXES[bay];sill=SILLS[level];top=HEADS[level];width=WIDTHS[level]
    if bay==3 and level in (3,4):
        cuts=[]
        for side in (-1,1):
            mid=x+side*.608;w=.96
            cuts.append(glazed(face,mid,w,sill,top,True,lod,depth=-.24))
            voussoirs(face,mid,top-w/2,w/2,w/2+.15,lod)
            if level==3:railing(face,mid,w,sill,lod)
        for u in (x-1.19,x,x+1.19):scroll_capital(face,u,top-.52,.34,lod)
        face.box(x,sill-.055,2.76,.095,.26,.060,LIME,'Paired aperture sill')
        return cuts
    doorway=bay==3 and level==0
    if doorway:sill=.11;width=2.38
    rounded=level!=2 or bay==3
    if bay==3 and level==2:top=14.35
    cut=glazed(face,x,width,sill,top,rounded,lod,door=doorway,depth=-.42 if doorway else -.21)
    if rounded:
        if bay==3 and level in (0,1):
            outer=arch(x,width+.55,sill,top+.24,16 if lod else 32)
            face.prism(outer.difference(cut),.026,.20,STONE,'Stone central portal archivolts')
        else:voussoirs(face,x,top-width/2,width/2,width/2+.17,lod)
    else:
        face.box(x,top+.058,width+.37,.14,.235,.085,LIME,'Rectangular third-storey lintels')
        for u in (x-width/2,x+width/2):face.box(u,top-.16,.20,.31,.14,.11,STONE,'Lintel end brackets')
    if not doorway:
        face.box(x,sill-.057,width+.21,.113,.29,.055,STONE,'Projecting window sills')
        if level in (1,2,3):railing(face,x,width,sill,lod)
    else:
        face.box(x,.075,width+.30,.15,.75,.14,STONE,'Street portal sill')
        for side in (-1,1):
            for i in range(5 if lod else 9):
                cy=1.45+i*(1.65/(4 if lod else 8));u=x+side*.52
                pts=[face.point(u+.26*cos(pi*2*k/12),cy+.13*sin(pi*2*k/12),-.362)for k in range(13)]
                face.builder.tube(pts,.019,IRON,5,'River front/Entry wrought-iron scroll bands')
    return [cut]

def central_pediment(face,z,w,h,lod,label):
    x=CENTRE;r=w/2;n=18 if lod else 36
    pts=[(x+r*cos(i*pi/n),z+h*sin(i*pi/n))for i in range(n+1)]
    field=Polygon([(x-r,z-.06),(x+r,z-.06),*pts])
    face.prism(field,-.15,.30,STONE,label+' face')
    face.box(x,z-.05,w+.27,.15,.55,.13,LIME,label+' moulded base')
    arc=LineString(pts).buffer(.066,cap_style=2,join_style=1)
    face.prism(arc,.28,.40,LIME,label+' arc moulding')
    if not lod:
        crown=LineString([(x+(r-.19)*cos(i*pi/n),z+.04+(h-.20)*sin(i*pi/n))for i in range(n+1)]).buffer(.025,cap_style=2)
        face.prism(crown,.305,.333,SHADOW,label+' recessed bead')
    if z>20:
        for u in (x-.28,x+.28):face.box(u,z+.48,.14,.50,.15,.32,LIME,'Crest relief supports')
        face.prism(Polygon([(x-.24,z+.53),(x,z+.29),(x+.24,z+.53),(x+.21,z+.78),(x-.21,z+.78)]),.30,.38,STONE,'Unlettered crest relief')
    else:
        for i in range(5 if lod else 9):
            ang=pi*(i+1)/(6 if lod else 10)
            face.line((x+.25*cos(ang),z+.10+.09*sin(ang),.303),(x+(r*.77)*cos(ang),z+.06+h*.65*sin(ang),.306),.019,LIME,5,'Pediment radial relief')

def add_building(builder,lod=False):
    face=Facade(builder,(-1,0),(1,0),'River front')
    cuts=[]
    for bay in range(7):
        for level in range(5):
            face.label=f'Bay {bay+1}, storey {level+1}'
            cuts.extend(timberless_window(face,bay,level,lod))
    face.label='River front'
    holes=set_precision(unary_union(cuts),.00001)
    def pane(u0,u1,z0,z1,material,d):
        poly=set_precision(box(u0,z0,u1,z1),.00001).difference(holes)
        if not poly.is_empty:face.prism(poly,-.55,d,material,'Outer brick wall' if material==BRICK else 'Jointed rusticated base')
    # Shallow channels articulate the large ruled blocks around the lower two rows.
    backing=box(0,0,LENGTH,10.52).difference(holes)
    face.prism(backing,-.55,-.046,TERRADARK,'Deep joints below the main ledge')
    for row in range(18):
        low=row*10.52/18;top=(row+1)*10.52/18-.035
        span=1.45
        start=-span/2 if row%2 else 0.
        while start<LENGTH:
            end=min(start+span,LENGTH)
            if end>max(start+.022,0):pane(max(start+.022,0),end,low,top,TERRA,.00)
            start+=span
    pane(0,LENGTH,10.52,26.20,BRICK,0)
    pilasters=[.61,5.19,9.03,13.16,17.54,21.72,25.76,30.14]
    for u in pilasters:
        for bottom,top,width,d in ((10.68,19.45,.59,.122),(20.16,24.84,.46,.100)):
            face.box(u,(bottom+top)/2,width,top-bottom,.21,d,BRICK,'Tall brick pilaster strips')
            scroll_capital(face,u,top-.13,width+.16,lod)
        for z,width in ((10.83,.54),(15.02,.48),(19.42,.60),(24.81,.55)):
            face.box(u,z,width,.105,.244,.103,LIME,'Pilaster stone bands')
    for u in (CENTRE-2.28,CENTRE+2.28):
        face.box(u,5.22,.46,10.44,.25,.08,STONE,'Great portal side piers')
        for z in (5.69,10.40):face.box(u,z,.70,.19,.41,.15,LIME,'Portal pilaster caps')
    for z,depth,height,mat in ((.37,.22,.16,STONE),(5.69,.36,.18,LIME),(10.49,.45,.17,LIME),(14.91,.26,.13,STONE),(19.53,.45,.18,SHADOW),(19.74,.51,.16,LIME),(19.94,.37,.12,SHADOW),(24.93,.46,.18,SHADOW),(25.11,.51,.15,LIME),(26.19,.27,.13,TERRA)):
        face.box(LENGTH/2,z,LENGTH+.10,height,depth,depth/2-.05,mat,'Continuous storey courses and cornice')
    central_pediment(face,10.50,4.49,1.16,lod,'Portal semicircular pediment')
    central_pediment(face,26.15,4.51,1.58,lod,'Parapet pediment')
    face.box(LENGTH/2,26.14,LENGTH,.16,1.47,-.61,TERRA,'Roof edge return')
    face.line((CENTRE,27.56,-.20),(CENTRE,31.34,-.20),.041,COPPER,7 if lod else 10,'Observed flag mast')
    for item in builder.parts:
        if item['material']==BRICK:
            item['texcoords']=[(u,1-v)for u,v in (brick_uv(item['label'],p) for p in item['vertices'])]
