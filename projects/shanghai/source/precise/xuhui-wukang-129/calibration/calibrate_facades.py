#!/usr/bin/env python3
"""Conditional multi-plane photo analysis, without altering frozen map geometry."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
COMMON = HERE.parent / 'common'
sys.path.insert(0, str(COMMON))
from photo_metric import calibrate, line, project


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    c = json.loads((HERE / 'controls.json').read_text())
    result = calibrate(c)
    K = np.asarray(result['camera_intrinsics_oriented'])
    basis = np.column_stack([result['directions_camera'][k] for k in ['facade_u', 'world_up', 'facade_outward_d']])
    C = np.asarray(result['camera_position_facade_u_z_d_m'])
    H = np.asarray(result['oriented_pixel_to_facade_u_z'])
    A_hinge = np.r_[project(H, c['plane_B_hinge_pixel']), 0.]

    def plane(group, anchor):
        # Fit one horizontal direction with the already fitted shared world up.
        # A u and outward d span the horizontal plane; z is explicitly shared.
        normals = np.asarray([K.T @ line(*s['points']) for s in group])
        normals /= np.linalg.norm(normals, axis=1)[:, None]
        candidates = normals @ basis[:, [0, 2]]
        h = np.linalg.svd(candidates)[2][-1]
        direction = np.array([h[0], 0., h[1]])
        if (basis @ direction)[0] < 0:
            direction *= -1
        normal = np.cross(direction, [0., 1., 0.])
        if normal @ (C-anchor) < 0:
            normal *= -1
        return {'anchor_u_z_d': anchor.tolist(), 'horizontal_u_z_d': direction.tolist(), 'normal_u_z_d': normal.tolist(),
                'horizontal_angle_from_A_deg': float(np.degrees(np.arctan2(-direction[2], direction[0])))}

    def intersect(p, pl):
        ray = basis.T @ np.linalg.solve(K, np.r_[p, 1.])
        a, n = np.asarray(pl['anchor_u_z_d']), np.asarray(pl['normal_u_z_d'])
        t = float(n @ (a-C) / (n @ ray))
        assert t > 0
        return C+t*ray

    A = {'anchor_u_z_d': [0., 0., 0.], 'horizontal_u_z_d': [1., 0., 0.], 'normal_u_z_d': [0., 0., 1.], 'horizontal_angle_from_A_deg': 0.}
    B = plane(c['plane_B_horizontal_lines'], A_hinge)
    D_hinge = intersect(c['plane_D_hinge_on_B_pixel'], B)
    D = plane(c['plane_D_horizontal_lines'], D_hinge)
    obs = json.loads((HERE.parent / 'references/review/observation-independent.json').read_text())
    windows = []
    planes = {'A': A, 'B': B, 'C': A, 'D': D}
    for zone in obs['zones']:
        name = zone['plane']
        if name not in planes:
            continue
        for key, q in zone['2026_controls'].items():
            if 'quad' not in key:
                continue
            p = np.asarray([intersect(x, planes[name]) for x in q])
            windows.append({'plane': name, 'name': key, 'pixels': q, 'u_z_d_m': p.tolist(),
                            'horizontal_width_m': float((np.linalg.norm(p[1]-p[0])+np.linalg.norm(p[2]-p[3]))/2),
                            'height_m': float((p[0,1]+p[1,1]-p[2,1]-p[3,1])/2),
                            'bottom_z_m': float((p[2,1]+p[3,1])/2),
                            'status': 'conditional reconstruction dimensions; D depends on occluded hinge assumption; C lower front tentatively assigned A plane'})
    rng = np.random.default_rng(20261026)
    rows = []
    for _ in range(128):
        s = calibrate(c, 1+rng.normal(0, .06), rng.normal(0,18,2), rng)
        rows.append([p['facade_u_z_m'][1] for p in s['height_points']])
    values = np.asarray(rows)
    for i, p in enumerate(result['height_points']):
        interval = np.percentile(values[:,i], [5,95])
        p['assumption_sensitivity_5_95_m'] = interval.tolist()
        corrections = np.asarray(p['conditional_depth_height_interval_m'])-p['facade_u_z_m'][1]
        p['assumption_sensitivity_plus_depth_m'] = (interval+corrections).tolist()
    result.update({'schema': 'wukang129-conditional-multiplane-calibration-v1',
        'status': 'Reconstruction aid only: envelope scale and occluded plane hinge assumptions are not surveyed measurements.',
        'source_image': {'file': c['image'], 'sha256': c['image_sha256'], 'author': 'Windmemories', 'license': 'CC-BY-SA-4.0', 'pixels': [1800,1200], 'orientation': 1},
        'sensor_evidence': 'camera-source.json', 'controls_file': 'controls.json', 'controls_sha256': sha(HERE/'controls.json'),
        'shared_photo_metric_tool_sha256': sha(COMMON/'photo_metric.py'), 'this_tool_sha256': sha(Path(__file__)),
        'fitted_planes': {'A': A, 'B': B, 'D': D}, 'window_checks': windows,
        'coordinate_contract': {'u': 'photo-left to photo-right along nominated A front; negative frozen native source u',
            'z': 'world up', 'd': 'outward toward camera; model depth is -d',
            'planeA_vs_source': 'Nominated A is a conditional front reference; source polygon unchanged. The observed gabled/circular/recessed superstructure is an explicitly inferred reconstruction.'},
        'limits': ['No single plane homography applies to the entire house.', 'B direction fitted from B window edges; D direction fitted separately from D window edges.',
                  'D hinge is obscured by a tree; its assumed location materially affects depth and width.', 'Rounded E cannot use the planar mapping; later curved-wall dimensions remain explicit photo-shape estimates.',
                  '128 samples propagate chosen uncertainty, not a measurement confidence interval.', 'Original photo bytes unchanged; no texture projected by this analysis.']})
    (HERE/'calibration-independent.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(15,10), dpi=120)
    ax.imshow(Image.open(HERE/c['image']))
    colors = {'A':'#00bfff','B':'#ff00bd','C':'#00ff65','D':'#ffb000','E':'#f0ff00'}
    for w in windows:
        q=np.asarray(w['pixels']); q=np.r_[q,q[:1]]
        ax.plot(q[:,0],q[:,1],color=colors[w['plane']],lw=1.4)
        ax.text(q[0,0],q[0,1]-8,w['plane']+' '+f"{w['horizontal_width_m']:.2f}×{w['height_m']:.2f}m",fontsize=7,color=colors[w['plane']],bbox={'facecolor':'black','alpha':.55,'pad':1})
    for key, color in [('horizontal_lines','#00bfff'),('plane_B_horizontal_lines','#ff00bd'),('plane_D_horizontal_lines','#ffb000')]:
        for seg in c[key]:
            q=np.asarray(seg['points']);ax.plot(q[:,0],q[:,1],color=color,lw=1.3)
    ax.scatter([A_hinge[0]],[A_hinge[1]],s=0) # retain explicit geometry calculations above, no second fabricated image
    ax.set_xlim(0,1800);ax.set_ylim(1200,0)
    ax.set_title('129 Wukang Road: separate visible planes — conditional dimensions, not a survey')
    fig.text(.5,.015,'Photo: Windmemories / CC BY-SA 4.0. Annotation derivative under CC BY-SA 4.0. Original JPEG unchanged. Full mapped width is an uncertain scale proxy.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(HERE/'comparison.png');plt.close(fig)
    print(json.dumps({'A_camera_u_z_d':C.tolist(),'A_fit_rms_px':result['line_endpoint_rms_px'],'planes':result['fitted_planes'],'windows':[{k:w[k] for k in ['plane','name','horizontal_width_m','height_m','bottom_z_m']} for w in windows]},indent=2))


if __name__ == '__main__':
    main()
