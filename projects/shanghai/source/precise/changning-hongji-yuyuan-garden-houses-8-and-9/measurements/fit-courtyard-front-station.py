"""Resolve a nearly front-on photograph's focal-length/distance ambiguity against the opposite house."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from shapely.geometry import Point

HERE=Path(__file__).resolve().parent
SIDE=[('left corner of flat terrace coping',[-3.50,1.22,3.24],[369.0,495.3],4.),
      ('outer corner of low cafe tile eave',[-5.24,4.88,3.96],[314.3,478.0],4.),
      ('brick-return sign top left',[-5.56,5.98,2.52],[331.,525.],6.),
      ('brick-return sign bottom left',[-5.57,5.98,1.70],[332.,561.],8.)]


def projection(v,size):
    x,y,z,yaw,pitch,roll,f=v
    forward=np.array([np.sin(yaw)*np.cos(pitch),np.cos(yaw)*np.cos(pitch),np.sin(pitch)])
    right=np.array([np.cos(yaw),-np.sin(yaw),0.])
    up=np.cross(right,forward)
    rotation=np.array([right*np.cos(roll)+up*np.sin(roll),right*np.sin(roll)-up*np.cos(roll),forward])
    k=np.array([[f,0,size[0]/2],[0,f,size[1]/2],[0,0,1.]])
    return k@rotation@np.c_[np.eye(3),-np.array([x,y,z])]


def local_to_world(layout):
    f=layout['garden_transform'];m=np.eye(4)
    m[:2,0]=f['local_X_unit_EN'];m[:2,1]=f['local_Y_unit_EN']
    m[:2,3]=f['left_wall_projection']['garden_ENU_m']
    return m


def fit():
    import sys
    sys.path.insert(0,str(HERE.parent/'source'))
    from garden_builder import GardenBuilder
    from garden_shells import footprint
    from courtyard import lawn_outline
    cameras=json.loads((HERE/'six-front-cameras.json').read_bytes())
    layout=json.loads((HERE.parent/'source/garden-layout.json').read_bytes())
    old=cameras['houses']['8']['views']['winter2023-04'];size=old['upright_pixels']
    controls=[(r['landmark'],r['xyz'],r['uv'],6. if 'foot' in r['landmark'] else 1.6) for r in old['landmarks']]+SIDE
    xyz=np.array([[*x,1.]for _,x,_,_ in controls]);uv=np.array([u for _,_,u,_ in controls]);weight=np.array([v for _,_,_,v in controls])
    m8=local_to_world(layout['8']);m9=local_to_world(layout['9']);into_nine=np.linalg.inv(m9)@m8
    def predicted(p):
        q=xyz@p.T
        return q[:,:2]/q[:,2,None]
    def residual(v):
        q=predicted(projection(v,size))
        eye9=into_nine@np.r_[v[:3],1.]
        # Lawn-side paved strip. The hedge occupies the nearest ~1.2 m; the
        # visible lawn edge is ~4.4 m out. This is a positional prior, not EXIF.
        return np.r_[((q-uv)/weight[:,None]).ravel(),(eye9[1]+2.75)/.90,(v[2]-1.65)/.45,v[5]/.10]
    result=least_squares(residual,[-.8,-23.3,1.8,.03,.16,-.01,940],
                         bounds=([-15,-29,.65,-.75,-.25,-.2,350],[15,-15,2.75,.75,.60,.2,1550]),
                         loss='soft_l1',f_scale=1.6)
    p=projection(result.x,size);difference=predicted(p)-uv
    old9=into_nine@np.r_[old['estimated_eye_local_m'],1.]
    new9=into_nine@np.r_[result.x[:3],1.]
    house9=footprint(9,layout['9'])
    assert house9.contains(Point(*old9[:2])) and not house9.contains(Point(*new9[:2]))
    eye=m8@np.r_[result.x[:3],1.]
    assert -4.70<new9[1]<-1.3 and not lawn_outline().contains(Point(*eye[:2]))
    return {'view':'winter2023-04','image_sha256':old['sha256'],'upright_pixels':size,
            'unconstrained_source':'six-front-cameras.json','unconstrained_eye_in_house9_m':old9[:3].tolist(),
            'unconstrained_inside_opposite_building':True,
            'exterior_eye_in_house9_m':new9[:3].tolist(),'exterior_eye_local_house8_m':result.x[:3].tolist(),
            'exterior_eye_garden_ENU_m':eye[:3].tolist(),'exterior_inside_other_building':False,
            'garden_to_upright_pixel_camera':(p@np.linalg.inv(m8)).tolist(),'house8_to_upright_pixel_camera':p.tolist(),
            'model':'A plausible camera on the west paved strip. The front elevation alone admits multiple focal lengths and positions. Four more marks on three deeper features and an explicit courtyard-depth prior constrain this scene registration. This does not establish the historical photographer position.',
            'paved_strip_prior_in_house9_axes':{'center_y_m':-2.75,'standard_deviation_m':.90,'estimated_clear_y_range_m':[-4.45,-1.22]},
            'focal_length_px':float(result.x[6]),'controls':[{'point':tag,'xyz':pt,'observed_px':observed,'weight_sigma_px':sigma,'projected_px':list(np.round(observed+err,3)),'residual_xy_px':list(np.round(err,3))}for (tag,pt,observed,sigma),err in zip(controls,difference)],
            'front_13_radial_rms_px':float(np.sqrt(np.mean((difference[:13]**2).sum(axis=1)))),
            'noncoplanar_4_radial_rms_px':float(np.sqrt(np.mean((difference[13:]**2).sum(axis=1))))}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path);args=parser.parse_args();record=fit()
    if args.output:args.output.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(record['exterior_eye_local_house8_m'],record['front_13_radial_rms_px'],record['noncoplanar_4_radial_rms_px'])
