"""The photographed twin-peak lintel on the south entrance of Rongkang Villas."""
import json
from pathlib import Path
from shapely.geometry import Polygon, box

DIRECTORY = Path(__file__).resolve().parents[1] / 'measurements'
PLAN = json.loads((DIRECTORY / 'southern-lane-registration.json').read_bytes())
LINES = json.loads((DIRECTORY / 'southern-lane-stone-outline.json').read_bytes())
FIELD = 'South lintel | sandy ochre facing'
CAP = 'South lintel | stone-coloured moulding'
ORNAMENT = 'South lintel | pale central ornament'


def material(rgb):
    unit = [c/255 for c in rgb]
    return {'color': [((c+.055)/1.055)**2.4 if c>.04045 else c/12.92 for c in unit], 'roughness': .88}


PALETTE = {FIELD: material([175,144,108]), CAP: material([204,197,177]),
           ORNAMENT: material([210,201,180])}


def native_xz(uv):
    u,v = uv
    base_v = 2263 + (u-2468)*12/716
    return ((u-2827)*PLAN['width_m']/716,
            PLAN['underside_m'] + (base_v-v)*PLAN['reference_rise_m']/218)


def boundary():
    """Return the south and north tips, underside and top in the agreed frame."""
    return (native_xz([2468,2263])[0], native_xz([3184,2275])[0],
            PLAN['underside_m'], PLAN['highest_m'])


def flat(x,z,d):
    return x,-d,z


def add_lane_head(b, lod=False):
    low = lod is True or lod == 'lod'
    depth = LINES['projection_m']
    def polygon(points):
        return Polygon([native_xz(uv) for uv in points])
    def relief(points, start, end, surface, name):
        b.prism(polygon(points), start, end, flat, surface, name)
    upper = LINES['crown_top_uv']
    inner = LINES['crown_inner_uv']
    if low:
        upper = [p for i,p in enumerate(upper) if i not in (5,7,9,11)]
        inner = [p for i,p in enumerate(inner) if i not in (5,8)]
    relief(upper + [[3184,2275],[2468,2263]], -depth['backing_behind_plaster'], 0.,
           FIELD, 'Plaque body with photographed saddle between peaks')
    relief(upper + list(reversed(inner)), -.002, depth['cap_front'],
           CAP, 'Returning pale cap across both peaks and shoulders')
    relief(LINES['base_uv'], -.002, depth['base_front'], CAP, 'Continuous underside moulding')
    for side, group in LINES['stripes'].items():
        u0,u1 = group['range_u']
        # Slope of the fascia in the source image is also present on the sill.
        def rect(row, u):
            return row + (u-group['reference_u'])*12/716
        for i,(top,bottom) in enumerate(group['rows_v'],1):
            points = [[u0,rect(top,u0)], [u1,rect(top,u1)],
                      [u1,rect(bottom,u1)], [u0,rect(bottom,u0)]]
            relief(points,-.001,depth['horizontal_strips_front'],CAP,f'{side} horizontal band {i}')
    lower = LINES['plate_lower_uv']
    upper = LINES['plate_upper_limit_uv']
    plate = polygon(upper + list(reversed(lower)))
    lz, uz = plate.bounds[1], plate.bounds[3]
    def plate_depth(z):
        return max(.001, depth['plate_foot_front'] * (uz-z)/(uz-lz))
    b.prism(plate,0,1,lambda x,z,d: (x,.001-d*(plate_depth(z)+.001),z),
            FIELD,'Shallow central field with raised lower seam')
    badge = polygon(LINES['badge']['stroke_contours_native_uv']['lod' if low else 'full'])
    b.prism(badge,0,1,lambda x,z,d: (x,-plate_depth(z)-d*depth['badge_front_above_face'],z),
            ORNAMENT,'Paired scrolls and central upright with two terminals')
