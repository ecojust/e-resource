"""Open balconies and the numbered court wall visible in the 2016 No. 9 photograph."""
import json
from math import cos, pi, sin
from pathlib import Path

import numpy as np
from shapely.affinity import scale, translate
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
SLAB = 'Qixia 9 | blue grey concrete balcony slab'
IRON = 'Qixia 9 | dark iron balcony rail'
RENDER = 'Qixia 9 | pale ochre court wall'
PIER = 'Qixia 9 | grey rendered court pier'
COPING = 'Qixia 9 | weathered court coping'
ENAMEL = 'Qixia 9 | green address enamel'
LETTER = 'Qixia 9 | ivory enamel numeral'


def finish(rgb, roughness, metallic=0.):
    s = np.asarray(rgb)/255.
    return dict(color=np.where(s <= .04045, s/12.92, ((s+.055)/1.055)**2.4).tolist(),
                roughness=roughness, metallic=metallic)


PALETTE = {
    SLAB: finish((147, 162, 172), .92), IRON: finish((48, 50, 49), .72, .28),
    RENDER: finish((191, 175, 133), .93), PIER: finish((125, 129, 130), .92),
    COPING: finish((111, 113, 110), .95), ENAMEL: finish((48, 107, 84), .49, .18),
    LETTER: finish((212, 219, 190), .52, .05),
}


def controls():
    return json.loads((ROOT/'measurements/no9-court-controls.json').read_text())


def level_section(camera, data, front_y):
    """Return horizontal construction levels and the four photographed X breaks."""
    def project(uv):
        p = camera.wall(uv, front_y)
        return float(p[0]), float(p[2])

    top = float(np.median([project(p)[1] for p in data['edge_top']]))
    underside = float(np.median([project(p)[1] for p in data['edge_bottom']]))
    handrail = float(np.median([project(p)[1] for p in data['black_handrail']]))
    cut = project(data['edge_top'][0])[0]
    divide_left, divide_right = sorted(float(np.mean([project(p)[0] for p in line]))
                                       for line in data['fixed_divider_edges'])
    rail_end = project(data['edge_top'][-1])[0]
    tip = project(data['right_tip_top'])[0]
    if not (cut < divide_left < divide_right < rail_end < tip and underside < top < handrail):
        raise ValueError('The court camera must use the registered X,Y,Z axes and photo 20.')
    return dict(cut=cut, divide_left=divide_left, divide_right=divide_right,
                end=rail_end, tip=tip, top=top, underside=underside, handrail=handrail)


def add_deck(builder, x0, x1, nose, front, back, base, top, lod, label):
    """Keep the actual right-hand overrun and turn of the thin concrete lip."""
    r = min(nose-x1, .46*(back-front))
    perimeter = [(x0,front),(x1,front)]
    if r > 0:
        for a in np.linspace(-pi/2, 0, 3 if lod else 9)[1:]:
            perimeter.append((x1+r*cos(a),front+r+r*sin(a)))
    perimeter.extend([(x1+r,back),(x0,back)])
    builder.prism(Polygon(perimeter), base, top, lambda x,y,z:(x,y,z), SLAB, label)


def diamond(builder, x, y, z, label):
    # Outline of the small open lozenge at mid-height of selected upright bars.
    w, h = .023, .037
    outer = Polygon([(x-w,z),(x,z-h),(x+w,z),(x,z+h)])
    inner = outer.buffer(-.0058,join_style=2)
    builder.prism(outer.difference(inner), -.005, .005,
                  lambda u,v,d:(u,y-d,v), IRON, label)


def add_guard(builder, x0, x1, front, section, pitch, observed_axes, bosses, label):
    z0, z1 = section['top'], section['handrail']
    height = z1-z0
    # Pickets descend to the deck. Many are visible through the open court air.
    y = front+.025
    guides = [x0, *(x for x in observed_axes if x0+.035 < x < x1-.035), x1]
    positions = [x0]
    for left,right in zip(guides,guides[1:]):
        count = max(1,round((right-left)/pitch))
        positions.extend(np.linspace(left,right,count+1)[1:])
    builder.box(((x0+x1)/2,y,z1), (x1-x0,.026,.023), IRON, label=label+' | handrail')
    builder.box(((x0+x1)/2,y,z0+.027), (x1-x0,.018,.017), IRON, label=label+' | foot flat')
    for i, x in enumerate(positions):
        stile = i in (0,len(positions)-1) or i%7 == 0
        width = .023 if stile else .012
        builder.box((x,y,(z0+z1)/2), (width,.019 if stile else .012,height),
                    IRON,label=label+f' | upright {i+1:02d}')
    for j,(x,z) in enumerate(bosses,1):
        if x0 < x < x1:
            closest = min(positions,key=lambda u:abs(u-x))
            diamond(builder,closest,y-.009,z,label+f' | open lozenge {j}')


