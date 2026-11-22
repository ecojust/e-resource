"""Independently measure two archival photographs of the Continental Court apartment façade.

Run with the directory containing the two cited archival JPEGs and an output JSON.
Only optical boundaries on each photographed façade enter the calculation.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

PHOTOS = {
    '836978': {
        'original_sha256': '3f72aaa4f7336b513af2da1e04b5def93ae509c44b7e76599a2ee2d9c400b8e5',
        'source': 'https://pastvu.com/p/836978',
        'description': 'Bubbling Well Road near Seymour Road，手工着色明信片。摄影者未署名，PastVu 上传者 avezink。',
        'years': [1930, 1940],
        'dimensions': [950, 613],
        'windows': [
            {'label': '较高一排的左、右两窗', 'centers': [[426, 258], [455, 255]], 'status': '树叶遮住一部分上缘，下缘及两片分开的暗口可辨。'},
            {'label': '其下同跨的左、右两窗', 'centers': [[427, 321], [456, 321]], 'status': '两处暗口和中间的实墙均清楚。用此层的四条竖边测量。'},
            {'label': '右侧较近开间的另外两窗', 'centers': [[610, 240], [650, 238]], 'status': '仅录树线以上的上部。'},
        ],
        'pier_sightings': [
            {'box': [389, 251, 409, 341], 'status': '上下两排之间连续的浅色突出部。'},
            {'box': [565, 219, 589, 257], 'status': '树线以上的浅色墩身。'},
            {'box': [657, 190, 691, 250], 'status': '临近转角的浅色竖带。下部有树遮。'},
        ],
        'limits': '电杆、树干及树叶遮住其余立面。明信片着色不足以测砖色、石色或栏片材质。',
        'training_rows': [312, 318, 324, 331, 334],
        'test_rows': [314, 320, 326, 329, 333],
        'bands': [[415, 422], [432, 437], [445, 451], [463, 468]],
        'section_y': 320,
    },
    '1156790': {
        'original_sha256': '1de72d760033ba4e5205443adbc986bcae3cdf50d03271171f32ac08d28473af',
        'source': 'https://pastvu.com/p/1156790',
        'description': 'Street view in central Shanghai，PastVu 原著录署 Coca Cola Archive，上传者 avezink。',
        'years': [1945, 1949],
        'dimensions': [1041, 716],
        'windows': [
            {'label': '最清楚的一跨双窗', 'centers': [[755, 115], [830, 113]], 'status': '两窗外框独立，各有窗台。右窗有向外打开的扇片，测量避开扇片。'},
            {'label': '相邻开间露出的一窗', 'centers': [[648, 147]], 'status': '可辨深色窗面、两条竖边和石窗台。同跨另一侧受店招遮挡。'},
        ],
        'pier_sightings': [
            {'box': [677, 84, 715, 207], 'status': '浅色墩身，下段竖长尖头凹槽可辨。'},
            {'box': [879, 25, 940, 184], 'status': '另一较宽浅色墩身，同层凹槽可辨。文字仅作影像定位。'},
        ],
        'limits': '较近一侧的招牌和窗扇遮边，最上檐与墩顶在画幅以外。',
        'training_rows': [75, 79, 82, 86, 89],
        'test_rows': [76, 78, 81, 84, 87],
        'bands': [[733, 743], [772, 780], [805, 815], [851, 859]],
        'section_y': 82,
    },
}


def get_edge(luma, y, bounds, sign):
    profile = luma[y - 1:y + 2].mean(axis=0)
    profile = np.convolve(profile, np.ones(3) / 3, mode='same')
    left, right = bounds
    xs = np.arange(left, right + 1)
    gradient = sign * (profile[xs + 1] - profile[xs - 1]) / 2
    k = int(np.argmax(gradient))
    assert gradient[k] > 2
    return int(xs[k])


def summarise(values):
    return {k: round(float(v), 4) for k, v in zip(('median', 'rms', 'max'), (np.median(values), np.sqrt(np.mean(np.square(values))), np.max(values)))}


def read_one(directory, number, cfg):
    p = directory / f'pastvu-{number}.jpg'
    assert hashlib.sha256(p.read_bytes()).hexdigest() == cfg['original_sha256']
    with Image.open(p) as image:
        assert list(image.size) == cfg['dimensions']
        luma = np.asarray(image.convert('L'), dtype=float)
    measurements = []
    for band, sign in zip(cfg['bands'], [-1, 1, -1, 1]):
        def measure(ys):
            return [[get_edge(luma, y, band, sign), y] for y in ys]
        training = np.array(measure(cfg['training_rows']))
        held = np.array(measure(cfg['test_rows']))
        slope, intercept = np.polyfit(training[:, 1], training[:, 0], 1)
        error = np.abs(held[:, 0] - (slope * held[:, 1] + intercept))
        x = slope * cfg['section_y'] + intercept
        measurements.append(dict(fit_pixels=training.tolist(), held_pixels=held.tolist(),
            x_at_section=round(float(x), 4), line_x_per_y=round(float(slope), 5),
            held_absolute_error_pixels=error.round(4).tolist()))
    x = [d['x_at_section'] for d in measurements]
    all_errors = [e for d in measurements for e in d['held_absolute_error_pixels']]
    return dict(source=cfg, measured_jambs=measurements, held_error_px=summarise(all_errors),
                apparent_widths_at_section_px=np.round(np.diff(x), 4).tolist())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('image_directory', type=Path)
    ap.add_argument('report', type=Path)
    args = ap.parse_args()
    rows = {n: read_one(args.image_directory, n, cfg) for n, cfg in PHOTOS.items()}
    a, b = (np.array([r['x_at_section'] for r in book['measured_jambs']]) for book in rows.values())
    # Normalize the photographed widths by the two outer jambs. The inner two
    # boundaries remain withheld. No homologous apartment is assumed.
    def residual(source, target):
        projected = target[0] + (source[1:3] - source[0]) * (target[-1] - target[0]) / (source[-1] - source[0])
        return (projected - target[1:3]).round(4).tolist()
    report = dict(order=620, photos=rows, comparison={
        'method': '各图分别拟合四道竖边，各留20个独立扫描点；跨图仅用各自成对窗最外两边归一化，对中间两个边作留验。',
        'held_inner_edges_1930s_to_1940s_px': residual(a, b),
        'held_inner_edges_1940s_to_1930s_px': residual(b, a),
        'minimum_visible': {'836978': {'upper_window_openings': 6, 'pale_pier_observations': 3}, '1156790': {'upper_window_openings': 3, 'pale_pier_observations': 2}},
        'limits': '两张图共同支持成对窗和间隔的浅色墩。相片显示立面的不同范围，重复的窗组不能唯一对应到同一户或同一根墩。外边归一化后的偏差不能当作整栋同名点的配准误差。'})
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    main()
