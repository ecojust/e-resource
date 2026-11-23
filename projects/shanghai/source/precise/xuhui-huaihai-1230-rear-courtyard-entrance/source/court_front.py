"""Build the measured 1230 entrance, adjacent steel windows, brick lintels, steps and eaves."""
from pathlib import Path
import json
import math

from shapely.affinity import scale,translate
from shapely.geometry import LineString,Point,Polygon,box
from shapely.ops import unary_union

from photo_architecture import Facade
from court_finishes import BRICK,SOLDIER,CAST,FOOT

STEEL='Huaihai 1230 | grey painted steel sash'
PALE='Huaihai 1230 | dulled pale painted sash'
GLASS='Huaihai 1230 | courtyard window glass'
INNER='Huaihai 1230 | dark vestibule'
MAIL='Huaihai 1230 | oxblood wall cabinet'
GREEN='Huaihai 1230 | street-number enamel'
LETTER='Huaihai 1230 | pale enamel number'
IRON='Huaihai 1230 | aged metal fixtures'
PALETTE={STEEL:{'color':[.16,.18,.17],'roughness':.68},
         PALE:{'color':[.43,.46,.43],'roughness':.69},
         GLASS:{'color':[.18,.23,.235],'roughness':.28,'metallic':.18},
         INNER:{'color':[.023,.021,.019],'roughness':.96},
         MAIL:{'color':[.235,.045,.054],'roughness':.65},
         GREEN:{'color':[.005,.12,.066],'roughness':.56},
         LETTER:{'color':[.73,.77,.65],'roughness':.65},
         IRON:{'color':[.085,.09,.083],'roughness':.69,'metallic':.18}}
MEASUREMENTS=Path(__file__).absolute().parent.parent/'measurements/window-controls.json'
WALL_LEFT=-3.40
WALL_RIGHT=9.93
UPPER_RIGHT=7.14
EAVE=13.02

def openings():
    rows={}
    for measured in json.loads(MEASUREMENTS.read_text())['windows']:
        points=measured['xyz']
        left=(points[0][0]+points[3][0])/2
        right=(points[1][0]+points[2][0])/2
        top=(points[0][2]+points[1][2])/2
        bottom=(points[2][2]+points[3][2])/2
        rows.setdefault(measured['opening'],[]).append((left,bottom,right,top))
    result={name:tuple(sum(v[i] for v in readings)/len(readings) for i in range(4)) for name,readings in rows.items()}
    # The west ground opening is partly obscured by the later cage. Its limits
    # are taken at the backing wall of the 2016 court view, with lower confidence.
    result['west-plain.ground']=(-3.04,1.81,-1.52,3.15)
    return result

def add_window(f, name, bounds):
    x0,z0,x1,z1=bounds
    x=(x0+x1)/2;w=x1-x0;h=z1-z0
    glass=box(x0+.039,z0+.045,x1-.039,z1-.042)
    outside=box(x0+.002,z0+.004,x1-.002,z1-.003)
    columns=3
    if '.ground' in name:
        columns=3 if 'east-of-entry' in name else 4
    if 'east-of-entry.top4' in name or 'east-of-entry.middle3' in name:columns=3
    bars=[]
    for i in range(1,columns):
        at=x0+w*i/columns
        bars.append(box(at-.014,z0,at+.014,z1))
    top_light=z1-min(.30,h*.23)
    bars.append(box(x0,top_light-.015,x1,top_light+.015))
    if '.ground' in name or 'lower2' in name:
        mid=z0+.43*h;bars.append(box(x0,mid-.011,x1,mid+.011))
    panes=glass.difference(unary_union(bars))
    material=PALE if 'west-plain' in name or '.ground' in name else STEEL
    f.prism(outside.difference(panes),-.103,-.067,material,name+'/steel-casement-and-transom')
    for k,pane in enumerate(getattr(panes,'geoms',(panes,))):
        f.prism(pane,-.104,-.093,GLASS,name+f'/pane-{k+1}')
    f.prism(box(x0-.064,z0-.056,x1+.064,z0+.002),-.06,.048,BRICK,name+'/projecting-sill')
    f.prism(box(x0-.080,z1+.002,x1+.080,z1+.168),-.012,.023,SOLDIER,name+'/upright-brick-head')