def add_wall(builder, camera, data, court_y, lod):
    """A foreground wall between separate piers. Only the left-hand numeral is legible."""
    label='No 9 court wall'
    def coord(uv,depth=court_y):
        pt=camera.wall(uv,depth)
        return float(pt[0]),float(pt[2])
    def piece(x0,x1,z0,z1,d0,d1,material,name):
        builder.box(((x0+x1)/2,(d0+d1)/2,(z0+z1)/2),(x1-x0,d1-d0,z1-z0),
                    material, label=label+' | '+name)
    wall_top=float(np.median([coord(p)[1] for p in data['wall_top']]))
    wall_face_top=float(np.median([coord(p)[1] for p in data['coping_bottom']]))
    bounds=[]
    for key in ('left_pier_crown','right_pier_crown'):
        corners=[coord(p) for p in data[key]]
        x0,x1=min(p[0] for p in corners),max(p[0] for p in corners)
        top=np.mean([p[1] for p in corners[:2]])
        bottom=np.mean([p[1] for p in corners[2:]])
        bounds.append((x0,x1))
        side=key.split('_')[0]
        piece(x0+.009,x1-.009,0.,bottom,court_y,court_y+.246,PIER,side+' pier')
        piece(x0,x1,bottom,top,court_y-.012,court_y+.258,PIER,side+' projecting cap')
    x0,x1=bounds[0][1]-.006,bounds[1][0]+.006
    piece(x0,x1,0.,wall_face_top,court_y+.025,court_y+.195,RENDER,'plain rendered panel')
    piece(x0,x1,wall_face_top,wall_top,court_y+.013,court_y+.207,COPING,'continuous coping')
    for side in ('left','right'):
        key='left_plaque' if side=='left' else 'right_plate'
        panel_y=court_y-.005
        poly=Polygon([coord(uv,panel_y) for uv in data[key]])
        builder.prism(poly,0.,.008,lambda x,z,d:(x,panel_y+.004-d,z),ENAMEL,label+' | '+side+' green plate')
        if side=='left':
            # Original modelling of the loop and descending stroke. The tiny text is unreadable.
            ellipse=scale(Point(0,0).buffer(1,resolution=7 if lod else 14),.183,.166)
            tail=LineString([(.15,.028),(.127,-.113),(.035,-.23),(-.087,-.261)]).buffer(.041)
            glyph=unary_union((ellipse.difference(ellipse.buffer(-.068)),tail))
            a,b,c,d=poly.bounds
            glyph=translate(scale(glyph,c-a,d-b,origin=(0,0)),a+.52*(c-a),b+.57*(d-b))
            builder.prism(glyph,0.,.002,lambda u,v,t:(u,panel_y-.004-t,v),LETTER,label+' | numeral 9')


def add_no9_court(builder,camera,face_y,rear_y,lod=False,court_y=-2.40):
    """camera=Camera(20); face_y is the slab nose, rear_y the wall behind the balconies.

    The left and right portions of each level carry separate editable labels.
    The data stop at the visible cut through foliage on the left. The foreground
    court has an independent depth. Use court_y=None when assembling balconies alone.
    """
    if rear_y <= face_y:
        raise ValueError('The posterior slab support must be behind the iron guard.')
    for key,value in PALETTE.items():
        builder.palette.setdefault(key,value)
    data=controls()
    sections={level:level_section(camera,data[level],face_y) for level in ('middle','upper')}
    # Derive regular pitch from the clear middle section of the right guard.
    middle_pixels=data['middle']['visible_upright_section'][0]
    xs=[camera.wall((u,220.-.19*(u-398)),face_y+.025)[0] for u in middle_pixels]
    pitch=float(np.median(np.diff(xs)))
    for level,sec in sections.items():
        for left,right,tip,group in ((sec['cut'],sec['divide_left'],sec['divide_left'],'adjacent visible portion'),
                                    (sec['divide_left'],sec['end'],sec['tip'],'open court bay')):
            label=f'No 9 view | {level} | {group}'
            add_deck(builder,left,right,tip,face_y,rear_y,sec['underside'],sec['top'],lod,label+' | thin slab')
            guard_left=sec['divide_right'] if group=='open court bay' else left
            axes, bosses = [], []
            if level == 'middle' and group == 'open court bay':
                for uv in data[level]['measured_front_pickets']:
                    axes.append(float(camera.wall(uv,face_y+.025)[0]))
                for uv in data[level]['diamond_details_px']:
                    pt = camera.wall(uv,face_y+.016)
                    bosses.append((float(pt[0]),float(pt[2])))
            add_guard(builder,guard_left,right,face_y,sec,pitch,axes,bosses,label)
    if court_y is not None:
        add_wall(builder,camera,data['foreground'],court_y,lod)
    return sections
