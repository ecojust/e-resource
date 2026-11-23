"""Relate the outer wing's measured eave to three independent readings of its roof silhouette."""
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
stations = json.loads((HERE/'lawn-return-stations.json').read_text())['stations']
historic = json.loads((HERE/'historic-lawn-roof-readings.json').read_text())
# These are original pixels. The oblique panorama has a small local stitching error.
ridges = {'ctny-front': [[1308,469],[1375,455]],
          'ctny-panorama': [[858,169.5],[1030,148.5]],
          'historic-lawn': historic['roof_ridge']}
panorama_cheeks = [[887.5,201],[937,196],[971,193],[1005.5,190],[1042,187],[1078,185]]

def intersect_x(station, uv, x):
    c = np.asarray(station['C'])
    direction = np.asarray(station['R']).T @ np.linalg.solve(station['K'],[*uv,1.0])
    return c + direction*(x-c[0])/direction[0]

def calibrate():
    # Half the mapped 15.30 m wing depth gives a conditional ridge datum.
    x_ridge = 36.55 + 15.30/2
    x_cheek = 38.08
    lines = {}
    for key,uv in ridges.items():
        xyz = [intersect_x(stations[key], point, x_ridge).tolist() for point in uv]
        lines[key] = {'original_pixels':uv,'intersections_xyz_m':xyz,'mean_height_m':np.mean(xyz,axis=0)[2]}
    z_ridge = np.median([line['mean_height_m'] for line in lines.values()])
    centers = [3.78-intersect_x(stations['ctny-panorama'],pt,x_cheek)[1] for pt in panorama_cheeks]
    historic_spans = []
    for i, item in enumerate(historic['dormers']):
        left,right = (intersect_x(stations['historic-lawn'],item[k],x_cheek)
                      for k in ('cheek_lower_left','cheek_lower_right'))
        centre = 3.78 - (left[1]+right[1])/2
        historic_spans.append(dict(axis=i+1,center_u=centre,width_m=abs(right[1]-left[1]),
                                   lower_z_m=(left[2]+right[2])/2))
        centers[i] = (centre+centers[i])/2
    return dict(eave_xyz_datum=[36.49,3.46,13.57],roof_ridge_x_m=x_ridge,roof_ridge_z_m=round(z_ridge,3),
                historic_centreline_at_selected_x_m=historic_spans, panorama_cheek_centers_source_pixels=panorama_cheeks,
                front_x_m=x_cheek, centers_u_m=np.round(centers,3).tolist(),three_station_roof_readings=lines,
                assumptions='The two mapped side walls are 15.3 m apart. Ridge setback uses half this width; a metre of plan shift changes inferred crest height by roughly 0.25–0.33 m. The photographed field is closed at this crest, with a plain section behind. The sixth dormer is screened by trees.')
if __name__=='__main__':
    p=HERE/'lawn-roof-parameters.json';p.write_text(json.dumps(calibrate(),ensure_ascii=False,indent=2)+'\n')
