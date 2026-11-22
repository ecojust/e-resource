"""Street-visible roof terrace of No. 13, in metres about the left front handrail post."""
import json
import math
from pathlib import Path

import numpy as np

MEASUREMENTS = Path(__file__).resolve().parents[1] / 'measurements'
SURVEY = json.loads((MEASUREMENTS / 'terrace-reconstruction.json').read_text())
PREFIX = 'No.13 roof terrace | '
IRON = PREFIX + 'dark green-black painted steel'
CAP = PREFIX + 'grey exposed coping'
RECESS = PREFIX + 'shadowed cement rebate'
DECK = PREFIX + 'weathered cement terrace'
METAL = PREFIX + 'grey roof covering'
WHITE = PREFIX + 'pale metal fascia'
SOFFIT = PREFIX + 'warm soffit'
FRAME = PREFIX + 'dark stained casements'
GLASS = PREFIX + 'muted blue-grey glass'
GLASS_DARK = PREFIX + 'shaded glazing'
MORTAR = PREFIX + 'warm mortar'
BRICKS = [PREFIX + 'ochre face brick ' + str(i) for i in range(1, 4)]


def pigment(rgb, roughness, metallic=0.):
    srgb = np.array(rgb) / 255
    linear = np.where(srgb <= .04045, srgb / 12.92, ((srgb + .055) / 1.055) ** 2.4)
    return dict(color=linear.tolist(), roughness=roughness, metallic=metallic)


PALETTE = {
    IRON: pigment((50, 59, 56), .53, .38), CAP: pigment((136, 133, 129), .89),
    RECESS: pigment((89, 89, 86), .89), DECK: pigment((118, 118, 111), .95),
    METAL: pigment((133, 139, 137), .61, .30), WHITE: pigment((204, 205, 197), .70, .14),
    SOFFIT: pigment((173, 157, 131), .87), FRAME: pigment((67, 54, 48), .67),
    GLASS: pigment((127, 145, 150), .34, .12), GLASS_DARK: pigment((92, 99, 96), .42, .10),
    MORTAR: pigment((167, 137, 115), .94),
    **dict(zip(BRICKS, [pigment(c, .94) for c in [(172, 128, 99), (179, 134, 104), (166, 120, 94)]])),
}

# Elevations are relative to the top rail, independently sampled in the two 2018 views.
RAIL_LEVELS = [(0., .054), (-.237, .025), (-.463, .025), (-.713, .025)]
RAIL_OFFSETS = [0., 0., 0., -.030]
DECK_Z = -.935


def section_solid(add, rings, material, label):
    n = len(rings[0])
    vertices = np.concatenate(rings, axis=0)
    faces = [tuple(reversed(range(n)))]
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            faces.append((k*n+i, k*n+j, (k+1)*n+j, (k+1)*n+i))
    faces.append(tuple(range(len(vertices)-n, len(vertices))))
    add(vertices, faces, material, label)


def rail_path(path, offset):
    delta = np.diff(path, axis=0)
    delta /= np.linalg.norm(delta, axis=1)[:, None]
    normals = np.column_stack((-delta[:, 1], delta[:, 0]))
    result = []
    for i, xy in enumerate(path):
        before = normals[max(i-1, 0)]
        after = normals[min(i, len(normals)-1)]
        result.append(xy + offset * (before + after) / (1 + np.dot(before,after)))
    return np.array(result)


def rail_mesh(add, path, z, diameter, sides, label):
    delta = np.diff(path, axis=0)
    delta /= np.linalg.norm(delta, axis=1)[:, None]
    normals = np.column_stack((-delta[:, 1], delta[:, 0]))
    rings = []
    for i, point in enumerate(path):
        before = normals[max(i-1, 0)]
        after = normals[min(i, len(normals)-1)]
        bisector = (before + after) / (1 + np.dot(before, after))
        ring = []
        for j in range(sides):
            a = 2 * math.pi * j / sides
            xy = point + bisector * (.5 * diameter * math.cos(a))
            ring.append([*xy, z + .5 * diameter * math.sin(a)])
        rings.append(ring)
    section_solid(add, rings, IRON, label)


