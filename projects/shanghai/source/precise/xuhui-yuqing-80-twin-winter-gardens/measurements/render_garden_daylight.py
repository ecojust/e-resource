"""Render the Yuqing Road house from two surveyed garden cameras under a sampled sky.

Run with a model path and an output directory. A C99 compiler, NumPy, Pillow and
the other published Shanghai measurement modules are required. No source photo
is needed. The dataset gives a solar time for the northeast photograph only.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw
from render_garden_front import Camera, backend, illumination

HERE = Path(__file__).resolve().parent
SAMPLES = 18
DEPTH_RESOLUTION = 512


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sky_maps(parts, native, renderer):
    """Build one orthographic depth map per direction, using the entire mesh."""
    vertices = np.concatenate([part[0] for part in parts])
    extent = np.linalg.norm(np.ptp(vertices, axis=0))
    center = (vertices.min(axis=0) + vertices.max(axis=0)) / 2
    directions = np.zeros((SAMPLES, 3), dtype='float32')
    transforms = np.zeros((SAMPLES, 3, 4), dtype='float32')
    depths = np.full((SAMPLES, DEPTH_RESOLUTION, DEPTH_RESOLUTION), -np.inf, dtype='float32')

    for i, direction in enumerate(directions):
        height = (i + .5) / SAMPLES
        azimuth = i * np.pi * (3 - np.sqrt(5))
        radius = np.sqrt(1 - height * height)
        light_axis = np.array([radius * np.cos(azimuth), radius * np.sin(azimuth), height])
        direction[:] = light_axis
        horizontal = np.cross([0., 0., 1.], light_axis)
        horizontal /= np.linalg.norm(horizontal)
        vertical = np.cross(light_axis, horizontal)
        transform = transforms[i]
        transform[:, :3] = [horizontal * (DEPTH_RESOLUTION - 4) / extent,
                            vertical * (DEPTH_RESOLUTION - 4) / extent, direction]
        transform[:2, 3] = (DEPTH_RESOLUTION - 1) / 2 - transform[:2, :3] @ center
        for positions, _, _, indices, _, _ in parts:
            projected = np.ascontiguousarray(positions @ transform[:, :3].T + transform[:, 3],
                                              dtype='float32')
            native.shadow_depth(len(indices) // 3, renderer.ptr(indices), renderer.ptr(projected),
                                DEPTH_RESOLUTION, renderer.ptr(depths[i]))
    return transforms, directions, depths


def render_camera(mesh, model, native, renderer, width, number):
    camera = Camera(number)
    projection = camera.projection()
    inverse = np.linalg.inv(projection[:, :3])
    inverse_camera = np.ascontiguousarray(np.column_stack((inverse, -inverse @ projection[:, 3])),
                                          dtype='float32')
    source_width, source_height = camera.size
    pixel_size = source_width / width
    sky_fraction = np.full((round(source_height / pixel_size), width), -1, dtype='float32')
    native.set_photo(renderer.ptr(inverse_camera), ctypes.c_float(pixel_size),
                     int(number == 4), renderer.ptr(sky_fraction))
    sun, angles, comment = illumination(number)
    clipped = backend['projected_parts'](model, projection)
    with patch.object(renderer, 'read_glb', return_value=clipped):
        image, stats = renderer.raster(mesh, native, width, projection, (0, 0, *camera.size),
                                       np.ascontiguousarray(sun, dtype='float32'), angles)
    foreground = sky_fraction[sky_fraction >= 0]
    if len(foreground) != stats['zbuffer_foreground_pixels']:
        raise ValueError('Sky coverage and the final camera depth buffer disagree')
    stats.update({
        'illumination': comment if number == 4 else 'Exposure time unconfirmed. Isotropic diffuse sky.',
        'camera_projection': projection.tolist(),
        'sky_samples': SAMPLES,
        'sky_depth_map_side_px': DEPTH_RESOLUTION,
        'less_than_half_sky_foreground_pixels': int((foreground < .5).sum()),
        'sky_visibility_quantiles_10_50_90': np.quantile(foreground, [.1, .5, .9]).tolist(),
        'light_model': 'Cosine-weighted hemisphere visibility of the model and constant indirect fill.'
    })
    return image, stats


def render(mesh, output, width=768):
    if width < 1:
        raise ValueError('The render width must be a positive pixel count')
    output.mkdir(parents=True, exist_ok=True)
    renderer = backend['renderer']
    model = renderer.read_glb(mesh)
    model_sha = sha256(mesh)
    source = HERE / 'garden_daylight.c'
    records = {}
    pictures = []
    with tempfile.TemporaryDirectory(prefix='yuqing-daylight-') as compiler_dir:
        library = Path(compiler_dir) / 'garden.so'
        subprocess.run(['cc', '-O2', '-std=c99', '-shared', '-fPIC', str(source), '-lm',
                        '-o', str(library)], check=True)
        native = ctypes.CDLL(str(library))
        # These arrays must live through both draws because the C rasterizer retains pointers.
        transforms, directions, depths = sky_maps(model[0], native, renderer)
        native.set_sky(SAMPLES, DEPTH_RESOLUTION, renderer.ptr(transforms),
                       renderer.ptr(directions), renderer.ptr(depths))
        for number in (4, 6):
            image, stats = render_camera(mesh, model, native, renderer, width, number)
            image_path = output / f'garden-photo-{number}-model.jpg'
            image.save(image_path, quality=94, optimize=True)
            pictures.append(image)
            stats.update(model_sha256=model_sha, image_sha256=sha256(image_path),
                         raster_source_sha256=sha256(source))
            records[number] = stats

    sheet = Image.new('RGB', (2 * width + 8, max(p.height for p in pictures) + 27), '#f4f3ed')
    draw = ImageDraw.Draw(sheet)
    labels = ('Northeast view | 14 September 2013', 'Southwest view | open lower terrace')
    for i, (image, label) in enumerate(zip(pictures, labels)):
        x = i * (width + 8)
        sheet.paste(image, (x, 0))
        draw.text((x + 8, sheet.height - 21), label, fill='#332e27')
    sheet.save(output / 'garden-elevation-model.jpg', quality=93, optimize=True)
    (output / 'registered-garden-renders.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--width', type=int, default=768)
    args = parser.parse_args()
    render(args.mesh, args.output, args.width)
