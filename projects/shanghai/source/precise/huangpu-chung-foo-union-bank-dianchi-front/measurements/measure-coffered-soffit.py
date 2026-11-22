"""Measure the portico lights, coffer rows and moulding rhythm in Fayhoo's original photograph."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, gaussian_filter1d, map_coordinates
from scipy.optimize import least_squares
from scipy.signal import find_peaks

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "source"))
from photo_plane import CAMERAS, position

SOURCE_SHA = "c488b0074286f2a53096c7a2ef64da30773bf27f5094539a6474d54ed4ace530"
CAMERA = CAMERAS["close"]
SOFFIT_Z = 6.62
SLOPE = -.022


def on_ceiling(u, v, z):
    h = CAMERA[:, [0, 1, 3]].copy()
    h[:, 2] += z * CAMERA[:, 2]
    q = np.linalg.solve(h, [u, v, 1.])
    return (q / q[2])[:2]


def project(points):
    q = np.column_stack((points, np.ones(len(points)))) @ CAMERA.T
    return q[:, :2] / q[:, 2, None]


def cover(im, centre, rim, left, right, beam_z):
    """Fit a surface of revolution to the traced lower outline and visible equator ends."""
    u, v = centre, rim
    lower = []
    for x in np.arange(left + 2., right - 1., 2.):
        # Inside the photographed lower rim is a distinct dark stroke. Its
        # lower edge reaches about two original pixels below the dark minimum.
        ys = np.arange(v + 2, v + 26)
        profile = im[ys, int(x)]
        lower.append([float(x), float(ys[np.argmin(profile)] + 1.7)])
    measured = np.array([[left, v + 2], *lower, [right, v]])
    angle = np.linspace(0, 2 * np.pi, 200, endpoint=False)
    lat = np.linspace(0, np.pi / 2, 33)
    theta, phi = np.meshgrid(angle, lat)
    unit = np.column_stack((np.cos(theta.ravel()) * np.cos(phi.ravel()),
                            np.sin(theta.ravel()) * np.cos(phi.ravel()), -np.sin(phi.ravel())))
    dirs = np.column_stack((np.cos(np.linspace(0., np.pi, 19)), np.sin(np.linspace(0., np.pi, 19))))
    observed_support = (measured @ dirs.T).max(axis=0)
    z = beam_z - .034
    def outline(params):
        x, y, radius, depth = params
        pts = unit * [radius, radius, depth] + [x, y, z]
        return (project(pts) @ dirs.T).max(axis=0)
    def residual(params):
        x, y, radius, depth = params
        rim_pixels = project(np.array([[x - radius, y, z], [x + radius, y, z]]))
        return np.r_[outline(params) - observed_support,
                     (np.mean(rim_pixels[:, 1]) - v) * 1.5]
    x, y = on_ceiling(centre, v, z)
    fit = least_squares(residual, [x, y, .245, .135], bounds=([x-.22,y-.4,.17,.04],[x+.22,y+.4,.35,.30]))
    x, y, radius, drop = fit.x
    return dict(observed_lower_stroke_and_edge_px=measured.round(2).tolist(),
                equator_z_m=z, centre_xy_m=[x, y], radius_m=radius, drop_m=drop,
                lower_outline_support_rms_px=float(np.sqrt(np.mean((outline(fit.x)-observed_support)**2))))


def beam_row(im, guess, intervals, beam_z):
    picked = []
    for xmin,xmax in intervals:
        for u in range(xmin, xmax, 13):
            vs = np.arange(guess - 4, guess + 5) + SLOPE*(u-1100)
            # Bright lower fillet is repeated on the unoccluded portions of each row.
            values = map_coordinates(im, [vs, np.full(len(vs),u)],order=1)
            picked.append([u, float(vs[values.argmax()])])
    return dict(highlights_px=np.round(picked,2).tolist(),
                underside_y_m=float(np.median([on_ceiling(u,v,beam_z)[1] for u,v in picked])),
                dark_edge_z_m=float(beam_z))


def repeating_relief(im):
    """Average separate visible repetitions after measuring their period along the band."""
    x=np.arange(1062,1299)
    v=np.arange(1097.,1108.)
    patch=map_coordinates(im,np.array(np.broadcast_arrays(v[:,None]+SLOPE*(x-1100),x[None,:])),order=1)
    residual=patch-gaussian_filter1d(patch,8,axis=1)
    shifts=np.arange(10.,18.,.05)
    scores=[]
    for shift in shifts:
        shifted=np.array([np.interp(x[:-19]+shift,x,row) for row in residual])
        scores.append(float(np.corrcoef(residual[:,:-19].ravel(),shifted.ravel())[0,1]))
    period=float(shifts[np.argmax(scores)])
    phase=np.arange(16)/16.
    starts=1066+np.arange(15)*period
    folded=np.mean([np.array([np.interp(start+phase*period,x,row)for row in residual])for start in starts],axis=0)
    # A single street exposure does not measure depths. Preserve the observed
    # repeat and folded edge pattern; estimate the carving depth independently.
    percentile=max(abs(np.percentile(folded,4)),abs(np.percentile(folded,96)))
    normalized=np.clip(folded/percentile,-1.,1.)
    return dict(sample_span_px=[1062,1298],sample_top_bottom_px=[1097,1107],observed_repetitions=15,
                period_original_px=period,period_correlation=max(scores),phase_samples=16,
                folded_profile_top_to_bottom=normalized.round(3).tolist(),estimated_cut_depth_m=.0065)


def main():
    args=argparse.ArgumentParser();args.add_argument("original",type=Path);args.add_argument("--output",type=Path,default=HERE/"coffered-soffit.json")
    a=args.parse_args()
    if hashlib.sha256(a.original.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError("Wrong original exposure")
    im=gaussian_filter(np.asarray(Image.open(a.original).convert("L"),float),1.)
    intervals=[(762,954),(1065,1290),(1402,1588)]
    stereo=json.loads((HERE/"coffer-cross-registration.json").read_bytes())["crossings"]
    near=np.mean([r["position_m"] for r in stereo[:2]],axis=0)
    far=np.asarray(stereo[2]["position_m"])
    slope=(far[2]-near[2])/(far[1]-near[1])
    intercept=near[2]-slope*near[1]
    def on_rib(u,v):
        inv=np.linalg.inv(CAMERA[:,:3]);eye=-inv@CAMERA[:,3]
        ray=inv@np.r_[u,v,1.]
        t=(intercept+slope*eye[1]-eye[2])/(ray[2]-slope*ray[1])
        return eye+t*ray
    rows=[beam_row(im,g,intervals,z)for g,z in zip([1125,1183],[near[2],far[2]])]
    beam_positions=[]
    for seed in [449,733,1038,1325,1626,1901]:
        us=np.arange(seed-11,seed+12)
        v=1206+SLOPE*(us-1100)
        values=map_coordinates(im,[v,us],order=1)
        u=float((us*np.exp(-(values-values.min())/6.)).sum()/np.exp(-(values-values.min())/6.).sum())
        original=[u,1206+SLOPE*(u-1100)]
        beam_positions.append(dict(sample_px=original,axis_x_m=float(on_rib(*original)[0]),basis="near rear stripe"))
    # The beam's hanging edge terminates before the recessed vestibule back wall.
    # Diagonal street light shifts the darkest point within each rib. For the
    # two middle ribs use the stereo visual centre, independently identified.
    for i,c in zip([2,3],stereo[:2]):
        beam_positions[i].update(axis_x_m=c["position_m"][0],basis="two-view joist centre",
                                 stereo_original_px=c["close_original_px"])
    ends=[[1039,1227],[1323,1220]]
    motif=repeating_relief(im)
    d=motif["period_original_px"]
    sample_y=rows[0]["underside_y_m"]-.100
    v=1103+SLOPE*(1160-1100)
    motif['period_m']=float(position(1160+d,v+SLOPE*d,sample_y)[0]-position(1160,v,sample_y)[0])
    out=dict(source="Fayhoo, Zhongfudalou, CC BY-SA 3.0, original uploaded 2015-01-19",
             source_url="https://commons.wikimedia.org/wiki/File:Zhongfudalou.jpg",source_sha256=SOURCE_SHA,
             level_reference_m=SOFFIT_Z,coffer_depth_estimate_m=.21,
             beam_underside_height={"outer_dark_step_xyz":near.tolist(),"inner_dark_step_xyz":far.tolist(),
                                     "intercept_m":intercept,"slope_per_m":slope,
                                     "interpretation":"Interpolate the estimated heights of the two observed bands. The uncertainty of an individual height is about 0.08 m."},
             transverse_rows=rows,longitudinal_ribs=beam_positions,inner_beam_ends_px=ends,
             inner_beam_ends_y_m=float(np.median([on_rib(*p)[1] for p in ends])),
             shallow_covers=[cover(im,*args,near[2])for args in [(854,1133,821,886),(1188,1125,1156,1220),(1514,1117,1482,1545)]],
             moulding_repeat=motif,
             qualifications="Source records only the visible faces. Dome thickness, moulding relief, and the rear backing are estimated; no lighting function is assigned.")
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print([(v['centre_xy_m'],v['radius_m'],v['drop_m'],v['lower_outline_support_rms_px']) for v in out['shallow_covers']])
    print([v['underside_y_m'] for v in rows],[v['axis_x_m'] for v in beam_positions],out['inner_beam_ends_y_m'],motif['period_original_px'],motif['period_m'])

if __name__=="__main__":main()
