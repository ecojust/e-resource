"""Visible polygonal retaining kerbs alongside the curved garden stair."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from zhu_garden_materials import PLASTER, STONE, STONE_EDGE, paint

PANEL = 'Garden planter | clipped grey mineral inset'
EARTH = 'Garden planter | exposed soil'
PALETTE = {PANEL: paint((105,106,109), .92), EARTH: paint((91,72,48), .98)}
SURVEY = Path(__file__).resolve().parent.parent/'measurements/garden-planter-corners.json'


def sections(survey, side):
    info = survey['walls'][side]
    points = np.array([survey['corner_observations'][k]['used_xy'] for k in info['corners']])
    edges = np.diff(points, axis=0)
    lengths = np.linalg.norm(edges, axis=1)
    t = edges/lengths[:,None]
    left = np.column_stack((-t[:,1],t[:,0]))
    joins = [left[0]]
    for a,b in zip(left,left[1:]):
        joins.append((a+b)/(1+np.dot(a,b)))
    joins.append(left[-1])
    return points, np.array(joins), lengths


def plan_band(points, joins, front, back):
    return Polygon(np.vstack((points+front*joins, (points+back*joins)[::-1])))


def panel_polygon(center, width):
    x0,x1=center-width/2,center+width/2
    z0,z1=.032,.302
    cx=min(.051,width*.15)
    cz=.043
    return Polygon([(x0+cx,z0),(x1-cx,z0),(x1,z0+cz),(x1,z1-cz),
                    (x1-cx,z1),(x0+cx,z1),(x0,z1-cz),(x0,z0+cz)])


def add_planters(b,lod,layout):
    survey=json.loads(SURVEY.read_bytes())
    for side,info in survey['walls'].items():
        points,joins,lengths=sections(survey,side)
        label=f'Garden planter | {side}'
        thickness=survey['depth_m']
        b.plan_prism(plan_band(points,joins,.018,thickness),.002,.357,PLASTER,label+' wall core')
        for i,(row,length) in enumerate(zip(info['segments'],lengths)):
            p,q=points[i:i+2]; j,k=joins[i:i+2]
            def strip(u,z,d):
                f=u/length
                xy=(1-f)*(p-d*j)+f*(q-d*k)
                return float(xy[0]),float(xy[1]),z
            centers=np.array(row['center_fractions'])*length
            holes=[]
            for n,c in enumerate(centers):
                # Width is limited by both adjoining joints and the photographed end.
                spaces=[c-centers[n-1] if n else 2*c,
                        centers[n+1]-c if n+1<len(centers) else 2*(length-c)]
                width=min(.82*(length/len(centers)),.88*min(spaces))
                shape=panel_polygon(c,width)
                holes.append(shape)
                b.prism(shape,-.0175,-.006,strip,PANEL,label+f' {i+1}.{n+1} inset')
            facing=box(0,.002,length,.357).difference(unary_union(holes))
            b.prism(facing,-.018,0,strip,PLASTER,label+f' {i+1} clipped surrounds')
        for lo,hi,d0,d1,mat,title in [
            (.357,.383,-.018,thickness+.018,STONE_EDGE,'dark drip'),
            (.383,.410,-.031,thickness+.032,STONE,'coping lip'),
            (.410,.430,-.021,thickness+.021,STONE,'coping top'),
            (.011,.359,thickness+.003,thickness+survey['soil_strip_m'],EARTH,'visible soil')]:
            b.plan_prism(plan_band(points,joins,d0,d1),lo,hi,mat,label+' '+title)
