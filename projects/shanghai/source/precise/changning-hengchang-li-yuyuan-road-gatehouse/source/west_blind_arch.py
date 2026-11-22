"""West return of the street tower, above the short band and ahead of the rear casement."""
from math import cos, pi, sin
from shapely.geometry import LineString, Polygon, box
from gatehouse_finishes import paint


LIME = 'Hengchang west arch | pale plaster'
ARRIS = 'Hengchang west arch | weathered arris'
OLD_BAND = 'Hengchang west arch | older muted band'
BAND = 'Hengchang west arch | russet return'
PALETTE = {LIME: paint((210,197,164), .91), ARRIS: paint((177,160,131), .89),
           OLD_BAND: paint((135,130,110), .9), BAND: paint((163,100,72), .85)}


def add_west_arch(b, lod, layout):
    """Model the two visible spring ends, the narrow moulding and the raised keystone."""
    for key, value in PALETTE.items():
        b.palette.setdefault(key, value)
    scale = layout['portal']['width'] / 6.34
    old = str(layout.get('period', '2022')).startswith('2018')

    def cast(outline, face, back, material, label):
        def west(y, z, x):
            return (scale*x, scale*y, scale*z)
        for part in getattr(outline, 'geoms', (outline,)):
            if part.geom_type == 'Polygon' and part.area > 1e-7:
                b.prism(part, face, back, west, material, 'West blind arch | '+label)

    # The north spring, crown and four exposed jamb-side points fix this semicircle.
    # The streetward end behind the post is reflected about the crown.
    count = 28 if lod else 64
    yc, spring, radius, rise = 1.208, 10.394, .997, .931
    centre = [(yc + radius*cos(pi*i/count), spring + rise*sin(pi*i/count))
              for i in range(count+1)]
    centre = LineString(centre)
    key = Polygon([(1.565,11.529),(1.215,11.515),(1.119,10.945),(1.374,10.951)])
    stopped = key.buffer(.003, join_style=2)
    rim = centre.buffer(.054,cap_style=2,join_style=1).difference(stopped)
    cast(rim,-.038,.003,ARRIS,'arch backing')
    bead = centre.buffer(.036,cap_style=2,join_style=1).difference(stopped)
    cast(bead,-.066,-.038,LIME,'raised face')
    cast(key,-.073,.002,ARRIS,'keystone sides')
    cast(key.buffer(-.012,join_style=2),-.112,-.073,LIME,'keystone face')

    # The current red course stops short of the casement farther north.
    # The 2015 view has a narrow, muted line before the street-front refurbishment.
    finish = OLD_BAND if old else BAND
    lo, hi = (8.815,8.870) if old else (8.771,8.885)
    cast(box(.012,lo,2.00,hi),-.062,.002,finish,'short horizontal band')
    if not old:
        cast(box(.012,lo+.025,2.00,hi-.008),-.080,-.062,finish,'band front face')
