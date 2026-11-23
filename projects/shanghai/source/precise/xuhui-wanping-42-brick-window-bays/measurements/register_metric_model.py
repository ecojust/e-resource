"""Place the 2019 facade in the independently surveyed 2015/2020 street frame."""
import argparse
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
BOWS=('south_outer','south_inner','north_inner','north_outer')
LEFT,RIGHT=-11.46,11.35

def anchors():
    points={}
    for side,x in [('south',LEFT),('north',RIGHT)]:
        points[side+'_corner_wall_pavement']=[x,0.,0.]
        points[side+'_corner_upper_edge_white_belt']=[x,-.09,16.75-674/50+.49]
        points[side+'_red_to_yellow_flat_junction']=[x,0.,6.15]
    points['entrance_actual_door_upper_edge_center']=[(582+642)/100-12.2,0.,16.75-726/50]
    for label,(yellow_column,red_x,depth) in zip(BOWS,[(229.5,-7.605,.57),(435,-3.755,.60),(789.5,3.205,.62),(1037,8.56,.65)]):
        points[label+'_bow_axis_yellow_window_sill']=[yellow_column/50-12.2,0,16.75-642/50]
        points[label+'_bow_axis_red_window_sill']=[red_x,-depth,7.31]
    return points

def solve(solution):
    measured={name:np.array(v['enu_m']) for name,v in solution['points'].items()}
    model=anchors()
    unit=measured['north_corner_wall_pavement'][:2]-measured['south_corner_wall_pavement'][:2]
    unit/=np.linalg.norm(unit)
    inward=np.array([-unit[1],unit[0]])
    basis=np.column_stack([unit,inward])
    widths=[];heights=[]
    for label in ('corner_wall_pavement','corner_upper_edge_white_belt','red_to_yellow_flat_junction'):
        if 'north_'+label not in measured or 'south_'+label not in measured:continue
        delta=measured['north_'+label]-measured['south_'+label]
        widths.append(float(delta[:2]@unit))
    for side in ['north','south']:
        if side+'_red_to_yellow_flat_junction' in measured:
            heights.append(float((measured[side+'_red_to_yellow_flat_junction']-measured[side+'_corner_wall_pavement'])[2]))
    sx=float(np.median(widths)/(RIGHT-LEFT))
    if heights:
        sz=float(np.mean(heights)/6.15)
    else:
        sz=float(np.mean([measured[side+'_corner_upper_edge_white_belt'][2]-measured[side+'_corner_wall_pavement'][2] for side in ['south','north']])/model['north_corner_upper_edge_white_belt'][2])
    scales=np.array([sx,sx,sz])
    cap=[f'{side}_corner_wall_pavement' for side in ['south','north']]
    origin=np.mean([measured[tag]-np.r_[basis@(np.array(model[tag])[:2]*scales[:2]),0.] for tag in cap],axis=0)
    rows=[]
    for tag,v in model.items():
        if tag not in measured:continue
        p=np.array(v)*scales
        residual=origin+np.r_[basis@p[:2],p[2]]-measured[tag]
        rows.append(dict(point=tag,author_xyz=v,scaled_xyz=p.tolist(),observed_ENU_m=measured[tag].tolist(),
                         model_minus_street_ENU_m=residual.tolist()))
    held=[r for r in rows if 'bow_axis' in r['point'] or 'door_upper' in r['point']]
    return dict(model_scales_xyz=scales.tolist(),baseline_widths_south_to_north_m=widths,
                corner_red_yellow_elevations_m=heights,origin_ENU_m=origin.tolist(),
                x_axis_bearing_deg=float(np.degrees(np.arctan2(*unit))%360),
                median_withheld_horizontal_m=float(np.median([np.linalg.norm(r['model_minus_street_ENU_m'][:2]) for r in held])),
                median_withheld_height_m=float(np.median([abs(r['model_minus_street_ENU_m'][2]) for r in held])),points=rows)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);a=p.parse_args()
    source=json.loads((HERE/'front-street-intersections.json').read_bytes())
    j=dict(method='Use the median of three independently triangulated front widths. Determine the vertical scale from the height of the red-to-ochre joint above the pavement at both ends. Depth takes the horizontal scale. Eight sash axes and the door head remain independent of these scale controls.',
           author_frame='2019 photo rectification built with a 22 m initial corner prior. Final authored solid extends X −11.46..11.35. Model heights start at the facade pavement datum.',
           wgs84_reference=source['basis_wgs84'],solutions={k:solve(v) for k,v in source['solutions'].items()})
    a.output.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n')
    for k,v in j['solutions'].items():print(k,v['model_scales_xyz'],v['median_withheld_horizontal_m'],v['median_withheld_height_m'])
