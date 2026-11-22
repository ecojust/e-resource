"""Recover central-window frame setbacks and casement poses from the observed edge displacements."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent


def fit(measurements=HERE):
    survey=json.loads((measurements/"jkk-street-camera-fit.json").read_text())
    data=json.loads((measurements/"central-steel-source-pixels.json").read_text())["frames"]
    sections=survey["derived_sections"]
    bounds=sections["central_openings"]
    face=sections["shaft_plane_y_m"]
    cams={k:np.array(m) for k,m in survey["camera_matrices"].items()}
    def project(cam,p):
        q=cams[cam]@np.r_[p,1.]
        return q[:2]/q[2]
    def native_f(cam):
        m=data[cam]
        return m["size"][0]/(2*math.tan(math.radians(m["hfov"])/2))
    def displacement(cam,world,measured):
        model=project(cam,world[1])-project(cam,world[0])
        target=np.subtract(measured[1],measured[0])
        return (model-target)*600/native_f(cam)
    def plane_z(cam,p,y):
        m=cams[cam]
        h=m[:,[0,2,3]].copy()
        h[:,2]+=y*m[:,1]
        v=np.linalg.solve(h,[*p,1.])
        return v[1]/v[2]
    rebates=json.loads((measurements/"central-steel-frame-corners.json").read_text())["corners"]
    def setback_errors(v):
        errors=[]
        for item in rebates:
            cam,lvl,side=item["frame"],item["opening"],item["side"]
            l,r,b,t=bounds[lvl]
            x=l if side=="west" else r
            dx=.043 if side=="west" else -.043
            errors.extend(displacement(cam,([x,face,t],[x+dx,face+v[0],t-.048]),
                                       [item["plaster_corner"],item["steel_corner"]]))
        return errors
    depth=float(least_squares(setback_errors,[.085],bounds=([.015],[.22]),loss="soft_l1",f_scale=.7).x[0])
    y=face+depth
    fractions={}
    for k,lvl,observations in [
            ("centre-lower-20","low",[(f"{side}_leaf","hinge_top") for side in ["left","right"]]),
            ("centre-middle-20","middle",[("middle_crossbar","W"),("middle_crossbar","E")])]:
        l,r,b,t=bounds[lvl]
        heights=[plane_z(k,data[k]["marks"][group][point],y) for group,point in observations]
        fractions[lvl]=float(np.clip((t-.048-np.mean(heights))/(t-b-.096),.22,.46))

    groups=[("low","left",["centre-lower-20","e20-low"]),("low","right",["centre-lower-20","w20-low"]),
            ("middle","right",["w20-mid"]),("upper_main","left",["e20-high"])]
    def hinge_errors(v,by_group=False):
        inset,axis_depth,extra_width=v[:3]
        residuals={}
        for i,(lvl,side,views) in enumerate(groups):
            l,r,b,t=bounds[lvl]
            sign=1 if side=="left" else -1
            hinge_x=l+inset if sign==1 else r-inset
            width=(r-l-.086)/3-.018+extra_width
            theta=np.radians(v[i+3])
            top=t-.048-fractions.get(lvl,0.)*(t-b-.096)-.016
            to_free=width*np.array([sign*np.cos(theta),-np.sin(theta),0.])
            errors=[]
            for cam in views:
                marks=data[cam]["marks"][side+"_leaf"]
                for label,z in [("top",top),("bottom",b+.048)]:
                    pivot=np.array([hinge_x,face+axis_depth,z])
                    for end,xyz in [("hinge",pivot),("free",pivot+to_free)]:
                        key=end+"_"+label
                        if key in marks:
                            errors.extend((project(cam,xyz)-marks[key])*600/native_f(cam))
            residuals[lvl+"_"+side]=errors
        if by_group:return residuals
        return [v for group in residuals.values() for v in group]+[
            .7*(inset-.048)/.05,.7*(axis_depth-.066)/.065,.65*extra_width/.035]
    # Six views locate the open steel stile on the outside of the recessed glazing.
    # Its rotation axis can lie at the plaster face or further inside the reveal.
    hinge=least_squares(hinge_errors,[.052,.065,0.,116.,123.,90.,78.],
                        bounds=([.003,0.,-.03,25.,25.,25.,25.],[.11,.14,.077,145.,145.,145.,145.]),
                        loss="soft_l1",f_scale=1.05)
    inset,axis_depth,extra_width=map(float,hinge.x[:3])
    angles={}
    fits={}
    for i,(lvl,side,views) in enumerate(groups):
        angle=float(hinge.x[3+i]);angles[lvl,side]=angle
        errors=hinge_errors(hinge.x,True)[lvl+"_"+side]
        fits[lvl+"_"+side]={"views":views,"angle_deg":round(angle,2),
            "equivalent_600px_focal_rms_px":round(float(np.sqrt(np.mean(np.square(errors)))),2)}
    l,r,b,t=bounds["middle"]
    h=t-.048
    leaf_height=fractions["middle"]*(t-b-.096)-.016
    cam="centre-middle-20"
    def tilt_residual(tilt):
        a=math.radians(tilt[0])
        residual=[]
        for side,x in [("left",l+.043+(r-l-.086)/3+.009),("right",r-.043-(r-l-.086)/3-.009)]:
            pivot=np.array([x,y-.005,h])
            end=pivot-np.array([0.,np.sin(a),np.cos(a)])*leaf_height
            pts=data[cam]["marks"]["middle_centre_transom"]
            residual.extend(displacement(cam,[pivot,end],[pts["hinge_"+side],pts["free_"+side]]))
        return residual
    tilt=least_squares(tilt_residual,[42.],bounds=([0.],[85.]),loss="soft_l1",f_scale=.7)
    openings=[]
    for lvl,(l,r,b,t) in bounds.items():
        o={"id":lvl.replace("_","-"),"rect_xz_m":[l,b,r,t],"face_y_m":face,"sash_y_m":y}
        if lvl!="upper_transom":
            o.update(hinge_inset_m=inset,hinge_y_m=face+axis_depth,open_leaf_width_increment_m=extra_width)
            o["lower_leaf_angles_deg"]=[angles.get((lvl,"left"),0.),0.,angles.get((lvl,"right"),0.)]
        if lvl in fractions:o["transom_fraction_from_top"]=fractions[lvl]
        if lvl=="middle":o["center_top_tilt_deg"]=float(tilt.x[0])
        openings.append(o)
    return {"reference":"Photographed February 2020 state, checked against April and December 2015 observations from other angles.",
            "scope":"Four apertures in the recessed street-facing central strip. The narrow transom above the upper casements is separated by solid plaster.",
            "setback_m":depth,"setback_equivalent_600px_focal_rms_px":round(float(np.sqrt(np.mean(np.square(setback_errors([depth]))))),2),
            "frame_pose_fits":fits,"middle_toplight_tilt_deg":round(float(tilt.x[0]),2),"openings":openings}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=HERE/"central-steel-reconstruction.json")
    args=parser.parse_args()
    args.output.write_text(json.dumps(fit(),ensure_ascii=False,indent=2)+"\n")
