"""Exterior joinery at the semicircular balcony of 129 Wukang Road.

Geometry and exterior materials: CC BY-SA 4.0. Sources: Antigng,
19 August 2017, and Windmemories, 9 February 2026, both via Wikimedia
Commons (CC BY-SA 4.0). Coordinates follow the existing tangent facade.
"""
import math

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union


WOOD = 'Wukang balcony | dark red painted joinery'
REFLECTION = 'Wukang balcony | cool reflecting glass'
DARK = 'Wukang balcony | shaded recess'
PALETTE = {
    WOOD: {'color': [.175, .046, .031], 'roughness': .52},
    REFLECTION: {'color': [.125, .159, .161], 'roughness': .30, 'metallic': .19},
    DARK: {'color': [.038, .033, .031], 'roughness': .97},
}
# Angles from the closed door plane. Each leaf is hinged on its outside jamb.
OPEN_ANGLES = {'left': 101.4, 'right': 50.3}
BAR_LEVELS = (3.186, 3.488, 3.803)


def half_arch(center, spring, radius, rise, segments):
    return [(center + radius*math.cos(i*math.pi/segments),
             spring + rise*math.sin(i*math.pi/segments)) for i in range(segments+1)]


def add_balcony_doors(builder, facade, hole, lod=False):
    """Fit the fixed fanlight, two outward leaves and a shallow shaded reveal."""
    for material,properties in PALETTE.items():
        builder.palette.setdefault(material,properties)
    x0, bottom, x1, top = hole.bounds
    center = (x0+x1)/2 + .019
    radius = .456
    spring = top-.478
    rise = top-.023-spring
    steps = 20 if lod else 44
    arch = half_arch(center, spring, radius, rise, steps)
    clear = Polygon([(center-radius,bottom+.029),(center+radius,bottom+.029),*arch])
    surround = hole.buffer(.009,join_style=2).difference(clear)
    facade.prism(surround,-.072,-.002,WOOD,'fixed-arched-jambs-and-threshold')
    # No room layout is visible. Four closed lining strips lead to a dark
    # image-space background, leaving the full space between the leaves open.
    straight = box(center-radius-.003,bottom+.025,center+radius+.003,spring+.01)
    rim = straight.buffer(.036,join_style=2).difference(straight)
    facade.prism(rim,-.36,-.052,DARK,'shaded-reveal-lining')
    facade.prism(straight.buffer(.024,join_style=2),-.39,-.37,DARK,'recess-background')

    fan = Polygon(arch)
    inner_radius, inner_rise = .216, .266
    inner = half_arch(center,spring,inner_radius,inner_rise,steps)
    ribs = [LineString(inner).buffer(.009,cap_style=2,join_style=2),
            box(center-.009,spring-.008,center+.009,spring+rise+.01)]
    for theta in [math.pi/4,3*math.pi/4]:
        start = (center+inner_radius*math.cos(theta),spring+inner_rise*math.sin(theta))
        end = (center+radius*math.cos(theta),spring+rise*math.sin(theta))
        ribs.append(LineString([start,end]).buffer(.010,cap_style=2))
    fixed_bars = unary_union(ribs)
    facade.prism(fan.intersection(fixed_bars),-.041,-.010,WOOD,'fanlight-ring-and-radii')
    facade.prism(fan.difference(fixed_bars),-.038,-.023,REFLECTION,'fanlight-glass')
    facade.prism(box(center-radius-.018,spring-.018,center+radius+.018,spring+.010),
                 -.057,-.004,WOOD,'fixed-transom')

    leaf_width = .426
    for side, sign, hinge in [('left',1,center-.430),('right',-1,center+.438)]:
        angle = math.radians(OPEN_ANGLES[side])
        # Increasing local x follows the original facade tangent even on the
        # right leaf: its free edge is at negative x. This preserves winding.
        along = facade.t*math.cos(angle) + sign*facade.n*math.sin(angle)
        normal = facade.n*math.cos(angle) - sign*facade.t*math.sin(angle)
        origin = facade.point(hinge,0.,0.)
        def leaf_point(x,z,depth):
            return origin + x*along + z*np.array([0.,0.,1.]) + depth*normal
        left, right = sorted((0.,sign*leaf_width))
        base, head = bottom+.039, spring-.024
        panel = box(left,base,right,head)
        aperture = box(left+.031,base+.052,right-.031,head-.035)
        bars = unary_union([box(left,z-.010,right,z+.010) for z in BAR_LEVELS])
        glass = aperture.difference(bars)
        builder.prism(panel.difference(glass),-.018,.018,leaf_point,WOOD,
                      'E-'+side+'-opened-stiles-rails-and-three-crossbars')
        builder.prism(glass,-.007,.005,leaf_point,REFLECTION,'E-'+side+'-opened-glass')
    return {'label':'E-bowed-balcony-opening','facade_label':facade.label,
            'opening_bounds':list(hole.bounds),'leaf_clear_width_m':leaf_width,
            'leaf_angles_from_closed_deg':dict(OPEN_ANGLES),'fixed_fanlight_spring_m':spring,
            'moving_sash_transverse_members_z_m':list(BAR_LEVELS),
            'facade_origin_enu':facade.center.tolist(),'facade_u_enu':facade.t.tolist(),
            'facade_outward_enu':facade.n.tolist(),
            'recess':'The dark backing bounds the visible shadow only.'}
