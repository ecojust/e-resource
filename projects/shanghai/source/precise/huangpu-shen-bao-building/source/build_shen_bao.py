"""Rebuild the chamfered Shen Bao office entrance at Hankou and Shandong roads."""
import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from photo_architecture import Facade, opening
from sign_lettering import add_facade_lettering

P = json.loads((HERE/'parameters.json').read_bytes())
META = {
    'id': P['id'], 'name': '申报馆（东北转角入口与两侧临街立面）',
    'status': 'photo-informed-partial-exterior',
    'scope': 'The chamfered corner entrance at 309 Hankou Road and four nearby facade bays on each street, using 2015 and 2016 photographs.',
    'model_scope_zh': '汉口路309号申报馆东北削角入口、门额及汉口路和山东中路各四个临街开间，包含二楼石栏、上部跨层壁柱、菱纹与大檐。两侧远端、后楼和印刷设施保留底图。',
    'viewer_page': 'shen-bao-building.html', 'audit_directory': 'data/audit/shen-bao-building-v1/',
    'coordinate_convention': 'glTF X along the chamfer to the northwest, Y up and Z facing the junction to the northeast.',
    'source_register': 'source/precise/'+P['id']+'/reference-review.json',
    'map_reference_license': 'OpenStreetMap and Overture Maps, ODbL-1.0.', 'interiors_modeled': False
}
PAL = {
    'office granite': {'color': [.291,.284,.265], 'roughness': .89},
    'channel granite': {'color': [.225,.220,.207], 'roughness': .93},
    'warm stone': {'color': [.455,.414,.366], 'roughness': .85},
    'stone relief': {'color': [.498,.459,.402], 'roughness': .82},
    'stone shade': {'color': [.347,.321,.284], 'roughness': .90},
    'aged bronze': {'color': [.54,.345,.165], 'metallic': .70, 'roughness': .55},
    'recessed glass': {'color': [.159,.203,.201], 'metallic': .24, 'roughness': .32},
    'entry glazing': {'color': [.102,.133,.132], 'metallic': .23, 'roughness': .35},
    'bronze window frame': {'color': [.133,.143,.134], 'metallic': .43, 'roughness': .50},
    'roof trim': {'color': [.225,.219,.201], 'roughness': .79},
    'roof skin': {'color': [.302,.292,.265], 'roughness': .91},
}
ROWS = [(5.08,2.78),(8.95,2.77),(12.51,2.84)]
FRONT = np.asarray(P['front_uv_m'])
SIDE_AXES = [-5.10,-1.70,1.70,5.10]


def sash(f, u, z, w, height, columns, rows):
    """Use the thin dark metal divides and almost flush surrounds in both photos."""
    pane = opening(u,z,w,height)
    f.prism(pane.buffer(.012,join_style='mitre'),-.33,-.31,'recessed glass','recessed office glazing')
    fields = []
    x0,z0,x1,z1 = pane.bounds
    for k in range(columns):
        for j in range(rows):
            x=x0+k*w/columns; y=z0+j*height/rows
            fields.append(box(x+.027 if k else x+.082, y+.025 if j else y+.072,
                              x+w/columns-(.027 if k+1<columns else .082),
                              y+height/rows-(.025 if j+1<rows else .072)))
    f.prism(pane.difference(unary_union(fields)),-.242,-.152,'bronze window frame','narrow-paned metal sash')
    f.box(u,z-.035,w+.08,.07,.16,-.035,'stone shade','flush sill')


def connected_band(builder, low, high, back, outer, material, label):
    """Miter all three elevations, including the outside corner returns."""
    line = LineString(FRONT)
    inner = line.offset_curve(-back,join_style='mitre')
    face = line.offset_curve(-outer,join_style='mitre')
    shape = Polygon(list(inner.coords)+list(face.coords)[::-1])
    builder.plan_prism(shape,low,high,material,label)


