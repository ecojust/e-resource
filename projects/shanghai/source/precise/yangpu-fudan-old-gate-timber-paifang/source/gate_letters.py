"""Black plaques and eight independently recorded relief characters on the reconstructed gate."""
import json
from pathlib import Path
from shapely.geometry import Polygon, box
HERE=Path(__file__).resolve().parents[1]/'measurements'
FIELD='Fudan | black lacquer'
GOLD='Fudan | gold brush lettering'
def faces():
    front=json.loads((HERE/'plaque-registration.json').read_bytes())['front']
    return {'front':front,'reverse':dict(half_width=1.122,top=3.86,bottom=3.14,top_y=.52,bottom_y=.33,center_x=0.)}
def add_letters_to_gate(b, geometry):
    data=json.loads((HERE/'inscription-contours.json').read_bytes())['faces']
    for side,plane in faces().items():
        direction=-1 if side=='front' else 1
        def locate(u,v,depth):
            x=plane['center_x']-direction*(u-.5)*2*plane['half_width']
            y=(1-v)*plane['bottom_y']+v*plane['top_y']+direction*depth
            z=(1-v)*plane['bottom']+v*plane['top']
            return x,y,z
        b.prism(box(0,0,1,1),-.062,0,locate,FIELD,side+' / lacquer inscription field')
        for item in data[side]['viewer_left_to_right']:
            for n,row in enumerate(item['polygons']):
                p=Polygon(row['exterior'],row['holes'])
                if not p.is_valid:raise ValueError(f"Invalid glyph outline {item['character']}")
                b.prism(p,.0003,.0048,locate,GOLD,f"{side} / gilded {item['character']} stroke {n+1}")
