"""Express the retained southern cameras and western wall homographies in the shared model metre frame."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from house_layout import LAYOUT
from curved_veranda import veranda_interface
from west_wing import WEST_CAL,ORIGIN,SEAT

def get(name):
    return json.loads((HERE/name).read_bytes())

def transform():
    scalar=LAYOUT['post_span']
    mat=np.eye(4)
    mat[:3,:3]/=scalar
    mat[:3,3]=-np.array([LAYOUT['center_x'],LAYOUT['front_y'],LAYOUT['deck_z']])/scalar
    south={}
    for name,d,key,field in [('south window and colonnade','south-window-and-gallery-fit.json','cameras','projection'),('arched timber and folded roof','curved-veranda-folded-roof.json','stations','P')]:
        rows={}
        for k,st in get(d)[key].items():
            M=np.array(st[field])@mat
            eye=-np.linalg.solve(M[:,:3],M[:,3])
            rows[k]={'world_xyz_metres_to_reference_pixels':M.tolist(),'camera_centre_model_metres':eye.tolist()}
        south[name]={'source':d,'source_sha256':sha256((HERE/d).read_bytes()).hexdigest(),'cameras':rows}
    source='west-eave-photo-control.json'
    survey=get(source)
    wall=np.array([[-1/WEST_CAL,0,ORIGIN],[0,1/WEST_CAL,-SEAT],[0,0,1]])
    nominal=np.array(survey['points_m']); actual=np.c_[np.zeros(len(nominal)),(ORIGIN-nominal[:,0])*WEST_CAL,(SEAT+nominal[:,1])*WEST_CAL]
    cams={}
    for k,st in survey['cameras'].items():
        M=np.array(st['plane_to_pixel'])@wall
        q=np.c_[actual[:,1:],np.ones(len(nominal))]@M.T; xy=q[:,:2]/q[:,2:]
        repro=np.linalg.norm(xy-np.array(st['native_points']),axis=1)
        cams[k]={'native_image_size':st['native_size'],'world_yz_metres_to_reference_pixels_on_x_zero':M.tolist(),
                 'control_reprojection_px':repro.round(3).tolist(),'median_px':round(float(np.median(repro)),3)}
    eave={'source':source,'source_sha256':sha256((HERE/source).read_bytes()).hexdigest(),
          'wall_x_m':0,'metres_per_conditional_west_study_metre':WEST_CAL,
          'world_xyz_metres':dict(zip(survey['point_names'],actual.round(5).tolist())),'cameras':cams}
    interface=veranda_interface(LAYOUT)
    return {'frame':'Local metres. X to the right along the south garden front, Y into the residence, Z above the model street datum.',
            'controls_source':'relative-street-dimensions.json','layout':LAYOUT,'world_to_normalized_timber_frame':mat.tolist(),
            'southern_photo_cameras':south,'western_wall_homographies':eave,
            'veranda_controls':{'ridge_end_xyz_m':interface['ridge_end'],'rear_roof_section_xyz_m':interface['rear_roof_section'],
                                'central_bow_projection_m':.163*scalar,'structural_timber_axis_width_m':scalar},
            'limits':['South-window and roof fits retain separate residuals and matrices. Plates 35 and 38 give similar oblique directions.',
                      'Western matrices predict original-image pixels for points on the main X=0 wall plane. The projecting timber and chimney breast require independent depth information.',
                      'The western original brick-module hypothesis is scaled once by the common facade datum. Outdoor image control is approximate.']}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);args=ap.parse_args()
    args.output.write_text(json.dumps(transform(),ensure_ascii=False,indent=2)+'\n')
