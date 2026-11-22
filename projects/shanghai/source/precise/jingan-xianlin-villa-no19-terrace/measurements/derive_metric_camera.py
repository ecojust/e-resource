"""Calibrate the X/Y/Z axes, common datum and image scale of the courtyard at No. 19."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter1d
from scipy.signal import find_peaks

def solve(photo, axes, terrace=None):
    image=np.asarray(Image.open(photo).convert('L'),float)
    points=dict(axes['vanishing'])
    if terrace is not None:
        points['Y']=terrace['Y_vp']
    vx,vy=points['X']
    cx,cy=axes['orthogonal_principal_point']
    focal=axes['focal_px']
    if terrace is not None:
        cx,cy=terrace['principal']
        focal=terrace['focal_px']
    K=np.array([[focal,0,cx],[0,focal,cy],[0,0,1.]])
    ki=np.linalg.inv(K)
    def unit(v):
        a=ki@np.r_[v,1.]
        return a/np.linalg.norm(a)
    # Increasing X approaches the camera along the long elevation. Increasing Y recedes.
    ex=-unit(points['X']); ey=unit(points['Y']); ez=unit(points['Z'])
    R=np.stack((ex,ey,ez),axis=1)
    assert abs(abs(np.linalg.det(R))-1)<1.e-7
    # Make the original photographed upper-storey corner and the image zenith collinear.
    u1,v1=924.4,199.4
    ux,vz=points['Z']
    foot_v=1340.
    foot_u=u1+(foot_v-v1)*(u1-ux)/(v1-vz)
    t0=ki@[foot_u,foot_v,1.]
    P0=K@np.column_stack((R,t0))
    def at_side(u,v):
        x,z,w=np.linalg.solve(P0[:,[0,2,3]],[u,v,1])
        return np.array([x/w,z/w])
    tracks=[]
    zsteps=[]
    for u in (907,911):
        v=np.arange(206,405,.125)
        traces=[]
        for x in range(-5,6):
            row=(v-vy)*(u+x-vx)/(u-vx)+vy
            traces.append(map_coordinates(image,(row,np.repeat(u+x,len(v))),order=1))
        tone=np.median(traces,axis=0)
        response=gaussian_filter1d(tone,4)-gaussian_filter1d(tone,30)
        indices=find_peaks(-response,distance=39,prominence=4)[0]
        centres=v[indices]
        assert len(centres)==31
        zs=np.array([at_side(u,y)[1] for y in centres])
        steps=-np.polyfit(np.arange(len(zs)),zs,1)[0]
        zsteps.append(steps)
        tracks.append(dict(u=u,bed_joint_centres_v=centres.tolist(),count=len(centres)-1,
                           depth_one_height_per_course=steps))
    k=.064/np.mean(zsteps)
    if terrace is not None:
        joint_spans=[at_side(q['u'],round(q['bed_joint_centres_v'][0],2))[1]-at_side(q['u'],round(q['bed_joint_centres_v'][-1],2))[1] for q in tracks]
        k=1.920/np.mean(joint_spans)
    t=k*t0
    P=K@np.column_stack((R,t))
    C=-np.linalg.solve(R,t)
    if terrace is not None:
        assert np.max(np.abs(P-np.array(terrace['P'])))<1.e-6
    return dict(terrace_refinement=('terrace-axis-check.json' if terrace else None),image="Xianlin Bieshu.JPG",source="https://commons.wikimedia.org/wiki/File:Xianlin_Bieshu.JPG",
        image_sha256=hashlib.sha256(Path(photo).read_bytes()).hexdigest(),author="Fayhoo",license="CC BY-SA 3.0",image_size=[2144,1424],
        coordinate_definition={"X":"Along the long photographed wall, positive toward the near masonry corner.","Y":"Into the house from its long wall. Short front wall at X=0.","Z":"Above estimated garden grade."},
        intrinsic_matrix=K.tolist(),orthogonal_vanishing_points=points,num_segments={a:(len(terrace['training_indices']) if a=='Y' and terrace else len(b)) for a,b in axes['used_segments'].items()},
        datum=dict(upper_corner_pixels=[[924.4,199.4],[921.1,314.4]],ground_pixel=[foot_u,foot_v],ground_v_interval=[1315,1365],
                   note="Garden additions conceal the foot of the masonry corner. Grade is an estimate projected down the measured plumb edge."),
        scale=dict(tracks=tracks,assumed_course_m=.064,plausible_course_m=[.058,.070],number_of_courses=30,
                   method="Median across eleven native-pixel columns transported along the long-wall vanishing direction. Thirty joint spacings in two overlapping strips. Physical brick plus mortar height is an assumption, not an on-site survey."),
        vanishing_source=("44 long-wall and 51 vertical segments. The terrace receding direction uses 15 labelled short-wall edges and four independent holdout edges." if terrace else "44 long-wall, four short-wall and 51 vertical segments."),
        P=P.tolist(),world_to_camera=R.tolist(),camera_origin_xyz_m=C.tolist(),
        fit_note="The camera model describes the photographed masonry faces. Objects outside those faces require an independently specified depth.")
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('photo');p.add_argument('axes');p.add_argument('output');p.add_argument('--terrace',type=Path)
    a=p.parse_args();j=solve(a.photo,json.loads(Path(a.axes).read_text()),json.loads(a.terrace.read_text()) if a.terrace else None);Path(a.output).write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n');print(j['datum'],j['camera_origin_xyz_m'])
