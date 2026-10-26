#!/usr/bin/env python3
"""Relative facade rectification with an explicit refusal to invent ground height.

Reuses the frozen camera mathematics, but writes an independent relative-plane
record. Width-based metric values are conditional, with origin at a chosen rail.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image

HELPER_SHA = 'dcab74584b59a7c891bbf13125b9c693908bb8ffcdac50444489d834abc8019c'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solve(helper, c, rng=None):
    c = json.loads(json.dumps(c))
    if rng is not None:
        for key in ('horizontal_lines', 'vertical_lines', 'bay_axis_lines'):
            for seg in c[key]:
                seg['points'] = (np.asarray(seg['points']) + rng.normal(0, c['uncertainty']['endpoint_sigma_px'], (2, 2))).tolist()
        for key in ('bay_reference_line',):
            c[key]['points'] = (np.asarray(c[key]['points']) + rng.normal(0, c['uncertainty']['endpoint_sigma_px'], (2, 2))).tolist()
    focal_scale = 1 if rng is None else 1 + rng.normal(0, c['uncertainty']['focal_scale_sigma'])
    principal = (0, 0) if rng is None else rng.normal(0, c['uncertainty']['principal_point_sigma_px'], 2)
    camera = helper.intrinsics(c['raw_size'], c['sensor_mm_for_stored_axes'], c['focal_mm'] * focal_scale, c['exif_orientation'], principal)
    K = camera['oriented']
    u, z, forward, errors = helper.fit_pose(K, [c['horizontal_lines'], c['vertical_lines']])
    H = np.vstack([u, z, forward]) @ np.linalg.inv(K)
    reference = helper.line(*c['bay_reference_line']['points'])
    pixels = [helper.intersection(reference, helper.line(*axis['points'])) for axis in c['bay_axis_lines']]
    plane = helper.project(H, pixels)
    width = plane[-1, 0] - plane[0, 0]
    assert width > 0
    fractions = (plane[:, 0] - plane[0, 0]) / width
    assert np.all(np.diff(fractions) > 0)
    nominal_scale = c['mapped_roof_front_width_m'] / width
    origin = (plane[0] + plane[-1]) / 2
    conditional = np.array([[nominal_scale, 0, -nominal_scale * origin[0]], [0, nominal_scale, -nominal_scale * origin[1]], [0, 0, 1.]]) @ H
    conditional /= conditional[2, 2]
    vp = K @ u
    return {'unit_homography': H, 'conditional_homography': conditional, 'fractions': fractions,
        'bay_widths': np.diff(fractions), 'axis_pixels': np.array(pixels), 'K': K, 'errors': errors,
        'horizontal_vanishing_point': vp / vp[2], 'conditional_scale': nominal_scale}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('controls', type=Path)
    sibling_helper = Path(__file__).resolve().with_name('photo_metric.py')
    default_helper = sibling_helper if sibling_helper.exists() else Path(__file__).absolute().parents[2] / 'common/photo_metric.py'
    parser.add_argument('--helper', type=Path, default=default_helper)
    parser.add_argument('--samples', type=int, default=256)
    args = parser.parse_args()
    assert sha(args.helper) == HELPER_SHA, 'Frozen helper mismatch'
    spec = importlib.util.spec_from_file_location('frozen_photo_metric', args.helper)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    c = json.loads(args.controls.read_text())
    image_path = args.controls.parent / c['image']
    image = Image.open(image_path)
    exif = image.getexif()
    details = exif.get_ifd(34665)
    assert list(image.size) == c['raw_size'] and exif.get(274) == c['exif_orientation']
    assert float(details[37386]) == c['focal_mm']
    result = solve(helper, c)
    rng = np.random.default_rng(20261026)
    samples = [solve(helper, c, rng)['bay_widths'] for _ in range(args.samples)]
    ranges = np.percentile(samples, [5, 95], axis=0).T
    reference_H = result['conditional_homography']
    apparent_lengths = []
    for segment in c.get('conditional_segments', []):
        p = helper.project(reference_H, segment['points'])
        apparent_lengths.append({'label': segment['label'], 'source_pixels': segment['points'],
            'conditional_vertical_span_m': float(abs(p[1, 1] - p[0, 1])), 'assumption_and_limit': segment['assumption_and_limit']})
    inverse = np.linalg.inv(result['unit_homography'])
    check = result['unit_homography'] @ inverse
    error = float(np.max(np.abs(check / check[2, 2] - np.eye(3))))
    assert error < 1e-10
    rms = float(np.sqrt(np.mean([v * v for row in result['errors'] for v in row['endpoint_residual_px']])))
    output = {'schema': 'relative-photo-plane-proportions-v1',
        'status': 'Relative three-bay proportions supported; absolute ground-referenced height calibration is not established',
        'absolute_height_calibrated': False, 'ground_referenced_metric_homography': None,
        'source_image': {'file': c['image'], 'sha256': sha(image_path), 'stored_size': list(image.size), 'exif_orientation': exif.get(274), **c['source_license']},
        'camera_evidence': c['camera_evidence'], 'controls': c, 'controls_file': args.controls.name,
        'controls_sha256': sha(args.controls), 'tool_sha256': sha(Path(__file__)), 'frozen_math_helper_sha256': HELPER_SHA,
        'camera_intrinsics_stored_and_oriented': result['K'].tolist(),
        'stored_to_oriented_pixel': np.eye(3).tolist(), 'oriented_pixel_to_unit_front_plane': result['unit_homography'].tolist(),
        'unit_front_plane_to_oriented_pixel': inverse.tolist(), 'matrix_inverse_max_error': error,
        'horizontal_vanishing_point_source_pixels': result['horizontal_vanishing_point'].tolist(),
        'line_fit': result['errors'], 'line_endpoint_rms_source_px': rms,
        'bay_boundary_source_pixels': result['axis_pixels'].tolist(), 'bay_boundary_fractions_left_to_right': result['fractions'].tolist(),
        'bay_width_fractions': result['bay_widths'].tolist(), 'bay_width_fraction_sensitivity_5_95': ranges.tolist(),
        'sensitivity_samples': args.samples, 'sensitivity_seed': 20261026,
        'conditional_map_width_projection': {'matrix': reference_H.tolist(), 'assumed_upper_gallery_front_width_m': c['mapped_roof_front_width_m'],
            'origin': 'Midpoint of end-post intersections with the chosen upper handrail line. z=0 IS THE UPPER HANDRAIL, not ground.',
            'status': 'Only if the satellite-derived roof width exactly matches this gallery end plane; not established by photo or footprint. Do not use this matrix as a world-height/texture calibration.',
            'segments': apparent_lengths},
        'height_for_model': c['height_model_advice'],
        'limitations': c['limitations']}
    path = args.controls.with_name('calibration-independent.json')
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    # A relative-plane diagram only, never a photorealistic wall texture.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 9), gridspec_kw={'width_ratios': [1, 1]})
    axes[0].imshow(image)
    for key, color in [('horizontal_lines', 'cyan'), ('vertical_lines', 'orange'), ('bay_axis_lines', 'magenta')]:
        for seg in c[key]:
            p = np.asarray(seg['points'])
            axes[0].plot(p[:, 0], p[:, 1], color=color, lw=1)
    p = result['axis_pixels']
    axes[0].scatter(p[:, 0], p[:, 1], c='yellow', s=20)
    axes[0].set_title('Original photograph + explicit line controls')
    fractions = result['fractions']
    for i, (a, b) in enumerate(zip(fractions, fractions[1:])):
        axes[1].barh([0], [b - a], left=[a], color=['#b99165', '#855c3d', '#b99165'][i])
        axes[1].text((a + b) / 2, 0, f'{b-a:.3f}', ha='center', va='center', color='white')
    axes[1].set_xlim(0, 1)
    axes[1].set_yticks([])
    axes[1].set_xlabel('Relative width of the same upper-gallery plane')
    axes[1].set_title('Three structural bays; no meter-height claim')
    axes[1].text(.5, .8, c['figure_limitations_text'], transform=axes[1].transAxes, ha='center', va='center')
    fig.suptitle(c['building_label'] + ': perspective-corrected frontage proportions, not a survey')
    fig.text(.5, .015, f"Photo: {c['source_license']['author']}, {c['source_license']['license']}. Original pixels unchanged; this annotated analysis derivative has the same license.", ha='center', fontsize=8)
    fig.tight_layout(rect=[0, .035, 1, .96])
    fig.savefig(args.controls.with_name('calibration-independent-comparison.png'), dpi=130)
    plt.close(fig)
    print(json.dumps({'file': str(path), 'rms_source_px': rms, 'bay_fractions': output['bay_width_fractions'], 'absolute_height_calibrated':False}, indent=2))


if __name__ == '__main__':
    main()
