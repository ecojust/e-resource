"""Camera poses and editable UV coordinates of the garden tower."""
import json
import math
from pathlib import Path

SOURCE=Path(__file__).resolve().parent
DIMS=json.loads((SOURCE.parent/'measurements/two-photo-fit.json').read_bytes())
MAIN='01 Garden tower and first veranda bay'
CAMERAS={
    MAIN:((15,-32,14),(1.45,2.55,8.70),25.4),
    '02 Street corner and three windows':((-15,-23,10),(0,1.1,8.4),20.8),
    '03 Festoon and recessed sash':((.9,-9.1,6.2),(0,-.03,5.9),4.3),
    '04 First bay and two clear passages':((11,-13,6.8),(4.55,4.25,4.8),12.6),
    '05 Upper iron rail and stone balusters':((10.5,-10,10.4),(4.42,3.7,7.4),7.2),
    '06 Red dome and finial':((8.3,-13,16.9),(0,2.35,15.0),9.6),
}
MATERIALS={'Warm ivory ashlar':('garden-lime-plaster.png','Restored garden plaster'),
           'Weathered red metal panels':('copper-panel-courses.png','Hand-seamed copper panels')}
UV_NAME='Garden surface coordinates'


def uv_for_face(material,vertices):
    if material=='Warm ivory ashlar':
        return [(.36+.034*x+.021*y,(z+.19)/15) for x,y,z in vertices]
    if material!='Weathered red metal panels':
        raise ValueError(material)
    levels=DIMS['fitted_elevations_m']
    base=levels['parapet']-.09; rise=levels['finial']-base-.65
    coords=[]
    for x,y,z in vertices:
        u=(math.atan2(y-DIMS['dome_axis_setback_m'],x)/math.tau)%1
        if u>1-1e-6:u=0.0
        height_fraction=min(1,max(0,(z-base)/rise))
        v=1.0 if height_fraction>1-1e-6 else (2/math.pi)*math.asin(height_fraction)
        coords.append((u,v))
    if max(u for u,_ in coords)-min(u for u,_ in coords)>.5:
        coords=[(u+1 if u<.5 else u,v)for u,v in coords]
    return coords
