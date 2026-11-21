"""Model the garden frontage of the Pei mansion from the attributed December 2013 photographs."""
import json
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from photo_architecture import Facade

P = json.loads((HERE / 'parameters.json').read_bytes())
META = {
    'id': P['id'], 'name': '贝宅花园侧主楼', 'viewer_page': 'pei-mansion-garden-front.html',
    'audit_directory': 'data/audit/pei-mansion-garden-front-v1/', 'status': 'photo-informed-exterior',
    'scope': 'Three-storey garden elevation, two faceted bays with metal casements, two recessed galleries, pierced Chinese geometric rails, stepped frieze, roof shaft and hotel entrance.',
    'model_scope_zh': '贝宅园侧三层主楼，包括左右折面钢窗、两层凹廊与镂空回纹石栏、分带墙面、女儿墙浅浮饰、屋顶竖井及酒店时期玻璃门和石阶。侧背及平屋面按足迹简化，未制作门墙、亭子和室内。',
    'coordinate_convention': 'Local X follows the garden facade towards true 64.14 degrees. glTF Y is up and +Z faces the garden at true 154.14 degrees.',
    'map_reference_license': 'The registered East Asian building footprint is attributed in footprint-review.json. Reference photographs are not embedded.',
    'interiors_modeled': False,
}
COLORS = {
    'ochre cut stone': (.684,.620,.506), 'light sandstone': (.756,.699,.599),
    'dark aggregate band': (.601,.542,.448), 'buff tooling': (.734,.658,.538),
    'raised border': (.799,.735,.624), 'carved rail stone': (.773,.703,.593),
    'grey glazed lights': (.322,.362,.361), 'shadowed glazing': (.210,.260,.263),
    'reflecting glass': (.388,.418,.408), 'steel casements': (.182,.191,.183),
    'brass entrance frame': (.545,.417,.236), 'bronze handle': (.407,.323,.202),
    'gallery floor': (.529,.499,.446), 'pale steps': (.674,.637,.573),
    'gallery ceiling': (.698,.673,.603), 'roof grey': (.481,.460,.410),
    'vent interior': (.210,.217,.201),
}
PALETTE = {key:{'color':list(color), 'roughness': .36 if key in ('grey glazed lights','reflecting glass','shadowed glazing','brass entrance frame') else .78}
           for key,color in COLORS.items()}
NW,NE,SE,SW=np.asarray(P['source_local_outline_m'])
XC=(SE[0]+SW[0])/2
Y=SW[1]
H=P['principal_parapet_m']
INNER=3.71
BALCONY=1.03
GALLERY_BACK=BALCONY+P['gallery_setback_m']
def pt(x,y):
    return (XC+x,Y+y)

BAYS=[pt(-9.34,1.13),pt(-8.37,0),pt(-5.37,0),pt(-INNER,BALCONY),
      pt(INNER,BALCONY),pt(5.37,0),pt(8.37,0),pt(9.34,1.13)]
PLAN=Polygon([*BAYS,tuple(NE),tuple(NW)])
LEVELS=[(1.25,5.10),(6.97,9.32),(11.29,13.61)]
BANDS=[(.11,.61,'dark aggregate band'),(.62,1.17,'light sandstone'),
       (5.16,5.35,'dark aggregate band'),(5.52,5.74,'buff tooling'),(5.94,6.17,'dark aggregate band'),
       (6.36,6.55,'buff tooling'),(6.73,6.89,'light sandstone'),
       (9.39,9.56,'dark aggregate band'),(9.76,9.97,'buff tooling'),(10.14,10.36,'dark aggregate band'),
       (10.57,10.77,'buff tooling'),(11.00,11.17,'light sandstone'),
       (13.71,13.84,'dark aggregate band'),(14.05,14.24,'buff tooling'),(14.56,14.76,'light sandstone')]


def frame_and_glass(face,shape,columns,horizontals,label,lod,material='steel casements',deep=False):
    """One joined set of mullions. Isolated inset glass lights vary in tint between casements."""
    x0,z0,x1,z1=shape.bounds; width=x1-x0; height=z1-z0
    gap=.055 if material=='steel casements' else .094
    inner=shape.buffer(-gap,join_style=2);bars=[]
    for k in range(1,columns):
        u=x0+k*width/columns
        bars.append(box(u-gap*.38,z0,u+gap*.38,z1))
    for ratio in horizontals:
        z=z0+ratio*height
        bars.append(box(x0,z-gap*.32,x1,z+gap*.32))
    grids=unary_union(bars)
    border=shape.difference(inner.difference(grids))
    face.prism(border,-.138,-.073,material,label+' joined metal frame')
    face.prism(shape.buffer(.005,join_style=2),-.205,-.185,'shadowed glazing' if deep else 'grey glazed lights',label+' inset glazing')
    if not lod:
        for k in range(columns):
            left=x0+k*width/columns+gap; right=x0+(k+1)*width/columns-gap
            if k%3==2 and right>left:
                pane=shape.intersection(box(left,z0+gap,right,z1-gap))
                face.prism(pane,-.183,-.177,'grey glazed lights' if deep else 'reflecting glass',label+' reflected light')