def pilaster(f, x, lod):
    base=8.29; cap=15.69
    f.box(x,(base+cap)/2,.58,cap-base,.19,.028,'stone shade','giant pilaster backing')
    # Separate narrow ribs leave actual vertical channels between the fillets.
    for k in range(7):
        f.box(x+(k-3)*.073,(base+cap)/2,.050,cap-base-.33,.16,.135,'warm stone','pilaster fillets')
    for z,w,h,d in [(8.29,.76,.21,.38),(8.48,.68,.13,.32),(15.43,.68,.12,.31),
                     (15.66,.81,.18,.41),(15.85,.93,.13,.51)]:
        f.box(x,z,w,h,d,.085,'stone relief','pilaster capitals and feet')
    for sign in (-1,1):
        path=[]
        for t in np.linspace(0,1,12 if lod else 23):
            ang=(.16+1.65*t)*math.pi
            rad=.150*(1-.77*t)
            path.append(f.point(x+sign*(.248+rad*math.cos(ang)),15.63+rad*math.sin(ang),.322))
        f.builder.tube(path,.032,'stone relief',5 if lod else 8,f.label+'/corner volutes in capital')
    for k in (-1,0,1):
        u=x+k*.129
        leaf=Polygon([(u,15.68),(u+.064,15.55),(u+.030,15.40),(u,15.32),(u-.050,15.47),(u-.060,15.57)])
        f.prism(leaf,.166,.233,'stone relief','capital leaves')


def upper(f, axes, is_corner, lod):
    width=2.52 if is_corner else 2.75
    vents=[opening(u,16.24,1.54 if is_corner else 1.28,.43) for u in axes]
    holes=[opening(u,z,width,h) for u in axes for z,h in ROWS]+vents
    f.wall(4.63,17.52,holes,.39,'warm stone')
    for u in axes:
        for j,(z,h) in enumerate(ROWS):
            sash(f,u,z,width,h,4 if is_corner else 6,5 if j<2 else 6)
        f.prism(opening(u,16.24,1.54 if is_corner else 1.28,.43).buffer(.008),-.29,-.252,'entry glazing','attic vent shadow')
        for t in (-.10,.035,.16):
            f.box(u,16.405+t,1.51 if is_corner else 1.24,.034,.13,-.21,'roof trim','attic louvres')
        if not is_corner:
            diamond=Polygon([(u-.43,12.11),(u,12.38),(u+.43,12.11),(u,11.84)])
            f.prism(diamond.difference(diamond.buffer(-.034,join_style='mitre')),.023,.090,'stone shade','diamond spandrel border')
    if not is_corner:
        for x in (-6.59,-3.40,0,3.40,6.59):
            pilaster(f,x,lod)
    for z,step,w,d,height,mat,title in [
            (16.96,.29,.095,.32,.18,'stone relief','small attic dentils'),
            (17.35,.72,.185,.85,.27,'stone shade','large cornice brackets')]:
        n=max(1,round(f.length/step))
        for i in range(n):
            f.box((i+.5-n/2)*f.length/n,z,w,height,d,d*.36,mat,title)


