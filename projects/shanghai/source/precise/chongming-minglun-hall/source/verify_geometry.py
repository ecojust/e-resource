"""Check actual exported Minglun Hall geometry and distinguish interpreted base from roof bounds."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh
from build_model import MinglunHall, ID, P

parser = argparse.ArgumentParser()
parser.add_argument('--assets', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
reports = {}
for role in ['raw', 'lod']:
    path = args.assets / f'{ID}-{role}.glb'
    scene = trimesh.load(path, force='scene', process=True)
    meshes = list(scene.geometry.values())
    assert meshes
    for mesh in meshes:
        assert np.isfinite(mesh.vertices).all() and (mesh.area_faces > 1e-12).all()
        mesh.merge_vertices(merge_norm=True, merge_tex=True)
        assert mesh.is_winding_consistent and mesh.volume > 0
    bounds = scene.bounds
    assert abs(bounds[0, 1]) < 1e-6 and abs(bounds[1, 1] - P['total_height']) < 1e-5
    authored = MinglunHall(role == 'lod').finish()
    for part in authored.b.parts:
        solid = trimesh.Trimesh(part['vertices'], part['triangles'], process=True)
        assert solid.is_watertight and solid.is_winding_consistent and solid.volume > 0, part['label']
    assert sum(len(m.faces) for m in meshes) == sum(len(part['triangles']) for part in authored.b.parts)
    total = trimesh.util.concatenate(meshes)
    basepart=next(p for p in authored.b.parts if p['label']=='documented-plan-size-assigned-to-base')
    v=np.array(basepart['vertices']);base=(v.max(0)-v.min(0))[:2]
    assert np.allclose(base,[20.6,12.7])
    # Probe one clear pane in every estimated window. A mistakenly solid wall
    # or a filled lattice cell would be hit before the deliberately inset backing.
    pane_offset = -P['window_width'] / 2 + P['window_width'] / (2 * P['window_columns'])
    pane_height = P['window_bottom'] + (P['window_top'] - P['window_bottom']) / (2 * P['window_rows'])
    origins = [[x + pane_offset, pane_height, 10] for x in authored.window_centres]
    directions = [[0, 0, -1] for _ in origins]
    locations, rays, _ = total.ray.intersects_location(origins, directions)
    first = [float(locations[rays == i, 2].max()) for i in range(len(origins))]
    assert np.allclose(first, [P['wall_depth'] / 2 - .32] * len(origins), atol=1e-5), first
    assert total.ray.intersects_any([[0, 2.0, 10]], [[0, 0, -1]]).all()
    # The corrected side-strip ends meet the front/rear inner faces; their caps
    # cannot lie on the exposed plaster planes at +/- wall_depth/2.
    side = next(p for p in authored.b.parts if p['label'] == 'side-skirting')
    rear = next(p for p in authored.b.parts if p['label'] == 'rear-skirting')
    assert np.isclose(np.array(side['vertices'])[:, 1].max(), np.array(rear['vertices'])[:, 1].min())
    assert not np.isclose(np.array(side['vertices'])[:, 1].max(), P['wall_depth'] / 2)
    span = bounds[1] - bounds[0]
    reports[role] = {
        'representation': 'uncompressed authored source GLB; packaged variants separately checked by manifest and browser',
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'triangles': sum(len(m.faces) for m in meshes),
        'bounds_glb': bounds.tolist(),
        'actual_total_envelope_width_depth_height_m': span[[0, 2, 1]].tolist(),
        'interpreted_base_width_depth_m': base.tolist(),
        'documentary_dimensions_are_not_eave_envelope': True,
        'authored_closed_solids': len(authored.b.parts), 'authored_solids_watertight': True,
        'nondegenerate': True, 'consistent_winding': True,
        'four_window_cell_rays_reach_inset_backing': True, 'closed_estimated_central_door_present': True,
        'skirting_endcaps_hidden_at_butt_joints': True,
        'documented_bays': None, 'estimated_front_divisions': 5, 'equal_divisions_are_estimated': True,
        'local_x_width_interpretation_m': 20.6, 'local_y_depth_interpretation_m': 12.7,
        'source_compass_directions_unspecified': True,
        'area_product_each_m2': P['base_width'] * P['base_depth'],
        'area_product_is_not_a_reported_area': True, 'museum_reported_area_m2': 261.6,
        'area_comparison_approximately_rounded': True,
        'historical_bays':5, 'chosen_height_m':10.37, 'alternate_documented_height_m':10.5, 'height_conflict_resolved':False, 'estimated_porch_columns':6, 'estimated_stair_steps':4, 'scope':'Text-size candidate and partly occluded photo context; modern grid, roof, openings and hidden elevations estimated; no full photographic or geographic acceptance',
    }
assert reports['lod']['triangles'] < reports['raw']['triangles']
args.out.parent.mkdir(parents=True, exist_ok=True)
args.out.write_text(json.dumps(reports, indent=2) + '\n')
print(json.dumps(reports))
