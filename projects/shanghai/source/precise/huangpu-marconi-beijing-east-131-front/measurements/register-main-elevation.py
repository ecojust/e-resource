"""Read the same corners on two north-front photographs on a common rectified board."""
from pathlib import Path
import sys,json,numpy as np
from scipy.optimize import minimize_scalar
here=Path(__file__).resolve().parent
sys.path.insert(0, str(here.parent / 'source'))
from marconi_photo_plane import on_wall,pixel
# This board is a reduced copy of the 1043 x 1533 metric rectification, shown at 610 x 896.
def uv(q,c):
 x=-11.5+q[0]*1043/610/70;z=21.5-q[1]*1533/896/70
 return pixel([x,0,z],c)
def mark(q0,q1):
 u,v=uv(q0,'2017_front');other=uv(q1,'2015_oblique')
 def loss(y):return np.linalg.norm(np.array(pixel(on_wall(u,v,y),'2015_oblique'))-other)
 r=minimize_scalar(loss,bounds=(-1.,6.),method='bounded')
 return {'2017_rect_px':q0,'2015_rect_px':q1,'2017_original_px':[round(k,3) for k in [u,v]],'2015_original_px':[round(k,3) for k in other],'inferred_xyz_m':[round(k,4)for k in on_wall(u,v,r.x)],'other_image_residual_px':round(r.fun,2)}
pairs={
 'main_roof_front_middle_edge':[[350,137],[350,133]],
 'right_dormer_front_apex':[[148,18],[185,7]],
 'right_dormer_inside_glazing_top_right':[[187,66],[244,58]],
 'right_dormer_eaves_front_east':[[73,40],[116,38]],
 'right_dormer_eaves_front_west':[[231,42],[269,35]],
 'right_dormer_wall_base_west':[[262,132],[399,129]],
 'broad_upper_east_fixed_frame_left':[[103,226],[146,223]],
 'broad_upper_west_fixed_frame_left':[[221,230],[253,218]],
 'broad_upper_centre_panel_top_left':[[153,231],[184,225]],
 'broad_middle_east_frame_lower_left':[[96,548],[129,549]],
 'broad_middle_frame_right_edge':[[264,550],[281,550]],
 'small_upper_middle_pier_left':[[468,226],[484,224]],
 'corner_attic_opening_left_jamb':[[423,219],[433,216]],
 'corner_attic_soffit_left':[[414,207],[434,205]],
 'right_attic_window_sill_outer_left':[[411,295],[410,296]],
 'corner_pier_sill_right':[[570,262],[571,259]],
}
records={name:mark(*p)for name,p in pairs.items()}
doc={'coordinate_notes':'Board 610 x 896 pixels samples rectified original to Y0 (1043 x 1533 at 70 pixels/m), X=-11.5+u/70, Z=21.5-v/70 at full board size. Original scale comes from independent 131 door width. Different first and last usable occlusion edges were excluded when building each recess.','pairs':records}
f=here/'whole-front-stereo.json';f.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
for k,r in records.items():print(k,r['inferred_xyz_m'],r['other_image_residual_px'])
