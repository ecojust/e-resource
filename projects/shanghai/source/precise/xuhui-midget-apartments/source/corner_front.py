"""Street corner of Midget Apartments, 115 Wukang Road, in metres."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

P = json.loads(Path(__file__).with_name('parameters.json').read_text())
WIDTH = P['front_at_curb_width_m']
ROOF = P['parapet_height_m']
FRONT_LEFT, FRONT_RIGHT = (-WIDTH / 2, 0), (WIDTH / 2, 0)
PATH = [tuple(P['left_return_end']), FRONT_LEFT, FRONT_RIGHT, tuple(P['right_return_end'])]
SHELL_DEPTH = P['section_depth_m']
GRIT = 'silver grey roughcast'; BASE = 'mottled grey plinth'
STONE = 'light artificial stone'; TILE = 'pale textured panels'
DARK = 'charcoal steel casements'; GREEN = 'grey green apartment glass'
OLIVE = 'green glass in lower broad window'
SHOP = 'warm shop front timber'; VISOR = 'dark narrow shop canopy'
RAIL = 'wrought metal window guard'; BRICK = 'shadowed reveal'
COPING = 'light coping'; ROOFING = 'grey roof covering'; CUT = 'section finish'
PALETTE = {
    GRIT: dict(color=[.637,.635,.613],roughness=.96),
    BASE: dict(color=[.455,.46,.447],roughness=.93),
    STONE: dict(color=[.792,.776,.704],roughness=.83),
    TILE: dict(color=[.846,.824,.734],roughness=.9),
    DARK: dict(color=[.146,.166,.166],roughness=.54,metallic=.20),
    GREEN: dict(color=[.368,.434,.452],roughness=.37,metallic=.15),
    OLIVE: dict(color=[.32,.418,.357],roughness=.39,metallic=.14),
    SHOP: dict(color=[.52,.301,.147],roughness=.62),
    VISOR: dict(color=[.32,.228,.197],roughness=.76),
    RAIL: dict(color=[.267,.247,.227],roughness=.65,metallic=.26),
    BRICK: dict(color=[.443,.432,.393],roughness=.91),
    COPING: dict(color=[.825,.808,.73],roughness=.79),
    ROOFING: dict(color=[.443,.455,.44],roughness=.95),
    CUT: dict(color=[.496,.49,.465],roughness=.92),
}

def strip(pairs, depth):
    """Single joined strip with flat ends and mitred corners."""
    return LineString(pairs).buffer(depth,single_sided=True,join_style=2,cap_style=2)

def framed(f, u, z, w, h, cols, rows, lod, label, *, d=0, depth=.23, wood=False, glass=GREEN, transoms=None):
    h0 = opening(u,z,w,h); inner=h0.buffer(-.050,join_style=2)
    divisions=[]
    for i in range(1,cols):
        x=u-w/2+w*i/cols
        divisions.append(box(x-.015,z,x+.015,z+h))
    fractions=transoms if transoms is not None else [i/rows for i in range(1,rows)]
    for fraction in fractions:
        y=z+h*fraction
        divisions.append(box(u-w/2,y-.015,u+w/2,y+.015))
    frame=h0.difference(inner.difference(unary_union(divisions)))
    f.prism(h0.buffer(.008,join_style=2),d-depth-.023,d-depth,glass,label+'/glazing')
    f.prism(frame,d-depth+.035,d-depth+.105,SHOP if wood else DARK,label+'/casement grid')
    f.box(u,z-.037,w+.075,.073,.135,d+.027,STONE,label+'/stone sill')
    if not lod and not wood:
        # Shallow glazing rebate. It is kept inside the opening edge.
        rebate=h0.buffer(-.01,join_style=2).difference(h0.buffer(-.035,join_style=2))
        f.prism(rebate,d-.083,d-.031,DARK,label+'/rebate')
    return h0

def panel(f,z0,z1,lod):
    f.box(0,(z0+z1)/2,1.49,z1-z0,.039,.022,TILE,'central light panel')
    if not lod:
        for i in range(1,5):
            f.box(-.745+i*1.49/5,(z0+z1)/2,.009,z1-z0-.03,.012,.043,STONE,'recessed panel joints')

def window_guard(f):
    for z in (4.60,4.83,5.13):
        f.box(0,z,2.32,.036,.039,.345,RAIL,'narrow guard/rails')
    for x in np.linspace(-1.10,1.10,11):
        f.box(x,4.865,.026,.52,.03,.344,RAIL,'narrow guard/uprights')
    for side in (-1,1):
        f.line([side*1.15,5.13,.345],[side*1.15,5.13,.03],.023,RAIL,8,'guard brackets')

def central(f,lod):
    holes=[]
    # A recessed commercial opening below the historical window decoration.
    shop=opening(0,.04,2.84,2.95);holes.append(shop)
    f.prism(shop.buffer(.008,join_style=2),-.387,-.36,SHOP,'shopfront/backing')
    for x,w in ((-.991,.63),(-.04,1.17),(1.,.65)):
        framed(f,x,.99,w,1.69,1,1,lod,'shopfront',d=-.238,depth=.05,wood=True)
    f.box(0,3.12,4.52,.18,.69,.25,VISOR,'shopfront/modern shallow canopy')
    f.box(0,3.235,4.39,.06,.64,.23,VISOR,'shopfront/visor lip')
    # The deeply set opening and narrow plant guard are visible in three periods.
    inset=opening(0,4.39,2.40,2.77);holes.append(inset)
    f.prism(inset.buffer(.012,join_style=2),-.57,-.535,BRICK,'Deep window/recess')
    framed(f,0,4.65,2.26,2.28,3,2,lod,'Deep window/inner window',d=-.39,depth=.105)
    f.box(0,4.415,2.51,.14,.89,-.042,STONE,'Deep window/projecting ledge')
    f.box(0,7.23,2.60,.13,.66,.135,STONE,'Deep window/lintel')
    window_guard(f)
    # Each outer cheek grows wider toward the bottom, with separate fillets.
    for side in (-1,1):
        for ix,(base,h,w) in enumerate([(4.43,.63,1.08),(5.06,.54,.91),(5.60,.48,.76),(6.08,.42,.64),(6.50,.37,.52),(6.87,.36,.405)]):
            height=base+h
            center=side*(1.48+.44-w*.45)
            f.box(center,(base+height)/2,w,h,.25+.035*(5-ix),.14,STONE,'flanking corbels/tier')
            f.box(center,base+.049,w+.07,.10,.305+.038*(5-ix),.17,STONE,'flanking corbels/projecting mould')
            if not lod and ix<3:
                for j in range(1,6):
                    px=center+w*(j/6-.5)
                    f.box(px,base+h*.52,.022,h-.16,.045,.292+.018*(5-ix),TILE,'flanking corbels/narrow fluting')
    for i,(z,h) in enumerate(((9.03,2.55),(12.96,2.33))):
        holes.append(framed(f,0,z,3.12,h,6,2,lod,'wide window',glass=GREEN if i else OLIVE,transoms=[.35,.68] if i==0 else [.66]))
    for x in (-.66,.66):
        holes.append(framed(f,x,17.44,.88,1.72,2,2,lod,'separate top window',transoms=[.77]))
    for z0,z1 in ((7.36,8.965),(11.64,12.87),(15.36,16.89)):
        panel(f,z0,z1,lod)
    return holes

def bay(f,lod):
    """Real three-sided projecting bay, open to recessed glazing on each plane."""
    front_center=-.03
    for level,(z,h) in enumerate(((4.22,2.29),(8.33,2.52),(12.41,2.49),(16.47,2.08))):
        start=front_center-1.245;end=front_center+1.245;front=.43
        points=[f.point(start,z,0)[:2],f.point(start+.35,z,front)[:2],
                f.point(end-.35,z,front)[:2],f.point(end,z,0)[:2]]
        for i,(a,b) in enumerate(zip(points,points[1:])):
            g=Facade(f.builder,a,b,f.label+'/oriel')
            w=g.length-.14
            hole=framed(g,0,z,w,h,3 if i==1 else 1,2,lod,'bay glazing',depth=.118)
            g.wall(z-.06,z+h+.10,[hole],thickness=.13,material=GRIT)
        lower=z-.37
        if level:lower=[6.61,10.95,15.00][level-1]
        plan=Polygon(points+[f.point(end,z,-.10)[:2],f.point(start,z,-.10)[:2]])
        f.builder.plan_prism(plan,lower,z-.059,GRIT,f.label+'/projected spandrel')
        f.builder.plan_prism(plan.buffer(.035,join_style=2),z-.12,z-.061,STONE,f.label+'/bay sill course')
        if level==0:
            # The bottom of the bay has two receding courses over the plinth window.
            for backset,bottom in ((.055,z-.45),(.13,z-.53)):
                smaller=plan.buffer(-backset,join_style=2)
                if not smaller.is_empty:f.builder.plan_prism(smaller,bottom,bottom+.08,STONE,f.label+'/bay support')
        if level==3:f.builder.plan_prism(plan,z+h+.085,z+h+.20,COPING,f.label+'/bay coping')

def side(f,lod,corner_end):
    """Narrow near-corner casements and a multi-storey faceted oriel."""
    toward_corner=1 if corner_end else -1
    narrow=toward_corner*(f.length/2-.80)
    holes=[]
    for z,h in ((.8,1.65),(4.42,2.08),(8.62,2.15),(12.63,2.12),(16.77,1.96)):
        holes.append(framed(f,narrow,z,.80,h,1,2,lod,'side sash'))
    bx=-toward_corner*.73
    a=f.point(bx-1.35,0,0);b=f.point(bx+1.35,0,0)
    sub=Facade(f.builder,a[:2],b[:2],f.label)
    for z,h in ((4.22,2.29),(8.33,2.52),(12.41,2.49),(16.47,2.08)):
        holes.append(opening(bx,z-.055,2.44,h+.13))
    holes.append(framed(f,bx,.73,1.98,1.91,3,2,lod,'plinth light'))
    bay(sub,lod)
    return holes

def add_corner(b,lod):
    for i,(a,end) in enumerate(zip(PATH,PATH[1:])):
        f=Facade(b,a,end,['Wukang return','Cut corner','Hunan return'][i])
        holes=central(f,lod) if i==1 else side(f,lod,i==0)
        # Split the base finish and upper roughcast at the photographed shop lintel.
        lower=box(-f.length/2,0,f.length/2,3.39).difference(unary_union(holes))
        upper=box(-f.length/2,3.39,f.length/2,ROOF-.20).difference(unary_union(holes))
        inset_path = list(LineString(PATH).offset_curve(.25,join_style=2).coords)
        # The back of every corner terminates at the intersection of the two
        # inset wall lines. No square end faces protrude through the adjoining wall.
        start_back=np.dot(np.asarray(inset_path[i])-np.asarray(a),f.t[:2])
        end_back=np.dot(np.asarray(inset_path[i+1])-np.asarray(end),f.t[:2])
        def mapped(u,z,d):
            end_weight=max(0.,1-(f.length/2-u)/.32)
            start_weight=max(0.,1-(f.length/2+u)/.32)
            return f.point(u+(-d/.25)*(end_back*end_weight+start_back*start_weight),z,d)
        b.prism(lower,-.25,0,mapped,BASE,f.label+'/shop level')
        b.prism(upper,-.25,0,mapped,GRIT,f.label+'/upper wall')
    path=LineString(PATH)
    plan=strip(PATH,SHELL_DEPTH)
    b.plan_prism(plan.buffer(.145,join_style=2),ROOF-.36,ROOF-.20,BRICK,'crown/shadow course')
    b.plan_prism(plan.buffer(.300,join_style=2),ROOF-.20,ROOF+.085,COPING,'crown/projecting cornice')
    b.plan_prism(plan.buffer(.230,join_style=2),ROOF+.085,ROOF+.115,COPING,'crown/cornice top')
    belt=strip(PATH,-.105).union(strip(PATH,.012))
    b.plan_prism(belt,16.89,17.005,STONE,'returning belt below top casements')
    b.plan_prism(plan,ROOF+.115,ROOF+.143,ROOFING,'section roof')
    b.plan_prism(plan,0,.042,CUT,'section floor')
    back=path.offset_curve(SHELL_DEPTH,join_style=2)
    for a,end in zip(list(back.coords),list(back.coords)[1:]):
        f=Facade(b,end,a,'neutral back section')
        f.wall(.042,ROOF-.20,thickness=.055,material=CUT)
    for a,end in [(PATH[0],back.coords[0]),(back.coords[-1],PATH[-1])]:
        f=Facade(b,a,end,'neutral end section')
        f.wall(.042,ROOF-.20,thickness=.065,material=CUT)
