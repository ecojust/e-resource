"""Rectify the photographed lawn-facing gable and record its adopted local scale."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).absolute().parent
CENTER = np.array([512.,384.])
FOCAL = 1024 * 7.40625 / 7.18
FRONT = np.array([489.,414.])
ROW_LINES = [
    [(415,355),(439,357),(478,360),(500,361),(530,364),(555,366)],
    [(415,364),(439,366),(478,369),(500,370),(530,372),(555,374)],
    [(414,410),(478,413),(553,416)],
]
# A + B*u + C*v plane through the principal point permits full perspective
# rectification. The lower line is on the parallel outward balcony face.
lines = []
for points in ROW_LINES:
    xy=np.array(points)
    slope,intercept=np.polyfit(xy[:,0],xy[:,1],1)
    lines.append((slope,intercept))
row_x,row_y=least_squares(lambda p:[p[1]-s*p[0]-i for s,i in lines],[1700.,455.]).x
def unit(v):
    return v/np.linalg.norm(v)
horizontal=unit(np.array([row_x-CENTER[0], row_y-CENTER[1], FOCAL]))
vertical=unit(np.array([0.,-1.,horizontal[1]/horizontal[2]]))
normal=unit(np.cross(horizontal,vertical))
def project_to_plane(uv):
    ray=np.array([*(np.array(uv)-CENTER),FOCAL])
    return ray/np.dot(normal,ray)
base=project_to_plane(FRONT)
def unscaled(uv):
    delta=project_to_plane(uv)-base
    return np.array([np.dot(horizontal,delta),np.dot(vertical,delta)])
# The single adopted width controls absolute scale. The building has no
# measured elevation drawing in the two records cited in this study.
width_points=[[464.2,332.],[484.,333.6]]
factor=1.32/abs(unscaled(width_points[1])[0]-unscaled(width_points[0])[0])
direction=np.sign(unscaled(width_points[1])[0]-unscaled(width_points[0])[0])
def metric(uv):
    return np.round(direction*factor*unscaled(uv),5).tolist()
def shape(points):
    return [metric(p) for p in points]
def window(b):
    a,c=metric(b[0]),metric(b[1])
    return [min(a[0],c[0]),min(a[1],c[1]),max(a[0],c[0]),max(a[1],c[1])]
upper=[[[464.,320.0],[484.,346.0]],[[490.0,322.5],[508.1,347.6]]]
lower=[[[403.1,363.0],[422.6,406.1]],[[429.2,365.0],[448.6,407.0]],[[463.8,368.2],[483.7,409.1]],[[490.,370.3],[508.3,410.3]],[[525.2,373.1],[541.3,412.1]],[[548.,374.8],[565.4,413.1]]]
# Two end points are taken at the weathered outer rake. The globe is distinct.
rake=[[386.5,349.0],[489.7,277.6],[584.7,366.0]]
# Closed light plaster bands surround two tall infill panels, two triangular
# spandrels and the five-sided field above the attic windows.
fields=[
 [[395.0,348.9],[410.7,336.2],[410.7,349.9]],
 [[434.9,331.1],[449.4,319.4],[449.4,351.9],[434.9,350.7]],
 [[464.6,305.2],[489.5,289.4],[508.7,307.5],[508.7,319.0],[464.6,315.6]],
 [[524.8,324.0],[537.9,338.6],[537.9,360.2],[524.8,359.1]],
 [[552.7,348.9],[563.7,359.5],[552.7,358.8]],
]
data=dict(photo_sha256='2e40d37f5ded9e69d17668ac24d31d4641891e35e42aa25f2b46b8acfc3d4b17',
  raw_size=[1024,768],focal_mm=7.40625,assumed_sensor_width_mm=7.18,focal_px=FOCAL,
  horizontal_control_lines_px=ROW_LINES,horizontal_vanishing_px=[row_x,row_y],
  assumed_horizontal_sash_width_m=1.32,scale_points_px=width_points,
  vertical_axis='vertical image direction with orthogonality to horizontal world direction',origin_px=FRONT.tolist(),
  raw_lower_openings=lower,raw_attic_openings=upper,raw_rake=rake,raw_plaster_fields=fields,
  scale_note='绝对尺度以一扇阁楼窗可见宽1.32米为假设。下窗被栏板遮住的窗脚、后退深度与阳台出挑均为估计。')
d=dict(rake=shape(rake),attic=[window(b) for b in upper],lower=[window(b) for b in lower],
       fields=[shape(ps)for ps in fields],base_band_z=metric([489,359.6])[1],
       cornice_bottom_z=metric([489,367.3])[1],rail_top_z=metric([489,396.6])[1],
       deck_top_z=metric([489,410.4])[1],bottom=-.18,section_depth=1.05,balcony_projection=1.13)
unit_bounds=[[[388.4,381.8],[403.6,393.1],[398.1,387.8]],[[510.1,382.2],[525.2,394.8],[521.4,389.4]],[[566.1,386.2],[581.8,398.4],[578.4,393.5]]]
d['visible_grille_cases']=[dict(front_xz=window([a,b]),centre_xz=metric(center))for a,b,center in unit_bounds]
data['grille_case_controls_px']=unit_bounds
camera=[float(-direction*factor*np.dot(horizontal,base)),-float(factor),float(-direction*factor*np.dot(vertical,base))]
focus2=metric([489.,345.])
focus=[focus2[0],0.,focus2[1]]
data['cropped_camera']={'eye_enu_m':camera,'focus_enu_m':focus,'cropped_width_px':248,
                        'perspective_width_m':248*np.linalg.norm(np.array(camera)-focus)/FOCAL}
if __name__=='__main__':
    for p,value in [(HERE/'photograph-plane-controls.json',data),(HERE.parent/'source/dimensions.json',d)]:
        p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:d[k]for k in ('rake','attic','lower','rail_top_z','deck_top_z','base_band_z')},indent=1))
