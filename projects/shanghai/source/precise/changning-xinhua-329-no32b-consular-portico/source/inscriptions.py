"""Place photographed ink contours and the two legible, re-typeset plaque headings."""
import json
from pathlib import Path
from shapely.geometry import Polygon


def add_ink(builder, point, plate, wall, gilt, dark):
    readings = json.loads(Path(__file__).with_name('inscription-readings.json').read_bytes())

    def add(group, y, thickness, mat, label):
        def loop_to_world(ring):
            return [point(u * 537 / 1280, v * 805 / 1919, y)[[0,2]] for u,v in ring]
        for index, contour in enumerate(group):
            face = Polygon(loop_to_world(contour['outer']), [loop_to_world(r) for r in contour['holes']])
            plate(builder,face,y-thickness,y,mat,f'{label}/stroke island {index+1}')

    add(readings['paper']['contours'],wall-.0003,.0014,gilt,'fanlight/observed seasonal paper ink')
    for line in readings['plaque']['lines']:
        add(line['contours'],wall-.0272,.0012,dark,'plaque/'+line['text'])
