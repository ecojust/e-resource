"""Measure the alternating dressed corner stones and visible rainwater head on photograph 93."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.optimize import least_squares
from fit_garden_corner import fixed_plane, project

HERE = Path(__file__).resolve().parent
PHOTO = "3839cbc07009853fb9d993fab33609d72c06e94c7ec662771a7826a1f3b3870c"
SEAMS = [129,148,165,185,205,225,244,264,283,304,322,344,362,383,403,424,443,465,483,504,523,545,564,585,605,625,645,665,687]
FRONT_RELIEF = .037


def read(photo):
    if hashlib.sha256(photo.read_bytes()).hexdigest() != PHOTO:
        raise ValueError("This measurement requires the original published 690 by 821 photograph.")
    pixels = np.asarray(Image.open(photo).convert("RGB"),float)
    cal = json.loads((HERE/"garden-corner-camera.json").read_text())
    P = np.asarray(cal["main_corner_projection"])
    x,y = cal["arranged_on_bay_datum_m"]
    def front_uv(uv):
        return fixed_plane(P, uv, 1, y-FRONT_RELIEF)
    def extent(v, target, face):
        a = np.median(pixels[v-2:v+3],axis=0)
        # Brick is redder than both the shaded front course and the sunlit return course.
        score = .45*a[:,2] + .55*a[:,1] - .72*a[:,0]
        pts = np.arange(target-2,target+3)
        direction = -1 if face == "front" else 1
        diffs = direction*(score[pts+2]-score[pts-2])
        i = int(np.argmax(diffs))
        return int(pts[i]), round(float(diffs[i]),2)
    cuts = [round(float(front_uv((269,v))[2]),4) for v in SEAMS]
    stones=[]
    for i,(top,bottom) in enumerate(zip(SEAMS,SEAMS[1:])):
        sample_v=round((top+bottom)/2)
        long_front = bool(i%2)
        east, east_strength=extent(sample_v,276 if long_front else 267,"front")
        # A horizontal course projects to different image rows on the two faces.
        # Put the left-face edge detector at the middle of this same masonry course.
        west_hint = 236 if long_front else 232
        provisional = fixed_plane(P,(west_hint,sample_v),0,x-FRONT_RELIEF)
        provisional[2] = (cuts[i]+cuts[i+1])/2
        side_v = round(float(project(P,provisional)[1]))
        west, west_strength=extent(side_v,west_hint,"return")
        front_len=float(front_uv((east,sample_v))[0]-x)
        return_len=float(fixed_plane(P,(west,side_v),0,x-FRONT_RELIEF)[1]-y)
        visible_return = bottom <= 645
        stones.append({
            "course_from_top":i+1,"top_bottom_z_m":[cuts[i],cuts[i+1]],
            "front_pattern":"long" if long_front else "short",
            "front_edge_px":[east,sample_v],"front_edge_score":east_strength,"front_length_m":round(front_len,4),
            "return_edge_px":[west,side_v] if visible_return else None,
            "return_edge_score":west_strength if visible_return else None,
            "return_length_m":round(return_len,4) if visible_return else None
        })
    # Use the two different calibrated plane derivatives to turn the actual dark
    # shaft silhouette width into diameter. A cylinder's silhouette is wider
    # than the projection of a segment lying along the x axis.
    shaft_y = 1.42
    pairs=[(188,291,298),(280,293,302),(370,294,302),(414,294,303),(573,294,303),(666,294,304)]
    widths=[]
    for v,a,b in pairs:
        c=fixed_plane(P,[(a+b)/2,v],1,shaft_y)
        deriv=np.array([(project(P,c+np.eye(3)[j]*.005)[0]-project(P,c-np.eye(3)[j]*.005)[0])/.01 for j in range(2)])
        widths.append(round(float((b-a)/np.linalg.norm(deriv)),4))
    centerline=[(315,96,1.181),(314,105,1.181),(312,111,1.21),(306,119,1.26),(301,126,1.32),
                (298,131,1.37),(297,136,1.405)]
    shaft=[(294.5,155),(294.5,190),(297.5,280),(298.5,375),(298.5,574),(299,697)]
    top_corners=np.array([[294,129],[313,137],[303,147],[284,139]],float)
    signs=np.array([[-1,-1],[1,-1],[1,1],[-1,1]])
    def corners(params):
        cx,cz,w,d=params
        return np.array([[cx+sx*w/2,shaft_y+sy*d/2,cz] for sx,sy in signs])
    fit=least_squares(lambda v:(np.array([project(P,pt)for pt in corners(v)])-top_corners).flatten(),
                      [-2.15,9.18,.37,.22],bounds=([-2.4,8.95,.15,.09],[-1.9,9.4,.55,.27]))
    return {
      "subject":"美丽园14号园侧主墙交错隅石与落水管",
      "source":{"author":"高参88","article":"https://blog.sina.cn/dpool/blog/s/blog_5d1bdf480102uyin.html",
          "photo":"https://s1.sinaimg.cn/mw690/001HIrzOzy7eMoPOZck90&690","sha256":PHOTO,"frame":[690,821],
          "date":"文章初刊2014-08-12，单幅实际拍摄日未注明","rights":"仅发布量测数值与原创几何。"},
      "photographic_camera_sha256":hashlib.sha256((HERE/"garden-corner-camera.json").read_bytes()).hexdigest(),
      "corner_xy_m":[x,y],"stone_relief_m":FRONT_RELIEF,"joint_probe_column_px":269,
      "joint_boundaries_v_px":SEAMS,"courses":stones,"shaded_unjointed_head_z_m":[cuts[0],cal["soffit_height_m"]-.018],
      "pipe":{"shaft_plane_y_m":shaft_y,"observed_widths_v_left_right_px":pairs,"diameter_estimates_m":widths,
        "shaft_radius_m":round(float(np.median(widths))/2,4),
        "shaft_px":shaft,"shaft_xyz_m":[fixed_plane(P,p,1,shaft_y).round(5).tolist() for p in shaft],
        "bent_neck_px_y_m":centerline,"bent_neck_xyz_m":[fixed_plane(P,[u,v],1,depth).round(5).tolist() for u,v,depth in centerline],
        "hopper_upper_corners_px":top_corners.tolist(),"hopper_upper_ring_xyz_m":corners(fit.x).round(5).tolist(),
        "hopper_mean_corner_error_px":round(float(np.mean(np.linalg.norm(fit.fun.reshape(-1,2),axis=1))),2),
        "shaft_visible_joint_at_px":[299,614],"visible_joint_z_m":round(float(fixed_plane(P,[299,614],1,shaft_y)[2]),4)},
      "scope":["石高依既有凸窗估尺与主墙共用相机求得。外挑厚度、排水管离墙距离均为估计。",
        "阴影内顶端只有连续的浅灰墙角可辨，未分开砌缝。最下面两个可辨前面块的左缘被花叶遮住。",
        "管身于花丛上缘结束。相邻浅色檐口方块与暗色排水头分列。无照片可辨的落地弯头或出口未纳入。",
        "门外第二视图可见同类石角，视角不足以认定同一隅石各缝。"]}
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("photograph",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    a.output.write_text(json.dumps(read(a.photograph),ensure_ascii=False,indent=2)+"\n")
