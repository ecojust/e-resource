"""Visible backing to open sashes, bounded by the photographed window rebates."""
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon
from photo_architecture import Facade
from photo_plane import original, front_shape, wall_coordinates

# The lower curtains are visible through the open leaves in the 2017 photograph.
# Use an original shallow geometric weave. Individual flowers are not legible.
LINEN = 'Linen visible behind lower sashes'
WEFT = 'Muted curtain weave'
SHADOW = 'Dark recess behind upper casements'
PALETTE = {
    'Recessed timber jamb lining': dict(color=[.11,.077,.056], roughness=.84),
    'Painted opening sill': dict(color=[.16,.086,.055], roughness=.81),
    LINEN: dict(color=[.31,.315,.259], roughness=.96),
    WEFT: dict(color=[.265,.272,.227], roughness=.97),
    SHADOW: dict(color=[.017,.019,.019], roughness=.97),
}
LOWER = [(101,599),(495,553),(520,768),(86,803)]
UPPER = [(143,207),(299,152),(352,126),(398,124),(440,132),(459,249),(134,309)]


def add_window_backing(builder, lod):
    facade = Facade(builder,(-5,0),(5,0),'Photographed window recess')
    tiers = json.loads((Path(__file__).resolve().parents[1]/'measurements/arch-outlines.json').read_text())['tiers']
    for tier, sill in [('upper',[(134,319),(470,253)]),('lower',[(84,818),(530,774)])]:
        # The aperture is set out on the front wall, while the timber heads and
        # fanlight are recessed. A continuous lining closes the junction behind
        # both planes and covers the photographed strip beneath the sprung arch.
        lip = wall_coordinates(tiers[tier]['front_intrados'],-.022)
        sill_ends = wall_coordinates([original(*uv) for uv in sill],0)
        aperture = Polygon([*lip,*sill_ends[::-1]]).buffer(.13)
        facade.prism(aperture,-.302,-.293,'Recessed timber jamb lining',tier+' jamb and arch liner')
        sill_face = Polygon([sill_ends[0]+[-.035,-.025],sill_ends[1]+[.035,-.025],
                             sill_ends[1]+[.035,.047],sill_ends[0]+[-.035,.047]])
        facade.prism(sill_face,-.291,.027,'Painted opening sill',tier+' recessed sill')
    for label, pixels, depth, material in [
        ('curtain behind lower window', LOWER, .234, LINEN),
        ('open upper window darkness', UPPER, .25, SHADOW)
    ]:
        polygon = front_shape([original(*uv) for uv in pixels],depth)
        facade.prism(polygon,-depth-.009,-depth,material,label)
        if material != LINEN:
            continue
        minx,minz,maxx,maxz = polygon.bounds
        for index,x in enumerate(np.arange(minx-.05,maxx,.095 if lod else .055)):
            # Narrow vertical folds follow the hanging fabric. Keep the visible
            # upper fanlight clear and the return inside the window opening.
            ys = np.linspace(minz,maxz,6)
            line = [(x+.0035*math.sin(3.8*z+.7*index),z) for z in ys]
            fold = Polygon(line+[(u+.005,v) for u,v in reversed(line)]).intersection(polygon)
            if fold.area>.00001:
                facade.prism(fold,-depth-.001,-depth+.003,WEFT,'lower curtain folds')
