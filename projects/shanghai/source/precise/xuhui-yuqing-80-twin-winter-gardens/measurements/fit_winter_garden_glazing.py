"""Fit window glass radii and opening heights to 14 observed quadrilaterals in the two garden views."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from register_garden import Camera

HERE = Path(__file__).resolve().parent
CAMERAS = {i: Camera(i) for i in (4,6)}
WINDOWS = {
    'SW': {
        6: [[[149,164],[234,150],[234,260],[147,268]], [[261,149],[351,158],[353,264],[260,260]],
            [[378,164],[431,183],[438,279],[380,267]], [[454,199],[468,213],[476,290],[457,282]]],
        4: [[[2,288],[29,285],[29,340],[1,343]], [[47,284],[94,285],[90,333],[43,338]],
            [[107,287],[158,291],[155,328],[103,331]]]},
    'NE': {
        4: [[[568,211],[622,188],[622,276],[568,281]], [[643,181],[718,176],[720,267],[642,273]],
            [[742,176],[812,182],[817,270],[744,267]], [[836,190],[873,207],[883,287],[838,273]]],
        6: [[[721,338],[768,330],[774,372],[724,363]], [[785,329],[817,331],[823,383],[790,377]],
            [[834,339],[845,346],[852,391],[838,387]]]}}
# The far views clip window bases behind the straight bridge parapet. Near jambs carry the aperture.
# The near 06 fourth right jamb is nearly tangent. The corresponding far 04 jamb has the wider baseline.
APERTURES = {'SW':[[-70.07,-48.23],[-42.30,-20.78],[-13.44,6.01],[16.16,46.65],[52.0,76.0]],
             'NE':[[-75.0,-55.0],[-39.5,-10.70],[-3.61,17.78],[24.17,43.56],[51.37,70.31]]}

def evaluate(parameters, report=False):
    errors, per_jamb = [], []
    for index,(side,views) in enumerate(WINDOWS.items()):
        cx=CAMERAS[4].data['centres_m'][side]
        radius=parameters[index]
        head,sill=parameters[2:]
        for view,openings in views.items():
            cam=CAMERAS[view]
            for i,quad in enumerate(openings):
                records=[]
                for a,b in ((0,3),(1,2)):
                    points=(cam.at_height(quad[a],head),cam.at_height(quad[b],sill))
                    theta=np.mean([np.arctan2(p[0]-cx,-p[1]) for p in points])
                    xy=[cx+radius*np.sin(theta),-radius*np.cos(theta)]
                    residual=np.r_[cam.pixel([*xy,head])-quad[a],cam.pixel([*xy,sill])-quad[b]]
                    errors.extend(residual/3)
                    records.append([round(float(np.degrees(theta)),2),np.round(residual,1).tolist()])
                per_jamb.append([side,view,i,records])
    return per_jamb if report else errors

def fit():
    garden=CAMERAS[4].data
    start=[garden['outer_radii_m'][s]-.5 for s in WINDOWS]+[garden['eave_soffit_z']-.18,garden['window_sill_z']+.025]
    opt=least_squares(evaluate,start,bounds=([1.7,1.7,4.,2.8],[3.45,3.3,9.6,6.8]),loss='soft_l1')
    return dict(camera_file_sha256=hashlib.sha256((HERE/'garden-cameras.json').read_bytes()).hexdigest(),
                windows=WINDOWS,radii_m=dict(zip(WINDOWS,opt.x[:2])),head_z=opt.x[2],sill_z=opt.x[3],
                angles=evaluate(opt.x,True),aperture_angles_deg=APERTURES,
                scope='Visible glazing only. The far images crop or hide several jambs, especially the westernmost northeast aperture, whose left return is seen in 06. The leader sits between the first two openings in both photographs.',
                western_jamb_returns_m={'NE':[[-55,0],[-39.5,-.152],[-10.7,0]]},
                western_jamb_note='04 and 06 place the left jamb of NE window 2 at a shallower return than a regular cylinder. Its plan radius is reduced by 0.152 m at the marked jamb and interpolated to the two adjoining jambs. Vertical reprojection in the far view is less certain.',
                angle_reference='Angles are in degrees with X = cx + R sin(theta), Y = -R cos(theta).',
                sw_open_leaf={'window':2,'view':6,'free_edge_observed_px':[[290,169],[290,249]],'hinge':'left lower light','angle_degrees':60,'free_edge_reprojection_px_approx':[[290,168],[291,246]]})
if __name__=='__main__':
    (HERE/'winter-garden-glazing.json').write_text(json.dumps(fit(),indent=2)+'\n')
