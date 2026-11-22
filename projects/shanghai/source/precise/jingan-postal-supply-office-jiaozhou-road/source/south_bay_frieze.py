"""Street-side terracotta and plaster details on the southernmost double bay."""

import json
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

SOURCE = Path(__file__).resolve().parents[1]/'measurements'/'south-bay-frieze-observations.json'
READING = json.loads(SOURCE.read_text())
PLAN = READING['layout']
BRICK = 'South bay | dusty oxblood terracotta'
LIGHT = 'South bay | light lime stone'
SHADE = 'South bay | shaded inset'
GROOVE = 'South bay | dark brick joint'
RIDGE = 'South bay | warm relief ridge'


def material(rgb, roughness):
    c = np.array(rgb)/255.
    return dict(color=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),
                metallic=0.,roughness=roughness)


PALETTE = {BRICK:material([156,95,88],.90), LIGHT:material([208,202,181],.86),
           SHADE:material([99,96,82],.93), GROOVE:material([121,76,67],.92),
           RIDGE:material([168,110,99],.86)}


def add_south_bay_frieze(b, lod=False, *, head_z=None):
    """Use head_z for the shared height of the two ground-floor window heads."""
    coarse = lod is True or lod=='lod'
    height = PLAN['window_head_z_m'] if head_z is None else head_z
    def slab(poly,back,front,mat,label):
        b.prism(poly,back,front,lambda x,z,d:(x,-d,z+height),mat,label)
    def face(bounds,back,front,mat,label):
        x1,x2,z1,z2=bounds
        slab(box(x1,z1,x2,z2),back,front,mat,label)
    z0,z1=PLAN['lower_z']
    for i,(left,right) in enumerate(PLAN['lower_red_x']):
        face([left,right,z0,z1],-.010,.017,BRICK,f'Lower pair | red facing {i+1}')
        for n,t in enumerate(PLAN['lower_lines'][i],1):
            mid=left+t*(right-left)
            face([mid-.005,mid+.005,z0+.018,z1-.016],.016,.019,GROOVE,
                 f'Lower facing {i+1} | measured joint {n}')
    for i,(left,right) in enumerate(PLAN['lower_end_stones_x']):
        face([left,right,z0-.009,z1+.010],-.010,.026,LIGHT,f'Lower pair | pale separator {i+1}')
    u0,u1=PLAN['upper_band_z']
    for i,(left,right) in enumerate(PLAN['upper_red_x']):
        face([left,right,u0,u1],-.010,.021,BRICK,f'Upper pair | red frieze field {i+1}')
        paths=READING['detail_source']['visible_centerline_paths_relative_to_panel']
        # The right panel is the clearest. In the centre field retain only the
        # broad return confirmed between branches in the other street view.
        paths=paths[:1] if i==0 else paths
        strokes=[]
        for path in paths:
            line=LineString([(left+p*(right-left),u1-q*(u1-u0))for p,q in path])
            strokes.append(line.buffer(.009 if coarse else .010,cap_style=2,join_style=2))
        merged=unary_union(strokes)
        shapes=[merged] if merged.geom_type=='Polygon' else list(merged.geoms)
        for j,shape in enumerate(shapes):
            slab(shape,.020,.031,RIDGE,f'Upper frieze {i+1} | returned rib {j+1}')
    left,right=PLAN['pale_frame_x']
    inner=box(left+.071,u0+.087,right-.071,u1-.084)
    slab(box(left,u0,right,u1).difference(inner),-.008,.042,LIGHT,'Street pier | pale square surround')
    slab(inner,-.009,.004,SHADE,'Street pier | shaded square inset')
    for name,bounds in PLAN['pilaster_faces'].items():
        if name.endswith('course'):
            face(bounds,-.009,.047,LIGHT,'Street pier | '+name.replace('_',' '))
        else:
            left,right,low,top=bounds
            inner=box(left+.018,low+.018,right-.018,top-.017)
            # The lower square crosses the edge of the built-up end pilaster.
            # Measure its front from that pilaster and carry the backing to the wall.
            support = .038 if name == 'lower_tile' else 0.
            slab(box(left,low,right,top).difference(inner),-.012,support+.024,
                 LIGHT,'Street pier | '+name+' rim')
            slab(inner,-.014,support+.001,SHADE,'Street pier | '+name+' well')
    xa,xb=PLAN['bracket_x'];za,zb=PLAN['bracket_z']
    # Actual upper return in the south photograph, traced as a broad curved
    # shoulder and a shallower supporting block; it meets the common cornice.
    shoulder=Polygon([(xa,zb),(xb,zb),(xb-.018,zb-.102),
        (xb-.055,zb-.160),(xb-.086,za+.057),(xa+.102,za),
        (xa+.060,za+.030),(xa+.017,za+.122)])
    slab(shoulder,-.018,.104,LIGHT,'Street pier | eaves shoulder')
    if not coarse:
        face([xa+.088,xb-.046,za-.028,za+.010],-.010,.083,LIGHT,'Street pier | shoulder bed')
