"""Individual raised capitals on the brick stringcourse facing Yuanmingyuan Road."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import LineString
from shapely.ops import unary_union

from east_photo_plane import on_wall
from street_entrance import plate, METAL

# These centre lines follow the shapes of the plain metal capitals in the two
# photographs. Letter widths and spacing are recorded separately per occurrence.
STROKES = {
    'Y': [[(0,1),(.5,.49),(1,1)],[(.5,.49),(.5,0)]],
    'U': [[(0,1),(0,.28),(.08,.11),(.26,.029),(.51,.009),(.77,.032),(.94,.14),(1,.29),(1,1)]],
    'A': [[(0,0),(.48,1),(.54,1),(1,0)],[(.21,.39),(.80,.39)]],
    'N': [[(0,0),(0,1),(1,0),(1,1)]],
    'M': [[(0,0),(0,1),(.52,.28),(1,1),(1,0)]],
    'I': [[(.5,0),(.5,1)]],
    'G': [[(.94,.83),(.81,.96),(.58,1),(.28,.96),(.09,.78),(0,.52),(.05,.27),(.20,.08),(.46,0),(.75,.02),(.95,.16),(.95,.47),(.57,.47)]],
    'P': [[(0,0),(0,1),(.57,1),(.79,.96),(.98,.81),(.99,.67),(.85,.55),(.64,.49),(0,.49)]],
    'R': [[(0,0),(0,1),(.58,1),(.83,.94),(.98,.79),(.93,.64),(.75,.55),(0,.55)],[(.52,.54),(1,0)]],
    'T': [[(0,1),(1,1)],[(.5,1),(.5,0)]],
    'E': [[(1,1),(0,1),(0,0),(1,0)],[(0,.51),(.81,.51)]],
    'S': [[(.98,.84),(.83,.97),(.57,1),(.28,.98),(.08,.89),(.03,.73),(.18,.59),(.63,.47),(.86,.39),(1,.25),(.9,.09),(.65,.009),(.31,0),(.10,.07),(0,.18)]],
}
DATA=Path(__file__).resolve().parents[1]/'measurements/english-entrance-layout.json'


def add_english_name(builder,lod=False):
    measured=json.loads(DATA.read_bytes())
    depth=measured['front_depth_m']
    for i,(letter,centre,width) in enumerate(measured['letters'],1):
        paths=[]
        for stroke in STROKES[letter]:
            points=[]
            for x,z in stroke:
                u=centre+(x-.5)*width
                baseline=np.interp(u,[495.,707.],[383.4,382.0])
                v=baseline-z*measured['height_px']
                world=on_wall(u,v,depth,'2016_front')
                points.append((world[0],world[2]))
            paths.append(LineString(points).buffer(.0156,cap_style=2,join_style=1,quad_segs=2 if lod else 5))
        plate(builder,unary_union(paths),depth,depth+.032,METAL,f'English entrance name {i:02} {letter}')
