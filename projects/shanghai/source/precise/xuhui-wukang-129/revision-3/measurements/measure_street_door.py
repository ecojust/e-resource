"""Register the two plaques and trace the readable 2017 number from its original pixels."""
import argparse
import hashlib
import json
from pathlib import Path

import contourpy
import numpy as np
from PIL import Image
from shapely.geometry import Polygon

from register_openings import Camera

CONTROL = {
    2017: {
        'plaque': [3160, 1687, 3231, 1742],
        'crest_top': [3202,1777], 'crest_shoulder': [3171,1807],
        'crest_foot_right': [3240,1910],
        'handle_high': [3327,2040], 'handle_low': [3323,2109],
    },
    2026: {
        'plaque': [1037,732,1058,749],
        'crest_top': [1049,760], 'crest_shoulder': [1039,766],
        'crest_foot_right': [1060,796],
        'letter_slot_left': [1039,804], 'letter_slot_right': [1060,804],
        'handle_high': [1082,833], 'handle_low': [1082,854],
    },
}
ORIGINAL_SHA = '89e59d2e55cd33b16636b004f09aa8d00994a6a93ffd654e8daf714ac51922b5'
# The small lower row is visible as three pale groups. Optical blur precludes
# reading the fine strokes from their pixel boundaries.
GLYPHS = {'1': (3166,1689,3184,1724), '2': (3184,1688,3202,1723),
          '9': (3203,1687,3223,1723), 'road-left': (3172,1724,3186,1740),
          'road-centre': (3187,1724,3201,1740), 'road-right': (3202,1723,3218,1739)}

def trace_glyph(image, bounds, camera):
    left,top,right,bottom=bounds
    green=np.asarray(image.crop(bounds),dtype=float)[:,:,1]
    outlines=contourpy.contour_generator(x=np.arange(left,right),y=np.arange(top,bottom),z=green).lines(101.)
    loops=[]
    for path in outlines:
        if not np.allclose(path[0],path[-1]):
            raise ValueError(f'Trace intersects photograph crop {bounds}')
        polygon=Polygon([camera.wall(xy,.035)[[0,2]] for xy in path]).simplify(.00066)
        if polygon.area>.000013:
            loops.append(polygon)
    if not loops:
        raise ValueError(f'No outlined lettering in {bounds}')
    outer=max(loops,key=lambda p:p.area)
    holes=[loop for loop in loops if loop!=outer and outer.contains(loop)]
    def ring(poly):
        return [[round(float(x),6),round(float(z),6)] for x,z in list(poly.exterior.coords)[:-1]]
    return {'exterior':ring(outer),'holes':[ring(p) for p in holes]}

def measure(image_path):
    assert hashlib.sha256(image_path.read_bytes()).hexdigest()==ORIGINAL_SHA
    result={'photo_2017':'Antigng, Wikimedia Commons, CC BY-SA 4.0','photo_2017_sha256':ORIGINAL_SHA,
            'photo_2026':'Windmemories, Wikimedia Commons, CC BY-SA 4.0',
            'coordinates':'U and Z in metres on a conditional plate face 0.035 m inside the street plane. Native image pixel centres.',
            'images':{},'lettering_note':'Numerals and the three small pale groups follow the 2017 contours. The letter-by-letter strokes of the lower row cannot be resolved.',
            'selection':'Two dates support a common centre (1.958,1.771), width 0.185 and height 0.146 m. Slightly rounded corners and plate thickness are conditional. The horizontal brass-coloured slot is identifiable in 2026.',
            'glyphs':{}}
    for year,controls in CONTROL.items():
        camera=Camera(year)
        left,top,right,bottom=controls['plaque']
        def coordinates(pixel):
            return camera.wall(pixel,.035)[[0,2]].round(6).tolist()
        result['images'][str(year)]={'original_pixels':controls,
            'plaque_corners_u_z':[coordinates(p) for p in [(left,top),(right,top),(right,bottom),(left,bottom)]],
            'plaque_centre_u_z':coordinates(((left+right)/2,(top+bottom)/2)),
            'fittings_u_z':{name:coordinates(xy) for name,xy in controls.items() if name!='plaque'}}
    with Image.open(image_path) as im:
        for name,bounds in GLYPHS.items():
            result['glyphs'][name]=trace_glyph(im,bounds,Camera(2017))
    assert len(result['glyphs']['9']['holes'])==1
    return result

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('original_2017',type=Path)
    cli.add_argument('output',type=Path)
    args=cli.parse_args()
    args.output.write_text(json.dumps(measure(args.original_2017),ensure_ascii=False,indent=2)+'\n')
