"""First visible surface at fixed source pixels and vertical roof/adjacent-building controls."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene
CLASSES={
    'open sky':[],
    'warm grey render':['lime render','shaded plaster panels','Crown | mineral','Crown | warm','Crown | cream'],
    'street windows':['Sashes |'],
    'pediment and lantern':['Crown |','Lantern','Roof crown','crown |','roof |','Roof |','Gable |'],
    'red pitched roof':['red brown roof tile','clay ridge caps'],
    'unmodelled low neighbour':[]}
# Measurements on the 835x900 working rendition of the Hongkou district photograph.
PIXELS={'open sky':[(96,170),(43,323),(673,96),(814,123)],
        'warm grey render':[(437,398),(436,472),(455,526),(440,340),(385,822),(465,810),(674,461),(763,542),(383,640),(500,535)],
        'street windows':[(440,615),(437,668),(518,614),(360,645),(373,426),(516,420),(730,428),(735,620),(812,448),(158,584),(125,602)]}
def check(path):
    scene=SerialScene(path);c=json.loads((HERE/'camera-fit/city-camera.json').read_bytes())
    layout=json.loads((HERE.parent/'source/street-layout.json').read_bytes())
    eye=np.array(layout['city_eye']);K,R=np.array(c['K']),np.array(c['R']);rows=[]
    def one(origin,direction,kind,control,series):
        h=scene.ray(origin,direction,160.);mat=h['material'] if h else None
        keys=CLASSES[kind];ok=mat is None if not keys else bool(mat and any(k.lower()in mat.lower() for k in keys))
        rows.append(dict(view=series,control=control,expected=kind,actual=mat,
                         world_hit=h['point_enu_m']if h else None,passed=ok))
    for k,ps in PIXELS.items():
        for pix in ps:
            one(eye,R.T@np.linalg.solve(K,[*pix,1.]),k,list(pix),'2023 street portrait')
    for x,y in [(16.7,2.0),(13.0,4.19),(14.3,9.3),(19.5,5.5),(-4.3,16.6),(-5.74,20.82),(-2.1,13.0),(-6.7,21.0),(9.5,8.5)]:
        one([x,y,34],[0,0,-1],'red pitched roof',[x,y],'field inside 2019/2021/2025 aerial outlines')
    from shapely.geometry import shape
    data=json.loads((HERE/'model-footprint-and-retained-owner.json').read_bytes())
    if data['retained_subpolygon']['geometry']['type'] in ('Polygon','MultiPolygon'):
        ll=shape(data['retained_subpolygon']['geometry']).representative_point()
        en=(np.array([ll.x,ll.y])-np.array(layout['origin_wgs84']))*[95175.,110860.]
        ang=np.deg2rad(layout['nanxun_bearing_degrees']);xy=np.array([[np.sin(ang),np.cos(ang)],[-np.cos(ang),np.sin(ang)]])@en
        one([*xy,34],[0,0,-1],'unmodelled low neighbour',list(map(float,xy)),'retained portion of owner 1372')
    groups={k:{'tested':len(g),'matched':sum(r['passed']for r in g)}for k in sorted(set(r['expected']for r in rows))if(g:=[r for r in rows if r['expected']==k])}
    structural=all(groups[k]['matched']==groups[k]['tested'] for k in ('open sky','red pitched roof','unmodelled low neighbour'))
    return dict(asset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_sha256=c['source_sha256'],points=rows,groups=groups,
                hits=sum(r['passed']for r in rows),total=len(rows),structural_controls_passed=structural)
