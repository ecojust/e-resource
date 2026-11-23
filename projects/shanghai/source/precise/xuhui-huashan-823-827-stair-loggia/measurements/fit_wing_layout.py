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
# The two west/front set-backs are currently the same local datum pending street intersections.
L['left']['windows']['middle six-light']['awning_measurements']=[-11.158,-9.049,5.315,.895]
L['right']['windows']['middle six-light']['awning_measurements']=[7.18,10.19,5.395,.875]
model=dict(camera_status='1300 x 731 provisional central facade registration; wing planes at local Y=0.',
           exact_photo=marks['original'],points_drawing_px=[1450,816],wings=L)
args.output.write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n')
print(args.output)
