"""Render the 1230 courtyard GLB from two calibrated photographic stations.

Both views sample the GLB textures, UVs and normal maps. The Gao88 photograph has
diffuse lighting. The 2016 direct-sun model uses the photographed EXIF time and measured facade bearing.
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
from PIL import Image, ImageDraw, ImageFont
from register_court import Camera


HERE = Path(__file__).absolute().parent
PRECISE = HERE.parents[1]
SHARED = PRECISE / 'xuhui-jianguo-336-lane-one-villa/measurements/render_registered_court.py'
ENGINE = runpy.run_path(str(SHARED))
RASTER = ENGINE['RASTER']
VIEWS = {
    '2013': ('2013   No. 1230 and east balcony, Gao88', 'https://blog.sina.com.cn/s/blog_5d1bdf480101d590.html'),
    '2016': ('2016   Facade across the courtyard, masa3594', 'https://4travel.jp/travelogue/11115719')
}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def sunlight(station):
    if station == '2013':
        return np.array([0., -.8, .6], dtype='float32'), None
    stamp = datetime.fromisoformat('2016-01-20T11:24:36')
    hour = stamp.hour + stamp.minute / 60 + stamp.second / 3600
    lat = np.radians(31.21642050919118)
    lon = 121.44798685280341
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
    # Local axes from the 45.33 m long facade edge of mapped rear block 2018 (75.650692 degrees).
    east_x, north_x = np.sin(np.radians(75.6506921725107)), np.cos(np.radians(75.6506921725107))
    local = [east * east_x + north * north_x, -east * north_x + north * east_x, up]
    return np.array(local, dtype='float32'), [
        round(np.degrees(np.arctan2(east, north)) % 360, 3),
        round(np.degrees(np.arcsin(up)), 3)
    ]


def sample_view(mesh, model, painter, lib, projection, frame, pixels, sun, angles, grid):
    """Integrate projected mortar and thin bars over each output pixel."""
    spacing = (frame[2]-frame[0])/pixels
    width, height = pixels, round((frame[3]-frame[1])/spacing)
    linear = np.arange(256, dtype='float32') / 255.
    linear = np.where(linear <= .04045, linear/12.92, ((linear+.055)/1.055)**2.4)
    sums = [np.zeros((height, width, 3), dtype='float32') for _ in range(2)]
    first_stats = None
    for iy in range(grid):
        for ix in range(grid):
            q = projection.copy()
            q[0] -= ((ix+.5)/grid - .5)*spacing*q[2]
            q[1] -= ((iy+.5)/grid - .5)*spacing*q[2]
            inverse = np.linalg.inv(q[:,:3])
            back = np.ascontiguousarray(np.column_stack((inverse, -inverse@q[:,3])), dtype='float32')
            field = np.full((height, width), -1., dtype='float32')
            lib.set_photo(RASTER.ptr(back), ctypes.c_float(spacing), bool(angles), RASTER.ptr(field))
            clipped = ENGINE['BACKEND']['projected_parts'](model,q)
            with patch.object(RASTER,'read_glb',return_value=clipped):
                for i,active in enumerate((True,False)):
                    painter.active=active
                    image,stats=RASTER.raster(mesh,painter,pixels,q,frame,sun,angles)
                    sums[i] += linear[np.asarray(image,dtype='uint8')]
                    if first_stats is None:
                        first_stats=stats
    images=[]
    for total in sums:
        mean=total/(grid*grid)
        srgb=np.where(mean<=.0031308,12.92*mean,1.055*mean**(1/2.4)-.055)
        images.append(Image.fromarray(np.clip(np.rint(srgb*255),0,255).astype('uint8')))
    first_stats.update(samples_per_output_pixel=grid*grid,antialias='Uniform subpixel grid in linear RGB')
    return *images,first_stats


def render(mesh, out, long_edge, grid):
    out.mkdir(parents=True, exist_ok=True)
    model = RASTER.read_glb(mesh)
    report = {
        'model_sha256': sha(mesh), 'camera_source_sha256': sha(HERE / 'registered-rear.json'),
        'renderer_sha256': sha(Path(__file__).absolute()),
        'material_backend_sha256': sha(SHARED),
        'normal_map_shader_sha256': sha(SHARED.parent / 'court_normal_map.h'),
        'daylight_backend_sha256': sha(ENGINE['DAYLIGHT']), 'views': {}
    }
    source = json.loads((HERE / 'research-sources.json').read_text())
    references = {'2013': 'gao-04', '2016': 'masa-43034625-650'}
    thumbs = []
    with tempfile.TemporaryDirectory(dir=out) as path:
        lib = ENGINE['make_library'](Path(path))
        painter = ENGINE['MaterialPass'](lib, model[1], model[2])
        transforms, directions, depths = ENGINE['sky_maps'](model[0], lib, RASTER)
        lib.set_sky(ENGINE['SAMPLES'], ENGINE['DEPTH_RESOLUTION'], RASTER.ptr(transforms),
                    RASTER.ptr(directions), RASTER.ptr(depths))
        for key, (label, url) in VIEWS.items():
            camera = Camera(key)
            intrinsic = np.array([[camera.f, 0, camera.cx], [0, camera.f, camera.cy], [0, 0, 1]])
            projection = intrinsic @ np.column_stack((camera.R, -camera.R @ camera.c))
            # The published cameras use integer pixel centres. The raster uses edges
            # with sample centres at +.5, so the image origins differ by half a pixel.
            projection[:2] += .5 * projection[2]
            width, height = camera.width, camera.height
            pixels = round(long_edge * width / max(width, height))
            frame = (0, 0, width, height)
            sun, angles = sunlight(key)
            image, flat, stats = sample_view(mesh,model,painter,lib,projection,frame,pixels,sun,angles,grid)
            target = out / ('view-' + key + '.jpg')
            image.save(target, quality=94, subsampling=0, optimize=True)
            delta = np.max(np.abs(np.asarray(image, dtype='int16') - np.asarray(flat, dtype='int16')), axis=2)
            visible = [m['name'] for m in model[1] if 'normalTexture' in m
                       and m['name'] in stats['materials_visible_samples']]
            if stats['zbuffer_foreground_pixels'] < 100:
                raise ValueError('Mesh is outside registered view ' + key)
            if visible and not np.any(delta):
                raise ValueError('Visible normal maps had no effect in view ' + key)
            reference = next(p for p in source['photographs'] if p['key'] == references[key])
            stats.update(source=url, source_photo_sha256=reference['sha256'], source_photo_url=reference['url'],
                         source_photographer=source['sources'][reference['source']]['credit'], image_time_local='2016-01-20T11:24:36+08:00' if angles else None,
                         time_evidence='Canon SX160 IS EXIF DateTimeOriginal 11:24:36. The date also appears on the image. Shanghai UTC+8 assumed.' if angles else None,
                         illumination='direct sun and diffuse sky' if angles else 'diffuse sky only',
                         solar_azimuth_altitude_deg=angles, camera_input_canvas=[camera.width, camera.height],
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
    font_path = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    font = ImageFont.truetype(str(font_path),18,index=2) if font_path.is_file() else ImageFont.load_default(size=15)
    captions = ['2013年发表的院内近照机位 · 高参88','2016年1月20日院向机位 · 中国の風景']
    for i, (tile, label) in enumerate(thumbs):
        x = 8 + 516 * i
        sheet.paste(tile, (x + (500 - tile.width) // 2, 7 + (331 - tile.height) // 2))
        draw.text((x + 5, 341), captions[i] if font_path.is_file() else label, font=font, fill='#39362c')
    name = out / 'registered-courtyard.jpg'
    sheet.save(name, quality=94, subsampling=0)
    report['sheet'] = {'file': name.name, 'sha256': sha(name)}
    (out / 'registered-renders.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--width', type=int, default=840, help='Maximum rendered dimension per view')
    parser.add_argument('--grid', type=int, choices=[1,2,3,4], default=3, help='Subpixel samples per axis')
    args = parser.parse_args()
    render(args.glb, args.output, args.width, args.grid)
