"""Render the delivered hall mesh at two measured photographic stations.

Both views sample the GLB textures, UVs and normal maps. The 1934 station has
diffuse lighting. The 2020 local solar model uses the image timestamp.
"""
import argparse
import ctypes
from datetime import datetime
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw
from register_court import Camera


HERE = Path(__file__).absolute().parent
PRECISE = HERE.parents[1]
SHARED = PRECISE / 'xuhui-jianguo-336-lane-one-villa/measurements/render_registered_court.py'
ENGINE = runpy.run_path(str(SHARED))
RASTER = ENGINE['RASTER']
VIEWS = {
    '1934': ('1934  South entrance and east wall', 'https://pastvu.com/p/1872086'),
    '2020': ('2020  South entrance', 'https://www.meipian.cn/547hqpfk')
}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def sunlight(station):
    if station == '1934':
        return np.array([0., -.8, .6], dtype='float32'), None
    stamp = datetime.fromisoformat('2020-10-17T11:14:20')
    hour = stamp.hour + stamp.minute / 60 + stamp.second / 3600
    lat = np.radians(31.1419)
    lon = 121.4332
    phase = 2 * np.pi / 365 * (stamp.timetuple().tm_yday - 1 + (hour - 12) / 24)
    equation = 229.18 * (.000075 + .001868 * np.cos(phase) - .032077 * np.sin(phase)
                         - .014615 * np.cos(2 * phase) - .040849 * np.sin(2 * phase))
    declination = (.006918 - .399912 * np.cos(phase) + .070257 * np.sin(phase)
                   - .006758 * np.cos(2 * phase) + .000907 * np.sin(2 * phase)
                   - .002697 * np.cos(3 * phase) + .00148 * np.sin(3 * phase))
    h = np.radians((60 * hour + equation + 4 * lon - 480) / 4 - 180)
    east = -np.cos(declination) * np.sin(h)
    north = np.sin(declination) * np.cos(lat) - np.cos(declination) * np.cos(h) * np.sin(lat)
    up = np.sin(lat) * np.sin(declination) + np.cos(lat) * np.cos(declination) * np.cos(h)
    # Local axes from the short south edge of parcel 1155 in the orthophoto.
    east_x, north_x = .9554733069107554, .2950775487579925
    local = [east * east_x + north * north_x, -east * north_x + north * east_x, up]
    return np.array(local, dtype='float32'), [
        round(np.degrees(np.arctan2(east, north)) % 360, 3),
        round(np.degrees(np.arcsin(up)), 3)
    ]


def render(mesh, out, long_edge):
    out.mkdir(parents=True, exist_ok=True)
    model = RASTER.read_glb(mesh)
    report = {
        'model_sha256': sha(mesh), 'camera_source_sha256': sha(HERE / 'court-cameras.json'),
        'renderer_sha256': sha(HERE / 'render_registered_hall.py'),
        'material_backend_sha256': sha(SHARED),
        'normal_map_shader_sha256': sha(SHARED.parent / 'court_normal_map.h'),
        'daylight_backend_sha256': sha(ENGINE['DAYLIGHT']), 'views': {}
    }
    thumbs = []
    with tempfile.TemporaryDirectory(dir=out) as path:
        lib = ENGINE['make_library'](Path(path))
        painter = ENGINE['MaterialPass'](lib, model[1], model[2])
        transforms, directions, depths = ENGINE['sky_maps'](model[0], lib, RASTER)
        lib.set_sky(ENGINE['SAMPLES'], ENGINE['DEPTH_RESOLUTION'], RASTER.ptr(transforms),
                    RASTER.ptr(directions), RASTER.ptr(depths))
        for key, (label, url) in VIEWS.items():
            camera = Camera(key)
            projection = camera.projection()
            width, height = camera.size
            if key == '1934':
                height = 1840  # Exclude the 43-row web attribution strip below the scan.
            pixels = round(long_edge * width / max(width, height))
            spacing = width / pixels
            frame = (0, 0, width, height)
            field = np.full((round(height / spacing), pixels), -1., dtype='float32')
            inverse = np.linalg.inv(projection[:, :3])
            back = np.ascontiguousarray(np.column_stack((inverse, -inverse @ projection[:, 3])), dtype='float32')
            sun, angles = sunlight(key)
            lib.set_photo(RASTER.ptr(back), ctypes.c_float(spacing), key == '2020', RASTER.ptr(field))
            clipped = ENGINE['BACKEND']['projected_parts'](model, projection)
            with patch.object(RASTER, 'read_glb', return_value=clipped):
                painter.active = True
                image, stats = RASTER.raster(mesh, painter, pixels, projection, frame, sun, angles)
                painter.active = False
                flat, _ = RASTER.raster(mesh, painter, pixels, projection, frame, sun, angles)
            target = out / ('view-' + key + '.jpg')
            image.save(target, quality=94, subsampling=0, optimize=True)
            delta = np.max(np.abs(np.asarray(image, dtype='int16') - np.asarray(flat, dtype='int16')), axis=2)
            visible = [m['name'] for m in model[1] if 'normalTexture' in m
                       and m['name'] in stats['materials_visible_samples']]
            if stats['zbuffer_foreground_pixels'] < 100:
                raise ValueError('Mesh is outside registered view ' + key)
            if visible and not np.any(delta):
                raise ValueError('Visible normal maps had no effect in view ' + key)
            stats.update(source=url, image_time_local='2020-10-17T11:14:20+08:00' if angles else None,
                         time_evidence='11:14 image watermark and 11:14:20 EXIF' if angles else None,
                         illumination='direct sun and diffuse sky' if angles else 'diffuse sky only',
                         solar_azimuth_altitude_deg=angles, camera_input_canvas=list(camera.size),
                         original_photo_frame=list(frame), world_to_pixel=projection.tolist(),
                         diffuse_sky_directions=ENGINE['SAMPLES'],
                         normal_materials_visible=visible, normal_map_changed_pixels=int(np.count_nonzero(delta)),
                         max_normal_map_channel_delta=int(delta.max()), file=target.name, sha256=sha(target))
            report['views'][key] = stats
            tile = image.copy()
            tile.thumbnail((500, 331))
            thumbs.append((tile, label))
    sheet = Image.new('RGB', (1036, 383), '#f3f1eb')
    draw = ImageDraw.Draw(sheet)
    for i, (tile, label) in enumerate(thumbs):
        x = 8 + 516 * i
        sheet.paste(tile, (x + (500 - tile.width) // 2, 7 + (331 - tile.height) // 2))
        draw.text((x + 5, 350), label, fill='#39362c')
    name = out / 'registered-hall.jpg'
    sheet.save(name, quality=94, subsampling=0)
    report['sheet'] = {'file': name.name, 'sha256': sha(name)}
    (out / 'registered-renders.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--width', type=int, default=840, help='Maximum rendered dimension per view')
    args = parser.parse_args()
    render(args.glb, args.output, args.width)
