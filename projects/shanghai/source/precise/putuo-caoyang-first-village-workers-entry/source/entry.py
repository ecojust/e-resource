"""Entrance return and stair light recorded in the August 1952 People's Pictorial."""
from math import cos, pi, sin
from pathlib import Path

import numpy as np
from PIL import Image
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ID = 'putuo-caoyang-first-village-workers-entry'
WALL = 'Warm lime plaster'
BASE = 'Cement plinth'
FRAME = 'Dark painted joinery'
GLASS = 'Shaded glazing'
LIGHT = 'Pale reflected glazing'
SHADE = 'Doorway shadow'
BOARD = 'Timber soffit'
TILES = ('Fired tile in shadow', 'Fired tile', 'Dry tile face')
PALETTE = {
    name: {'color': color, 'roughness': rough} for name, color, rough in [
        (WALL, [1., 1., 1.], .94), (BASE, [.51, .50, .46], .97),
        (FRAME, [.23, .22, .18], .85), (GLASS, [.24, .26, .26], .39),
        (LIGHT, [.47, .48, .46], .41), (SHADE, [.115, .106, .091], .96),
        (BOARD, [.27, .24, .20], .91), (TILES[0], [.43, .32, .26], .96),
        (TILES[1], [.48, .365, .305], .94), (TILES[2], [.51, .40, .34], .95)
    ]
}
HEIGHT = 5.12
REAR = lambda u, z, d: (u, -d, z)
SIDE = lambda u, z, d: (-.82 + d, u, z)
FRONT = lambda u, z, d: (u, -2.14 - d, z)
STAIR = (-.53, .105, 2.22, 4.00)
DOOR = (1.30, 2.41, .105, 2.24)
SIDE_LOW = (-1.68, -.43, .96, 2.47)
SIDE_HIGH = (-1.68, -.43, 3.46, 4.91)
FRONT_LOW = (-3.03, -2.38, .97, 2.43)
FRONT_HIGH = (-3.03, -2.38, 3.47, 4.92)

def texture():
    path = Path(__file__).with_name('limewash.png')
    if not path.exists():
        rng = np.random.default_rng(1952)
        grain = rng.normal(0, 2.5, (256, 256))
        variation = rng.integers(0, 255, (20, 22), dtype=np.uint8)
        clouds = np.asarray(Image.fromarray(variation).resize((256, 256), Image.Resampling.BICUBIC))
        levels = grain + (clouds.astype(float) / 255 - .5) * 7
        rgb = np.array([224, 218, 201])[None, None, :] + levels[:, :, None]
        Image.fromarray(np.clip(rgb, 0, 255).astype('u1')).quantize(128).save(path)
    PALETTE[WALL]['texture'] = str(path)

def rect(model, mapper, extents, front, depth, material, label):
    left, right, bottom, top = extents
    model.prism(box(left, bottom, right, top), front - depth, front, mapper, material, label)

def wall(model, mapper, span, height, holes):
    full = box(span[0], 0, span[1], height)
    cuts = unary_union([box(l, b, r, t) for l, r, b, t in holes])
    for bottom, top, mat in [(0, .265, BASE), (.265, height, WALL)]:
        surface = full.intersection(box(span[0], bottom, span[1], top)).difference(cuts)
        model.prism(surface, -.22, 0, mapper, mat, 'Rendered masonry with through reveals')

def sash(model, mapper, extent, narrow=False, open_leaf=False):
    left, right, bottom, top = extent
    edge = .045
    center = (left + right) * .5
    for u in (left, right):
        rect(model, mapper, (u - .008, u + .038, bottom, top), -.035, .09, FRAME, 'Outer casement jamb')
    for z in (bottom, top):
        rect(model, mapper, (left, right, z - .03, z + .03), -.028, .10, FRAME, 'Sash sill and head')
    rect(model, mapper, (left - .06, right + .06, bottom - .074, bottom - .02), .094, .27, BASE, 'Projecting cement sill')
    def glazed(axes, l, r, depth, lower, upper, bars):
        for i in range(bars):
            z0 = lower + (upper-lower)*i/bars
            z1 = lower + (upper-lower)*(i+1)/bars
            rect(model, axes, (l, r, z0+.016, z1-.016), depth-.034, .012, LIGHT if i==bars-1 else GLASS, 'Recessed glass')
        for index in range(bars+1):
            z = lower + (upper-lower)*index/bars
            rect(model, axes, (l, r, z-.018, z+.018), depth, .038, FRAME, 'Horizontal glazing rail')
        for x in (l,r):
            rect(model, axes, (x-.022,x+.022,lower,upper), depth, .05, FRAME, 'Casement stile')
    if narrow:
        glazed(mapper,left+edge,right-edge,-.10,bottom+.025,top-.025,2)
    else:
        glazed(mapper,center,right-edge,-.075,bottom+.025,top-.025,4)
        if open_leaf:
            angle = .91
            def opened(u,z,d):
                offset = u - left-edge
                return mapper(left+edge+cos(angle)*offset-sin(angle)*d,z,-.075+sin(angle)*offset+cos(angle)*d)
            glazed(opened,left+edge,center,-.006,bottom+.025,top-.025,4)
        else:
            glazed(mapper,left+edge,center,-.075,bottom+.025,top-.025,4)

