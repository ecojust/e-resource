"""Read Richardson Hall's lawn frontage in the published visitor-agency photograph."""
import json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
# The temple-like central opening is framed by three-window bays. The earlier Five-One hall is east of the lawn.
LOW,HIGH=17.,1134.
SPAN=58.78
GROUND=439.
SCALE=(HIGH-LOW)/SPAN
def x(px):return (px-(LOW+HIGH)/2)/SCALE
def z(py):return (GROUND-py)/SCALE
def rect(a,top,b,bottom):
    from shapely.geometry import box
    return box(x(a),z(bottom),x(b),z(top))
SASH_GROUPS=[
    [(51,87),(111,146)],
    [(199,235),(242,278),(285,322)],
    [(355,391),(399,435),(442,478)],
    [(518,554),(560,595),(602,637)],
    [(675,711),(718,754),(760,796)],
    [(832,869),(875,911),(917,953)],
    [(1004,1041),(1063,1099)]]
DORMERS=[268,320,372,423,527,576,625,727,778,830,881]
# Fit the optical depth from the 17.01-m return and the ridge row. Vertical lines are corrected in the publisher's canvas.
def matrix():
    focal=1685.;distance=focal/SCALE;eye=[0.,-distance,1.62]
    horizon=GROUND-1.62*SCALE
    m=np.array([[focal,(LOW+HIGH)/2,0.,(LOW+HIGH)/2*distance],
                [0.,horizon,-focal,GROUND*distance],[0.,1.,0.,distance]])
    return dict(frame=[1200,486],projection=m.tolist(),eye=eye,front_width_m=SPAN,front_ground_px=[LOW,HIGH,GROUND],original='https://www.meet-in-shanghai.net/cn/uploads/2025/06/12/1933037928873709569.jpg',current_footprint='w494669990 / city source 733; 58.78 m is the measured long edge and ground width is conditional on the façade occupying it. The 1200×486 frontal image is published with corrected verticals.',manual_pixels={'glazing_upper':[239,275],'glazing_middle':[307,345],'glazing_lower':[376,421],'sash_groups':SASH_GROUPS,'dormer_centres':DORMERS})
if __name__=='__main__':(HERE/'frontage-station.json').write_text(json.dumps(matrix(),ensure_ascii=False,indent=2)+'\n')
