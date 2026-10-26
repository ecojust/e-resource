#!/usr/bin/env python3
"""Additional finite support-band measurement; preserves the failed wider-band test."""
from pathlib import Path
import json, math, time
import numpy as np
from actual_glb import loadraw, enu_tri, z, need, filemeta, sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RAW = ROOT / 'run-v1/raw/songjiang-fangta-pagoda-raw.glb'
PRIOR = HERE / 'actual-roles-contacts.json'
OUT = HERE / 'actual-hip-support-band.json'

started = time.monotonic()
need(not OUT.exists(), 'Use a new output')
original_prior = PRIOR.read_bytes()
prior = json.loads(original_prior)
raw = loadraw(RAW)
need(raw['raw']['sha256'] == prior['raw']['sha256'], 'Original support report refers to different raw')
need(prior['hip_full_width_finite_contact_passed'] is False and prior['hip_centerline_contact_passed'] is True, 'Expected original wider-band failure and centerline result')
cal = json.loads((ROOT / 'calibration.json').read_bytes())
need(sha((ROOT / 'calibration.json').read_bytes()) == raw['doc']['extras']['calibration_sha256'], 'Calibration binding differs')
ring = np.asarray(raw['doc']['extras']['model_square_ring_enu'], float)
cache = {}
def part(label):
    if label not in cache:
        matches = [p for k, p in raw['parts'].items() if k[0] == label]
        need(len(matches) == 1, 'Ambiguous actual part ' + label)
        cache[label] = enu_tri(matches[0])
    return cache[label]

rows = []
for v in cal['levels']:
    level = v['level']
    roof = part(f'L{level}/continuous-curved-roof')
    inner = v['wall_scale'] * .945 if level < 9 else .075
    for corner in range(4):
        seat = part(f'L{level}/continuous-grey-ridge-seat{corner}')
        ridge = part(f'L{level}/continuous-upturned-corner-ridge{corner}')
        axis = ring[corner] / np.linalg.norm(ring[corner])
        across = np.array([-axis[1], axis[0]])
        for radial in [.05, .20, .40, .60, .80, .95, .995]:
            center = ring[corner] * (inner * (1 - radial) + v['roof_scale'] * radial)
            for lateral in [-.010, -.005, 0., .005, .010]:
                xy = center + across * lateral
                vals = {name: z(mesh, xy, top) for name, mesh, top in [
                    ('roof_bottom', roof, False), ('roof_top', roof, True),
                    ('seat_bottom', seat, False), ('seat_top', seat, True),
                    ('ridge_bottom', ridge, False), ('ridge_top', ridge, True),
                ]}
                missing = [name for name, value in vals.items() if value is None]
                roof_overlap = None if missing else min(vals['roof_top'], vals['seat_top']) - max(vals['roof_bottom'], vals['seat_bottom'])
                ridge_overlap = None if missing else min(vals['seat_top'], vals['ridge_top']) - max(vals['seat_bottom'], vals['ridge_bottom'])
                rows.append({'level': level, 'corner': corner, 'radial_fraction': radial, 'lateral_m': lateral, 'xy_enu_m': xy.tolist(), 'actual_vertical_surface_intervals_m': vals, 'missing_surfaces': missing, 'roof_seat_interval_overlap_m': roof_overlap, 'seat_ridge_interval_overlap_m': ridge_overlap, 'finite_sample_passed': not missing and roof_overlap > 0 and ridge_overlap > 0})
need(len(rows) == 1260, 'Coverage differs')
passed = all(row['finite_sample_passed'] for row in rows)
report = {
    'schema': 'fangta-actual-hip-finite-support-band-v1',
    'finite_support_band_passed': passed, 'raw': raw['raw'],
    'prior_unmodified_wider_band_report': filemeta(PRIOR),
    'prior_full_width_test_passed': prior['hip_full_width_finite_contact_passed'],
    'scope': 'Additional finite measurements at lateral offsets -10,-5,0,+5,+10 mm for all36 hip seats and seven radial positions. Every measured vertical interval derives from exported FLOAT32 triangles. This tests a finite-width central support band. The original±25mm gaps and footprint misses remain recorded and are not reclassified or waived by this report. Samples do not prove all-point continuous contact or physical safety.',
    'levels': list(range(1, 10)), 'corners': list(range(4)),
    'radial_samples': [.05, .20, .40, .60, .80, .95, .995],
    'lateral_offsets_m': [-.010, -.005, 0., .005, .010],
    'sample_count': len(rows), 'failed_sample_count': sum(not row['finite_sample_passed'] for row in rows),
    'minimum_roof_seat_interval_overlap_m': min(row['roof_seat_interval_overlap_m'] for row in rows if row['roof_seat_interval_overlap_m'] is not None),
    'minimum_seat_ridge_interval_overlap_m': min(row['seat_ridge_interval_overlap_m'] for row in rows if row['seat_ridge_interval_overlap_m'] is not None),
    'samples': rows, 'elapsed_seconds': time.monotonic() - started,
    'all_geometry_and_prior_report_unchanged': True,
    'model_accepted': False, 'native_or_browser_accepted': False,
    'whole_model_collision_free_claim': False,
}
need(PRIOR.read_bytes() == original_prior and sha(RAW.read_bytes()) == raw['raw']['sha256'], 'Original data changed during audit')
text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
need(len(text.encode()) < 1_500_000, 'Report exceeded bound')
OUT.write_text(text)
print(json.dumps({k: report[k] for k in ['finite_support_band_passed', 'sample_count', 'failed_sample_count', 'minimum_roof_seat_interval_overlap_m', 'minimum_seat_ridge_interval_overlap_m', 'elapsed_seconds']}, indent=2))
