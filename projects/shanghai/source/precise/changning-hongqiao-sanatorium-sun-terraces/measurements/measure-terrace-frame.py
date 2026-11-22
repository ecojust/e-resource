"""Reconcile the terrace section with the tiled-floor frame. The physical scale is conditional."""
from pathlib import Path
from statistics import median
import hashlib,json,math
from PIL import Image
w=Path(__file__).resolve().parents[1];p=w/'measurements';section=Path(__import__('os').environ.get('HONGQIAO_ARCHIVES',w))/'archive-3.jpg';px=Image.open(section).convert('L').load()
load=lambda name:json.loads((p/name).read_bytes())
tiles=load('terrace-checker-grid.json');h=tiles['homography_tile_to_working'];z=load('drawn-section.json');scale=z['pixels_per_graphic_division']
def point(x,y):
 a,b,c,d,e,f=[h[0]-x*h[6],h[1]-x*h[7],x-h[2],h[3]-y*h[6],h[4]-y*h[7],y-h[5]]
 det=a*e-b*d;return [(c*e-b*f)/det,(a*f-d*c)/det]
def axis(x,y0,y1,hw):
 v=[(k,sum(max(0.,145-px[k,j])for j in range(y0,y1)))for k in range(x-hw,x+hw+1)];m=max(s for k,s in v);wins=[(k,s) for k,s in v if s>m*.40];return sum(k*s for k,s in wins)/sum(s for k,s in wins)
post=axis(700,34,165,10);upperwall=axis(761,34,165,7);rear=axis(988,34,165,10)
front=z['successive_south_edges_x'][-1];terrace_div=(post-front)/scale
# Gallery post front edges and outer coping base in the photograph; vegetation obscures the middle segment.
rail_xy=[[374,243],[429,271],[650,362]];col_xy=[[76,391],[149,279]];rail=[point(*q) for q in rail_xy];col=[point(*q) for q in col_xy];ext_i=median(r[0]for r in rail);post_i=median(r[0]for r in col);pitch=terrace_div/(ext_i-post_i)
# The total guard height is estimated. Vertical members lean a little in the scanned photograph.
# Match five separated positions along the visible upper rail and the base of its straight parapet.
correspondences=[[[374,243],[372,198]],[[407,256],[405,202]],[[462,280],[460,209]],[[500,297],[497,215]],[[642,356],[638,235]]];guard=.91
vertical_scale=median((a[1]-b[1])*(1+h[6]*point(*a)[0]+h[7]*point(*a)[1])/guard for a,b in correspondences)
vertical_dx=.034;near_j=-1.65;far_j=point(*rail_xy[0])[1];bay=[r[1] for r in col]
row_z=[(703-f)/scale for f in z['slab_centres_y']];levels=[0.,*row_z[::-1]]
r={'section_sha256':hashlib.sha256(section.read_bytes()).hexdigest(),'terrace_photo_sha256':tiles['source_sha256'],'upper_gallery_column_x':post,'upper_room_wall_x':upperwall,'enclosed_rear_edge_x':rear,'section_scale_px_per_division':scale,'conditional_metres_per_graphic_division':1.,'raw_ground_floor_y_conditional':703,'floor_to_roof_z_m':levels,'south_edges_x_m':[(post-i)/scale for i in z['successive_south_edges_x']], 'upper_gallery_to_rail_m':terrace_div,'upper_room_x_m':(post-upperwall)/scale,'north_limit_x_m':(post-rear)/scale,'outer_rail_floor_pixels':rail_xy,'outer_rail_grid':rail,'gallery_post_floor_pixels':col_xy,'gallery_post_grid':col,'grid_i_at_outer_edge':ext_i,'grid_i_at_post_row':post_i,'estimated_tile_pitch_m':pitch,'assumption':'采用与史料退台六七尺相符的一分格约一米；黑白照支持方格线和相机配准，方砖两向先取同一公称边长，均非实测。','longitudinal_bounds_grid_j':[near_j,far_j],'upper_post_grid_j':bay,'projection_h_tile_to_image':h,'guard_calibration':{'adopted_height_m':guard,'foot_and_top_xy':correspondences,'pixel_height_times_plane_w_per_m':vertical_scale,'vertical_dx_per_dy':vertical_dx}}
(p/'terrace-frame.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('nominal pitch and top width',pitch,terrace_div,'upright',vertical_scale,'levels',levels)
