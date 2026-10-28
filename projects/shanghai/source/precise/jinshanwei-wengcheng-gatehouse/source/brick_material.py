"""Generic original brick material and metric UV assignment; agent, MIT.

Use before baking architectural XYZ into geographic ENU. This module does not
create building geometry and does not assign or infer building dimensions.
"""
from pathlib import Path
import numpy as np

REPEAT_U_M = 1.28
REPEAT_V_M = .64
ROOT = Path(__file__).resolve().parent.parent


def brick_palette():
    textures = ROOT/'textures'
    return {'original grey brick': {
        'color': [1., 1., 1.], 'roughness': 1., 'metallic': 1.,
        'texture': str(textures/'jinshan-original-grey-brick-basecolor.png'),
        'normal_texture': str(textures/'jinshan-original-grey-brick-normal.png'),
        'orm_texture': str(textures/'jinshan-original-grey-brick-orm.png'),
        'normal_scale': .35,
        'extras': {'author': 'agent', 'license': 'MIT',
                   'repeat_metres': [REPEAT_U_M, REPEAT_V_M],
                   'original_generic_material_not_scan': True,
                   'normal_contract': 'No TANGENT; raw V down; encoded G positive PNG-row derivative',
                   'occlusion_strength': .35},
    }}


def assign_brick_uv(part):
    """Continuous architectural-metre projection, splitting plane corners.

    Vertical faces follow U=cross(Z, outward normal), V=-Z. For a sloped face,
    V remains orthogonal to U and normal. Horizontal faces use architecture X
    projected onto the plane. Raw U cross V is opposite the outward normal,
    matching the reviewed no-TANGENT glTF derivative-frame convention.
    """
    old = np.asarray(part['vertices'], dtype=float)
    vertices, uvs, triangles, bases = [], [], [], {}
    for tri in part['triangles']:
        points = old[list(tri)]
        normal = np.cross(points[1]-points[0], points[2]-points[0])
        length = np.linalg.norm(normal)
        if not np.isfinite(length) or length <= 1e-12:
            raise ValueError('Cannot map a collapsed or non-finite triangle')
        normal /= length
        key = tuple(np.round(normal, 9))
        if key not in bases:
            if abs(normal[2]) < .999999:
                u = np.cross([0., 0., 1.], normal)
            else:
                u = np.array([1., 0., 0.])-normal*normal[0]
            u /= np.linalg.norm(u)
            v = -np.cross(normal, u)
            bases[key] = u, v
        u, v = bases[key]
        start = len(vertices)
        vertices.extend(points.tolist())
        uvs.extend([[float(np.dot(p, u)/REPEAT_U_M),
                     float(np.dot(p, v)/REPEAT_V_M)] for p in points])
        triangles.append((start, start+1, start+2))
    part['vertices'] = vertices
    part['texcoords'] = uvs
    part['triangles'] = triangles
    return {'plane_basis_groups': len(bases), 'triangle_count': len(triangles),
            'raw_U_cross_V': 'opposite outward normal',
            'repeat_metres': [REPEAT_U_M, REPEAT_V_M]}
