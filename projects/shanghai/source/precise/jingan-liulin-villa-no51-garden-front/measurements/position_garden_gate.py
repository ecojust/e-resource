"""Fit the gate along its original sightlines using the full, unobstructed second garden photograph."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'source'), str(HERE.parents[1] / 'hongkou-general-post-office/source/common')]
from court_gate import PALETTE, add_local_gate
from photo_architecture import Builder

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def eye(P):
    return -np.linalg.solve(P[:, :3], P[:, 3])

def intersects_frustum(tri, width, height):
    # Clip all surviving triangles to the true native sensor, including crossings
    # whose three projected vertices fall outside the image.
    u, v, w = np.moveaxis(tri, 2, 0)
    keep = np.logical_and.reduce([plane.max(axis=1) >= 0 for plane in (w, u, v, width*w-u, height*w-v)])
    planes = np.array([(0,0,1),(1,0,0),(-1,0,width),(0,1,0),(0,-1,height)])
    for polygon in tri[keep]:
        for plane in planes:
            out = []
            if not len(polygon):
                break
            for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
                da, db = a @ plane, b @ plane
                if da >= 0:
                    out.append(a)
                if (da >= 0) != (db >= 0):
                    out.append(a + (b-a) * da/(da-db))
            polygon = np.asarray(out)
        if len(polygon) >= 3:
            return True
    return False

def determine():
    hf, gf = HERE/'no51-house-cameras.json', HERE/'gate-plane-and-inscription.json'
    h, g = json.loads(hf.read_text()), json.loads(gf.read_text())
    p5, p6 = [np.array(h['source_poses'][n]['P']) for n in ('gao05','gao06')]
    pg = np.asarray(g['P_native'])
    c5, c6, cg = eye(p5), eye(p6), eye(pg)
    # Both 05 matrices describe exactly the same exposure. A single positive scale
    # remains after matching their optical centres and every image ray.
    basis = np.linalg.solve(p5[:,:3], pg[:,:3])
    basis /= np.linalg.norm(basis[:,0])
    def transform(s):
        out = np.eye(4)
        out[:3,:3] = s*basis
        out[:3,3] = c5 - s*basis@cg
        return out

    builder=Builder(PALETTE)
    add_local_gate(builder,False)
    triangles=np.concatenate([np.asarray(q['vertices'])[q['triangles']] for q in builder.parts])
    optics=p6[:,:3]@basis
    tri_rot=(triangles-cg)@optics.T
    anchor=p6[:,:3]@c5+p6[:,3]
    size=h['source_poses']['gao06']['native_size']
    def visible(s):
        return intersects_frustum(tri_rot*s+anchor,*size)
    lower,upper=.98,1.01
    assert not visible(lower) and visible(upper)
    for _ in range(21):
        mid=(lower+upper)/2
        if visible(mid): upper=mid
        else: lower=mid
    # Common grade is an estimate because the street threshold is outside 05.
    # Keep the original nominal wicket width and its physical tolerance, and the
    # previously documented uncertainties of its ground and handle datum.
    scale_info=g['physical_scale']
    wicket=scale_info['pedestrian_clear_width_proxy_m']; spread=scale_info['spread_m']
    limits=[1-spread/wicket,lower]
    scales=np.linspace(*limits,2401)
    z=c5[2]-(basis@cg)[2]*scales
    sigma=np.hypot(.20,scale_info['uncertainty_m'])
    weights=np.exp(-.5*((scales*wicket-wicket)/spread)**2-.5*(z/sigma)**2)
    weights=np.cumsum(weights)/weights.sum()
    quantiles=np.interp([.05,.5,.95],weights,scales)
    s=float(quantiles[1]);matrix=transform(s)
    c6_local=np.linalg.solve(matrix,np.r_[c6,1])[:3]
    assert not visible(s)
    fixed_depths={str(k):bool(visible(k)) for k in [.87,.92,.95,.98,.99,1.,1.05,1.1547672]}
    gground=matrix[:3,3].tolist()
    return dict(gate_to_house=matrix.tolist(),gate_joint_world_m=gground,
        gate_scale=s,gate_yaw_degrees_relative_to_house_x=float(np.degrees(np.arctan2(basis[1,0],basis[0,0]))),
        gate_camera_sha256=sha(gf),house_camera_sha256=sha(hf),source_native_sha256=h['images_sha256'],
        gate_local_eye_before_transfer_m=cg.tolist(),house05_eye_m=c5.tolist(),house06_eye_m=c6.tolist(),
        house06_eye_in_transferred_gate_m=c6_local.tolist(),positive_y_is_courtyard=True,
        optical_transfer=dict(uniform_scale_removed_singular_values=np.linalg.svd(basis)[1].tolist(),
            vertical_axis_difference_deg=float(np.degrees(np.arccos(basis[2,2]/np.linalg.norm(basis[:,2])))),
            comment='The two 05 calibrations are related by a measured near-similarity. Transferring through their common optical centre preserves the entire native image, including the plaque and near-zero-width scroll edges. Small departures from orthogonality are calibration differences, not a surveyed lean.'),
        field06_unobstructed=dict(native_size=size,triangles=len(triangles),visibility_by_scale=fixed_depths,
            largest_scale_with_all_triangles_outside=lower,smallest_intruding_scale=upper,
            selected_scale_leaves_any_visible_triangles=visible(s)),
        conditioning=dict(wicket_gauge_m=wicket,wicket_tolerance_m=spread,uncertainty_in_courtyard_grade_m=.20,
            assumed_handle_elevation_uncertainty_m=scale_info['uncertainty_m'],plausible_scale_range=limits,
            model_5_50_95_percentiles=quantiles.tolist(),alternative_gate_origin_grade_at_range_ends_m=[transform(k)[2,3] for k in limits],
            method='Intersect the original wicket-width interval with the measured upper bound from every triangle and the full second photograph. Select the median of the remaining grid weighted by the independent approximate width and height priors. This is a conditional model range, not a measured gate distance.'),
        physical_grade=dict(working_local_datum_elevation_m=gground[2],finished_post_base_house_z_m=-.016,
            finished_iron_clearance_house_z_m=.035,explanation='The gate feet are below the source image. Only the plain post bases and unadorned bottom ends of the uprights continue to the observed forecourt level.'),
        limits='The closed leaves are visible in 05. Their open or closed state 21 seconds later cannot be observed in 06. This reconstruction retains the photographed 05 state and also places the entire gate outside the 06 camera frame. No camera was moved.')

if __name__=='__main__':
    out=determine()
    (HERE/'garden-gate-placement.json').write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n')
    print(out['gate_scale'],out['gate_joint_world_m'],out['house06_eye_in_transferred_gate_m'],out['field06_unobstructed'])
