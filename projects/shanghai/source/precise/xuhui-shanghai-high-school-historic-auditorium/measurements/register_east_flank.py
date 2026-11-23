"""Map the measurable 1934 window edges to the east plane selected by the common registration."""
from pathlib import Path
from statistics import median
import hashlib,json
import numpy as np
from register_court import Camera
HERE=Path(__file__).absolute().parent
read=lambda name:json.loads((HERE/name).read_bytes())
def solve():
    c=Camera(1934)
    photo=read('1934-east-flank-observed.json');env=read('hall-envelope.json')
    x=env['historic_east_wall_plane_x'];end=env['rear_limit_of_candidate_1155_y']
    def wall(pixel):return c.wall_x(pixel,x)
    def rectangle(a):
        y0,top=wall(a['frame'][0])[1:]
        y1,bottom=wall(a['frame'][1])[1:]
        return [float(y0),float(bottom),float(y1),float(top)]
    axes=[0.]
    for row in photo['pier_axis_top_foot'][1:]:
        a=c.wall_x(row['top'],x+.155);b=c.wall_x(row['foot'],x+.155)
        axes.append(float((a[1]+b[1])*.5))
    # The camera can recover the top where its silhouette is continuous. The front
    # ends of the first two bays step down only slightly relative to their cap lip.
    tops=[median(wall(p)[2] for p in cap) for cap in photo['step_caps']]
    low=median(wall(p)[2] for p in photo['cornices']['hall_projecting_lip'])
    zbase=median(wall(p)[2] for p in photo['cornices']['plinth_top'])
    bays=[]
    for row in photo['bays']:
        bays.append({'bay':row['bay'],**{role:[rectangle(q) for q in row[role].get('apertures',[])] for role in ['lower','upper']}})
    # The near tree blocks complete upper rectangles in the first two bays. The
    # marginal dark features alone cannot give all four jambs and both sills.
    joint=photo['stage_return']
    projected_joint=wall(joint['hall_to_stage_joint'][0])
    north_window=[c.wall(p,float(projected_joint[1])).tolist() for p in joint['upper_dark_opening']]
    return dict(east_x=x,pier_axes_y=axes,bays=bays,wall_limits_y=[0.,end],
        wall_heights=[*tops,low],plinth_height=zbase,visible_stage_return=None,
        pier_width=1.02, pier_width_basis="Clear pilaster stripes in uninterrupted lower wall at original crop x 428–450, 495–510 and 551–567; the angular widths decrease with distance.",
        capping_status='First three high bays carry a banded parapet. The low eave continues to the end. The narrow interval after the eighth bay has no measured opening.',
        obscured_upper='Branches obscure the first two upper bays. The low-pass rectangles are recorded only where all four aperture edges can be distinguished.',
        stage_boundary={'edge_intersection':projected_joint.tolist(),'hypothetical_south_wall_opening':north_window,
            'reason':'Treat the northern high roof as an independent volume. Extending the dark background window onto the plane of the observed joint places it well outside the high roof shown in multiple aerial photographs. Its ownership and depth are unresolved.'},
        calibration_sha256=hashlib.sha256((HERE/'court-cameras.json').read_bytes()).hexdigest())
if __name__=='__main__':
    (HERE/'registered-east-flank-plane.json').write_text(json.dumps(solve(),ensure_ascii=False,indent=2)+'\n')
