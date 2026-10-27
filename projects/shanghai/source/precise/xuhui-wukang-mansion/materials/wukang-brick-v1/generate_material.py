"""Original periodic brick material. No source photograph is read or copied.

The dimensions, coloring and weathering are inferred illustration parameters,
not measurements of Wukang Mansion's masonry. Outputs are CC0-1.0.
"""
from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'maps'
OUT.mkdir(exist_ok=False)
WIDTH, HEIGHT = 1024, 608
TILE_U, TILE_V = 1.984, 1.184
COLS, ROWS = 8, 16
PITCH_U, PITCH_V = TILE_U / COLS, TILE_V / ROWS
rng = np.random.default_rng(20261027)
u = (np.arange(WIDTH)[None, :] + .5) / WIDTH * TILE_U
v = (np.arange(HEIGHT)[:, None] + .5) / HEIGHT * TILE_V
row = np.floor(v / PITCH_V).astype(int)
offset_u = u + (row % 2) * PITCH_U / 2
col = np.floor(offset_u / PITCH_U).astype(int) % COLS
in_u, in_v = offset_u % PITCH_U, v % PITCH_V
edge_u = np.minimum(in_u, PITCH_U - in_u)
edge_v = np.minimum(in_v, PITCH_V - in_v)
joint_distance = np.minimum(edge_u - .0045, edge_v - .0035)
brick_weight = np.clip(joint_distance / .0025, 0, 1)
brick_weight = brick_weight * brick_weight * (3 - 2 * brick_weight)

def periodic_noise(sigma, amplitude=1):
    data = gaussian_filter(rng.normal(size=(HEIGHT, WIDTH)), sigma, mode='wrap')
    return data / data.std() * amplitude

fine = periodic_noise(.9)
medium = periodic_noise(5)
broad = periodic_noise(26)
tint = rng.uniform(.78, 1.18, size=(ROWS, COLS))[row, col]
warm = rng.uniform(-1, 1, size=(ROWS, COLS))[row, col]
brick_color = np.array([144., 76., 48.])[None, None, :] * tint[:, :, None]
brick_color = brick_color + warm[:, :, None] * np.array([10., 4., 1.])
brick_color += (fine * 2.7 + medium * 4.5 + broad * 2.2)[:, :, None]
mortar_color = np.array([115., 105., 88.])[None, None, :] + (fine * 2.4 + medium * 2)[:, :, None]
albedo = brick_color * brick_weight[:, :, None] + mortar_color * (1 - brick_weight[:, :, None])
albedo = np.clip(albedo, 0, 255).astype(np.uint8)

height_m = brick_weight * (.0038 + medium * .00020 + broad * .00012) + fine * .000035
dhdu = (np.roll(height_m, -1, axis=1) - np.roll(height_m, 1, axis=1)) / (2 * TILE_U / WIDTH)
dhdv = (np.roll(height_m, -1, axis=0) - np.roll(height_m, 1, axis=0)) / (2 * TILE_V / HEIGHT)
normal = np.stack([-dhdu, -dhdv, np.ones_like(height_m)], axis=-1)
normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
normal_rgb = np.round((normal * .5 + .5) * 255).astype(np.uint8)
roughness = np.clip(.89 + medium * .025 + (1 - brick_weight) * .045, .77, .98)
orm = np.stack([np.full_like(roughness, 255), np.round(roughness * 255), np.zeros_like(roughness)], axis=-1).astype(np.uint8)

outputs = []
for name, pixels, role, colorspace in [
    ('brick-basecolor.png', albedo, 'baseColorTexture', 'sRGB'),
    ('brick-normal.png', normal_rgb, 'normalTexture', 'linear'),
    ('brick-orm.png', orm, 'metallicRoughnessTexture', 'linear; R=1,G=roughness,B=0'),
]:
    p = OUT / name
    Image.fromarray(pixels).save(p, optimize=True)
    outputs.append({'path': str(p), 'file': name, 'bytes': p.stat().st_size,
                    'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                    'role': role, 'colorspace': colorspace})
metadata = {
    'schema': 'original-procedural-material-v1',
    'name': 'Inferred warm red-brown running-bond brick',
    'creator': 'agent', 'license': 'CC0-1.0',
    'license_url': 'https://creativecommons.org/publicdomain/zero/1.0/',
    'source_photographs_used_as_pixels': False,
    'accuracy': 'Generic original illustration material, not a scan, measured brick size or exact building color.',
    'pixels': [WIDTH, HEIGHT], 'tile_metres': [TILE_U, TILE_V],
    'brick_pitch_metres': [PITCH_U, PITCH_V], 'tile_bricks': [COLS, ROWS],
    'uv': 'U=horizontal facade distance/1.984; V=height/1.184. REPEAT on both axes. Keep direction consistent on curved faces.',
    'normal_convention': 'Tangent normal XYZ is (-dh/dU,-dh/dV,1) normalized, RGB encoded0..1; green is positive tangentV, not a DirectX Y flip.',
    'material_factors': {'baseColorFactor': [1, 1, 1, 1], 'roughnessFactor': 1,
                         'metallicFactor': 1, 'normalTextureScale': .65},
    'note': 'metallicFactor1 is intentional: ORM blue is0 everywhere, yielding nonmetal. Do not tint baseColor twice.',
    'periodicity': 'Noise uses circular convolution, brick pattern wraps modulo8 columns/16 rows; derivatives use circular differences.',
    'outputs': outputs,
    'generator': {'file': str(Path(__file__).resolve()), 'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
}
(ROOT / 'material.json').write_text(json.dumps(metadata, indent=2) + '\n')
print(json.dumps({'total_png_bytes': sum(x['bytes'] for x in outputs), 'outputs': outputs}))
