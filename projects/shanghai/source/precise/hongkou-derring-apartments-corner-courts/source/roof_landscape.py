"""Roof houses and small roofing seams visible around the two covered courts."""
from pathlib import Path
import json
from shapely.geometry import LineString,Polygon
from shapely.geometry.polygon import orient

from photo_architecture import Facade
from street_elevation import CAP,COVER,METAL,ROOF,ROUGH,FRAME

ROOF_FEATURES=json.loads(Path(__file__).with_name('roof-houses.json').read_bytes())


def roof_houses(b,plan,holes,z,lod):
    for entry in ROOF_FEATURES:
        poly=Polygon(entry['outline_m']).intersection(plan.buffer(-.30,join_style=2))
        if poly.is_empty:raise ValueError('Roof house lies outside surveyed outer ring')
        top=z+entry['height_estimate_m'];label=entry['name']
        b.plan_prism(poly,z-.10,top-.13,ROUGH,label+' / walls')
        b.plan_prism(poly.buffer(.075,join_style=2),top-.13,top+.03,CAP,label+' / coping')
        b.plan_prism(poly.buffer(-.081,join_style=2),top+.031,top+.073,ROOF if entry['shape']=='tower' else METAL,label+' / roof')
    for idx,hole in enumerate(holes):
        # Both covers appear broadly opaque with fine longitudinal sheets in 2021.
        # Their detailed lower structure is outside the image-supported scope.
        zz=z-3.15;left,bottom,right,top=hole.bounds
        spacing=1.25 if not lod else 2.5
        x=left+spacing*.5
        while x<right:
            line=LineString([(x-.35,bottom-.4),(x+.35,top+.4)])
            seam=hole.buffer(-.17).intersection(line.buffer(.023,cap_style=2))
            if not seam.is_empty:b.plan_prism(seam,zz+.004,zz+.035,METAL,'West cover seams' if idx==0 else 'East cover seams')
            x+=spacing
    # Narrow raised lip runs along the outer margins of the two main wings.
    lip=plan.buffer(-.31,join_style=2).difference(plan.buffer(-.48,join_style=2))
    b.plan_prism(lip,z,z+.16,CAP,'Outer rooftop coping')
