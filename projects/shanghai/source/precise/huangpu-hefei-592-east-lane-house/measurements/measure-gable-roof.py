"""Reconstruct the two rake lines from the 2015 winter west street panorama."""
from pathlib import Path
import json,sys
import numpy as np
m=Path(__file__).resolve().parent
sys.path.insert(0,str(m.parent/'source'))
from hefei_photo_plane import on_side
observations={
    'street_slope':[(307,146),(316,150),(325,153),(336,160),(346,164),(356,168)],
    'lane_slope':[(132,185),(140,175),(148,163),(160,146),(166,137)]}
collected={}
for name,points in observations.items():
    yz=np.array([on_side(u,v,0.,'2015_west')[1:] for u,v in points])
    slope,intercept=np.polyfit(yz[:,0],yz[:,1],1)
    collected[name]=dict(source_uv=points,wall_yz_m=yz.round(5).tolist(),slope=float(slope),intercept_m=float(intercept),
        rms_vertical_m=float(np.std(yz[:,1]-(slope*yz[:,0]+intercept))))
a,b=collected.values()
y=(b['intercept_m']-a['intercept_m'])/(a['slope']-b['slope'])
r=dict(order=552,camera='2015_west',street_panorama_id='09000300001502091227113707B',image_size=[980,650],
       planes='The interior edge where each sloping eaves return meets the rendered wall is referred to the X=0 gable.',
       axes='X east into the house. Y north into the lane. Z up.',
       profiles=collected,inferred_ridge_yz_m=[float(y),float(a['slope']*y+a['intercept_m'])],
       wall_start_y_m=0.,wall_end_y_m=9.80,roof_strip_x_m=[-.29,1.12],
       unknowns='A tree covers the ridge junction. Its height and position are obtained by extending the two visible rake lines. The inland cut is the last photographed strip of gable, and the width of the roof sample eastwards is a display limit. The remaining roof and the dormers above other street numbers are excluded.',
       material='Lime-painted roughcast, grey plinth, dark timber underside and weathered red clay roof edging; the tile module and concealed thickness are approximate.')
(m/'gable-roof-and-visible-extent.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
