"""Intersect hand-read architectural pixels with the fitted winter frontage plane."""
from pathlib import Path
from math import cos, sin, atan2, radians, tan, hypot
import numpy as np
import json,hashlib
import argparse
p=argparse.ArgumentParser()
p.add_argument('output',type=Path)
args=p.parse_args()
folder=Path(__file__).resolve().parent
fit=folder/'street-measurements.json'
base=json.loads(fit.read_bytes())['epoch_solutions']['winter']
west,east=[np.array(base[k]['xy']) for k in ('west','east')]
midpoint=(west+east)/2
axis=(east-west)/np.linalg.norm(east-west)
inside=np.array([-axis[1],axis[0]])
cam=np.array(base['west']['references']['11']['cam'])
frames = {'gate-11-342-z5': {'width': 1000, 'height': 900, 'heading': 342, 'pitch': 1, 'fov': 58, 'sha256': 'ac07183b314bbcc1e3c1f140ed50d38b176bcc3a1b726d03e13ad4afd6ed5a22', 'station': '09000300122002201539441295O'}, 'gate-11-307-z5': {'width': 1000, 'height': 900, 'heading': 307, 'pitch': 1, 'fov': 58, 'sha256': '97edd89754c8f935d606ce5b15e58109f8c09a74013101bf53762d7f230b2b0c', 'station': '09000300122002201539441295O'}}
sources={}
def project(file,picks):
    frame=frames[file]
    hf=radians(frame['fov']/2)
    W,H=frame['width'],frame['height'];f=W/(2*tan(hf));pitch=radians(frame['pitch'])
    rows={}
    for k,(u,v,back) in picks.items():
        a=(u-W/2)/f;b=(H/2-v)/f
        fl=cos(pitch)-b*sin(pitch)
        az=radians(frame['heading'])+atan2(a,fl)
        alt=atan2(sin(pitch)+b*cos(pitch),hypot(fl,a))
        ray=np.array([sin(az),cos(az)])
        distance=((midpoint-cam)@inside+back)/(ray@inside)
        rows[k]=dict(pixel=[u,v],frontage_depth_m=back,local_x=float((cam+distance*ray-midpoint)@axis),height_over_lens_m=tan(alt)*float(distance))
    sources[file]=dict(sha256=frame['sha256'],station=frame['station'],rectilinear=[W,H,frame['heading'],frame['pitch'],frame['fov']],points=rows)
    return rows
b=project('gate-11-342-z5',dict(west_foot=(384,771,0),east_foot=(939,785,0),west_top=(403,140,0),east_top=(952,192,0),
    west_recess_low=(391,641,0.07),west_recess_high=(400,190,0.07),
    west_plinth=(386,660,0),east_plinth=(935,681,0),
    west_field_left=(362,457,.07),west_field_right=(420,457,.07),
    highest_crest_right_gate=(669,330,.91),hinge_crest_right_gate=(838,407,.44),
    east_notice_center=(758,460,0.72),east_green_plate=(858,441,.32)))
ground=(b['west_foot']['height_over_lens_m']+b['east_foot']['height_over_lens_m'])/2
w=project('gate-11-307-z5',dict(
    wall_112_outer_foot=(477,683,.09),wall_112_inner_foot=(533,696,.12),wall_at_pier_foot=(893,765,.12),
    wall_112_top=(507,365,.09),wall_field_cap_at_112=(564,377,.14),wall_field_cap_near_pier=(894,377,.14),
    lower_coping_near_112=(572,424,.14),lower_coping_near_pier=(892,434,.14),dado_near_112=(565,628,.14),dado_near_pier=(884,677,.14),
    west_number=(510,447,.09),screen_first_top=(571,229,.31),screen_last_top=(891,185,.31),
    screen_first_bottom=(575,338,.31),screen_last_bottom=(887,320,.31),
    west_panel_low_edge=(908,650,0),west_pier_foot=(942,784,0)))
for group in sources.values():
    for row in group['points'].values():row['above_ground_m']=round(row['height_over_lens_m']-ground,3)
vals=dict(control='same-day three-station fit',fit_sha256=hashlib.sha256(fit.read_bytes()).hexdigest(),local_axes='X along the two winter street faces; Y into lane; Z upwards',ground_below_lens_m=ground,views=sources)
args.output.write_text(json.dumps(vals,ensure_ascii=False,indent=2)+'\n')
