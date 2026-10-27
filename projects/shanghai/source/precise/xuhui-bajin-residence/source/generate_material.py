#!/usr/bin/env python3
"""Original, deterministic, periodic pebble-dash PBR tile. Copyright agent, MIT.

This program reads no photographs. The only input is the numerical design below.
PNG rows increase downward. The normal texture uses the OpenGL/glTF green-up
convention; see MATERIAL.json and the independent convention review.
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
REPEAT_M = 0.40
SEED = 1131923
NORMAL_SCALE = 0.35
AO_STRENGTH = 0.35


def periodic_mean(a, radius):
    """Square averaging on a torus, with no artificial border extension."""
    out = np.zeros_like(a, dtype=np.float64)
    for j in range(-radius, radius + 1):
        for i in range(-radius, radius + 1):
            out += np.roll(np.roll(a, j, axis=0), i, axis=1)
    return out / (2 * radius + 1) ** 2


def generate_fields():
    rng = np.random.Generator(np.random.PCG64(SEED))
    noise = rng.normal(0, 1, (SIZE, SIZE))
    fine_noise = periodic_mean(noise, 1)
    height = fine_noise * 0.000018
    color = np.zeros((SIZE, SIZE, 3), dtype=np.float64)
    color[:] = [0.520, 0.490, 0.445]
    color += fine_noise[:, :, None] * 0.014
    roughness = np.full((SIZE, SIZE), 0.955, dtype=np.float64)
    owner = np.full((SIZE, SIZE), -1, dtype=np.int32)
    palette = np.asarray([
        [.620, .580, .510], [.520, .510, .480], [.680, .610, .500],
        [.490, .430, .350], [.730, .700, .620], [.370, .370, .350],
    ])
    weights = np.asarray([.26, .22, .16, .14, .14, .08])
    grid = 90
    diameters = []
    for stone_id in range(grid * grid):
        gy, gx = divmod(stone_id, grid)
        cx = (gx + .5 + rng.uniform(-.46, .46)) * SIZE / grid
        cy = (gy + .5 + rng.uniform(-.46, .46)) * SIZE / grid
        diameter_m = rng.triangular(.003, .0046, .008)
        diameters.append(float(diameter_m))
        rx = .5 * diameter_m * SIZE / REPEAT_M
        ry = rx * rng.uniform(.65, 1.08)
        angle = rng.uniform(0, 2 * np.pi)
        phase = rng.uniform(0, 2 * np.pi)
        peak_m = rng.uniform(.00045, .00105)
        tint = palette[rng.choice(len(palette), p=weights)] + rng.uniform(-.035, .035)
        stone_roughness = rng.uniform(.835, .945)
        radius = int(np.ceil(max(rx, ry) * 1.16)) + 1
        xs = np.arange(int(np.floor(cx)) - radius, int(np.floor(cx)) + radius + 1)
        ys = np.arange(int(np.floor(cy)) - radius, int(np.floor(cy)) + radius + 1)
        xx, yy = np.meshgrid(xs - cx, ys - cy)
        ca, sa = np.cos(angle), np.sin(angle)
        ax = (xx * ca + yy * sa) / rx
        ay = (-xx * sa + yy * ca) / ry
        theta = np.arctan2(ay, ax)
        rim = 1 + .065 * np.sin(3 * theta + phase) + .035 * np.cos(5 * theta - phase)
        radial = (ax * ax + ay * ay) / (rim * rim)
        cap = np.where(radial < 1, peak_m * np.maximum(1 - radial, 0) ** .62, -1)
        iy, ix = np.meshgrid(ys % SIZE, xs % SIZE, indexing='ij')
        old = height[iy, ix]
        take = cap > old
        if not np.any(take):
            continue
        yyw, xxw = iy[take], ix[take]
        height[yyw, xxw] = cap[take]
        color[yyw, xxw] = tint + .009 * noise[yyw, xxw, None]
        roughness[yyw, xxw] = stone_roughness + .007 * noise[yyw, xxw]
        owner[yyw, xxw] = stone_id

    pixel_m = REPEAT_M / SIZE
    dh_du = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) / (2 * pixel_m)
    dh_drow = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) / (2 * pixel_m)
    # OpenGL/glTF normal texture: positive G is up in the image, not PNG-row down.
    # The current loader without TANGENT uses a downward derivative bitangent and
    # negates normalScale.y. Blender imports V -> 1-V, with no green inversion.
    normal = np.stack([-dh_du, +dh_drow, np.ones_like(height)], axis=-1)
    normal /= np.linalg.norm(normal, axis=-1)[:, :, None]
    local_mean = periodic_mean(height, 3)
    cavity = np.maximum(local_mean - height, 0)
    ao = np.clip(1 - .32 * cavity / .00050, .72, 1)
    orm = np.stack([ao, np.clip(roughness, .80, .98), np.zeros_like(height)], axis=-1)
    fields = {'basecolor': np.clip(color, 0, 1), 'normal': normal * .5 + .5, 'orm': orm}
    encoded = {name: np.rint(a * 255).astype(np.uint8) for name, a in fields.items()}
    stats = {
        'generated_grain_count': grid * grid,
        'visible_grain_count': int(len(np.unique(owner[owner >= 0]))),
        'aggregate_pixel_coverage': float(np.mean(owner >= 0)),
        'input_grain_major_diameter_m': {'min': min(diameters), 'max': max(diameters), 'mean': float(np.mean(diameters))},
        'height_field_m': {'min': float(height.min()), 'max': float(height.max()), 'mean': float(height.mean())},
        'albedo_channel_mean_srgb': [float(v) for v in fields['basecolor'].mean(axis=(0, 1))],
        'roughness_min_max': [float(orm[:, :, 1].min()), float(orm[:, :, 1].max())],
        'ao_min_max': [float(ao.min()), float(ao.max())],
        'normal_z_min': float(normal[:, :, 2].min()),
        'normal_length_max_error_before_encoding': float(np.max(np.abs(np.linalg.norm(normal, axis=-1) - 1))),
    }
    return encoded, height, stats


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    names = ['basecolor', 'normal', 'orm']
    paths = [output / f'bajin-original-pebbledash-{name}.png' for name in names]
    descriptor = output / 'MATERIAL.json'
    if any(p.exists() for p in paths + [descriptor]):
        raise FileExistsError('Use a fresh output directory; existing artifacts are not overwritten.')
    encoded, height, stats = generate_fields()
    checks = {
        'finite_height': bool(np.isfinite(height).all()),
        'normal_positive_hemisphere': bool(np.all(encoded['normal'][:, :, 2] >= 128)),
        'metallic_channel_entirely_zero': bool(np.all(encoded['orm'][:, :, 2] == 0)),
        'all_images_rgb_uint8_512': all(a.dtype == np.uint8 and a.shape == (SIZE, SIZE, 3) for a in encoded.values()),
        'height_periodic_derivative_uses_wrapped_neighbors': True,
    }
    if not all(checks.values()):
        raise ValueError(checks)
    for name, path in zip(names, paths):
        Image.fromarray(encoded[name]).save(path, optimize=True)
    doc = {
        'schema': 'bajin-original-pebbledash-pbr-v1',
        'author': 'agent', 'license': 'MIT', 'random_generator': 'NumPy PCG64', 'random_seed': SEED,
        'source_photograph_pixels_read': False, 'surface_scan': False,
        'scope': 'Original generic fine pebble-dash material, visually informed by a reference photograph. Colour, grain size and relief are estimates, not measurements of Ba Jin house.',
        'dimensions_px': [SIZE, SIZE], 'repeat_metres': [REPEAT_M, REPEAT_M],
        'pixel_pitch_m': REPEAT_M / SIZE,
        'periodic_method': 'Jittered pebble centres on a torus; every ellipse deposit wraps modulo512; matrix smoothing and height derivatives use wrapped neighbours. Pixel-centre rows0and511 need not be identical: their adjacency is an ordinary one-pixel toroidal step, not a duplicated gutter.',
        'sampler': {'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497},
        'baseColorFactor': [1, 1, 1, 1], 'roughnessFactor': 1, 'metallicFactor': 1,
        'normalScale': NORMAL_SCALE, 'occlusionStrength': AO_STRENGTH,
        'normal_height_scope': 'The encoded height gradients are attenuated by normalScale0.35 at render time. This is a conservative shading choice, not displacement geometry or a measured surface relief.',
        'color_spaces': {'basecolor': 'sRGB', 'normal': 'Non-Color', 'orm': 'Non-Color'},
        'channels': {'orm': {'R': 'ambient occlusion', 'G': 'roughness', 'B': 'metallic, exactly0'}},
        'uv_contract': {
            'raw_gltf': 'For a vertical facade: U=local horizontal metres/0.40; V=-height metres/0.40. Keep unbounded UVs and REPEAT, with no per-part normalization, modulo or atlas-cell clamping.',
            'png_rows': 'Top-to-bottom row index increases with stored PNG V.',
            'encoded_normal': 'Normalize(-dH/dU_metres, +dH/dPNG_row_metres, 1), then encode from[-1,1]to[0,255].',
            'current_no_tangent_web_frame': 'Three derivative frame follows raw+U right, raw+V down, outward normal. Frozen GLTFLoader negates normalScale.y when TANGENT is absent; effective scale is[+0.35,-0.35].',
            'standard_blender_import': 'Importer converts V to1-V and keeps the green channel; its upward bitangent gives the same physical bump. Do not manually invert G or add another V flip.',
            'physical_interpretation': 'On the left flank of a raised pebble the normal leans left; on the upper flank it leans up. These signs must be checked on the final renderer, not inferred merely from a normal map thumbnail.',
            'if_explicit_tangents_added': 'Re-audit the actual tangent frame and loader behavior. The current tested contract is for primitives without TANGENT.',
        },
        'statistics': stats, 'generator_checks': checks,
        'files': [{'file': p.name, 'bytes': p.stat().st_size, 'sha256': sha256(p)} for p in paths],
        'generator_sha256': sha256(Path(__file__).resolve()),
        'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'Pillow': PIL.__version__},
    }
    descriptor.write_text(json.dumps(doc, indent=2) + '\n')
    print(json.dumps({'descriptor': str(descriptor), 'files': doc['files'], 'statistics': stats}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args().output.resolve())
