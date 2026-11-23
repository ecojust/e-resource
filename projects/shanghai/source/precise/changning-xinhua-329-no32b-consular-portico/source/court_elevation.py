"""Exposed courtyard walls and window reveals visible around the two-column entrance."""
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union


def courtyard_wall(builder, cameras, wall, opening, plate, point, materials):
    brick, stone, timber, glass, pale, bronze = materials
    station = cameras['wide']
    matrix = np.array(station['R']).T @ np.linalg.inv(station['K'])
    eye = np.array(station['C'])

    def from_wide(loop):
        # Original 579 by 386 courtyard photograph, enlarged crop at (97,95).
        uv = np.asarray(loop) / 2 + [97,95]
        rays = np.c_[uv, np.ones(len(loop))] @ matrix.T
        xyz = eye + rays * ((wall-eye[1]) / rays[:,1])[:,None]
        return Polygon(xyz[:,[0,2]])

    def from_portrait(loop):
        return Polygon([point(u,v,wall)[[0,2]] for u,v in loop])

    west = from_wide([(30,190),(208,195),(243,155),(248,104),(337,118),
                      (340,64),(398,48),(412,59),(417,131),
                      (438,139),(434,446),(130,457),(23,444)])
    east = from_wide([(337,118),(348,62),(394,39),(505,58),(527,128),
                      (538,242),(540,411),(527,449),(429,453),(414,390)])
    centre = from_portrait([(-4,647),(506,647),(505,145),(-4,145)])
    windows = [
        ('west ground-floor window',[(63,257),(115,256),(100,369),(41,370)],2,3),
        ('east ground-floor light',[(450,294),(479,294),(480,382),(452,385)],2,1),
        ('east upper-floor light',[(445,147),(470,150),(469,195),(445,194)],2,2),
    ]
    holes = [from_wide(loop) for _,loop,_,_ in windows]
    panel = unary_union([centre,west,east]).difference(unary_union([opening,*holes]))
    plate(builder,panel,wall,wall+.32,brick,'courtyard/brickwork around three window openings')
    for (name,loop,columns,rows),hole in zip(windows,holes):
        frame = hole.buffer(-.034,join_style='mitre')
        plate(builder,hole.difference(frame),wall+.057,wall+.107,timber,name+'/recessed frame')
        plate(builder,frame,wall+.101,wall+.125,glass,name+'/glazing')
        quad=np.asarray(loop,float)
        def at(u,v):
            top=quad[0]*(1-u)+quad[1]*u
            bottom=quad[3]*(1-u)+quad[2]*u
            return top*(1-v)+bottom*v
        for i in range(1,columns):
            u=i/columns
            band=from_wide([at(u-.018,.015),at(u+.018,.015),at(u+.018,.985),at(u-.018,.985)])
            plate(builder,band,wall+.07,wall+.106,timber,name+f'/mullion {i}')
        for i in range(1,rows):
            v=i/rows
            band=from_wide([at(.01,v-.01),at(.99,v-.01),at(.99,v+.01),at(.01,v+.01)])
            plate(builder,band,wall+.065,wall+.102,timber,name+f'/transom {i}')
        sill=from_wide([at(-.04,1),at(1.04,1),at(1.04,1.04),at(-.04,1.04)])
        plate(builder,sill,wall-.045,wall+.093,stone,name+'/sill')
    plaque=from_portrait([(37,418),(95,418),(95,464),(37,464)])
    plate(builder,plaque,wall-.027,wall-.002,pale,'courtyard/heritage plaque beside west column')
    # Keep the fine border distinct from the pale enamel face.
    rim=plaque.buffer(-.009,join_style='mitre')
    plate(builder,rim.difference(rim.buffer(-.004,join_style='mitre')),wall-.029,wall-.026,bronze,'plaque/recessed border')
