"""The short, lower roof and brick piers visible between the two separate historic wings."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from court_frame import panel
from service_materials import TILE,BRICK,FRAME,DOOR,EDGE

HERE=Path(__file__).resolve().parent.parent/'measurements'
def add_link(b,frame,lod=False):
    picks=json.loads((HERE/'connecting-roof-readings.json').read_bytes())
    front=.43
    pitches=(frame.ridge-frame.eave)/(frame.depth/2)
    rows=[]
    for station in ('design','album'):
        cam=getattr(frame,station)
        ev=[cam.wall(p,front) for p in picks['eaves'][station]]
        rd=[cam.wall(p,front) for p in picks['ridge'][station]]
        rows.append((ev,rd))
    z0=np.mean([p[2] for ev,_ in rows for p in ev])
    ridge_at_front=np.mean([p[2] for _,rd in rows for p in rd])
    # The low ridge projects against a chimney of the main residence. Its actual
    # depth is estimated from the neighbouring roof pitch and the two elevations.
    back=front+(ridge_at_front-z0)/pitches
    def plane_z(y):return z0+(y-front)*pitches
    top=[np.mean([getattr(frame,station).wall(picks['ridge'][station][i],back) for station in ('design','album')],axis=0) for i in range(2)]
    e1,e2=(np.mean([v[0][i] for v in rows],axis=0)[0] for i in range(2))
    e1=min(frame.width-.07,e1)
    plan=Polygon([(e1,front),(e2,front),(top[1][0],back),(top[0][0],back)])
    b.prism(plan,-.135,0,lambda x,y,z:(x,y,plane_z(y)+z),TILE,'Eves link / lower tiled pitch')
    b.box([(e1+e2)/2,front+.022,z0-.065],[e2-e1,.092,.13],EDGE,label='Eves link / low eaves board')
    # Only the visibly open parts are cut. Interior fittings are concealed by shadow.
    plane=front+.23
    hollows=[]
    for rect in picks['dark_recesses_2014']:
        pts=np.array([frame.design.wall(uv,plane) for uv in rect])
        a=np.mean(pts[[0,3],0]);c=np.mean(pts[[1,2],0]);h=min(z0-.12,np.mean(pts[:2,2]))
        c=min(e2-.12,c)
        if c>a+.1:hollows.append(box(a,.13,c,h))
    wall=box(e1,0,e2,z0-.06).difference(unary_union(hollows))
    panel(b,wall,plane,plane+.20,BRICK,'brick bays under low linking roof')
    for rec in hollows:
        a,z,c,h=rec.bounds
        panel(b,rec,plane+.37,plane+.42,DOOR,'inside of shaded connecting bay')
        panel(b,box(a-.012,.10,c+.012,.19),plane-.027,plane+.18,FRAME,'base rail inside connecting bay')
