"""Three glazing planes, separate projecting sill courses and a pair of tapered stone consoles."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade
from photograph import face_coordinates, wall_coordinates
from garden_wall import CREAM, FIELD, GLASS, PLINTH, SASH, EDGE

RECORDS = Path(__file__).resolve().parents[1] / 'measurements'
MEASURED = json.loads((RECORDS / 'oriel-facets.json').read_bytes())
RELIEF = {feature['feature']: feature['research_800x600_pixels']
          for feature in json.loads((RECORDS / 'garden-bay-relief-and-brackets.json').read_bytes())['features']}
RELIEF_BASE = 'Recessed cream apron panels'
CARVING = 'Pale stone on the apron ribbons'


def panels(face, index):
    bounds = box(-face.length / 2 + .008, -5.22, face.length / 2 - .008, -4.36)
    if index == 2:
        panel = Polygon(face_coordinates(face, RELIEF['front_panel_outline'])).intersection(bounds)
        ribbon = Polygon(face_coordinates(face, RELIEF['front_descending_pale_band'])).intersection(panel)
        names = ['front_opposing_pale_branch', 'front_top_and_bottom_notches']
        face.prism(ribbon, .015, .043, CARVING, 'diagonal folded ribbon')
    elif index == 3:
        panel = Polygon(face_coordinates(face, RELIEF['right_oblique_panel_outline'])).intersection(bounds)
        names = ['right_oblique_panel_stem_and_fork']
    else:
        points = face_coordinates(face, RELIEF['left_oblique_panel_visible_edges'])
        panel = box(points[:, 0].min() - .02, points[:, 1].min() - .025,
                    points[:, 0].max() + .025, points[:, 1].max() + .01).intersection(bounds)
        names = ['left_oblique_panel_visible_edges']
    face.prism(panel, -.013, .015, RELIEF_BASE, 'inset apron field')
    face.prism(panel.buffer(.027, join_style=2).difference(panel), -.005, .031, PLINTH, 'panel reveal')
    for name in names:
        line = LineString(face_coordinates(face, RELIEF[name]))
        stripe = line.buffer(.026 if index == 2 else .021, cap_style=2, join_style=2).intersection(panel)
        face.prism(stripe, .013, .038, CARVING, name.replace('_', ' '))


def consoles(builder):
    for side in ['left', 'right']:
        px = RELIEF[side + '_cantilever_profile']
        front = np.asarray(px)[[0, 1]]
        foot = np.asarray(px)[[6, 7]]
        x = np.mean(wall_coordinates(front, -.70)[:, 0])
        width = np.ptp(wall_coordinates(front, -.70)[:, 0])
        shoulder_z = np.mean(wall_coordinates(front, -.70)[:, 1])
        toe_z = np.mean(wall_coordinates(foot, -.025)[:, 1])
        profile = [(-.70, shoulder_z), (.115, shoulder_z), (.115, toe_z),
                   (-.025, toe_z), (-.15, toe_z + .038), (-.30, toe_z + .142),
                   (-.46, toe_z + .265), (-.59, shoulder_z - .097), (-.70, shoulder_z - .028)]
        builder.prism(Polygon(profile), x-width/2, x+width/2, lambda y,z,u:(u,y,z),
                      PLINTH, 'Lower consoles/'+side+' curved support')


def add_oriel(builder):
    axes = MEASURED['faceted_bay_xy']
    shape = Polygon([*axes, (axes[-1][0], .105), (axes[0][0], .105)])
    center_sill = MEASURED['sill_elevation_m']
    front = Facade(builder, axes[2], axes[3])
    apron_bottom = face_coordinates(front, [[559, 324]])[0, 1]
    head = face_coordinates(front, [[560, 220]])[0, 1]
    builder.plan_prism(shape.buffer(.055, join_style=2), apron_bottom-.073, apron_bottom+.06,
                       PLINTH,'Oriel belts/lower projecting course')
    builder.plan_prism(shape.buffer(.021, join_style=2), apron_bottom+.059, apron_bottom+.105,
                       FIELD,'Oriel belts/top of lower course')
    builder.plan_prism(shape.buffer(.081, join_style=2), center_sill-.069, center_sill+.048,
                       PLINTH,'Oriel belts/window sill')
    builder.plan_prism(shape.buffer(.038, join_style=2), head-.038, head+.15,
                       PLINTH,'Oriel belts/head and soffit')
    for i,(a,c) in enumerate(zip(axes,axes[1:])):
        face = Facade(builder, a, c, 'Three sided garden oriel '+str(i+1))
        outer = box(-face.length/2,apron_bottom+.045,face.length/2,head+.115)
        if i not in (1,2,3):
            face.prism(outer,-.109,.0,CREAM,'solid wall return')
            continue
        u,v,x,y = MEASURED['glass_samples'][i-1]['approx_image_xyxy']
        outline=[[u,v],[x,v],[x,y],[u,y]]
        bounds = box(-face.length/2+.006,center_sill+.038,face.length/2-.006,head-.016)
        def projected_at(depth):
            shift=face.n[:2]*depth
            plane=Facade(builder,np.asarray(a)+shift,np.asarray(c)+shift)
            return Polygon(face_coordinates(plane,outline))
        # At the steep left facet a square reveal hides nearly all of the actual
        # 12-pixel light. Splay the jamb to accommodate the front and rear sightlines.
        glass_shape=projected_at(-.082)
        daylight=projected_at(-.036)
        opening=unary_union([projected_at(.006),projected_at(-.108)]).convex_hull.buffer(.032,join_style=2).intersection(bounds)
        if opening.is_empty:
            raise ValueError('A photographed pane falls outside the measured facade')
        face.prism(outer.difference(opening),-.108,0.,CREAM,'pier and apron with through opening')
        x0,z0,x1,z1=daylight.bounds
        bar=z0+(z1-z0)*.682
        frame_bars=[box(x0-.01,bar-.031,x1+.01,bar+.031)]
        if i==2:
            mid=(x0+x1)/2
            frame_bars.append(box(mid-.034,z0-.01,mid+.034,bar))
        # The visible border follows the same projection on the recessed sash.
        glass=daylight.difference(unary_union(frame_bars))
        backing=opening.union(glass_shape).buffer(.008,join_style=2)
        face.prism(backing,-.104,-.082,GLASS[4 if i==1 else 2],'recessed window glass')
        face.prism(opening.difference(glass),-.043,-.036,SASH,'window joinery')
        bead=opening.buffer(.019,join_style=2).difference(opening).intersection(outer)
        face.prism(bead,-.018,.009,EDGE,'narrow raised bead')
        panels(face,i)
    consoles(builder)
