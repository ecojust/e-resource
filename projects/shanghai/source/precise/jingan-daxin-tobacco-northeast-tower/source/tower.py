"""The alternation of actual open and blind arches on the six-sided eastern tower."""
from math import cos,pi,sin
from shapely.geometry import Polygon,box
from photo_architecture import Facade,opening
from brickwork import BRICK,TRIM,CLAY,PALE,IRON,YARD,window,grating


def vertices(r):
    return [(r*cos((195+i*60)*pi/180),r*sin((195+i*60)*pi/180)) for i in range(6)]


def polygon_band(builder,outline,z,height,expand,material,label):
    part=outline.buffer(expand,join_style=2).difference(outline.buffer(-.20,join_style=2))
    builder.plan_prism(part,z,z+height,material,label)


def tower(builder,fit,lod):
    radius=fit['hexagon_radius_m'];ring=vertices(radius);outline=Polygon(ring)
    levels={k:v['height_m']for k,v in fit['levels'].items()};first,upper,eave,top=[levels[k] for k in ('belt','sill','cornice','parapet')]
    builder.plan_prism(outline,.035,.17,YARD,'Tower base stone')
    for i in range(6):
        f=Facade(builder,ring[i],ring[(i+1)%6],f'Hex {i}')
        # Side 3 abuts the original wing. Leave the enclosed side as continuous masonry.
        if i==3:
            f.wall(.12,eave,[],.33,BRICK)
            continue
        w=f.length;low=opening(0,.91,w*.498,first-1.44,.13,10 if lod else 22)
        middle=opening(0,first+.79,w*.535,upper-first-1.69,.192,12 if lod else 28)
        attic=opening(0,upper+.92,w*.515,eave-upper-1.57,.60,12 if lod else 26)
        open_top=i in (0,2,4)
        blind=[]
        if not open_top:
            for u in (-.22*w,.22*w):
                blind.append(opening(u,upper+.92,.408*w,eave-upper-1.76,.39,12 if lod else 26))
        f.wall(.12,eave,[low,middle]+([attic] if open_top else blind),.33,BRICK)
        window(f,low,.13,(.5,),(.71,),lod,'lower barred sash')
        window(f,middle,.192,(),(.15,.72,),lod,'middle segmental sash')
        grating(f,0,1.72,w*.53,1.44,lod,'courtyard grille')
        if open_top:
            window(f,attic,.60,(.49,),(.75,),lod,'upper round headed sash')
        else:
            for panel in blind:
                # The photo shows solid pressed-brick panels set behind a raised, paired arch.
                f.prism(panel.buffer(.012,join_style=2),-.165,-.096,BRICK,'recessed blind brick panels')
                edge=panel.buffer(.071,join_style=2).difference(panel)
                f.prism(edge,-.016,.083,TRIM,'paired blind arch outlines')
            f.box(0,eave-.92,.109,.28,.155,.070,CLAY,'central brick drop')
        for side in (-1,1):
            u=side*(w/2-.086)
            f.box(u,(first+upper)/2,.157,upper-first-.47,.143,.046,TRIM,'middle angled piers')
            f.box(u,(upper+eave)/2,.148,eave-upper-.34,.126,.035,TRIM,'upper angled piers')
        for n in range(5 if lod else 9):
            f.box(w*((n+.5)/(5 if lod else 9)-.5),upper-.28,.15,.18,.22,.096,TRIM,'dentils under attic')
    for label,z,height,d,mat in [('base course',.18,.12,.10,TRIM),('lower belt',first-.18,.12,.11,TRIM),('lower sill cap',first-.04,.11,.113,PALE),('attic ledge bed',upper-.30,.16,.15,TRIM),('attic cutwater',upper-.14,.14,.205,CLAY),('attic ledge cap',upper,.085,.19,PALE),('upper window sill',upper+.81,.096,.10,TRIM),('top brick cornice',eave-.29,.19,.187,TRIM),('top coping underside',eave-.09,.14,.212,CLAY)]:
        polygon_band(builder,outline,z,height,d,mat,label)
    # The cap tapers, with a shallow flat roof behind the raised perimeter coping.
    lower=vertices(radius*1.066);inner=vertices(radius*.936);bottom=eave+.016
    for i in range(6):
        j=(i+1)%6
        front=[(*lower[i],bottom),(*lower[j],bottom),(*inner[j],top-.105),(*inner[i],top-.105)]
        back=[(x*.95,y*.95,z)for x,y,z in front];builder.add(front+back,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],PALE,f'Hex {i}/grey sloping parapet face')
    polygon_band(builder,Polygon(inner),top-.105,.105,.048,PALE,'Hexagonal parapet coping')
    builder.plan_prism(Polygon(inner).buffer(-.06,join_style=2),top-.31,top-.245,YARD,'Recessed flat roof')
    return outline
