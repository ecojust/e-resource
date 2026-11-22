"""Compare the observed clay-tile nose with the reconstructed eastern and western roof edges."""
from pathlib import Path
import json
import sys
import numpy as np
M=Path(__file__).resolve().parent
sys.path.insert(0,str(M.parent/'source'))
from xiangshan_photo_plane import on_wall,pixel
# Native 2015 frame pixels; the tree covers the western middle portion in one view.
west={'roof-15-west':[(280,401),(340,390),(440,367),(500,353),(580,333)],
      'alignment-roof-0':[(827,423),(843,426),(859,428)]}
east_rect={'roof-15-west':[(650,289)],'alignment-roof-0':[(390,281),(580,284),(650,284)]}
east={view:[pixel((u/70-15,0,13-v/70),view) for u,v in values] for view,values in east_rect.items()}
rows={}
for label,views,fitted in [('eastern',east,8.615),('western',west,8.05)]:
    records=[]
    for camera,uvs in views.items():
        for u,v in uvs:
            xyz=on_wall(u,v,y=-.56,camera=camera)
            records.append(dict(view=camera,pixel=[round(u,3),round(v,3)],xyz_at_estimated_eave_y_m=xyz))
    heights=[r['xyz_at_estimated_eave_y_m'][2] for r in records]
    rows[label]={'samples':records,'observed_elevation_range_m':[min(heights),max(heights)],
                 'assumed_front_y_m':-.56,'fitted_tile_edge_z_m':fitted,'median_difference_m':float(np.median(heights)-fitted)}
out={'method':'Independent rays through the two December 2015 camera matrices. The western tile nose runs lower than the eastern one. Its absolute altitude and the eave projection covary. At Y = -0.75 m the western edge is about Z = 7.94 m instead of 8.05 m. The model uses Y = -0.56 m. The lower pitch is observed at the base of the dormers. The hidden upper continuation of both slopes is estimated.','measurements':rows}
(M/'two-main-eaves.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
for label,r in rows.items():print(label,r['observed_elevation_range_m'],r['median_difference_m'])
