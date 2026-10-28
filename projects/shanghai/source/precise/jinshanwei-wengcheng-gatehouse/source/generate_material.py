#!/usr/bin/env python3
"""Original deterministic grey-brick PBR material; Copyright agent, MIT.

The only inputs are the constants below. No photograph pixels or external
textures are read. Physical sizes describe a generic material design, not a
measurement of the Jinshanwei wall. This script never overwrites artifacts.
"""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import numpy as np
import PIL
from PIL import Image

SIZE = 512
REPEAT_M = (1.28, .64)
SEED = 20261027021
NORMAL_SCALE = .35
AO_STRENGTH = .35


def mean_wrap(a, radius):
    return sum(np.roll(np.roll(a, y, 0), x, 1)
               for y in range(-radius, radius+1)
               for x in range(-radius, radius+1)) / (2*radius+1)**2


def smoothstep(a):
    a = np.clip(a, 0., 1.)
    return a*a*(3-2*a)


def generate_fields():
    rng = np.random.Generator(np.random.PCG64(SEED))
    yy, xx = np.mgrid[:SIZE, :SIZE]
    x = (xx+.5)*REPEAT_M[0]/SIZE
    y = (yy+.5)*REPEAT_M[1]/SIZE
    row = np.floor(y/.08).astype(int)
    bx = np.mod(x + (row % 2)*.16, .32)
    by = np.mod(y, .08)
    col = (np.floor((x + (row % 2)*.16)/.32).astype(int)) % 4
    grain = rng.normal(0, 1, (SIZE, SIZE))
    soft = mean_wrap(grain, 1)
    broad = mean_wrap(grain, 7)
    variation = rng.uniform(-.050, .050, (8, 4))[row, col]
    # A low-amplitude periodic irregularity keeps the mortar edge from being
    # a machine-straight drawn line. It does not perturb the nominal bond.
    edge_noise = .00032*soft
    distance = np.minimum(np.minimum(bx, .32-bx), np.minimum(by, .08-by))
    blend = smoothstep((distance-.0036+edge_noise)/.0032)
    brick_height = .0038 + rng.uniform(-.00045, .00045, (8, 4))[row, col]
    height = blend*brick_height + soft*.000085
    # Seamless hand-authored Fourier terms give restrained kiln/cloud variation.
    waves = (np.sin(2*np.pi*(3*x/REPEAT_M[0]+2*y/REPEAT_M[1])+.4)
             + .55*np.cos(2*np.pi*(7*x/REPEAT_M[0]-3*y/REPEAT_M[1])+1.3)
             + .25*np.sin(2*np.pi*(11*x/REPEAT_M[0]+5*y/REPEAT_M[1])))
    brick_rgb = np.array([.386, .409, .403])
    mortar_rgb = np.array([.303, .321, .309])
    color = mortar_rgb[None, None, :]*(1-blend[:, :, None])
    color += (brick_rgb[None, None, :] + variation[:, :, None]
              + .010*waves[:, :, None])*blend[:, :, None]
    color += (soft*.009 + broad*.035)[:, :, None]
    roughness = .955*(1-blend) + blend*(.875 + .025*waves + soft*.010)
    # Small shallow pores wrap across all tile boundaries. The coarsest pores
    # remain visible at this 512px resolution; they are generic wear detail.
    pore_count = 880
    for _ in range(pore_count):
        cx, cy = rng.uniform(0, SIZE, 2)
        radius_m = rng.uniform(.0017, .0045)
        rx, ry = radius_m*SIZE/REPEAT_M[0], radius_m*SIZE/REPEAT_M[1]
        ix = np.arange(int(cx-rx-1), int(cx+rx+2))
        iy = np.arange(int(cy-ry-1), int(cy+ry+2))
        dx, dy = np.meshgrid((ix-cx)/rx, (iy-cy)/ry)
        cap = np.maximum(1-dx*dx-dy*dy, 0)**1.6
        ty, tx = np.meshgrid(iy % SIZE, ix % SIZE, indexing='ij')
        cap *= blend[ty, tx]
        height[ty, tx] -= cap*rng.uniform(.00013, .00055)
        color[ty, tx] -= cap[:, :, None]*rng.uniform(.009, .025)
        roughness[ty, tx] += cap*.025
    du = (np.roll(height, -1, 1)-np.roll(height, 1, 1))/(2*REPEAT_M[0]/SIZE)
    dv = (np.roll(height, -1, 0)-np.roll(height, 1, 0))/(2*REPEAT_M[1]/SIZE)
    # glTF/OpenGL green-up convention, compatible with the frozen no-TANGENT
    # helper and raw V-down world UVs; see the material descriptor.
    normal = np.stack([-du, dv, np.ones_like(height)], -1)
    normal /= np.linalg.norm(normal, axis=-1)[:, :, None]
    cavity = np.maximum(mean_wrap(height, 2)-height, 0)
    ao = np.clip(1-.23*(1-blend)-.14*cavity/.001, .69, 1)
    orm = np.stack([ao, np.clip(roughness, .80, .98), np.zeros_like(height)], -1)
    fields = {'basecolor': np.clip(color, 0, 1), 'normal': normal*.5+.5, 'orm': orm}
    pixels = {name: np.rint(value*255).astype(np.uint8) for name, value in fields.items()}
    stats = {
        'brick_cells_per_tile': 32, 'brick_course_count': 8,
        'pore_deposits': pore_count, 'height_range_m': [float(height.min()), float(height.max())],
        'albedo_mean_srgb': fields['basecolor'].mean((0, 1)).tolist(),
        'roughness_range': [float(orm[:, :, 1].min()), float(orm[:, :, 1].max())],
        'ao_range': [float(ao.min()), float(ao.max())],
        'normal_z_min': float(normal[:, :, 2].min()),
        'normal_length_max_error_unencoded': float(np.abs(np.linalg.norm(normal, axis=-1)-1).max()),
        'mortar_and_edge_pixel_fraction': float(np.mean(blend < .95)),
    }
    return pixels, height, stats


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    paths = {k: output/f'jinshan-original-grey-brick-{k}.png' for k in ['basecolor', 'normal', 'orm']}
    descriptor = output/'MATERIAL.json'
    if any(p.exists() for p in [*paths.values(), descriptor]):
        raise FileExistsError('Use a fresh output directory; existing files are never overwritten.')
    pixels, height, stats = generate_fields()
    checks = {
        'finite_height': bool(np.isfinite(height).all()),
        'all_images_rgb_uint8_512': all(a.shape == (512, 512, 3) and a.dtype == np.uint8 for a in pixels.values()),
        'metallic_channel_exactly_zero': bool(np.all(pixels['orm'][:, :, 2] == 0)),
        'normal_positive_hemisphere': bool(np.all(pixels['normal'][:, :, 2] >= 128)),
        'no_photo_pixels_read': True,
    }
    if not all(checks.values()):
        raise ValueError(checks)
    for key, path in paths.items():
        Image.fromarray(pixels[key]).save(path, optimize=True)
    files = [{'file': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in paths.values()]
    doc = {
        'schema': 'jinshan-original-grey-brick-pbr-v1', 'author': 'agent', 'license': 'MIT',
        'source_photograph_pixels_read': False, 'surface_scan': False,
        'scope': 'Original generic grey brick with running bond, mortar and small pores. Colour, bond, dimensions and relief are design estimates; not recovered measurements or exact masonry layout of Jinshanwei.',
        'dimensions_px': [512, 512], 'repeat_metres': list(REPEAT_M),
        'nominal_generic_brick_cell_metres': [.32, .08],
        'sampler': {'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497},
        'baseColorFactor': [1, 1, 1, 1], 'roughnessFactor': 1, 'metallicFactor': 1,
        'normalScale': NORMAL_SCALE, 'occlusionStrength': AO_STRENGTH,
        'color_spaces': {'basecolor': 'sRGB', 'normal': 'Non-Color', 'orm': 'Non-Color'},
        'channels': {'orm': {'R': 'ambient occlusion', 'G': 'roughness', 'B': 'metallic, exactly zero'}},
        'uv_contract': {
            'vertical_faces': 'U=continuous horizontal metres/1.28; V=-height metres/0.64. Keep UVs unbounded with REPEAT. Do not normalize individual wall parts.',
            'horizontal_faces': 'Apply the same 1.28m by0.64m metric repeat in a consistent architectural plane frame; this is a generic bond, not surveyed paving.',
            'normal_encoding': 'normalize(-dH/dU_metres, +dH/dPNG_row_metres, 1); PNG row index increases downwards.',
            'current_web_contract': 'No TANGENT. Three GLTFLoader negates normalScale.y for the derivative frame. Effective scale is [+0.35,-0.35]; verify on final runtime.',
            'blender_contract': 'Standard importer changes V to1-V without inverting the normal green channel. Do not add another flip.',
            'if_tangents_added': 'Re-audit tangent basis and loader; this contract is for absent TANGENT.',
        },
        'periodicity': 'All row/cell indices close on the8-by4 brick grid. Fourier phases, smoothing, pore deposits and derivatives wrap on a torus; opposite pixel-centre edges need not be duplicate pixels.',
        'height_not_geometry': 'Encoded relief is normal shading attenuated by0.35, not physical displaced bricks or collision geometry.',
        'generator': {'file': 'source/generate_material.py', 'sha256': sha(Path(__file__).resolve()), 'seed': SEED, 'random_generator': 'NumPy PCG64'},
        'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'Pillow': PIL.__version__},
        'statistics': stats, 'generator_checks': checks, 'files': files,
        'model_generated': False, 'model_dimensions_accepted': False,
    }
    descriptor.write_text(json.dumps(doc, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'files': files, 'statistics': stats, 'descriptor': str(descriptor)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args().output.resolve())