def ground(f, axes, corner, lod):
    if corner:
        openings=[opening(0,.08,2.82,3.62)]
    else:
        openings=[opening(x,.12,2.72,3.47) for x in axes]
    f.wall(.09,4.65,openings,.53,'channel granite')
    void=unary_union([o.buffer(.012,join_style='mitre') for o in openings])
    for j in range(7):
        z=.105+j*.64
        # Real dark courses have alternating vertical joints at window piers.
        shift=.0 if j%2 else .72
        spans=[-f.length/2]+[u for u in np.arange(-f.length/2+1.35+shift,f.length/2,1.57)]+[f.length/2]
        for a,b in zip(spans,spans[1:]):
            if b-a<.06: continue
            slab=box(a+.009,z,b-.009,z+.61).difference(void)
            f.prism(slab,-.047,.050,'office granite','rusticated ground courses')
    for u,o in zip(axes,openings):
        low=o.bounds[1];hi=o.bounds[3];w=o.bounds[2]-o.bounds[0]
        f.prism(o.buffer(.009,join_style='mitre'),-.469,-.447,'entry glazing','entrance and shop glazing')
        for x in (-w/2+.058,w/2-.058,0):
            f.box(u+x,(hi+low)/2,.075,hi-low-.020,.13,-.32,'bronze window frame','door stiles')
        for z in (.18,2.69,hi-.065):
            f.box(u,z,w-.02,.105,.13,-.32,'bronze window frame','door rails')
        if corner:
            for x in (-w/2-.18,w/2+.18):
                f.box(u+x,2.20,.26,4.24,.38,.16,'office granite','entrance surround')
                for z,dz in [(3.82,.26),(4.07,.20),(4.23,.12)]:
                    f.box(u+x,z,.35,dz,.56,.24,'stone shade','scrolled door corbels')
            f.box(0,3.94,3.21,.50,.19,.082,'office granite','gold sign fascia')
            add_facade_lettering(f,'申報館',0,3.95,1.43,.28,.183,.216,'aged bronze',font=HERE/'fonts/ShenBaoSign.otf',label='entrance inscription')
            for k in range(22):
                f.box((k-10.5)*.143,4.27,.061,.085,.28,.12,'stone shade','small entrance dentils')
    if corner: return
    # The upper photographs resolve rectangular, pierced stone railing panels;
    # the rail stops on the two sides of the corner opening.
    f.box(0,4.61,f.length,.22,.90,.23,'office granite','balcony floor')
    count=round(f.length/.34)
    for k in range(count+1):
        x=(k/count-.5)*(f.length-.32)
        f.box(x,4.98,.105 if k%10 else .20,.67,.20,.620,'stone shade','pierced balcony stone rails')
    for z,h,depth in [(4.72,.10,.25),(5.37,.13,.35)]:
        f.box(0,z,f.length-.10,h,depth,.62,'office granite','balcony stone coping')
    for x in (-6.51,0,6.51):
        f.box(x,4.29,.36,.47,.66,.18,'office granite','balcony corbels')


def assemble(builder, lod):
    for i,(a,b,label) in enumerate(zip(FRONT,FRONT[1:],['Shandong Middle Road','Chamfered entrance','Hankou Road'])):
        f=Facade(builder,a,b,label)
        axes=[0.] if i==1 else SIDE_AXES
        ground(f,axes,i==1,lod)
        upper(f,axes,i==1,lod)
    for bottom,top,inside,out,material,title in [
            (4.42,4.57,-.19,.31,'office granite','base capping'),
            (4.56,4.70,-.21,.50,'stone shade','corner canopy moulding'),
            (8.16,8.31,-.23,.28,'stone shade','second storey course'),
            (8.30,8.39,-.15,.18,'stone relief','fine second storey bead'),
            (15.82,15.94,-.16,.18,'stone relief','architrave face'),
            (15.94,16.03,-.21,.32,'stone shade','architrave bead'),
            (16.89,16.98,-.12,.25,'stone relief','dentil lower moulding'),
            (17.12,17.22,-.25,.40,'stone shade','cornice spring'),
            (17.44,17.53,-.22,.90,'roof trim','main roof soffit'),
            (17.53,17.66,-.22,1.06,'stone shade','main roof lip'),
            (17.66,17.75,-.21,.96,'roof trim','top cornice')]:
        connected_band(builder,bottom,top,inside,out,material,title)
    plan=Polygon(P['study_uv_m'])
    builder.plan_prism(plan,.0,.12,'office granite','Plan/entrance floor')
    builder.plan_prism(plan,17.50,17.68,'roof skin','Plan/estimated office section roof')
    points=list(plan.exterior.coords)
    for a,b in zip(points[3:],points[4:]):
        Facade(builder,a,b,'Section boundary').wall(.12,17.56,(),.16,'stone shade')


if __name__ == '__main__':
    from final_preview import package
    package(build,HERE,META,PAL,assemble)
