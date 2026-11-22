"""Cast street-side landmark rays against the three actual delivered GLB variants."""
from pathlib import Path
import numpy as np


def first(triangles, materials, origin, direction):
    edge1 = triangles[:, 1]-triangles[:, 0]
    edge2 = triangles[:, 2]-triangles[:, 0]
    p = np.cross(np.broadcast_to(direction, edge2.shape), edge2)
    det = np.einsum('ij,ij->i', edge1, p)
    inverse = np.zeros_like(det)
    good = abs(det) > 1e-9
    inverse[good] = 1/det[good]
    t = origin-triangles[:, 0]
    u = np.einsum('ij,ij->i', t, p)*inverse
    q = np.cross(t, edge1)
    v = (q@direction)*inverse
    distance = np.einsum('ij,ij->i', edge2, q)*inverse
    hits = np.where(good & (u >= -1e-10) & (v >= -1e-10) & (u+v <= 1+1e-10) & (distance > 0))[0]
    if not len(hits):
        return None, None
    at = hits[np.argmin(distance[hits])]
    return materials[at], float(distance[at])


def check_triangles(triangles, materials, distant):
    # Local X points north, -Y toward Yuanmingyuan Road, and Z up.
    shaft = -10.595655
    wing = 3.635
    glass = 'light reflected street glass'
    frame = 'dark bronze street frames'
    ashlar = 'pearl grey ashlar'
    light = 'warm tower limestone'
    stone = 'sand grey mouldings'
    brick = 'ochre garden brick'
    tests = []

    def front(label, x, z, material):
        tests.append((label, [x, -3, z], [0, 1, 0], material))

    for z in [5.51, 8.96, 12.39, 15.83, 19.19, 23.21, 29.69, 30.73, 32.54]:
        front('塔楼前窗玻璃 '+str(z), shaft+.15, z, glass)
    for z in [5.70, 9.01, 12.55, 15.99, 19.44]:
        front('塔楼前窗中竖梃 '+str(z), shaft, z, frame)
    for u, z, material, label in [
        (.35, 1.15, 'deep recessed door', '石门后退阴影'),
        (.16, 2.55, glass, '门上交叉铁格气窗'),
        (1.36, 1.64, stone, '门右石枋'),
        (1.33, 3.70, stone, '四字额底石'),
        (1.52, 4.51, light, '外挑门檐'),
        (-2.27, 4.89, light, '前伸外檐南端'),
        (0, 18.54, light, '下层券窗挑出石台'),
        (.92, 18.05, stone, '石台外侧托块'),
        (0, 21.50, light, '券窗上部横枋'),
        (.26, 21.92, ashlar, '三角楣心'),
        (-1.07, 20.36, light, '券窗侧石框'),
        (2.21, 11.8, brick, '塔身砖壁'), (3.34, 11.64, ashlar, '塔角浅石'),
        (1.72, 31.47, light, '高塔石窗框外壁'),
        (.15, 33.54, light, '上层拱窗楣顶'),
        (2.66, 35.01, light, '上部水平檐带')
    ]:
        front(label, shaft+u, z, material)
    for sill in [5.32, 8.80, 12.30, 15.75, 19.15, 22.48]:
        for index, x in enumerate([-5.9357, -2.2457, 2.6343, 7.5143, 12.3943]):
            # Both first-storey security grille levels use the same centerlines.
            front(f'第{sill}米第{index+1}组玻璃', x+.091, sill+.37, glass)
            if index and sill != 5.32:
                front(f'第{sill}米第{index+1}组三联窗梃', x+3.65/6, sill+.51, frame)
    for u in [-7.62, -2.18, 3.29, 8.40]:
        front('底层大窗 '+str(u), wing+u+.14, 1.31, glass)
    for x in [-5.50, -1.91, 2.33, 6.57, 10.81, 13.9]:
        front('退台栏杆 '+str(x), x, 19.07, frame)
    for x in [-4.6, -.1, 5.0, 9.89, 13.81]:
        front('檐下浅色腰线 '+str(x), x, 17.90, ashlar)
    metal = 'oxidized plaque metal'
    for glyph, x, z in [
        ('兰', -11.199755, 3.653),
        ('心', -10.831055, 3.89235),
        ('大', -10.357105, 3.7825),
        ('樓', -9.965855, 3.7806),
        ('L', -13.872636, 3.896434),
        ('Y', -13.562166, 3.903916),
        ('C', -13.382259, 3.891021),
        ('E', -13.088249, 3.896128),
        ('U', -12.766032, 3.910801),
        ('M', -12.657542, 3.839345),
        ('L', -8.672636, 3.896434),
        ('Y', -8.362166, 3.903916),
        ('C', -8.182259, 3.891021),
        ('E', -7.888249, 3.896128),
        ('U', -7.566032, 3.910801),
        ('M', -7.457542, 3.839345),
    ]:
        front('门楣金属字 '+glyph, x, z, metal)
    for glyph, x, z in [('1', -10.689455, 2.19505), ('8', -10.604605, 2.1817), ('5', -10.489205, 2.1794)]:
        front('门号 '+glyph, x, z, frame if distant else light)
    tests.append(('北向真实塔楼侧返券窗', [-4.2, 1.63, 30.06], [-1, 0, 0], glass))
    results = []
    for label, origin, direction, expected in tests:
        material, depth = first(triangles, materials, np.array(origin), np.array(direction, dtype=float))
        results.append(
            dict(
                label=label,
                origin=origin,
                direction=direction,
                expected=expected,
                hit=material,
                distance_m=depth))
    wrong = [row for row in results if row['hit'] != row['expected']]
    if wrong:
        raise ValueError(wrong)
    return dict(distant=distant, triangles=len(triangles), rays=results)
