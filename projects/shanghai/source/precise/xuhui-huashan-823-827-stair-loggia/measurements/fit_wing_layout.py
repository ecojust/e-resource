"""Resolve the photographed wing points against the registered central elevation."""
import argparse
import json
from pathlib import Path
import numpy as np

parser=argparse.ArgumentParser(description=__doc__)
here=Path(__file__).resolve().parent
parser.add_argument('--marks',type=Path,default=here/'wing-photo-readings.json')
parser.add_argument('--camera',type=Path,default=here/'front-camera.json')
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
marks=json.loads(args.marks.read_bytes())
camera=json.loads(args.camera.read_bytes())
ratio=np.asarray(camera['working_size'])/marks['mark_canvas']
K=np.asarray(camera['intrinsic']);R=np.asarray(camera['world_to_camera']);C=np.asarray(camera['camera_centre'])
inverse=R.T@np.linalg.inv(K)
def wall(p,y=0.):
    ray=inverse@[*((np.asarray(p)+.5)*ratio-.5),1.]
    xyz=C+ray*(y-C[1])/ray[1]
    return xyz[[0,2]]
def bounds(points):
    p=np.asarray([wall(v) for v in points]);return [*p.min(axis=0),*p.max(axis=0)]
def rect(ul,ur,ll,lr,crown=None):
    a,b,c,d=[wall(p) for p in (ul,ur,ll,lr)]
    return [(a[0]+c[0])/2,(c[1]+d[1])/2,(b[0]+d[0])/2,
            wall(crown)[1] if crown else (a[1]+b[1])/2]
def w(bounds,cols=6,rows=4,fan=False,hood=False):
    return dict(bounds=list(np.round(bounds,5)),columns=cols,rows=rows,fan=fan,hood=hood)
def poly(points):
    return [list(np.round(wall(p),5)) for p in points]
def window_item(name,fan=False):
    p=marks['pixel_readings'][name]
    if fan: return rect(p['upper_left_spring'],p['upper_right_spring'],p['lower_left'],p['lower_right'],p.get('crown'))
    return rect(p['upper_left'],p['upper_right'],p['lower_left'],p['lower_right'])
def v(label,cells=1):
    item=marks['pixel_readings'][label]
    return dict(bounds=list(np.round(bounds([item[k] for k in ('left','right','top','bottom')]),5)),cells=cells)
left_rect=window_item('left-fanlight',True)
right_rect=window_item('right-fanlight',True)
right_rect[3]+= (right_rect[2]-right_rect[0])*.333
split_left=float(wall((377,145))[0])
split_right=float(wall((1020,180))[0])
left_outer=float(wall((65,149))[0])
right_outer=12.90
left_left_eave=float(wall((65,149))[1]);left_right_eave=float(wall((377,145))[1])
# The street panorama corroborates the two gable slopes on the masked right wing.
# Mark only their ends which remain visible in 2018, and use the opposite gable's rise as an estimate.
r_ledge=float(wall((1020,180))[1]);r_redge=left_left_eave
L={
    'left':dict(x0=left_outer,x1=split_left,ridge=poly([(266,75)])[0],outer_eave=left_left_eave,inner_eave=left_right_eave,
                windows={'upper fan':w(left_rect,fan=True,hood=True),
                         'middle six-light':w(rect((175,428),(292,428),(175,525),(291,523)),hood=True),
                         'lower six-light':w(rect((170,615),(289,614),(169,709),(292,707)),hood=True)},
                vents={'upper diamond':v('left-diamond'),'three-cell band':w(bounds([(177,567),(278,567),(226,554),(228,582)]))}),
    'left connector':dict(x0=split_left,x1=-4.58,outer_eave=left_right_eave,inner_eave=float(wall((539,154))[1]),
                        windows={'upper divided casement':w(window_item('left-inner-up'),6,3),'middle divided casement':w(window_item('left-inner-middle'),6,3),'lower divided casement':w(window_item('left-inner-low'),6,3)}),
    'right connector':dict(x0=4.98,x1=split_right,outer_eave=float(wall((953,182))[1]),inner_eave=r_ledge,
                        windows={'upper partly visible casement':w(window_item('right-inner-up'),2,3),'middle partly visible casement':w(window_item('right-inner-middle'),2,3)}),
    'right':dict(x0=split_right,x1=right_outer,ridge=[8.46,left_rect[3]+(wall((266,75))[1]-left_rect[3])],outer_eave=r_ledge,inner_eave=r_redge,
                 windows={'upper fan':w(right_rect,fan=True,hood=True),
                          'middle six-light':w(rect((1079,420),(1154,421),(1086,498),(1160,497)),hood=True)},
                 vents={'upper diamond':v('right-diamond'),'three-cell band':v('right-long-vent',3)})
}
left=L['left'];slots=marks['pixel_readings']['left-slot-cross']
left['slot_bounds']=[list(np.round(bounds(slots[p]),5)) for p in ('top','left','right','bottom')]
left['vents']['three-cell band']=dict(bounds=list(np.round(bounds([(174,573),(285,568),(225,554),(223,583)]),5)),cells=3)
# The hole and skyline points were first inverted at Y=0. Each ray is now
# intersected with the corresponding registered wall plane, without moving the camera.
L['left']['windows']['middle six-light']['awning_measurements']=[-11.158,-9.049,5.315,.895]
L['right']['windows']['middle six-light']['awning_measurements']=[7.18,10.19,5.395,.875]
WING_Y = 5.50
CONNECTOR_Y = .75
def on_plane_x(x, y):
    return C[0]+(x-C[0])*(1-y/C[1])
