"""Cast original photograph controls and eight measured character strokes into an actual GLB."""
from pathlib import Path
import argparse,hashlib,json,runpy
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import polylabel

HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
# Source pixels, measured separately from the column endpoints in the camera fit.
OBS={
'commons-2006':[('left white panel',448,633,'wall'),('right white panel',1164,650,'wall'),('inner left post',672,704,'wood'),('inner right post',973,684,'wood'),('central black plaque',752,471,'board'),('inside central portal',786,611,'clear'),('first step',866,935,'stone'),('central circular medallion',826,780,'leaf'),('left pale ridge ornament',488,187,'ornament'),('centre covered roof',829,304,'clay')],
'school-front':[('left white wall',103,150,'wall'),('right white wall',318,169,'wall'),('right inner post',260,154,'wood'),('left inner post',168,145,'wood'),('clear space above leaves',215,143,'clear'),('central tread',217,230,'stone'),('central roundel',214,184,'leaf'),('covered roof',212,62,'clay'),('ridge ornament',123,37,'ornament')],
'school-postcard':[('right white wall',354,162,'wall'),('lower left white wall',106,200,'wall'),('outer right post',321,179,'wood'),('open central portal',217,160,'clear'),('dark plaque',190,129,'board'),('roof field',193,86,'clay')],
'editorial-reverse':[('right white render',703,388,'wall'),('left white render',155,369,'wall'),('left inner timber post',313,385,'wood'),('right inner timber post',514,384,'wood'),('central clear space',411,326,'clear'),('roundel at the meeting',414,442,'leaf'),('stone at lower step',399,538,'stone'),('grey barrel tiles',404,164,'clay'),('dark inscription surround',330,255,'board'),('left glazed ornament',208,101,'ornament')]}
CLASSES={'wood':['weathered cypress','dark eave timber'],'wall':['white lime render'],'board':['black lacquer'],'ornament':['pale glazed ridge ornaments'],'leaf':['reddish wooden gate','warm bronze relief','dark eave timber'],'stone':['light edge stone','cut grey stone'],'clay':['dark grey clay','grey ridge tile'],'gold':['gold brush lettering'],'clear':[]}
def evaluate(mesh):
    st=json.loads((HERE/'four-gate-stations.json').read_bytes())['stations']
    inscriptions=json.loads((HERE/'inscription-contours.json').read_bytes())['faces']
    points={k:list(v)for k,v in OBS.items()}
    for side,k in [('front','commons-2006'),('reverse','editorial-reverse')]:
        p=inscriptions[side];inverse=np.linalg.inv(np.array(p['native_to_unit_board']))
        for glyph in p['viewer_left_to_right']:
            outline=max([Polygon(q['exterior'],q['holes'])for q in glyph['polygons']],key=lambda q:q.area)
            xy=polylabel(outline,tolerance=.0003);v=inverse@[xy.x,xy.y,1]
            points[k].append((glyph['character']+' stroke',*list(v[:2]/v[2]),'gold'))
    scene=runpy.run_path(str(HELPER))['SerialScene'](mesh);report={}
    delta=sorted([(x,y)for x in range(-5,6)for y in range(-5,6)if x*x+y*y<=25],key=lambda t:t[0]**2+t[1]**2)
    for key,obs in points.items():
        s=st[key];eye=np.array(s['C']);inv=np.array(s['R']).T@np.linalg.inv(s['K']);rows=[]
        for name,u,v,expect in obs:
            first=None;offset=None
            for dx,dy in delta:
                r=scene.ray(eye,inv@[u+dx,v+dy,1.],28)
                if (dx,dy)==(0,0):first=r
                if (expect=='clear' and r is None) or (r and any(r['material'].endswith(t)for t in CLASSES[expect])):
                    offset=[dx,dy];break
            rows.append(dict(label=name,native=[round(u,2),round(v,2)],expect=expect,first_hit=first,nearest_in_5px=offset))
        report[key]=dict(total=len(rows),direct=sum(x['nearest_in_5px']==[0,0]for x in rows),within_5=sum(x['nearest_in_5px']is not None for x in rows),points=rows)
    return dict(mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),stations=report,method='Open-space probes require an unobstructed ray through the complete mesh. A stroke uses the most interior point of its strongest recorded outline in normalized board space, reversed to its original native photo. Stroke controls share the planimetric outline data; they are not independent source authentication. Spatial material hits use the absolute photo registration.')
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();d=evaluate(a.mesh);a.out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print({k:(v['direct'],v['within_5'],v['total'])for k,v in d['stations'].items()})
