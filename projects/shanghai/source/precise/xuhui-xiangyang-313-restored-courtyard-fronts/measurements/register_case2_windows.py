"""Convert manually digitized window reveals and canopy corners into the case 2 wall frame."""
from pathlib import Path
import json
import numpy as np
from register_courtyard import Camera

here=Path(__file__).parent
source=json.loads((here/'case2-window-photograph.json').read_bytes())['features']
camera=Camera('case2')
def wall(uv,y=0):return camera.wall(uv,y)
def at_z(uv,z):
    direction=camera.ray(uv)
    return camera.c+direction*((z-camera.c[2])/direction[2])
def rounded(v):return np.round(v,5).tolist()
def make_shelf(a,b,c,d,fall):
    back=np.array([wall(a),wall(b)])
    z=np.mean(back[:,2])
    front=np.array([at_z(uv,z-fall) for uv in [c,d]])
    left,right=(back[:,0]+front[:,0])/2
    depth=-np.mean(front[:,1])
    assert .12<depth<1.1,(depth,z)
    return {'left':float(left),'right':float(right),'depth':float(depth),'rear_z':float(z),'fall':fall,
            'back_xyz_observed':rounded(back),'front_xyz_observed':rounded(front),
            'pixels_residual_for_regularized_rectangle':rounded([np.linalg.norm(camera.pixel(xyz)-uv)for xyz,uv in zip(
                [[left,0,z],[right,0,z],[left,-depth,z-fall],[right,-depth,z-fall]],[a,b,c,d])])}
openings={}
for name,quad in source['openings'].items():
    pts=np.array([wall(q) for q in quad])
    openings[name]=rounded([np.mean(pts[[0,3],0]),np.mean(pts[[2,3],2]),np.mean(pts[[1,2],0]),np.mean(pts[[0,1],2])])
hoods={}
for name,g in source['glass_canopies'].items():
    hoods[name]=make_shelf(g['back_left'],g['back_right'],g['tip_left'],g['tip_right'],.018)
s=source['projecting_centre_shelf']
shelf=make_shelf(s['wall_left'],s['wall_right'],s['outer_left'],s['outer_right'],0)
rail_z=np.mean([wall(s[k],-shelf['depth'])[2]for k in ['rail_upper_left','rail_upper_right']])
shelf['rail_height']=round(rail_z-shelf['rear_z'],5)
leaf=source['open_right_hand_leaf']
hinge=np.array([wall(leaf['hinge_'+s],.035)for s in ['top','bottom']])
free=np.array([at_z(leaf['free_'+s],xyz[2])for s,xyz in zip(['top','bottom'],hinge)])
delta=np.mean(free[:,:2]-hinge[:,:2],axis=0)
pipe=[rounded(wall(uv,-.09))for uv in source['downpipe_centreline']]
boundary=[wall([274,51]),wall([516.8,69.9]),wall([273,375])]
out={'camera': 'case2','sources':['courtyard-cameras.json','case2-window-photograph.json'],'wall_xz':[round(float(boundary[0][0]),4),round(float(boundary[2][2]),4),round(float(boundary[1][0]),4),round(float((boundary[0][2]+boundary[1][2])/2),4)],
     'openings':openings,'canopies':hoods,'plant_shelf':shelf,'outward_leaf':{'hinge_xy':rounded(hinge[:,:2].mean(axis=0)),'free_xy':rounded(free[:,:2].mean(axis=0)),'hinge_top_z':round(hinge[0][2],4),'hinge_bottom_z':round(hinge[1][2],4),'hinge_to_tip_xy_m':rounded(delta),'apparent_open_leaf_width_m':round(float(np.linalg.norm(delta)),4),'direction_deg_from_closed_toward_street':round(float(np.degrees(np.arctan2(-delta[1],-delta[0]))),2)},
     'pipe_xyz':pipe,'left_pipe_arm':[rounded(wall(uv,-.09))for uv in source['downpipe_left_arm']],'right_pipe_arm':[rounded(wall(uv,-.09))for uv in source['downpipe_right_arm']],
     'scope':'Case 2 local fragment. Upper wall edge and truncated foot height are image-supported. No common lot pose with photograph 1 is asserted. Root of each partial lower reveal is visibly screened by trees and its lower section is not reconstructed. Rain sheets and frames are separated; thickness and the small sheet fall are modeling assumptions.'}
fixtures=source['appliances_and_western_sliver']
def bounds(quad,depth):
    xyz=np.array([wall(uv,depth) for uv in quad])
    return rounded([xyz[[0,3],0].mean(),xyz[[2,3],2].mean(),xyz[[1,2],0].mean(),xyz[[0,1],2].mean()])
ac=fixtures['large'];depth=-ac['assumed_face_offset_m']
fan=wall(ac['fan_centre'],depth)
rz=np.mean([abs(wall(ac['fan_edges'][j],depth)[2]-fan[2])for j in [2,3]])
out['exterior_unit']={'bounds':bounds(ac['face'],depth),'front_y':depth,'fan_xz':rounded(fan[[0,2]]),
 'fan_radius':round(float(rz),5),'mounts':[[rounded(wall(m['outer'],depth+.025)),rounded(wall(m['wall_foot'],-.015))] for m in ac['mounts']],
 'service_pipe':[rounded(wall(p,y)) for p,y in zip(ac['pipe'],[depth+.1,-.13,-.07,-.013])]}
j=fixtures['left_sliver']['right_jamb'];zbottom=wall(j[2:])[2];ztop=wall(j[:2])[2];right=(wall(j[:2])[0]+wall(j[2:])[0])/2
out['west_sliver']={'bounds':[out['wall_xz'][0],round(zbottom,5),round(right,5),round(ztop,5)],
 'rail_z':[round(wall([278,y],.065)[2],5) for y in fixtures['left_sliver']['transoms_y_px']]}
sg=fixtures['small_grille'];out['small_grille']={'bounds':bounds(sg['face'],-.10),'shelf':[rounded(wall(uv,-.14))for uv in sg['shelf_ends_px']],
 'hook_face_y':-2.034,'hook':[rounded(wall(uv,-2.034+d))for uv,d in zip(sg['wire_hook_px'],[-.012,-.068,-.075,-.02])]}
out['scope']='Case 2 local fragment registered in ENU with 3304-local-footprint.json. Unseen widths and lower ends are clipped at the visible extent. Condenser projection and small grille depth are modeling estimates; their photographic outlines, brackets and visible pipe are independently recorded.'
(here/'case2-window-registration.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
print(out['wall_xz'],[(k,round(v['depth'],3),v['pixels_residual_for_regularized_rectangle'])for k,v in hoods.items()],round(shelf['depth'],3),out['outward_leaf'])
