#!/usr/bin/env python3
"""Analytic camera fixture verifies metric scale, EXIF axes and depth projection."""
import hashlib
import json
from pathlib import Path

import numpy as np

from photo_metric import calibrate, homogeneous, intrinsics, project


def main():
    camera=intrinsics([5184,3456],[22.3,14.9],24,6);K=camera['oriented']
    eye=np.array([3.,2.,30.]);target=np.array([0.,14.,0.]);forward=target-eye;forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0,1,0]);right/=np.linalg.norm(right);down=np.cross(forward,right)
    rotation=np.vstack([right,down,forward]);P=K@np.column_stack([rotation,-rotation@eye])
    def pixel(world):
        p=P@np.r_[world,1];return (p[:2]/p[2]).tolist()
    horizontal=[{'label':f'h{i}','points':[pixel([-10,z,0]),pixel([10,z,0])]}for i,z in enumerate([2,10,24])]
    vertical=[{'label':f'v{i}','points':[pixel([x,0,0]),pixel([x,30,0])]}for i,x in enumerate([-10,-3,4,10])]
    controls={'raw_size':[5184,3456],'sensor_mm':[22.3,14.9],'focal_mm':24,'exif_orientation':6,
        'horizontal_lines':horizontal,'vertical_lines':vertical,
        'width_edge_lines':[{'points':[pixel([x,0,0]),pixel([x,30,0])]}for x in [-10,10]],
        'ground_reference':{'point':pixel([0,0,0])},'front_width_m':20,
        'height_points':[{'label':'top','point':pixel([1,30,0]),'plane_status':'synthetic known plane','depth_range_m':[0,0]}]}
    result=calibrate(controls)
    assert np.allclose(result['camera_position_facade_u_z_d_m'],eye,atol=1e-8)
    H=np.asarray(result['oriented_pixel_to_facade_u_z'])
    max_plane_error=0.;max_depth_pixel_error=0.
    inferred=np.asarray(result['facade_u_z_d_to_oriented_pixel_projection_3x4'])
    for x in [-9,0,9]:
        for z in [0,15,30]:
            max_plane_error=max(max_plane_error,float(np.linalg.norm(project(H,pixel([x,z,0]))-[x,z])))
            for d in [-2,.4,2]:
                p=inferred@np.array([x,z,d,1]);p=p[:2]/p[2]
                max_depth_pixel_error=max(max_depth_pixel_error,float(np.linalg.norm(p-pixel([x,z,d]))))
    assert max_plane_error<1e-8 and max_depth_pixel_error<1e-7
    corners=np.array([[0,0],[5183,0],[0,3455],[5183,3455]])
    oriented=project(camera['stored_to_oriented'],corners)
    assert np.array_equal(oriented,[[3455,0],[3455,5183],[0,0],[0,5183]])
    assert np.array_equal(project(camera['oriented_to_stored'],oriented),corners)
    landscape=intrinsics([5184,3456],[22.3,14.9],22,1)
    assert landscape['oriented_size']==[5184,3456]
    assert np.array_equal(landscape['raw'],landscape['oriented'])
    assert np.array_equal(project(landscape['stored_to_oriented'],corners),corners)
    assert np.array_equal(project(landscape['oriented_to_stored'],corners),corners)
    assert np.allclose(project(result['stored_pixel_to_facade_u_z'],
                              project(camera['oriented_to_stored'],[pixel([0,0,0]),pixel([1,30,0])])),[[0,0],[1,30]],atol=1e-8)
    report={'passed':True,'known_camera_facade_u_z_d_m':eye.tolist(),'recovered_camera_m':result['camera_position_facade_u_z_d_m'],
        'plane_coordinate_max_error_m':max_plane_error,'nonzero_depth_projection_max_error_px':max_depth_pixel_error,
        'exif6_all_four_stored_corners_and_roundtrip':'passed',
        'exif1_identity_intrinsics_and_all_four_corners':'passed','source_photo_or_model_mutations':False,
        'tool_sha256':hashlib.sha256(Path(__file__).with_name('photo_metric.py').read_bytes()).hexdigest()}
    path=Path(__file__).with_name('photo-metric-validation.json');path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
