"""Closed scalloped fabric gores and the rib frame of the refurbished portal."""
from math import acos, cos, pi, sin
from gatehouse_finishes import FITTING, LINING, ROSE, WINE, paint


BOW = 'Awning | pale metal bow'
PALETTE = {BOW: paint((174, 163, 145), .57, .25)}


def bow_point(angle, deployment, layout):
    """Point on one whole semicircular bow rotating around its two fixed pivots."""
    scale = layout['portal']['width'] / 6.34
    cx, radius, spring = 2.70, 2.56, 11.29
    rear_rise, front_rise, reach = 1.70, .68, 1.36
    turn = acos(front_rise / rear_rise)
    arch = sin(angle)
    return (scale * (cx-radius*cos(angle)),
            scale * (-.34-reach*arch*sin(turn*deployment)/sin(turn)),
            scale * (spring+rear_rise*arch*cos(turn*deployment)))


def add_awning(b, lod, layout):
    for name, value in PALETTE.items():
        b.palette.setdefault(name, value)
    count = 11
    inset = .010

    def fabric(angle, depth, edge_drop=0):
        x,y,z = bow_point(angle,depth,layout)
        # Small drapes between the seams become shallow beside the pivots.
        slack = .021 * sin(pi*depth) * sin(count*angle)**2 * sin(angle)
        return x,y-slack-.046*depth*sin(angle),z+.054*sin(angle)+slack-edge_drop

    def closed_patch(grids, material, label):
        top, underside = grids
        rows, cols = len(top),len(top[0])
        n = rows*cols
        vertices = [p for grid in grids for row in grid for p in row]
        faces=[]
        for j in range(rows-1):
            for i in range(cols-1):
                a=j*cols+i
                faces.extend([(a,a+1,a+cols+1,a+cols),(a+n+cols,a+n+cols+1,a+n+1,a+n)])
        rim = list(range(cols)) + [j*cols+cols-1 for j in range(1,rows)]
        rim += list(range(n-2,n-cols-1,-1)) + [j*cols for j in range(rows-2,0,-1)]
        for a,c in zip(rim,rim[1:]+rim[:1]):
            faces.append((a,a+n,c+n,c))
        # Increasing gore angle runs east and depth runs south. Both the
        # top skin and the hanging valance wind inward in this grid order.
        b.add(vertices,[tuple(reversed(face)) for face in faces],material,label)

    for gore in range(count):
        cols = 4 if lod else 9
        depth_stations = (0,.28,.57,.79,1.) if lod else (0,.14,.28,.425,.57,.68,.79,.895,1.)
        angles = [inset + (gore+i/(cols-1))*(pi-2*inset)/count for i in range(cols)]
        outside = [[fabric(a,t) for a in angles] for t in depth_stations]
        inside = [[(x,y,z-.020) for x,y,z in row] for row in outside]
        closed_patch((outside,inside),WINE,'Awning | tensioned gore %02d'%(gore+1))
        # The visible scallop has a high cusp at each seam and a lower
        # rounded middle. Its wide face hangs below the leading edge.
        drops = [.048 + .137*sin(i*pi/(cols-1))**1.12 for i in range(cols)]
        front = [[fabric(a,1,h) for a,h in zip(angles,ds)] for ds in [[0]*cols,drops]]
        back = [[(x,y+.023,z) for x,y,z in row] for row in front]
        closed_patch((front,back),WINE,'Awning | scalloped valance %02d'%(gore+1))
        b.tube([fabric(a,1) for a in angles],.016,ROSE,6 if lod else 8,'Awning | bound leading edge')
    subdivisions = 28 if lod else 64
    arc = [i*pi/subdivisions for i in range(subdivisions+1)]
    for number, deployment in enumerate((.28, .57, .79, 1.), 1):
        b.tube([bow_point(a, deployment, layout) for a in arc], .024,
               BOW, 8 if lod else 12, f'Awning | folding bow {number}')
    b.tube([bow_point(a,0,layout) for a in arc], .026, LINING,
           8 if lod else 12, 'Awning | rear fixing bow')
    for side, a in (('west', 0), ('east', pi)):
        x, y, z = bow_point(a,0,layout)
        b.box((x,(y+.02)/2,z),(.095,.02-y,.155),FITTING,label=f'Awning | {side} pivot bracket')
        b.tube([(x-.082,y,z),(x+.082,y,z)],.052,FITTING,12,
               f'Awning | {side} axial pin')
