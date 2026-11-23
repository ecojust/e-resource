"""Single-image, independent local frame of the open side door photographed by Ctny."""
import json
import hashlib
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from fit_vestibule import matrix, project, plane_point

HERE = Path(__file__).resolve().parent
FILENAME = 'side-entrance-photo.json'
SIZE = [1600, 1067]
URL = "https://commons.wikimedia.org/wiki/File:Shanghai_No._3_Girls%27_High_School,_Five-Four_lecture_building_side_entrance.jpg"
ORIGINAL = '7a4bc18b7fede6599b227f44df953c324c2741f22a004b413d2c0a437c76d4ac'
DOOR_WIDTH = 1.82
# Coordinates below were read on an 840 x 560 reduction. Published tables are native.
def px(point):
    return np.array([(point[0]+.5)*SIZE[0]/840-.5, (point[1]+.5)*SIZE[1]/560-.5])

JAMBS = [(137.5,230.1),(321.7,233.3),(324.1,439.8),(140.0,455.7)]
HORIZONTAL = [((463.8,150.4),(837.7,172.3)), ((465.3,214.0),(837.5,228.8)),
              ((137.5,230.1),(321.7,233.3)), ((140.0,455.7),(324.1,439.8))]
VERTICAL = [((321.7,233.3),(324.1,439.8)),((390.5,108.0),(394.6,392.0)),
            ((672.3,174.7),(678.7,340.0))]
OBS = dict(
 arch_open=[(135,455.7),(131,205),(133,193),(141,185),(154,181),(205,177),(233,171),(255,178),(302,186),(315,192),(320,199),(323.8,440)],
 arch_wood_outer=[(127,457),(125,201),(126,188),(131,180),(143,174),(190,169),(212,166),(233,160),(253,167),(299,176),(318,183),(326,191),(328,200),(330,440)],
 arch_stone_outer=[(105,458),(101,201),(105,182),(115,168),(128,160),(149,155),(198,150),(232,144),(258,152),(305,162),(325,173),(337,187),(340,199),(341,441)],
 left_leaf=[(137.5,230.1),(103.4,224.5),(102.2,483.7),(139.5,455.6)],
 right_leaf=[(321.8,233.5),(365.1,228.1),(369.7,463.7),(324.3,440.1)],
 awning=[(77,39),(390,72),(431,103),(52,68)],
 arm=[(386,74),(430,104)],pipe=[(392.1,111),(396.3,390.5)],
 window1=[(464.8,154.9),(590.4,162.0),(593.0,346),(467.3,349.8)],
 window2=[(622.4,163.4),(728.2,169.4),(731.2,340.5),(625.4,343.7)],
 window3=[(755.1,170.5),(838.8,175.3),(838.8,338.0),(758.6,340.0)],
 bottom_step=[(94.5,545.8),(407.6,522.4)],
 transverse_stone=[(625,219.1),(729.1,222.7)],
 stair_front=[(96.3,492.9),(377.3,466.8),(387.8,485.8),(397.2,509.6),(404.2,529.4)],
 right_knob=[(366.7,354.4)],
)
def fit():
    # SONY ILCE-5100, 21 mm lens and nominal 23.5 mm active sensor width.
    nominal_f = SIZE[0]*21/23.5
    def corners(p):
        h=p[7]
        return [[-DOOR_WIDTH/2,0,h],[DOOR_WIDTH/2,0,h],[DOOR_WIDTH/2,0,0],[-DOOR_WIDTH/2,0,0]]
    def residual(p):
        m=matrix(p); errors=[]
        for xyz,uv in zip(corners(p),JAMBS):
            errors.extend(project(m,xyz)-px(uv))
        for lines,axis in [(HORIZONTAL,0),(VERTICAL,2)]:
            vp=m[:,axis]
            for a,b in lines:
                line=np.cross([*px(a),1],vp)
                errors.append((line@[*px(b),1])/np.linalg.norm(line[:2]))
        errors.extend([(p[6]-nominal_f)/22,(p[7]-2.1)/.22])
        return errors
    sol=least_squares(residual,[-2.5,-6.8,1.1,.64,0,0,nominal_f,2.13],
        bounds=([-12,-20,-1,-1,-.45,-.2,1100,1.65],[7,-2,3,1.3,.5,.2,1800,2.75]),
        x_scale='jac', loss='soft_l1', f_scale=3, max_nfev=1300)
    m=matrix(sol.x)
    target=lambda p:[round(float(n),3) for n in p]
    return dict(photo=URL,photographer='Ctny',date='2017-08-21',license='CC BY-SA 4.0',
        original_sha256=ORIGINAL,dimensions=SIZE,local_frame='Threshold midpoint is (0,0,0); +X right along this wall, +Y through the door, +Z up. No azimuth or link to the lawn or indoor model measured.',
        metric_basis='1.82 m clear width is a conditional scale (approximately +/-0.20 m). No surveyed building dimension or second matched exterior photograph has been located.',
        lens=dict(camera='Sony ILCE-5100',physical_mm=21,nominal_sensor_width_mm=23.5,nominal_focal_px=nominal_f),
        camera=sol.x.tolist(), projection=m.tolist(), fitted_clear_height_m=float(sol.x[7]),
        jambs=[dict(uv=target(px(uv)),local=xyz,residual_px=round(float(np.linalg.norm(project(m,xyz)-px(uv))),2)) for xyz,uv in zip(corners(sol.x),JAMBS)],
        observed_alignment_lines={k:[[target(px(a)),target(px(b))] for a,b in v] for k,v in [('wall_horizontal',HORIZONTAL),('wall_vertical',VERTICAL)]},
        window_mullion_edges_native_at_row_368=[[986,1014],[1265,1292],[1505,1530]],
        outlines={key:[target(px(point)) for point in value] for key,value in OBS.items()},
        interpretation=['Stone-cased cross windows to the right: two full pairs and the visible beginning of the third. Sills behind planting are approximate.',
                        'Both timber leaves stand open; narrow recessed panels and projecting right-hand knob are legible. No interior room or fittings reconstructed.',
                        'Pale projecting awning with rolled front edge; material type and hidden brackets not established. Four stair nosings (the lowest partly cropped).'])
if __name__=='__main__':
    data=fit(); (HERE/FILENAME).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(data['camera'],[p['residual_px'] for p in data['jambs']])
