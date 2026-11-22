"""Fit two 2016 detail cameras to the masonry and solve the five sash swings.

Both archived photographs are independent of the 2015 street photograph used
to determine the masonry coordinates. The 2016 images are not redistributed.
"""
import json
import sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar

M=Path(__file__).resolve().parent
sys.path.insert(0,str(M.parent/"source"))
from upper_bookshop_windows import openings

def fit_camera(homography,controls,rows,photo):
    # The SIFT wall registration supplies the plane exactly. Derive the depth
    # direction from its horizontal/vertical columns and the recorded focal length.
    w,h=photo["dimensions"]
    K=np.array([[w*controls["focal_mm"]/controls["sensor_mm"][0],0,(w-1)/2],
                [0,h*controls["focal_mm"]/controls["sensor_mm"][1],(h-1)/2],[0.,0.,1.]])
    H=np.asarray(homography["matrix"])
    witness=next(iter(controls.get("controls",{})),"B1-R1-W1")
    r=rows[witness];H*=np.sign(H[2]@[r["left"],r["bottom"],1])
    A=np.linalg.solve(K,H); x,z=A[:,0],A[:,1]
    depth=np.cross(z,x);depth*=.5*(np.linalg.norm(x)+np.linalg.norm(z))/np.linalg.norm(depth)
    matrix=np.column_stack((H[:,0],K@depth,H[:,1],H[:,2]))
    def project(points):
        q=np.asarray(points)@matrix[:,:3].T+matrix[:,3]
        return q[...,:2]/q[...,2,None]
    reprojection=[]
    for name,quad in controls.get("controls",{}).items():
        g=rows[name];xl,xr,b,t=g["left"],g["right"],g["bottom"],g["top"]
        match=list(zip([[xl,0,t],[xr,0,t],[xr,0,b],[xl,0,b]],quad))
        reprojection.extend(float(np.linalg.norm(project(xyz)-uv)) for xyz,uv in match if uv is not None)
    info={"intrinsics":K.tolist(),"camera_matrix":matrix.tolist(),
          "eye_m":np.round(-np.linalg.solve(matrix[:,:3],matrix[:,3]),3).tolist(),
          "registered_inliers":homography["matched_points"],
          "median_registration_error_px":round(homography["median_detail_residual_px"],3),
          "median_masonry_control_error_px":round(float(np.median(reprojection)),2) if reprojection else None}
    return project,info

def solve():
    obs=json.loads((M/"bookshop-window-details.json").read_bytes())
    rows={r["label"]:r for r in openings()}
    models={}; cam_reports={}
    homographies=json.loads((M/"bookshop-detail-homographies.json").read_bytes())
    calibrations={**obs["calibration_controls"],"5":{"sensor_mm":[35.9,23.9],"focal_mm":72}}
    for key,control in calibrations.items():
        models[key],cam_reports[key]=fit_camera(homographies[key]["commons-a"],control,rows,obs["detail_images"][key])
    profiles=[]
    for v in obs["section_readings"]:
        row=rows[v["label"]]
        fraction=(v["frame_foot_v"]-v["transom_centre_v"])/(v["frame_foot_v"]-v["frame_head_v"])
        rec={"window":v["label"],"view":v["image"],"lower_height_fraction":round(fraction,4)}
        if v["image"] in models:
            project=models[v["image"]]
            x=(row["left"]+row["right"])/2
            z=row["top"]
            wall=project([x,0,z])
            observed=v["frame_head_v"]-v["masonry_head_v"]
            def depth_at(clearance):
                return minimize_scalar(lambda d:(project([x,d,z-clearance])[1]-wall[1]-observed)**2,
                                       bounds=(0,.85),method='bounded').x
            rec.update(head_return_observed_px=observed,depth_at_15mm_head_clearance=round(float(depth_at(.015)),4),
                       depth_spread_at_0_to_40mm=[round(float(depth_at(c)),4) for c in [.040,0.]])
        profiles.append(rec)
    frame=float(np.median([r["depth_at_15mm_head_clearance"] for r in profiles if "depth_at_15mm_head_clearance" in r]))
    ratio=float(np.median([r["lower_height_fraction"] for r in profiles]))
    local_depths={}
    for v in profiles:
        group=v["window"].rsplit("-",1)[0]
        local_depths.setdefault(group,[]).append(v["depth_at_15mm_head_clearance"])
    local_depths={k:round(float(np.median(vals)),4) for k,vals in local_depths.items()}
    poses=[];angles={}
    for v in obs["open_leaves"]:
        r=rows[v["label"]]; project=models[v["image"]]
        w=r["right"]-r["left"]; mount=min(.042,.05*w)
        span=(w-2*mount)/2-.004
        side=1. if v["leaf"]=="left" else -1.
        hinge=(r["left"]+mount+.002 if side>0 else r["right"]-mount-.002)
        zs={"bottom":r["bottom"]+mount+.002,"top":r["bottom"]+mount+ratio*(r["top"]-r["bottom"]-2*mount)-.0325}
        levels=[s for s in zs if "hinge_"+s in v]
        def difference(angle):
            rad=np.radians(angle);diff=[]
            for s in levels:
                depth=local_depths.get(v["label"].rsplit("-",1)[0],frame)
                base=np.array([hinge,depth+.010,zs[s]])
                end=base+np.array([side*span*np.cos(rad),-span*np.sin(rad),0.])
                delta=project(end)-project(base)
                observed=np.subtract(v["free_"+s],v["hinge_"+s])
                diff.extend(delta-observed)
            return np.asarray(diff)
        fit=minimize_scalar(lambda ang:np.sum(difference(ang)**2),bounds=(-89.8,89.8),method='bounded')
        angle=round(float(fit.x),1)
        angles[v["label"]+"/"+v["leaf"]]=angle
        # Points chosen on partly cut-off leaves have larger endpoint uncertainty.
        tol=6 if len(levels)==1 else 4
        grid=np.arange(-89.8,89.9,.2)
        interval=[float(a) for a in grid if np.linalg.norm(difference(a))<=np.linalg.norm(difference(angle))+tol]
        poses.append({"window":v["label"],"leaf":v["leaf"],"view":v["image"],"angle_deg":angle,
                      "approximate_pixel_tolerance_deg":[round(min(interval),1),round(max(interval),1)],
                      "end_to_hinge_vector_residual_px":np.round(difference(angle).reshape(-1,2),2).tolist(),
                      "closed_reference_error_px":round(float(np.linalg.norm(difference(0))),2)})
    result={"units":"metres, degrees and original undistorted-as-delivered image pixels",
            "camera_approximation":"Principal point at image centre, Nikon D610 sensor dimensions and the recorded lens focal length; uncalibrated lens distortion is included in image residuals.",
            "sections":{"front_frame_y_m":round(frame,4),"local_frame_y_m":local_depths,"lower_height_fraction":round(ratio,4)},
            "angle_convention":"Positive angles swing out towards the street. Angle bounds reflect endpoint ranges, not survey accuracy.",
            "cameras":cam_reports,"sash_profiles":profiles,"swing_degrees":angles,"open_leaves_fit":poses,
            "caveat":"Absolute jamb depth also depends on the unobserved clearance behind the brick lintel. A 0–40 mm clearance is shown for each reading."}
    (M/"bookshop-sash-fit.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result["sections"],angles,{k:v["median_registration_error_px"] for k,v in cam_reports.items()})

if __name__=='__main__':
    solve()
