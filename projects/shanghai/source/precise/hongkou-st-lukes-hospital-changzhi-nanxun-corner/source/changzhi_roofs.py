"""Model the three documented tiled roof tracts above the two street wings."""
import json
from math import hypot
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely.ops import triangulate
from changzhi_finish import TILE,TILE_TEXTURE
from changzhi_roof_crown import gable_street_span
RIDGE='Changzhi | weathered clay ridge caps'
EDGE='Changzhi | shadow below the tiled eaves'
PALETTE={
    TILE:dict(color=[1.,1.,1.],texture=str(TILE_TEXTURE),roughness=.94),
    RIDGE:dict(color=[.238,.094,.065],roughness=.89),
    EDGE:dict(color=[.217,.175,.145],roughness=.96)}
BASE=Path(__file__).resolve().parents[1]/'measurements'
def point(face,s,depth=0.):
    a=np.array(face['a']);return a+(np.array(face['b'])-a)*s/face['length']+np.array(face['out'])*depth

def roof_panel(b,verts,label):
    """Triangulate in plan and give each individual roof facet a closed edge and underside."""
    xyz=[tuple(map(float,v)) for v in verts]
    poly=orient(Polygon([v[:2] for v in xyz]),sign=1.)
    if poly.is_empty or poly.area<1e-6:return
    lookup={v[:2]:v[2] for v in xyz};ordered=list(poly.exterior.coords)[:-1]
    vertices=[(x,y,lookup[(x,y)]) for x,y in ordered]
    n=len(vertices);vertices += [(x,y,z-.10)for x,y,z in vertices]
    ids={xy:i for i,xy in enumerate(ordered)}
    faces=[];area=0.
    for tr in triangulate(poly):
        if not poly.covers(tr):continue
        ring=list(orient(tr,sign=1.).exterior.coords)[:3];indices=[ids[xy]for xy in ring]
        faces.extend([tuple(indices),tuple(i+n for i in reversed(indices))]);area+=tr.area
    if abs(area-poly.area)>.001:raise ValueError('Roof triangulation lost area: '+label)
    faces.extend([(i+n,(i+1)%n+n,(i+1)%n,i)for i in range(n)])
    b.add(vertices,faces,TILE,'Roof | '+label)

def with_z(points,z):return [(*pt,z)for pt in points]

def add_roof(b,lod,layout):
    trace=json.loads((BASE/'three-edition-roof-traces.json').read_bytes())['local_roof_polylines']
    trace={key:value['median_xy_m'] for key,value in trace.items()}
    faces=layout['faces'];front=faces[0];north=faces[-1]
    sp=gable_street_span(layout);geometry=json.loads((BASE/'roof-crown-geometry.json').read_bytes())
    e_s=layout['eaves']['changzhi']-.31;e_n=layout['eaves']['nanxun']-.32
    outer=trace['outer_north'];seam=trace['inner_wing_seam'];north_ridge=list(reversed(trace['ridge_north']))
    n0=(seam[-1][0],.17);nf=point(north,north['length']-.10,-.15)
    efront=with_z([n0,nf],e_n);back=with_z(outer[1:],e_n-.22);inner=with_z(seam,e_n-.2)
    r=with_z(north_ridge,e_n+1.05)
    roof_panel(b,[efront[0],efront[1],r[-1],r[1],r[0]],'Nanxun street pitch')
    roof_panel(b,[efront[1],*back[:4],r[-1]],'Nanxun polygonal end hip')
    roof_panel(b,[*back[3:],inner[0],r[0],r[1],r[-1]],'Nanxun court pitch')
    roof_panel(b,[*inner,efront[0],r[0]],'Nanxun inner hip')
    b.tube(r,.111,RIDGE,9 if lod else 16,'Roof | Nanxun ridge capping')
    for i,v in enumerate([efront[1],back[3],inner[0],efront[0]]):
        b.tube([v,r[-1] if i<2 else r[0]],.065,RIDGE,7 if lod else 12,'Roof | Nanxun hip roll '+str(i+1))
    # Southwest wing. The measured rear eave belongs to the tall street roof;
    # the lower adjoining roof on the other side of this edge is kept separate.
    front0=point(front,.05,-.13);front1=point(front,sp['s0'],-.13)
    join=trace['return_join'];rear=trace['long_wing_back_edge']
    rear0=np.array(rear[-1]);rear1=np.array(join[0]);frontline=with_z([front0,front1],e_s)
    backline=with_z([rear1,*rear],e_s-.22)
    # Three dates independently show the break of pitch along the long wing.
    # Local XY only constrains the spine; its rise is estimated.
    ridge_xy=[(-5.74,20.82),(-4.33,17.49),(-2.42,13.81),(-.92,10.44)]
    southridge=with_z(ridge_xy,e_s+.82)
    roof_panel(b,[*frontline,*reversed(southridge)],'Changzhi street pitch')
    roof_panel(b,[*backline,*southridge],'Changzhi back pitch')
    roof_panel(b,[frontline[0],backline[-1],southridge[0]],'Changzhi southwest hip')
    roof_panel(b,[frontline[1],backline[0],southridge[-1]],'Changzhi inner hip')
    b.tube(southridge,.10,RIDGE,9 if lod else 16,'Roof | Changzhi ridge')
    # Behind the triangular front its ridge runs across the street wall.
    # The opening through the pediment remains clear below the two inclined slopes.
    tri=geometry['gable']['triangle']
    front_g=[(*point(front,s,-.16),z-.16)for s,z in tri]
    edge0=np.array(join[0]);shift=edge0-np.array(front_g[0][:2])
    rear_g=[(*(np.array(v[:2])+shift),v[2]-.1)for v in front_g]
    roof_panel(b,[front_g[0],front_g[1],rear_g[1],rear_g[0]],'Gable southwest slope')
    roof_panel(b,[front_g[1],front_g[2],rear_g[2],rear_g[1]],'Gable corner slope')
    b.tube([front_g[1],rear_g[1]],.091,RIDGE,8 if lod else 14,'Roof | Gable ridge')
    # The photographed roof changes direction between the two wings. Clip this lower
    # connecting field to their outlines and to the eight faces of the raised lantern.
    north_plan=Polygon([n0,nf,*outer[1:],*seam])
    south_plan=Polygon([front0,front1,rear1,*rear]);gable_plan=Polygon([*(v[:2]for v in front_g),*(v[:2]for v in reversed(rear_g))])
    footprint=Polygon([f['a']for f in faces]+[faces[-1]['b']]+layout['back_points'])
    tower=geometry['lantern'];cap=Polygon(tower['face_vertices']+tower['roofward_vertices']) if 'roofward_vertices' in tower else None
    connector=footprint.buffer(-.17,join_style='mitre').difference(north_plan.union(south_plan).union(gable_plan))
    if cap is not None:connector=connector.difference(cap.buffer(-.15))
    for i,tr in enumerate(triangulate(connector)):
        if connector.covers(tr) and tr.area>.013:
            xy=list(tr.exterior.coords)[:3]
            roof_panel(b,[(x,y,14.34+.10*y) for x,y in xy],'Recessed connecting plane '+str(i+1))