def add_front(b,lod=False):
    f=Facade(b,(-1,0),(1,0),'1230 court elevation')
    windows=openings()
    fields=[box(*bounds) for bounds in windows.values()]
    mouth=box(-.98,.84,.98,3.49)
    stacked=box(4.10,.842,6.92,12.91)
    fields.extend([mouth,stacked])
    # The upper east section falls outside the two recorded photographs.
    # End this measured fragment at the pier beside the stacked balcony.
    outline=Polygon([(WALL_LEFT,0),(WALL_RIGHT,0),(WALL_RIGHT,6.45),
                     (UPPER_RIGHT,6.45),(UPPER_RIGHT,EAVE),(WALL_LEFT,EAVE)])
    front=outline.difference(unary_union(fields))
    greys=unary_union([box(WALL_LEFT-1,-1,WALL_RIGHT+1,1.335),box(WALL_LEFT-1,3.77,WALL_RIGHT+1,4.575)])
    f.prism(front.difference(greys),-.264,0,BRICK,'continuous-facing-with-door-and-window-reveals')
    f.prism(front.intersection(greys),-.264,.002,FOOT,'grey-socle-and-first-floor-band')
    for name,bounds in windows.items():add_window(f,name,bounds)
    # Eastern and western portions of the band meet the balcony ends.
    for l,r in ((WALL_LEFT,4.10),(6.92,WALL_RIGHT)):
        f.prism(box(l,3.745,r,3.837),-.13,.085,CAST,'projecting-course-below-first-floor-band')
    for i,(bottom,top,projection) in enumerate([(12.88,12.99,.10),(12.99,13.13,.22),(13.13,13.20,.30)]):
        f.prism(box(WALL_LEFT,bottom,UPPER_RIGHT,top),-.36,projection,CAST,f'eaves-layer-{i+1}')
    # Transverse laid bricks below the ground window sills are discernible
    # in Gao 04, including the thin belt visible alongside the letter box.
    for l,r in ((WALL_LEFT,-.98),(.98,4.10),(6.92,WALL_RIGHT)):
        f.prism(box(l,1.62,r,1.764),-.015,.003,SOLDIER,'narrow-upright-brick-course')
    # Physical returns close the recessed vestibule. No interior room is inferred.
    wall_y=1.066
    f.box(-.953,2.12,.054,2.58,wall_y,-wall_y/2,BRICK,'west-door-reveal')
    f.box(.953,2.12,.054,2.58,wall_y,-wall_y/2,BRICK,'east-door-reveal')
    f.box(0,3.455,1.96,.07,wall_y,-wall_y/2,FOOT,'shadowed-porch-soffit')
    f.prism(box(-.98,.84,.98,3.49),-wall_y-.045,-wall_y,INNER,'shaded-back-of-entry')
    frame=box(-.70,.842,.69,3.018).difference(box(-.657,.86,.647,2.941))
    f.prism(frame,-wall_y-.002,-wall_y+.039,STEEL,'dark-inner-door-frame')
    f.prism(box(-.658,.86,.648,2.944),-wall_y+.001,-wall_y+.013,INNER,'inner-door-leaf')
    f.box(0,.816,1.96,.048,wall_y+.05,-wall_y/2,CAST,'upper-landing')

    # Five nosing lines appear at y=794 / 812 / 830 / 848 / 867 of the 2013
    # frame. The last riser is below the crop. A sixth ascending riser joins
    # the conditional 0.84-m landing; pitch and the hidden lowest step are estimates.
    for k in range(6):
        height=(k+1)*.14;front_y=-(5-k)*.28-.20
        rear_y=front_y+.28
        b.box((0,(front_y+rear_y)/2,height/2),(1.98,.28,height),CAST,label=f'entrée flight / step {k+1}')
        b.box((0,front_y+.023,height-.016),(2.00,.068,.032),FOOT,label=f'entrée flight / rounded nosing {k+1}')
    for side in (-1,1):
        cheek=Polygon([(-1.63,0),(-1.63,.18),(-.15,.96),(.12,.96),(.12,0)])
        b.prism(cheek,side*1.08-.06,side*1.08+.06,lambda y,z,x:(x,y,z),CAST,'low-entrance-stair-cheek')
    add_number_and_box(f,lod)
    for x in (3.934,6.99):
        f.line((x,1.30,.070),(x,12.93,.070),.039,IRON,8 if lod else 14,'rainwater-downpipe')
        for z in (1.55,3.82,7.06,10.15,12.68):
            f.box(x,z,.125,.055,.104,.045,IRON,'downpipe-wall-strap')
    return windows

def add_number_and_box(f,lod):
    cx,cz=1.27,2.46
    f.box(cx,cz,.282,.139,.015,.0075,GREEN,'green-1230-number-plate')
    # Draw original strokes for the legible address. The lower caption in the
    # original photograph has too little detail for an attributed transcription.
    paths={
        '1':[(.14,.76),(.50,.99),(.50,.05),(.19,.05),(.84,.05)],
        '2':[(.06,.74),(.16,.92),(.42,1),(.75,.94),(.91,.79),(.88,.63),(.68,.46),(.15,.075),(.94,.075)],
        '3':[(.10,.87),(.34,.98),(.68,.99),(.91,.85),(.89,.69),(.70,.56),(.43,.52),(.71,.52),(.91,.38),(.91,.20),(.73,.06),(.38,.04),(.11,.16)],
        '0':[(.48,.98),(.72,.95),(.90,.76),(.91,.28),(.75,.08),(.52,.04),(.26,.08),(.09,.26),(.08,.75),(.24,.94),(.48,.98)]}
    for i,ch in enumerate('1230'):
        line=LineString(paths[ch]).buffer(.069,cap_style='round',join_style='round',quad_segs=2 if lod else 4)
        shape=translate(scale(line,xfact=.045,yfact=.081,origin=(0,0)),cx-.109+i*.056,cz-.026)
        f.prism(shape,.0150,.0168,LETTER,'number-plate-digit-'+ch)
    x,z=1.296,2.105
    f.box(x,z,.292,.389,.102,.053,MAIL,'red-wall-cabinet')
    f.box(x,z+.194,.328,.028,.126,.060,MAIL,'cabinet-coping')
    f.box(x,z+.091,.231,.024,.009,.107,IRON,'cabinet-opening')
    f.box(x+.101,z-.057,.017,.056,.014,.109,LETTER,'cabinet-latch')
