"""Establish the entrance cutout and the number plate on the registered ground-floor wall."""
import json
from hashlib import sha256
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from register_house import Camera

ROOT = Path(__file__).resolve().parent


def measure():
    document = ROOT/'house-cameras.json'
    survey = json.loads(document.read_bytes())
    front = survey['parameters']['door']
    base = np.array([front[0],front[1],front[4]])
    other = np.array([front[2],front[3],front[4]])
    diff = other-base
    width = np.linalg.norm(diff)
    height = front[5]-front[4]
    across = diff/width
    normal = np.array([across[1],-across[0],0.])
    camera = Camera('84')
    images = json.loads((ROOT/'entrance-observations.json').read_bytes())
    observed = np.array(images['measurements_84']['green_house_plaque_corners_px'])
    quad = np.array(images['close_house_plaque_83']['outline_px'])
    ratio = sum(np.linalg.norm(quad[i]-quad[j]) for i,j in [(0,1),(2,3)])/sum(np.linalg.norm(quad[i]-quad[j]) for i,j in [(1,2),(3,0)])

    def board_pixels(params):
        u,z,h = params
        corners=np.array([[-.5,.5],[.5,.5],[.5,-.5],[-.5,-.5]]) * [h*ratio,h]+[u,z]
        return np.array([camera.pixel(base+across*x+[0.,0.,z]+.011*normal) for x,z in corners])

    fit = least_squares(lambda params:(board_pixels(params)-observed).ravel(),[-width*.11,height*.87,.16],loss='soft_l1',f_scale=1.)
    pu,pz,ph = fit.x
    assert fit.success and width*.05 < -pu < width*.2 and height*.7 < pz < height
    true_corners=np.array([base+[0.,0.,height],other+[0.,0.,height],other,base])
    camera_pair=[Camera('84'),Camera('86')]
    insert_pixels=np.array([images['measurements_'+k]['right_pale_rectangle_px'] for k in ['84','86']])
    def insert_errors(parameters, observations=insert_pixels):
        u0,u1,z0,z1,depth=parameters
        vertices=[base+u*width*across+[0.,0.,z*height]+normal*depth for u,z in ((u0,z1),(u1,z1),(u1,z0),(u0,z0))]
        return np.array([[c.pixel(v) for v in vertices] for c in camera_pair])-observations
    fitted=least_squares(lambda v:insert_errors(v).ravel(),[.54,.92,.63,.90,0.],loss='soft_l1',f_scale=1.)
    assert fitted.success and -.09 < fitted.x[-1] < .10
    cover_px=np.array([images['measurements_'+k]['central_cover_px'] for k in ('84','86')])
    # Constrain the raised centre plate to the visible outer face of the slatted door.
    cover=least_squares(lambda v:insert_errors([*v,.071],cover_px).ravel(),[.2,.47,.42,.58],loss='soft_l1',f_scale=1.)
    assert cover.success
    errors={}
    for k in ('84','86'):
        proj=np.array([Camera(k).pixel(point) for point in true_corners])
        given=images['jamb_corners_px'][k]
        errors[k]={'observed_px':given,'projected_px':proj.tolist(),'error_px':np.linalg.norm(proj-given,axis=1).tolist()}
    return {'coordinates':survey['axes'],'parent_registration':document.name,
            'parent_registration_sha256':sha256(document.read_bytes()).hexdigest(),
            'left_sill_enu_m':base.tolist(),'right_sill_enu_m':other.tolist(),'across_unit_enu':across[:2].tolist(),
            'outside_unit_enu':normal[:2].tolist(),'opening_size_m':[width,height],
            'head_elevation_m':front[5],'door_opening_3d':true_corners.tolist(),'jambs_native_px':errors,
            'threshold':'The fitted sill elevation is relative to the street datum. The private passage paving is not level-surveyed.',
            'central_cover_fit':{'placement':cover.x.tolist(),'front_offset_m':.071,
                                  'radial_residual_px_84_86':np.linalg.norm(insert_errors([*cover.x,.071],cover_px),axis=2).tolist()},
            'pale_insert_fit':{'placement':fitted.x.tolist(),
                               'parameters':'u0,u1,z0,z1 as fractions of door opening, and outward offset in metres',
                               'radial_residual_px_84_86':np.linalg.norm(insert_errors(fitted.x),axis=2).tolist()},
            'house_plaque':{'centre_local_m':[pu,pz],'size_m':[ph*ratio,ph],
                            'centre_enu_m':(base+across*pu+[0.,0.,pz]+normal*.011).tolist(),'aspect_83':ratio,
                            'corners_projected_84_px':board_pixels(fit.x).tolist(),
                            'residual_native_84_px':np.linalg.norm(board_pixels(fit.x)-observed,axis=1).tolist(),
                            'source':'Photo 83 provides the inscription and aspect. In 84 the board is seen independently against the plaster left of the jamb.'}}


if __name__=='__main__':
    (ROOT/'entrance-placement.json').write_text(json.dumps(measure(),ensure_ascii=False,indent=2)+'\n')