def inset_corners(path, amount):
    """Offset front and clipped corners. The rear edge stays at the cut through the terrace."""
    inside = []
    for i in range(len(path)):
        a = path[i] - path[i-1]
        b = path[(i+1) % len(path)] - path[i]
        a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
        n, m = np.array([-a[1], a[0]]), np.array([-b[1], b[0]])
        inside.append(path[i] + amount * (m + n) / (1 + np.dot(n, m)))
    return np.array(inside)


def level_ring(plan, z):
    return np.column_stack((plan, np.full(len(plan), z)))


def add_terrace(builder, lod=False, origin=(0., 0., 0.), yaw_degrees=0.):
    """Emit closed, editable parts. Translate and rotate the local datum to the courtyard gate."""
    low = lod is True or lod in ('lod', 'low', 'distant')
    angle = math.radians(yaw_degrees)
    rotation = np.array([[math.cos(angle), -math.sin(angle), 0.],
                         [math.sin(angle), math.cos(angle), 0.], [0., 0., 1.]])

    def add(vertices, faces, material, label):
        points = np.asarray(vertices, dtype=float) @ rotation.T + np.asarray(origin)
        builder.add(points.tolist(), faces, material, PREFIX + label)

    bay = np.array(SURVEY['masonry_corners_m'])[:, :2]
    deckplan = np.vstack((bay, [bay[-1, 0], 3.18], [bay[0, 0], 3.18]))
    # The cornice is only on the projecting front and its two visible returns.
    frontplan = np.vstack((bay, [bay[-1, 0], 1.34], [bay[0, 0], 1.34]))
    profile = [(-1.300, .000), (-1.271, -.020), (-1.249, -.024), (-1.236, -.057),
               (-1.195, -.057), (-1.179, -.032), (-1.130, -.032), (-1.107, -.076),
               (-1.061, -.077), (-1.043, -.055), (-1.012, -.055), (-.995, -.080), (DECK_Z, -.080)]
    for i, ((za, da), (zb, db)) in enumerate(zip(profile, profile[1:])):
        mat = RECESS if i in (4, 8) else CAP
        rings = [level_ring(inset_corners(frontplan, offset), z) for z,offset in [(za,da),(zb,db)]]
        section_solid(add, rings, mat, 'stepped bay cornice band ' + str(i+1))
    rearplan = np.array([[bay[0,0], 1.338], [bay[-1,0], 1.338], *deckplan[-2:]])
    section_solid(add, [level_ring(rearplan, -1.206), level_ring(rearplan, DECK_Z-.003)],
                  DECK, 'terrace deck behind the coping')
    path = np.array(SURVEY['handrail_path_m'])[:, :2]
    for i, (z, diameter) in enumerate(RAIL_LEVELS):
        rail_mesh(add, rail_path(path, RAIL_OFFSETS[i]), z, diameter, 8 if low else 16,
                  'continuous bent handrail' if i == 0 else 'continuous intermediate rail ' + str(i))
    for i, center in enumerate(path):
        radius = .017
        plan = np.array([[-1,-1],[1,-1],[1,1],[-1,1]]) * radius + center
        foot = rail_path(path, -.034)[i] - center
        section_solid(add, [level_ring(plan+foot, DECK_Z-.018), level_ring(plan, -.007)],
                      IRON, 'corner upright ' + str(i+1))
    add_roof_room(add, low)


