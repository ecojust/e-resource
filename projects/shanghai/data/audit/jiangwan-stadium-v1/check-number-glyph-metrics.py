"""Bound two-digit label ink using the actual production glyph PBF metrics.

The PBF is kept in memory only. Browser SDF/pixel inspection remains separate.
Use --pbf to reuse a privately retained exact input without another download.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

URL = 'https://tiles.openfreemap.org/fonts/Noto%20Sans%20Regular/0-255.pbf'
EXPECTED_SHA = 'ef1f38a3f1978591e846e9eaddf8a54f7047f546fc6aaed7872cc53151a5de78'


def varint(data, index):
    value = shift = 0
    while True:
        byte = data[index]
        index += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, index
        shift += 7


def fields(data):
    index = 0
    while index < len(data):
        tag, index = varint(data, index)
        key, kind = tag >> 3, tag & 7
        if kind == 0:
            value, index = varint(data, index)
        elif kind == 2:
            length, index = varint(data, index)
            value = data[index:index + length]
            index += length
        else:
            raise ValueError('Unexpected glyph protobuf wire type: ' + str(kind))
        yield key, value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pbf', type=Path)
    args = parser.parse_args()
    if args.pbf:
        raw = args.pbf.read_bytes()
        acquisition = 'Private retained bytes; no new HTTP request'
    else:
        request = urllib.request.Request(URL, headers={'User-Agent': 'Shanghai-model-layout-check/1.0'})
        with urllib.request.urlopen(request, timeout=40) as response:
            assert response.status == 200
            raw = response.read()
        acquisition = 'Actual HTTP200 response body'
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA, 'Font input changed; preserve the earlier report and review new glyph bytes separately'
    digits = {}
    for key, stack in fields(raw):
        if key != 1:
            continue
        for key, glyph in fields(stack):
            if key != 3:
                continue
            row = dict(fields(glyph))
            if 48 <= row[1] <= 57:
                digits[chr(row[1])] = {'width': row[3], 'height': row[4],
                    'left': (row[5] >> 1) ^ -(row[5] & 1),
                    'top': (row[6] >> 1) ^ -(row[6] & 1), 'advance': row[7]}
    assert len(digits) == 10
    measurements = []
    for number in range(1, 100):
        text, cursor, left, right = str(number), 0, float('inf'), -float('inf')
        for char in text:
            glyph = digits[char]
            left = min(left, cursor + glyph['left'])
            right = max(right, cursor + glyph['left'] + glyph['width'])
            cursor += glyph['advance']
        low, high = (left - cursor / 2) * .5 - .5, (right - cursor / 2) * .5 + .5
        measurements.append({'text': text, 'advance_px': cursor * .5,
            'glyph_ink_and_halo_width_px': (right - left) * .5 + 1,
            'centered_ink_plus_halo_x_px': [low, high],
            'clearance_to_sprite_stroke_inner_edge_px': 8.5 - max(-low, high)})
    assert all(row['clearance_to_sprite_stroke_inner_edge_px'] > 0 for row in measurements)
    report = {'url': URL, 'input_bytes': len(raw), 'input_sha256': EXPECTED_SHA,
        'acquisition': acquisition, 'base_font_px': 24, 'font_size_px': 12,
        'halo_px': .5, 'sprite_css_px': [20, 18], 'sprite_stroke_inner_edge_x_px': [-8.5, 8.5],
        'measurement': 'Actual glyph metrics with zero letter spacing and0.5px halo. Bounds horizontal ink geometry; antialiasing and browser SDF pixels require separate QA.',
        'minimum_horizontal_clearance_px': min(row['clearance_to_sprite_stroke_inner_edge_px'] for row in measurements),
        'widest_width_px': max(row['glyph_ink_and_halo_width_px'] for row in measurements),
        'current_78_and_88_controls': [row for row in measurements if row['text'] in ['78', '88']],
        'all_number_metrics': measurements, 'digits': digits, 'passed': True}
    Path(__file__).with_name('glyph-metrics-reproduction.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': True, 'widest_width_px': report['widest_width_px'], 'minimum_horizontal_clearance_px': report['minimum_horizontal_clearance_px']}))


if __name__ == '__main__':
    main()
