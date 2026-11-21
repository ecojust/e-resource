"""Extract the curved arch and the sash dividers from plate 725 of the 2020 visit."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import least_squares

PHOTO_SHA = '9a07b2ef6e075d0497c1785d7d352bf4ee3f89420324ded855db8ffc316e76d5'


def plane_mapping(pixels, points):
    system, values = [], []
    for (x, y), (u, v) in zip(pixels, points):
        system.extend([[x, y, 1, 0, 0, 0, -u*x, -u*y],
                       [0, 0, 0, x, y, 1, -v*x, -v*y]])
        values.extend([u,v])
    return np.append(np.linalg.solve(system, values), 1).reshape(3,3)


def transform(matrix, coordinates):
    pixels = np.column_stack([coordinates, np.ones(len(coordinates))])
    projected = pixels @ matrix.T
    return projected[:, :2] / projected[:, 2, None]


def measure(path):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == PHOTO_SHA
    rgb = np.asarray(Image.open(path).convert('RGB'), dtype=float)
    assert rgb.shape == (1280,960,3)
    fixture = [[317,753],[528,757],[522,1213],[302,1210]]
    height, width, threshold = 2.05, .98, .105
    frame = [[-width/2, threshold+height], [width/2, threshold+height],
             [width/2, threshold], [-width/2, threshold]]
    matrix = plane_mapping(fixture, frame)
    # The arch is on a separate, projecting plane. The correction below
    # scales apparent spans about the optical axis at an estimated eye height.
    scale = .94
    def arch_plane(points):
        metric = transform(matrix, points)
        return (metric-[0,1.50])*scale+[0,1.50]
    samples=[]
    for x in range(270,591,20):
        middle=671+(x-420)**2*.00065
        band=rgb[:,x-2:x+3].mean((1,2))
        gradient=gaussian_filter1d(band,1.8,order=1)
        lo,hi=int(middle-13),int(middle+14)
        y=lo+int(np.argmin(gradient[lo:hi]))
        assert gradient[y] < -12
        samples.append([x,y])
    measured=arch_plane(samples)
    def residual(params):
        center=params[:2]
        return np.linalg.norm(measured-center,axis=1)-params[2]
    solution=least_squares(residual,[0,.79,1.66])
    circle=solution.x
    bar_rows=[]
    for x in [345,370,388,472,495,510]:
        region=rgb[:,x-3:x+4].mean(1)
        signal=gaussian_filter1d(region[:,0]-region[:,1],1.1)+.11*(region[:,0]-region[:,2])
        bars=[[x,lo+int(np.argmax(signal[lo:hi]))] for lo,hi in [(100,150),(183,232),(280,321)]]
        bar_rows.append(bars)
    sash_corners=[[302,5],[570,14],[565,423],[290,408]]
    sash=transform(matrix,sash_corners)
    dividers=transform(matrix,np.reshape(bar_rows,(-1,2))).reshape(6,3,2)
    sample_heights=np.median(dividers[:,:,1],axis=0).tolist()
    # Use only the unoccluded half of each side at the cap and at the cut.
    features={k:transform(matrix,v).round(5).tolist() for k,v in {
        'lower_door_casing':[[295,753],[549,757],[544,1213],[282,1210]],
        'projecting_window_stool':[[306,431],[584,446]],
        'capstone_crown_apparent':[[400,545],[430,546],[460,549]],
    }.items()}
    return dict(photo_sha256=PHOTO_SHA,pixels=[960,1280],url='https://imagepphcloud.thepaper.cn/pph/image/78/162/725.jpg',
                coordinate_note='Pixel centres from top left. The assumed 0.98 by 2.05 m clear doorway sets scale. Shape observations survive a uniform change in scale.',
                assumption=dict(doorway_clear_size_m=[width,height],height_uncertainty_m=.12,threshold_m=threshold,porch_relative_scale=scale,estimated_front_offset_m=.44),
                doorway_control_pixels=fixture,doorway_model_xz_m=frame,door_plane_homography=matrix.tolist(),
                reduced_window_corners_px=sash_corners,reduced_window_corners_m=sash.round(5).tolist(),
                mullion_samples_px=bar_rows,mullion_sample_heights_m=dividers[:,:,1].round(5).tolist(),
                median_horizontal_divider_heights_m=sample_heights,
                arch_edge_pixels=samples,arch_edge_on_assumed_plane_m=measured.round(6).tolist(),
                circle_center_xz_m=circle[:2].tolist(),circle_radius_m=circle[2],circle_fit_rms_m=float(np.sqrt(np.mean(solution.fun**2))),
                separate_plane=True,additional_apparent_controls_m=features)


if __name__=='__main__':
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument('photograph',type=Path)
    args.add_argument('output',type=Path)
    inputs=args.parse_args()
    inputs.output.write_text(json.dumps(measure(inputs.photograph),ensure_ascii=False,indent=2)+'\n')
