"""Rebuild the metric arch and glazing schedule of the street-facing brick storey."""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from daren_photo_plane import on_wall


def fit(row, sill_survey):
    cx,a,cy,rise,shape = row['current_cx_halfwidth_crown_rise_exponent']
    slope = row['orientation_slope']
    arc = np.array([on_wall(*p)[::2] for p in row['surveyed_edge_pixels']])
    left = np.array(on_wall(cx-a,cy+rise-slope*a))[::2]
    right = np.array(on_wall(cx+a,cy+rise+slope*a))[::2]
    crown = on_wall(cx,cy)[2]
    seed = np.array([(left[0]+right[0])/2,(right[0]-left[0])/2,(left[1]+right[1])/2,crown,shape])
    angles = np.linspace(0,np.pi,301)
    def curve(v):
        x,half,spring,top,power = v
        return np.column_stack((x+half*np.cos(angles),spring+(top-spring)*np.sin(angles)**(2*power)))
    def errors(v):
        # Use the true shortest distance to the sampled profile, including its
        # steep springing. Endpoints keep the fitted clear width measurable.
        dist=np.linalg.norm(arc[:,None,:]-curve(v)[None,:,:],axis=-1).min(axis=1)
        return np.r_[dist/.02,(v-seed)/[.022,.020,.038,.025,.11]]
    v=least_squares(errors,seed,bounds=(seed-[.055,.045,.060,.045,.13],seed+[.055,.045,.060,.045,.15]),loss='soft_l1').x
    key=row['index'];center,half,spring,top,power=v
    # Most projecting sills hide the very bottom of their glass. These upper
    # stone arrises are independent hand-read locations on the 2026 frame.
    visible_sill={1:(145,365.5),2:(208,371.5),3:(272,375),4:(336,379),5:(399,382.5),
                  11:(714,398.5),12:(769,404),13:(815,408.5),14:(864,414.8)}
    # At #6,7,9,10 the white balustrade covers the stone. Continue the heights
    # of #5 and #11. The lower part of #8's orange door is behind the parapet.
    def surveyed_sill(number):
        bands=sill_survey[str(number)]
        facing='east20-wall' if number<=4 else 'centre20-wall'
        # The latest full facade shows the ledge directly. The opposite station
        # checks its elevation and width after excluding the obstructed views.
        top=.65*bands['video-4.28']['top']+.35*bands[facing]['top']
        base=.65*bands['video-4.28']['bottom']+.35*bands[facing]['bottom']
        return np.asarray([top+.024,top+.024-base])
    if key in visible_sill:
        bottom,thickness=surveyed_sill(key);provenance='edge gradients of pale stone at Y=-0.12 in 2026 and an independent 2020 view'
    elif key==8:
        bottom=4.99;thickness=0.;provenance='door threshold behind terrace, estimated'
    else:
        west=on_wall(*visible_sill[5]);east=on_wall(*visible_sill[11]);t=(center-west[0])/(east[0]-west[0]);bottom,thickness=surveyed_sill(5)*(1-t)+surveyed_sill(11)*t;provenance='continuation between visible sills, lower edge occluded'
    # Wrought/steel sash subdivisions are observations of the latest front. The
    # central twin-narrow interval is deliberately retained. Only #8 is a door.
    # Different paint/shade is visible in the earlier street photographs.
    glazing={1:(3,3),2:(6,4),3:(3,3),4:(6,4),5:(2,3),6:(6,4),7:(3,3),
             8:(1,1),9:(6,4),10:(3,3),11:(6,4),12:(3,3),13:(6,4),14:(2,3)}
    depth={4:.105,5:.13,6:.215}.get(key,.17)
    return dict(number=key,opening='orange timber door' if key==8 else row['kind']+' glazed opening',
                center=round(center,5),half_width=round(half,5),spring=round(spring,5),
                top=round(top,5),profile_exponent=round(power,5),sill=round(bottom,5),
                sill_native_pixel=visible_sill.get(key),sill_thickness=round(thickness,5),sill_evidence=provenance,glazing_setback_m=depth,
                glazing_grid=glazing[key],edge_points=len(arc),median_fitted_contour_error_m=round(float(np.median(errors(v)[:len(arc)]))*.02,5))


def measure():
    photo=json.loads((HERE/'brick-arcade-source-pixels.json').read_text())
    openings=[fit(r,photo['sill_band_survey']['per_opening']) for r in photo['openings']]
    for i,o in enumerate(openings):
        a=o['center']-o['half_width'];b=o['center']+o['half_width']
        o['partition_left']=0. if i==0 else round((a+openings[i-1]['center']+openings[i-1]['half_width'])/2,5)
        o['partition_right']=26.537 if i==len(openings)-1 else round((b+openings[i+1]['center']-openings[i+1]['half_width'])/2,5)
    return dict(wall_span_m=[0.,26.537],front_Y_m=0.,wall_back_Y_m=.34,wall_storey_Z_m=[4.57,8.59],
         source='brick-arcade-source-pixels.json',camera='street-front-cameras.json',
         original_video='https://www.bilibili.com/video/BV1MeFVzqEiJ/?t=4.28',
         limits='The scale uses the historic footprint edge. Springings and clear widths use the 2026 video plus three street perspectives. Glazing recesses are shallow at openings 4 and 5, and near 0.21 m at opening 6 in both cross-view checks. Other recesses, arch depth, the individual mortar joints, obscured lower sills and door threshold are estimates.',
         openings=openings)


if __name__=='__main__':
    (HERE/'brick-arcade-sections.json').write_text(json.dumps(measure(),ensure_ascii=False,indent=2)+'\n')
