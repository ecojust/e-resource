"""Lift observed chair rails onto their vertical side planes and the seat onto its stretched frame."""
from pathlib import Path
import json,math
w=Path(__file__).resolve().parents[1];m=w/'measurements'
r=json.loads((m/'terrace-frame.json').read_bytes());o=json.loads((m/'chair-observations.json').read_bytes());h=r['projection_h_tile_to_image'];pitch=r['estimated_tile_pitch_m'];i0=r['grid_i_at_post_row'];j0=r['longitudinal_bounds_grid_j'][0]
vl=r['guard_calibration']['pixel_height_times_plane_w_per_m'];a=r['guard_calibration']['vertical_dx_per_dy']
def grid(pixel,z=0.):
    x,y=pixel
    c1,c2,c3=h[0]-x*h[6],h[1]-x*h[7],x-h[2]+a*vl*z
    d1,d2,d3=h[3]-y*h[6],h[4]-y*h[7],y-h[5]+vl*z
    det=c1*d2-c2*d1
    return [(c3*d2-c2*d3)/det,(c1*d3-c3*d1)/det]
def world(i,j,z):return [(i-i0)*pitch,(j-j0)*pitch,z]
def unproject(pixel):return world(*grid(pixel),0.)[:2]
def lift(pixel,side):
    # Each source pixel defines a straight line. Intersect this line with the rocker side plane.
    foot=unproject(pixel);above=world(*grid(pixel,1.),1.)[:2];d=[above[j]-foot[j]for j in range(2)]
    vec=[side[1][j]-side[0][j]for j in range(2)];normal=[-vec[1],vec[0]]
    z=sum(normal[k]*(side[0][k]-foot[k])for k in range(2))/sum(normal[k]*d[k]for k in range(2))
    return [foot[0]+z*d[0],foot[1]+z*d[1],z]
def project(p):
    x,y,z=p;i=x/pitch+i0;j=y/pitch+j0;sw=h[6]*i+h[7]*j+1
    return [(h[0]*i+h[1]*j+h[2]-a*vl*z)/sw,(h[3]*i+h[4]*j+h[5]-vl*z)/sw]
shape={}
for role,tips,inner in [('near_chair',[(103,377.5),(238.7,367)],(224.1,355.1)),('far_chair',[(236.2,286.8),(318.4,287.0)],(299.3,289.0))]:
    side=list(map(unproject,tips));d=[side[1][j]-side[0][j]for j in range(2)];L=math.hypot(*d);d=[v/L for v in d];normal=[-d[1],d[0]];other=unproject(inner);width=sum((other[i]-side[0][i])*normal[i] for i in range(2));n=[k*width for k in normal];opposite=[[p[i]+n[i]for i in range(2)]for p in side];edges=o[role]['observations'];paths={}
    if role=='far_chair':
        # The distant chair turns toward the camera. Its upper loop gives an independent transverse axis.
        # Its two visible ground arcs overlap. Their screen separation underestimates the frame width.
        cb=[[244.5,225.5],[261.5,224.0]]
        ends=[world(*grid(pt,.72),.72)for pt in cb];cross=[ends[1][i]-ends[0][i]for i in range(2)]
        width=math.hypot(*cross);d=[cross[1]/width,-cross[0]/width];foot=unproject(tips[1]);side=[foot,[foot[i]+d[i]for i in range(2)]]
        n=[-v for v in cross];opposite=[[p[i]+n[i]for i in range(2)]for p in side]
    if role=='near_chair':
        for key,idx,plane in [('outer_rocker',0,side),('visible_tail',1,side),('inner_rocker',2,opposite),('back_tube',3,side),('arm',4,side)]:
            paths[key]=[lift(pt,plane)for pt in edges[idx]['xy_660x478']]
        # Upper and lower edges of the light fabric run along the two steel seat rails.
        fabric=edges[5]['xy_660x478'];paths['seat_near']=[lift(fabric[i],side) for i in [12,11,10,9,8,7]];paths['seat_far']=[lift(fabric[i],opposite)for i in [0,1,2,3,4,5]]
    else:
        for key,idx,picked,plane in [('outer_rocker',3,None,side),('inner_rocker',4,None,opposite),('arm',2,None,side),('back_tube',1,[1,2,3,4],side),('back_opposite',1,[0,8,7,6],opposite)]:
            pts=edges[idx]['xy_660x478'];paths[key]=[lift(pts[i],plane)for i in (picked if picked is not None else range(len(pts)))]
        hoop=edges[0]['xy_660x478'];paths['back_hoop']=[lift(pt,opposite if i in [0,1,5,6]else side)for i,pt in enumerate(hoop)]
    shape[role]={'assumed_ground_contact_xy':tips,'second_side_low_contact':inner,'signed_plane_offset_m':width,'span_between_visible_ground_contacts_m':L,'side_axis_xy':d,'second_side_displacement_xy':n,'side_baseline':side,'lifted_traces':paths,'bounds_z':[min(p[2]for path in paths.values()for p in path),max(p[2]for path in paths.values()for p in path)]}
print([(k,v['span_between_visible_ground_contacts_m'],v['signed_plane_offset_m'],v['bounds_z'])for k,v in shape.items()]);(m/'chair-profiles.json').write_text(json.dumps({'photo_sha256':o['source_sha256'],'frame_calibration':'terrace-frame.json','assumptions':'上下方向依相片竖杆近似平行；可见摇架局部沿两条竖直平面提升。管径、不可见连接和座布厚度估计。','chairs':shape},ensure_ascii=False,indent=2)+'\n')