def folded_window(face,index,lod):
    half=face.length/2;holes=[]
    for j,(low,high) in enumerate(LEVELS):
        aperture=box(-half+.107,low,half-.107,high)
        frame_and_glass(face,aperture,4 if index in (1,5) else (3 if index in (2,4) else 2),
                        [.20,.40,.62,.81] if not lod else [.33,.66],f'storey {j+1}',lod)
        holes.append(aperture);face.box(0,low-.060,face.length+.012,.12,.23,.024,'light sandstone','projecting window sill')
        face.box(0,high+.045,face.length,.09,.15,.016,'buff tooling','window head')
    face.wall(.08,H,holes,.18,'ochre cut stone')
    for z0,z1,material in BANDS:
        face.box(0,(z0+z1)/2,face.length,z1-z0,.026,.023,material,'horizontal stone course')
    if not lod:
        for z in [5.33,6.38,9.57,10.56,13.95]:
            for k in range(max(1,int(face.length/.15))):
                x=-half+(k+.5)*.15
                if x<half-.032:
                    face.box(x,z,.017,.147,.016,.038,'buff tooling','fine vertical tooling')


def path_band(points,width):
    return LineString(points).buffer(width/2,cap_style='flat',join_style='mitre')


def meander(face,low,width,height,period,n,lod,relief=False):
    """Hand trace the interlocking stepped frame and three central rectangular apertures in the garden photograph."""
    left=-width/2
    motifs=[]
    for k in range(-1,n+1):
        u=left+k*period
        def mapped(nodes):
            return [(u+x*period,low+y*height)for x,y in nodes]
        # The rectangular eye links a high and a low, reversed right-angle scroll.
        for line in [[(0,.53),(.14,.53),(.14,.13),(.38,.13),(.38,.53),(.50,.53)],
                     [(0,.53),(.14,.53),(.14,.87),(.38,.87),(.38,.53),(.50,.53)],
                     [(.50,.53),(.60,.53),(.60,.87),(.86,.87),(.86,.53),(1,.53)],
                     [(.50,.53),(.60,.53),(.60,.13),(.86,.13),(.86,.53),(1,.53)]]:
            motifs.append(path_band(mapped(line),.115 if not relief else .064))
        outer=box(u+.64*period,low+.29*height,u+.82*period,low+.70*height)
        motifs.append(outer.difference(outer.buffer(-.088 if not relief else -.045,join_style=2)))
        motifs.append(path_band(mapped([(.38,.53),(.60,.53)]),.115 if not relief else .064))
    clip=box(left,low,left+width,low+height)
    if relief:
        raised=unary_union(motifs).intersection(clip)
        face.prism(raised,.011,.077,'raised border','parapet hand-drawn relief')
    else:
        motifs.extend([box(left,low,left+width,low+.065),box(left,low+height-.073,left+width,low+height)])
        panel=unary_union(motifs).intersection(clip)
        face.prism(panel,-.185,.032,'carved rail stone','openwork gallery stone balustrade')
        if not lod:
            # A narrow planted arris catches light on both horizontal ledges.
            for h in [low+.035,low+height-.035]:
                face.box(0,h,width,.027,.244,-.070,'raised border','balustrade nosing')


def gallery_entrance(b,front,lod):
    half=front.length/2
    ground=box(-half+.14,.83,half-.14,5.11)
    frame_and_glass(front,ground,4,[.78], 'hotel entrance',lod,'brass entrance frame',True)
    front.wall(.10,5.21,[ground],.19,'light sandstone')
    # Paired glazed doors between the fixed, glazed flanks have bronze pull bars.
    for sign in [-1,1]:
        front.box(sign*.12,2.13,.037,.61,.075,-.012,'bronze handle','paired entrance pull')
    for j in range(5):
        depth=(5-j)*.274
        b.box((XC,Y+BALCONY-depth/2,.088+j*.154),(7.05,depth,.154),'pale steps',label='Entry / five stone treads')
    for i,floor in enumerate([5.18,9.49]):
        edge=Facade(b,pt(-INNER,BALCONY),pt(INNER,BALCONY),f'Gallery {i+1}')
        back=Facade(b,pt(-INNER,GALLERY_BACK),pt(INNER,GALLERY_BACK),f'Gallery {i+1} recessed wall')
        # Floors and soffits extend continuously to the rear wall without filling the open gallery.
        b.box((XC,Y+(GALLERY_BACK+BALCONY)/2,floor+.05),(2*INNER,GALLERY_BACK-BALCONY,.20),'gallery floor',label=f'Gallery {i+1}/deck')
        next_floor=[9.49,13.66][i]
        b.box((XC,Y+(GALLERY_BACK+BALCONY)/2,next_floor-.07),(2*INNER,GALLERY_BACK-BALCONY,.16),'gallery ceiling',label=f'Gallery {i+1}/soffit')
        edge.box(0,floor+.44,2*INNER,.72,.26,-.08,'light sandstone','stone parapet base')
        edge.box(0,floor+.80,2*INNER+.02,.09,.32,-.08,'buff tooling','rail lower coping')
        meander(edge,floor+.85,2*INNER,.89,2*INNER/3,3,lod)
        holes=[]
        for x in [-1.83,1.83]:
            shape=box(x-1.50,floor+.16,x+1.50,next_floor-.67)
            frame_and_glass(back,shape,4,[.30,.60,.82],f'Gallery door {x}',lod,deep=True);holes.append(shape)
        back.wall(floor+.03,next_floor,holes,.16,'light sandstone')
        for side in [-1,1]:
            x=side*INNER
            a0,b0=(pt(x,BALCONY),pt(x,GALLERY_BACK))if side<0 else(pt(x,GALLERY_BACK),pt(x,BALCONY))
            sidewall=Facade(b,a0,b0,f'Gallery {i+1} reveal {side}')
            sidewall.wall(floor,next_floor,[],.13,'ochre cut stone')
            outline=[(0,0),(.63,0),(.63,.15),(.39,.15),(.39,.28),(.18,.28),(.18,.40),(0,.40)]
            stone=Polygon([(side*(half-dx),floor-.016-dz)for dx,dz in outline])
            edge.prism(stone,-.19,.027,'raised border','stepped corner corbel')
    top=Facade(b,pt(-INNER,BALCONY),pt(INNER,BALCONY),'Gallery / roof lintel')
    top.wall(13.64,H,[],.27,'light sandstone')


