"""Recover proportions of the entrance plane from plate 17 of the 1936 school book."""
from pathlib import Path
import json
import numpy as np

HERE=Path(__file__).absolute().parent
CROP=[929,610]
FACE=[[122.,193.0],[257.8,176.5],[269.5,359.5],[126.2,367.7]]
unit=np.array([[-.5,1],[.5,1],[.5,0],[-.5,0]])
def homography(points,dest):
    rows=[]
    for (u,v),(x,z) in zip(points,dest):
        rows.extend([[u,v,1,0,0,0,-x*u,-x*v,-x],[0,0,0,u,v,1,-z*u,-z*v,-z]])
    return np.linalg.svd(rows)[2][-1].reshape(3,3)
H=homography(FACE,unit)
def straight(uv):
    q=H@[*uv,1]
    return q[:2]/q[2]
# The light portal spring shoulders, visible below the circular head, allow
# perpendicular scales to be fitted without measuring the historical site.
spring=[[154.8,248.3],[220.4,245.9]];crown=[187.4,212.45]
l,r=map(straight,spring);t=straight(crown);width=2.64
sx=width/(r[0]-l[0]);sz=(width/2)/(t[1]-(l[1]+r[1])/2)
def metric(uv):
    u,v=straight(uv)
    return [round(float((u-(l[0]+r[0])/2)*sx),5),round(float(v*sz),5)]
left,right=[metric(v)[0]for v in FACE[:2]]
sill=metric([190,382])[1];center_z=sum(metric(p)[1]for p in spring)/2
# Deep shadow under the upper eave does not resolve individual glazing bars.
d=dict(clear_width=width,spring=center_z,arch_centre_x=0.,ground=sill,plinth=0.,wall_left=left,wall_right=right,
    wall_top=sz,
    reconstruction_depth_note='垂直券面有照片约束。屋面进深、侧面的半开间和遮阴下的构件剖面为示意值。')
controls=dict(pdf_page=17,pdf_sha256='bd383a970b14de6b223e113598bd749e09360dc98b25070d8eca4a96ece4efdf',
    raster_sha256='b3e0e73f6c661275826633083c73ee552cd3551d3d070db56b2ae00eefc1dbc8',
    raster_size=[2440,1723],detail_origin_px=CROP,facade_plane_controls_local_px=FACE,arch_spring_points=spring,crown=crown,
    adopted_arch_width_m=width,circular_head_assumption=True,metres_per_unit=[sx,sz],
    rectification_matrix=(H/H[2,2]).tolist(),absolute_scale='相对测量以券口净宽2.64米为参考假设；没有实测标尺。')
if __name__=='__main__':
    for f,value in [(HERE/'arch-plane-controls.json',controls),(HERE.parent/'source/dimensions.json',d)]:
        f.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(d)