def on_plane_z(z, y):
    return C[2]+(z-C[2])*(1-y/C[1])
def on_plane_bounds(bounds, y):
    a,lo,b,hi=bounds
    return [round(on_plane_x(a,y),5),round(on_plane_z(lo,y),5),
            round(on_plane_x(b,y),5),round(on_plane_z(hi,y),5)]

for name,panel in L.items():
    y=CONNECTOR_Y if 'connector' in name else WING_Y
    panel['y']=y
    panel['angular_scale']=1-y/C[1]
    panel['x0']=round(on_plane_x(panel['x0'],y),5)
    panel['x1']=round(on_plane_x(panel['x1'],y),5)
    panel['outer_eave']=round(on_plane_z(panel['outer_eave'],y),5)
    panel['inner_eave']=round(on_plane_z(panel['inner_eave'],y),5)
    if 'ridge' in panel:
        x,z=panel['ridge']
        panel['ridge']=[round(on_plane_x(x,y),5),round(on_plane_z(z,y),5)]
    for window in panel['windows'].values():
        bb=on_plane_bounds(window['bounds'],y)
        # Hedges obscure the bottom edges. The ground datum bounds this local model.
        bb[1]=max(.056,bb[1])
        window['bounds']=bb
        if 'awning_measurements' in window:
            a,b,top,drop=window['awning_measurements']
            window['awning_measurements']=[round(on_plane_x(a,y),5),round(on_plane_x(b,y),5),
                                           round(on_plane_z(top,y),5),round(drop*(1-y/C[1]),5)]
    for vent in panel.get('vents',{}).values():
        vent['bounds']=on_plane_bounds(vent['bounds'],y)
    if 'slot_bounds' in panel:
        panel['slot_bounds']=[on_plane_bounds(bb,y) for bb in panel['slot_bounds']]

# Returns have a wall-normal plan axis. The arms behind the stepped connecting bays
# are allowed to continue to their physical joins underneath the nearer face. Their
# measured starting pixel remains the visible transition line.
left,middle_l,middle_r,right=(L[n] for n in ('left','left connector','right connector','right'))
upper_west=middle_l['outer_eave'];upper_east=middle_r['inner_eave']
left['x1']=middle_l['x0']
middle_l['x1']=-4.58
middle_r['x0']=4.98
right['x0']=middle_r['x1']
# Twelve street images identify the white downpipe on the outer high wall corner.
# Its offset from the southern ridge is about 2.8 m at the production scale.
right['x1']=17.15
# A covered extension to the right behind its short bay needs an extra point on
# the roof profile. Otherwise the visible sloping verge would move when the wall
# below joins the stepped portion.
right['verge_start']=[round(on_plane_x(split_right,WING_Y),5),right['outer_eave']]
left['verge_end']=[round(on_plane_x(split_left,WING_Y),5),left['inner_eave']]
returns=[
    dict(name='north gable to northern connecting strip',x=middle_l['x0'],y0=CONNECTOR_Y,
         y1=WING_Y,z0=upper_west,z1=left['inner_eave'],outside=-1),
    dict(name='central stair to northern connecting strip',x=-4.58,y0=0.,y1=CONNECTOR_Y,
         z0=11.49,z1=middle_l['inner_eave'],outside=-1),
    dict(name='central stair to southern connecting strip',x=4.98,y0=0.,y1=CONNECTOR_Y,
         z0=10.76,z1=middle_r['outer_eave'],outside=1),
    dict(name='southern connecting strip to south gable',x=middle_r['x1'],y0=CONNECTOR_Y,
         y1=WING_Y,z0=upper_east,z1=right['outer_eave'],outside=1)]
model=dict(camera_status='Sources use the registered 1300 x 731 Commons view. The retained provisional camera stays at its original position.',
           exact_photo=marks['original'],points_drawing_px=[1450,816],wings=L,returns=returns,
           placement=dict(global_scale=.683,central_y=0.,wing_y=WING_Y,connecting_y=CONNECTOR_Y,
             street_survey='The central gable is 3.81 m ahead of the line joining the outer gable peaks. Independent years give 3.86 and 3.57 m. At the shared scale the authored setback is 3.7565 m.',
             frontage_check='The two projected outer gable peaks are 15.7 m apart at this scale. Independent street intersections give 15.61 m.',
             mirror_hypothesis='A single-image symmetry assumption yields depths of 1.93, 2.05 and 2.13 authored units from the diamonds and the upper and middle window sills. It does not reproduce the independent survey depth.',
             southern_corner='The white downpipe fixes the outside high wall edge about 2.90 m beyond the southern ridge axis; the year-only solutions give 2.48 and 2.83 m. The authored edge uses 17.15, 2.81 m beyond the ridge at scale .683.',
             connector='The right outer edge of the complete six-column window on the northern connector reaches the central side wall at a setback of about 1 authored unit. The connecting bays use 0.75 unit; their exact depth is not independently surveyed.'))
args.output.write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n')
print(args.output)
