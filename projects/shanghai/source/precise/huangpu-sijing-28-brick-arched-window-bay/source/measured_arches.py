"""Build the photographed radial brickwork and recessed intrados of both eastern window arches."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon
from photo_architecture import Facade
from photo_plane import front_shape, position, wall_coordinates

MEASUREMENTS = Path(__file__).resolve().parents[1] / 'measurements' / 'arch-outlines.json'
BRICK = {'red':'Red radial arch brick','blue':'Blue-grey radial arch brick'}
MORTAR = 'Arch pointing'
RIM = 'Cut red rim brick'
STONE = 'Pale keystone and skewbacks'

def fired_color(rgb):
    srgb = np.asarray(rgb) / 255.
    return dict(color=np.where(srgb < .04045,srgb/12.92,((srgb+.055)/1.055)**2.4).tolist(),roughness=.92)

# Median photo samples of the two storeys, with the lower tier in more daylight.
PALETTE = {BRICK['red']:fired_color([130,87,76]),BRICK['blue']:fired_color([114,118,121]),
           RIM:fired_color([123,82,73]),MORTAR:fired_color([177,176,168]),STONE:fired_color([171,171,154])}
# These points bound the pale springing blocks separately from the radial bricks,
# avoiding the neighbouring arch on the other side of the left-hand pier.
SPRING_BLOCKS = {
    'lower': [[(2822,1618),(2900,1688),(2902,1743),(2750,1754),(2751,1640)],
              [(4250,1380),(4275,1376),(4282,1512),(4140,1530),(4136,1500)]],
    'upper': [[(2955,532),(3028,575),(3016,592),(2820,623),(2861,575)],
              [(4078,220),(4098,217),(4106,278),(3965,306),(3980,292)]]}

def shape(points, depth, lod):
    polygon = front_shape(points,depth).buffer(0)
    if lod:
        polygon = polygon.simplify(.0023,preserve_topology=True)
    return polygon

def add_intrados(builder, row, tier, lod):
    # A slight inset into the opening separates the dedicated brick returns
    # from the continuous mortar arch behind them. The exposed normals point down.
    for item in row['visible_intrados']:
        original = item['line'][::2] if lod else item['line']
        xz = wall_coordinates(original,-.022)
        xz[:,1] -= .0028
        front = [(x,-.0215,z) for x,z in xz]
        back = [(x,.159,z) for x,z in xz]
        count = len(front)
        faces = [[i+1,i,i+count,i+count+1] for i in range(count-1)]
        builder.add(front+back,faces,BRICK[item['color']],tier+'/'+item['id'])

def add_arches(builder,lod):
    report = json.loads(MEASUREMENTS.read_bytes())
    facade = Facade(builder,(-4,0),(4,0),'Measured brick arches')
    for tier,row in report['tiers'].items():
        outline = row['outer'] + list(reversed(row['front_intrados']))
        body = shape(outline,-.022,lod)
        facade.prism(body,-.16,.013,MORTAR,tier+' arch pointing and intrados')
        for item in row['face_cells']:
            face = shape(item['polygon'],-.022,lod)
            facade.prism(face,.011,.022,BRICK[item['color']],item['id'])
        for item in row['rim_bricks']:
            face = shape(item['polygon'],-.036,lod)
            facade.prism(face,.011,.036,RIM,item['id'])
        add_intrados(builder,row,tier,lod)
        # The key is pale both on the face and beneath its deep projecting nose.
        key = shape(row['key'],-.06,lod)
        facade.prism(key,-.16,.060,STONE,tier+' projecting keystone')
        for i,points in enumerate(SPRING_BLOCKS[tier],1):
            facade.prism(shape(points,-.024,lod),-.16,.024,STONE,tier+' pale springing block '+str(i))