def crest(b,lod):
    for i,(a,bb) in enumerate(zip(BAYS,BAYS[1:])):
        face=Facade(b,a,bb,f'Garden crest {i+1}')
        face.box(0,14.81,face.length,.067,.14,.005,'raised border','lower frieze course')
        face.box(0,15.33,face.length,.08,.19,.014,'buff tooling','crest cap')
        n=max(1,round(face.length/.96));meander(face,14.86,face.length,.405,face.length/n,n,lod,True)
        for k in range(n):
            face.box((-0.5+(k+.25)/n)*face.length,15.402,face.length/(2*n),.085,.13,0,'light sandstone','stepped skyline')
    face=Facade(b,pt(-INNER,BALCONY),pt(INNER,BALCONY),'Garden crest / key block')
    face.box(0,15.06,.66,.88,.24,.084,'buff tooling','central keystone')
    if not lod:
        panel=box(-.233,14.79,.233,15.38)
        face.prism(panel.difference(panel.buffer(-.027,join_style=2)),.205,.227,'raised border','recessed key border')


def roof_and_returns(b,lod):
    # Their outlines are known; the side and rear elevations are deliberately schematic.
    for k,(a,bb) in enumerate([(BAYS[-1],NE),(NE,NW),(NW,BAYS[0])]):
        face=Facade(b,a,bb,['East return','Beijing Road rear mass','West return'][k])
        face.wall(.10,14.40,[],.20,'ochre cut stone')
        for z in [1.0,5.25,9.50,13.70]:
            face.box(0,z,face.length,.11,.23,.018,'dark aggregate band','course continuing around mass')
        face.box(0,14.40,face.length,.15,.30,.02,'light sandstone','parapet coping')
    b.plan_prism(PLAN,-.04,.17,'dark aggregate band','Continuous base')
    b.plan_prism(PLAN,.17,.77,'light sandstone','Ground level edge')
    b.plan_prism(PLAN,13.62,13.82,'roof grey','Inferred flat roof deck')
    # A narrow capped shaft is visible to the right of the axis behind the crest.
    shaft=box(XC+3.18,Y+3.64,XC+5.14,Y+5.06)
    b.plan_prism(shaft,13.82,17.06,'light sandstone','Roof shaft/rectangular body')
    ctr=Facade(b,(XC+3.18,Y+3.64),(XC+5.14,Y+3.64),'Roof shaft / garden face')
    aperture=box(-.172,15.38,.172,16.30)
    # The front-facing vent is recessed in a framed skin on the shaft.
    ctr.prism(aperture,.007,.023,'vent interior','dark recessed vent')
    for z in [15.57,15.83,16.10]:
        ctr.box(0,z,.35,.036,.065,.032,'steel casements','vent frame')
    b.plan_prism(shaft.buffer(.075,join_style=2),17.035,17.165,'buff tooling','Roof shaft / cornice')
    for k in range(7):
        z=17.28 if k%2==0 else 17.22
        b.box((XC+3.24+k*.302,Y+3.66,(17.164+z)/2),(.155,.16,z-17.164),'light sandstone',label='Roof shaft / crenellated crown')
    b.box((XC+4.16,Y+3.66,17.292),(.24,.17,.256),'light sandstone',label='Roof shaft / raised central tooth')


def assemble(builder,lod=False):
    for i,(a,bb) in enumerate(zip(BAYS,BAYS[1:])):
        face=Facade(builder,a,bb,'Garden folded bay '+str(i+1))
        if i==3:
            gallery_entrance(builder,face,lod)
        else:
            folded_window(face,i,lod)
    crest(builder,lod)
    roof_and_returns(builder,lod)


if __name__=='__main__':
    from final_preview import package
    package(build,HERE,META,PALETTE,assemble)
