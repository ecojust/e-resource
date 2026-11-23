"""Street elevation's seven staggered green steel windows, in their photographed 2018 state."""
import json
from pathlib import Path

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade
from register_street import Camera

DATA = json.loads((Path(__file__).parent.parent / 'measurements/front-window-photo-points.json').read_bytes())
STEEL = 'Xinlefang | green-black rolled steel sash'
EDGE = 'Xinlefang | worn green transom nosing'
UPPER = 'Xinlefang | sky-lit steel window glass'
LOWER = 'Xinlefang | shaded steel window glass'
LINER = 'Xinlefang | dark reveal bed'
BACK = 'Xinlefang | unlit space behind glazing'
BRICK = 'Xinlefang | red facing units with pale mortar'
PALETTE = {
    STEEL: {'color': [.035,.064,.053], 'roughness': .48, 'metallic': .28},
    EDGE: {'color': [.058,.085,.069], 'roughness': .51, 'metallic': .27},
    UPPER: {'color': [.20,.30,.36], 'alpha': .79, 'roughness': .21, 'metallic': .29},
    LOWER: {'color': [.073,.122,.113], 'alpha': .77, 'roughness': .25, 'metallic': .20},
    LINER: {'color': [.09,.078,.069], 'roughness': .87},
    BACK: {'color': [.026,.030,.028], 'roughness': .94},
}
FRAME_DEPTH = .09


def front_openings():
    return [Polygon(row['rough_wall_xz_m']) for row in DATA['windows']]


def on_frame(camera, pixel):
    return camera.wall(pixel, FRAME_DEPTH)[[0,2]]


def add_front_windows(builder, lod=False):
    camera = Camera('2018')
    for row, opening in zip(DATA['windows'], front_openings()):
        face = Facade(builder,(-1,0),(1,0),'street sash/'+row['name'])
        a,b,c,d = [on_frame(camera,p) for p in row['frame_edge_2018_original_px']]
        # The measured rolled frame is square. Average corresponding jamb and rail
        # readings to remove sub-micrometre differences from pixel rounding.
        frame = box((a[0]+d[0])*.5,(c[1]+d[1])*.5,(b[0]+c[0])*.5,(a[1]+b[1])*.5)
        # The front jamb and the more deeply seated rolled frame are distinct.
        # Cover the opening behind the frame, leaving its individual lights open.
        pane_field = frame.buffer(-.021,join_style=2)
        frame_edge = frame.difference(pane_field)
        closure = opening.union(frame).buffer(.014,join_style=2)
        face.prism(closure.difference(pane_field),-.154,-.118,LINER,'rebate behind steel')
        face.prism(closure,-.29,-.275,BACK,'depth behind glazing')
        face.prism(frame_edge,-.117,-.086,STEEL,'rolled surround')
        left,bottom,right,top = frame.bounds
        stile = on_frame(camera,row['meeting_stile_px'])[0]
        divisions = [on_frame(camera,p)[1] for p in row['crossbars_2018_original_px']]
        transom = row.get('transom_2018_original_px')
        head = on_frame(camera,transom)[1] if transom else top
        bars = [box(left,z-.008,right,z+.008) for z in divisions]
        # The two leaves close onto a thicker meeting stile. The top lights
        # have a slender central bar independent of the meeting stiles beneath.
        bars.append(box(stile-.025,bottom,stile+.025,head))
        if transom:
            bars.extend((box(left,head-.026,right,head+.026),
                         box(stile-.010,head,stile+.010,top)))
        cuts = unary_union(bars)
        steel = cuts.intersection(pane_field)
        face.prism(steel,-.112,-.087,STEEL,'meeting stile and glazing bars')
        glass = UPPER if transom else LOWER
        for i,light in enumerate(_polygons(pane_field.difference(cuts)),1):
            # Discrete panes leave no transparent duplicate behind the steel.
            face.prism(light,-.111,-.105,glass,f'glass light {i:02}')
        if transom and not lod:
            bead=box(left,head-.009,right,head+.010).intersection(pane_field)
            face.prism(bead,-.087,-.073,EDGE,'leading lip of transom')
        if row['separate_brick_sill']:
            coords=list(opening.exterior.coords)
            a,b=coords[3],coords[2]
            slab=Polygon([(a[0]-.037,a[1]-.003),(b[0]+.037,b[1]-.003),
                          (b[0]+.037,b[1]-.101),(a[0]-.037,a[1]-.101)])
            face.prism(slab,-.012,.043,BRICK,'short brick sill')


def _polygons(geometry):
    if isinstance(geometry,Polygon):
        return [geometry]
    return [part for part in geometry.geoms if isinstance(part,Polygon) and part.area>1e-6]
