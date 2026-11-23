"""The east return and its three small openings, observed from both eastern street stations."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
from photo_architecture import Facade
from flat_windows import add_window
from house_finishes import WALL,GROUND,SILL,STEEL

HERE=Path(__file__).resolve().parent.parent/'measurements'
def data():
    return json.loads((HERE/'eastern-window-planes.json').read_text())['eastern_roof_and_windows']
def point_at_x(p,q,x):
    return p+(q-p)*(x-p[0])/(q[0]-p[0])
def east_corner(info):
    four=json.loads((HERE/'eastern-roof-four-stations.json').read_text())
    corner=np.array(four['all']['xyz'])
    roof=info['two_station_roof']
    height=roof['roof_rail_corner']['free_xyz'][2]-roof['roof_solid_corner']['free_xyz'][2]
    return corner,corner+np.array([0.,0.,height])
def ray(info,key,uv):
    c=info['east_cameras'][key]
    return np.array(c['C']),np.array(c['R']).T@np.linalg.solve(c['K'],[*uv,1.])
def side_measurements():
    info=data();measure=json.loads((HERE/'east-side-apertures.json').read_text())
    tip,rail=east_corner(info);ends=[]
    for k,uv in measure['far_roof_cap'].items():
        c,d=ray(info,k,uv);ends.append(c+d*(tip[2]-c[2])/d[2])
    far=np.mean(ends,axis=0)
    tangent=(far[:2]-tip[:2]);tangent/=np.linalg.norm(tangent)
    normal=np.array([tangent[1],-tangent[0],0.])
    mid=(tip[:2]+far[:2])/2
    apertures={}
    for key,stations in measure['side_windows'].items():
        polygons=[]
        for station,quad in stations.items():
            if station not in info['east_cameras']:continue
            hits=[]
            for uv in quad:
                c,d=ray(info,station,uv)
                p=c+d*(normal@(tip-c))/(normal@d)
                hits.append([(p[:2]-mid)@tangent,p[2]])
            polygons.append(hits)
        pts=np.mean(polygons,axis=0)
        apertures[key]=box(np.mean(pts[[0,3],0]),np.mean(pts[[2,3],1]),np.mean(pts[[1,2],0]),np.mean(pts[[0,1],1]))
    return tip,far,rail,apertures
def turn_curve(bank_left,bank_right,tip,far,samples):
    tangent=bank_right-bank_left
    tangent=tangent/np.linalg.norm(tangent)
    side=far[:2]-tip[:2]
    side=side/np.linalg.norm(side)
    along,_=np.linalg.solve(np.column_stack([tangent,-side]),tip[:2]-bank_left)
    virtual=bank_left+tangent*along
    setback=np.linalg.norm(tip[:2]-virtual)
    start=virtual-tangent*setback
    # The photographed outline rounds into the east wall. The last tangent
    # contact is held at the measured four-ray corner, with two horizontal tangents.
    return [(1-t)**2*start+2*t*(1-t)*virtual+t*t*tip[:2] for t in np.linspace(0,1,samples)]

def round_skin(b,path,z0,z1,material,label):
    xy=np.asarray(path)
    line=np.gradient(xy,axis=0)
    line/=np.linalg.norm(line,axis=1)[:,None]
    inward=np.column_stack((-line[:,1],line[:,0]))
    outline=Polygon(np.vstack([xy,(xy+.21*inward)[::-1]]))
    b.plan_prism(outline,z0,z1,material,label)

def add_east_face(b,lod):
    tip,far,rail,windows=side_measurements()
    info=data();xyz=info['geometry_on_retained_eight_station_system']
    for floor,z0,z1,material in [('1',0.,3.7,GROUND),('2',3.7,tip[2],WALL)]:
        path=turn_curve(np.array(xyz['E'+floor+'BL'][:2]),np.array(xyz['E'+floor+'BR'][:2]),tip,far,8 if lod else 20)
        round_skin(b,path,z0,z1,material,'280-2 east / rounded transition to end wall')
        if floor=='2':
            round_skin(b,path,tip[2],tip[2]+.046,SILL,'280-2 east / rounded cap on parapet')
            for offset in (.47*(rail[2]-tip[2]),rail[2]-tip[2]):
                b.tube([(*v,tip[2]+offset) for v in path],.013,STEEL,6 if lod else 9,'280-2 east / curved corner rail')
    surf=Facade(b,tip[:2],far[:2],'280-2 eastern wall')
    holes=unary_union(list(windows.values()))
    lo,hi=-surf.length/2,surf.length/2
    for z0,z1,mat in [(0.,3.7,GROUND),(3.7,tip[2],WALL)]:
        surf.prism(box(lo,z0,hi,z1).difference(holes),-.21,0,mat,'east wall facing adjoining plot')
    surf.prism(box(lo,tip[2]-.025,hi,tip[2]+.045),-.22,.030,SILL,'edge of east parapet')
    for label,code in [('top','S5'),('middle','S4'),('lower','S3')]:
        add_window(surf,windows[label],'east side',code,lod)
    # Two thin horizontal rails and their returning corner are visible over the roof.
    dz=rail[2]-tip[2]
    for offset in [.47*dz,dz]:
        b.tube([surf.point(lo,tip[2]+offset,-.12),surf.point(hi,tip[2]+offset,-.12)],.014,STEEL,
               6 if lod else 9,'280-2 east / roof rail')
    for u in np.linspace(lo,hi,int(np.ceil(surf.length))+1):
        b.tube([surf.point(u,tip[2]+.04,-.12),surf.point(u,rail[2]+.012,-.12)],.014,STEEL,
               6 if lod else 9,'280-2 east / upright in roof rail')