def add_roof_room(add, low):
    left, right, rear = [np.array(SURVEY[k]) for k in
                         ('eave_lower_left_front_m','eave_lower_right_front_m','eave_lower_right_occlusion_m')]
    front = right - left
    width = np.linalg.norm(front[:2])
    ex = front[:2] / width
    ey = np.array([-ex[1], ex[0]])
    depth = np.dot(rear[:2] - right[:2], ey)
    cross_fall, roof_fall = front[2] / width, (rear[2]-right[2]) / depth

    def point(x, y, z):
        return [*(left[:2]+ex*x+ey*y), z]

    def height(x, y):
        return left[2] + x*cross_fall + y*roof_fall

    def solid(rect, lower, upper, mat, label):
        a,b,c,d = rect
        corners = [(a,c),(b,c),(b,d),(a,d)]
        def ring(h):
            return [point(x,y,h(x,y) if callable(h) else h) for x,y in corners]
        section_solid(add, [ring(lower), ring(upper)], mat, label)

    def parallel(offset):
        return lambda x,y: height(x,y)+offset

    # These surfaces stop at the last visible point on the right roof slope.
    solid((0.,width,0.,depth), parallel(0.), parallel(.038), SOFFIT, 'overhanging soffit')
    solid((-.008,width+.008,-.009,depth), parallel(.038), parallel(.094), WHITE, 'light fascia around eave')
    solid((-.014,width+.014,-.015,depth), parallel(.094), parallel(.163), METAL, 'single-pitch roof with folded outer edge')

    wall_front, inner = .302, .431
    wall_left, wall_right = .16, width-.195
    jamb_l, jamb_r = .417, width-.395
    sill, head = -.455, .974
    solid((wall_left,wall_right,wall_front,inner), DECK_Z-.015, sill, MORTAR, 'lower front wall')
    solid((wall_left,jamb_l,wall_front,inner), sill, head, MORTAR, 'left reveal')
    solid((jamb_r,wall_right,wall_front,inner), sill, head, MORTAR, 'right reveal')
    solid((wall_left,wall_right,wall_front,inner), head, parallel(.001), MORTAR, 'brick head under eave')
    for a,b,side in [(wall_left,wall_left+.115,'left'),(wall_right-.115,wall_right,'right')]:
        solid((a,b,inner,depth-.006), DECK_Z, parallel(-.001), MORTAR, side+' visible return')
    solid((wall_left+.116,wall_right-.116,depth-.070,depth-.002), DECK_Z, parallel(-.002),
          MORTAR, 'closure at crop behind main roof')

    if not low:
        for course in range(32):
            z = DECK_Z + course*.065 + .004
            for col in range(-1,19):
                l = max(wall_left, wall_left+col*.224 + (course%2)*.112)
                r = min(wall_right, wall_left+(col+1)*.224 + (course%2)*.112-.005)
                if r-l <= .012:
                    continue
                spans = [(l,r,z,min(z+.059, height((l+r)/2,wall_front)))]
                if z < head and z+.059 > sill:
                    spans = [(l,min(r,jamb_l),z,min(z+.059,head)),(max(l,jamb_r),r,z,min(z+.059,head))]
                    if z < sill:
                        spans.append((max(l,jamb_l),min(r,jamb_r),z,sill))
                    if z+.059 > head:
                        spans.append((max(l,jamb_l),min(r,jamb_r),head,z+.059))
                for a,b,za,zb in spans:
                    if b-a>.009 and zb-za>.006:
                        solid((a,b,wall_front-.009,wall_front+.001), za, zb,
                              BRICKS[(course+col*2)%3], f'roof-room brick {course+1}.{col+2}.{a:.3f}')

        # The eastern photograph also exposes the ochre brickwork below the sloping rake.
        for course in range(32):
            za = DECK_Z + course*.065 + .004
            for k in range(-1,6):
                y1 = max(wall_front, wall_front + k*.224 + (course%2)*.112)
                y2 = min(depth-.008, wall_front + (k+1)*.224 + (course%2)*.112-.005)
                if y2-y1 <= .012:
                    continue
                for x,side in [(wall_left,'west'),(wall_right,'east')]:
                    z2 = min(za+.059, height(x,y2)-.002)
                    if z2-za <= .010:
                        continue
                    a,b = (x-.009,x+.001) if side=='west' else (x-.001,x+.009)
                    solid((a,b,y1,y2), za,z2, BRICKS[(k+2*course)%3],
                          f'roof-room {side} return brick {course+1}.{k+2}')

    # Two narrow left lights and the broad right light can be distinguished above the foreground eave.
    bars = [jamb_l, jamb_l+.71, jamb_l+1.49, jamb_r]
    frame_width = .055
    for i, x in enumerate(bars):
        a,b = (x, x+frame_width) if i==0 else (x-frame_width,x) if i==3 else (x-.024,x+.024)
        solid((a,b,wall_front+.020,wall_front+.109), sill+.015,head-.013,FRAME,'roof-room upright '+str(i+1))
    for z, name in [(sill,'sill'),(head-.055,'head')]:
        solid((jamb_l,jamb_r,wall_front+.013,wall_front+.112), z,z+.055,FRAME,'roof-room '+name)
    for i,(x1,x2) in enumerate(zip(bars,bars[1:])):
        solid((x1+.016,x2-.016,wall_front+.087,wall_front+.101),sill+.042,head-.045,
              GLASS if i==2 else GLASS_DARK,'roof-room glass '+str(i+1))