def roof(model, corner, across, uphill, columns, rows, far, label):
    corner = np.array(corner)
    across = np.array(across)
    uphill = np.array(uphill)
    normal = np.cross(across,uphill)
    normal = normal / np.linalg.norm(normal)
    if normal[2] < 0: normal = -normal
    def at(x, y, height): return corner + across*x + uphill*y + normal*height
    def quad(v, faces, m, name):model.add(v,faces,m,name)
    skin = [at(x,y,z) for z in (-.07,0.) for x,y in [(0,0),(1,0),(1,1),(0,1)]]
    faces = [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    quad(skin,faces,BOARD,label+' timber underside')
    grouped = {m:([],[]) for m in TILES}
    steps = 3 if far else 6
    for r in range(rows):
        for c in range(columns):
            mat = TILES[(r*5+c*7+c//5)%3]
            vertices, faces = grouped[mat]
            start = len(vertices)
            for t, ridge_height in [(-.085, .026),(.95, .008),(1.005,.005)]:
                y = max(0.,min(1.,(r+t)/rows))
                for j in range(steps+1):
                    f = j/steps
                    profile = .016*sin(pi*f)**2 + .022*max(0.,cos(2*pi*f))**2
                    vertices.append(at((c+f)/columns,y,ridge_height+profile))
            for k in range(2):
                for j in range(steps):
                    a=start+k*(steps+1)+j
                    faces.append((a,a+1,a+steps+2,a+steps+1))
            # Edge beneath each projecting course casts a short shadow.
            for j in range(steps+1):
                vertices.append(vertices[start+j]-normal*.019)
            edge = start+3*(steps+1)
            for j in range(steps):faces.append((edge+j,edge+j+1,start+j+1,start+j))
    for mat,(vertices,faces) in grouped.items():
        quad(vertices,faces,mat,label+' overlapping profiled tile courses')

def add_building(model, far=False):
    texture()
    wall(model, REAR, (-.84, 2.93), HEIGHT, [STAIR, DOOR])
    wall(model, SIDE, (-2.14, .04), HEIGHT, [SIDE_LOW,SIDE_HIGH])
    wall(model, FRONT, (-3.27,-.82), HEIGHT, [FRONT_LOW,FRONT_HIGH])
    # The left wall meets the underside of the roof all the way up its sloping front edge.
    left, right = -3.27, -.82
    front_heights = [5.078 + (-.68-x)*.85/2.64 for x in (left,right)]
    gable = Polygon([(left,HEIGHT-.015),(right,HEIGHT-.015),(right,front_heights[1]),(left,front_heights[0])]).buffer(0)
    model.prism(gable,-.22,0,FRONT,WALL,'Plastered front wall beneath the sloping verge')
    # Show a finished section at the outside cut, where the roof rises above the long eave.
    end = lambda u,z,d: (2.93+d,u,z)
    roof_end = Polygon([(0,HEIGHT-.02),(1.31,HEIGHT-.02),(1.31,5.875),(0,5.16)])
    model.prism(roof_end,-.115,0,end,WALL,'Return of the entrance roof above the end wall')
    sash(model, REAR, STAIR, narrow=True)
    for mapper, extent, open_leaf in [(SIDE,SIDE_LOW,True),(SIDE,SIDE_HIGH,False),(FRONT,FRONT_LOW,False),(FRONT,FRONT_HIGH,False)]:
        sash(model,mapper,extent,open_leaf=open_leaf)
    l,r,b,t = DOOR
    rect(model,REAR,DOOR,-.31,.03,SHADE,'Unlit entry behind the wall reveal')
    rect(model,REAR,(l-.06,r+.06,.01,b),.13,.45,BASE,'Slightly raised threshold')
    for x in (l-.09,r+.09):
        rect(model,REAR,(x-.055,x+.055,2.28,2.43),.41,.49,BOARD,'Dark backing below the hood')
    roof(model,(l-.235,-.64,2.40),(r-l+.47,0,0),(0,.685,.29),10,3,far,'Door canopy')
    roof(model,(-.94,-.23,5.11),(3.98,0,0),(0,1.47,.83),25,7,far,'Entrance roof')
    roof(model,(-.68,-2.34,5.14),(0,2.47,0),(-2.64,0,.85),17,9,far,'Returning roof')
    model.tube([(-.73,-.16,5.1),(-.70,-.09,4.94),(-.71,-.087,.30),(-.69,-.14,.18)],.043,FRAME,6 if far else 12,'Corner rainwater pipe')
    for part in model.parts:
        if part['material'] == WALL:
            # Horizontal distance follows both plastered faces of the courtyard return.
            part['texcoords'] = [[(x + y + 4.0) / 6.5, .03 + z / 6.4]
                                 for x, y, z in part['vertices']]
