"""Render the two dated southern garden photographs with eighteen-direction geometric sky occlusion."""
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
import math
import runpy

HERE = Path(__file__).resolve().parent
backend=runpy.run_path(str(HERE.parents[1]/'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))
class Camera:
    def __init__(self,number):
        self.station=json.loads((HERE/'two-stations.json').read_bytes())[number]
        self.size=self.station['size']
    def projection(self):
        return np.asarray(self.station['P'])
def illumination(number):
    if number=='garden-2023':
        return np.array([.13,-.71,.69]),[],'Undated exposure. Diffuse sky.'
    # NOAA fractional-year estimate at the EXIF civil time in Shanghai.
    hour=11+30/60+15/3600;phase=2*math.pi/365*(15-1+(hour-12)/24)
    dec=.006918-.399912*math.cos(phase)+.070257*math.sin(phase)-.006758*math.cos(2*phase)+.000907*math.sin(2*phase)-.002697*math.cos(3*phase)+.00148*math.sin(3*phase)
    et=229.18*(.000075+.001868*math.cos(phase)-.032077*math.sin(phase)-.014615*math.cos(2*phase)-.040849*math.sin(2*phase))
    lat=math.radians(31.20451);ha=math.radians((60*hour+et+4*121.4240-480)/4-180)
    e=-math.cos(dec)*math.sin(ha);n=math.sin(dec)*math.cos(lat)-math.cos(dec)*math.cos(ha)*math.sin(lat);z=math.sin(lat)*math.sin(dec)+math.cos(lat)*math.cos(dec)*math.cos(ha)
    ax=math.radians(110.62)
    return np.array([e*math.sin(ax)+n*math.cos(ax),-e*math.cos(ax)+n*math.sin(ax),z]),[round(math.degrees(math.atan2(e,n))%360,2),round(math.degrees(math.asin(z)),2)],'EXIF 2010-01-15 11:30:15, presumed China Standard Time.'
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
                     int(number == 'garden-2010'), renderer.ptr(sky_fraction))
    sun, angles, comment = illumination(number)
    clipped = backend['projected_parts'](model, projection)
    with patch.object(renderer, 'read_glb', return_value=clipped):
        image, stats = renderer.raster(mesh, native, width, projection, (0, 0, *camera.size),
                                       np.ascontiguousarray(sun, dtype='float32'), angles)
    foreground = sky_fraction[sky_fraction >= 0]
    if len(foreground) != stats['zbuffer_foreground_pixels']:
        raise ValueError('Sky coverage and the final camera depth buffer disagree')
    stats.update({
        'illumination': comment if number == 'garden-2010' else 'Exposure time unconfirmed. Isotropic diffuse sky.',
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
    with tempfile.TemporaryDirectory(prefix='xinhua-daylight-') as compiler_dir:
        library = Path(compiler_dir) / 'garden.so'
        subprocess.run(['cc', '-O2', '-std=c99', '-shared', '-fPIC', str(source), '-lm',
                        '-o', str(library)], check=True)
        native = ctypes.CDLL(str(library))
        # These arrays must live through both draws because the C rasterizer retains pointers.
        transforms, directions, depths = sky_maps(model[0], native, renderer)
        native.set_sky(SAMPLES, DEPTH_RESOLUTION, renderer.ptr(transforms),
                       renderer.ptr(directions), renderer.ptr(depths))
        for number in ('garden-2010','garden-2023'):
            image, stats = render_camera(mesh, model, native, renderer, width, number)
            image_path = output / f'{number}-model.jpg'
            image.save(image_path, quality=94, optimize=True)
            pictures.append(image)
            stats.update(model_sha256=model_sha, image_sha256=sha256(image_path),
                         raster_source_sha256=sha256(source))
            records[number] = stats

    sheet = Image.new('RGB', (2 * width + 8, max(p.height for p in pictures) + 27), '#f4f3ed')
    draw = ImageDraw.Draw(sheet)
    labels = ('Garden view | 15 January 2010', 'Garden view | municipal tourism publication, 2023')
    for i, (image, label) in enumerate(zip(pictures, labels)):
        x = i * (width + 8)
        sheet.paste(image, (x, 0))
        draw.text((x + 8, sheet.height - 21), label, fill='#332e27')
    sheet.save(output / 'registered-views.jpg', quality=93, optimize=True)
    (output / 'registered-garden-renders.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--width', type=int, default=768)
    args = parser.parse_args()
    render(args.mesh, args.output, args.width)
