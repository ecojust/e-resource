"""Project photographed details from the two public camera viewports against frozen city mass and the delivered mesh."""
import argparse
import gzip
import json
import math
from pathlib import Path
import runpy
import numpy as np
from shapely.geometry import Point,shape
from shapely.affinity import translate,scale
HERE=Path(__file__).resolve().parent;P=HERE.parents[2]
camera=runpy.run_path(str(HERE.parent/'pure-heart-church-v1/check-overview-sightlines.py'))
gap=runpy.run_path(str(HERE.parent/'longmen-village-gatehouse-v1/check-camera.py'))['equipped_sightline']
def read(p):return json.loads(p.read_bytes())
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--contract',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);ap.add_argument('--surfaces',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--explore',action='store_true')
    ar=ap.parse_args();d=read(ar.contract);r=read(P/'source/precise'/d['id']/'footprint-review.json')
    lon,lat=d['lng'],d['lat'];mn=math.radians(1)*camera['EARTH'];me=mn*math.cos(math.radians(lat))
    def meters(poly):return scale(translate(poly,-lon,-lat),xfact=me,yfact=mn,origin=(0,0))
    assert d['replacement_geometry'] is None and d['owner'] is None
    vol=[]
    f=ar.work/'feature-table.json.gz';data=f.read_bytes()
    assert camera['digest'](data)==next(row['sha256'] for row in r['frozen_bindings'] if row['repository_path'].endswith('/'+f.name))
    for entity in json.loads(gzip.decompress(data))['features']:
        poly=shape(entity['geometry'])
        if poly.distance(Point(lon,lat))>.0013:continue
        poly=meters(poly)
        vol.append((entity['localId'],poly,entity['height']))
    row=next(x for x in read(ar.work/'delivered-decode.json') if x['variant']=='web')
    from surface_data import triangles
    tri,_,_=triangles(row['decoded_glb'])
    probes=read(ar.surfaces)['web'];assert row['sha256']==probes['sha256']==d['model_geometry_sha256']['web']
    checks=probes['checks'];local={}
    for name,detail,i in [
       ('朝院蓝绿门扇','facet 1: blue-green door leaf',0),('另一门扇','facet 1: ochre door leaf',0),
       ('门扇上亮子','facet 1: door fanlight',0),('石阶','courtyard stone step 1',0),
       ('上层侧墙','facet 1: ochre wall beside opening',1),('上层窗玻璃','facet 1: recessed upper glass',2),
       ('上部亮子','facet 1: transom glass',0),('如意纹','facet 1: ruyi segment',0),
       ('前面斗拱','facet 1: upper bracket',0),('下层挑檐','facet 1: lower green eave',0),
       ('东折面窗','facet 2: recessed upper glass',1),('西折面窗','facet 8: recessed upper glass',1),
       ('正面屋瓦','facet 1: pitched green roof',2),('攒尖宝顶','central glazed finial',0)]:
        hit=[c for c in checks if c['name']==detail][i];assert hit['passed']
        local[name]=np.array(hit['origin'])+np.array(hit['direction'])*hit['distance_m']
    h=math.radians(d['heading']);c,s=math.cos(h),math.sin(h)
    targets=[(name,x*c+y*s,-x*s+y*c,z) for name,(x,y,z) in local.items()]
    configs=[(d['overviewBearing'],d['overviewPitch'])]
    if ar.explore: configs +=[(d['heading']+delta,pitch)for delta in (-45,-37,-28,-22,16,24,31,39)for pitch in (40,46,50,54,60,64,68,73,78)]
    results=[]
    for b,pitch in configs:
        screens=[]
        for label,w,ht,pad in camera['VIEWS']:
            vp=dict(width=w,height=ht,insets=dict(zip(['left','right','top','bottom'],pad)))
            z=camera['evaluate']({**d,'overviewBearing':b,'overviewPitch':pitch},vp,label,vol,lon,lat,me,mn,targets)
            e,n,up=z['camera_enu'];eye=[e*c-n*s,e*s+n*c,up]
            for test in z['probes']:
                diff=gap(tri,eye,local[test['feature']]);test['mesh_occlusion_m']=diff
                test['clear_with_own_mesh']=bool(test['clear'] and diff is not None and diff<=.09)
            z['visible_detail_count']=sum(v['clear_with_own_mesh']for v in z['probes']);screens.append(z)
        results.append(dict(bearing=b,pitch=pitch,viewports=screens))
    if ar.explore:
        for out in sorted(results,key=lambda q:min(x['visible_detail_count']for x in q['viewports']),reverse=True)[:7]:
            print(round(out['bearing']-d['heading'],1),out['pitch'],[x['visible_detail_count']for x in out['viewports']],[v['feature']for v in out['viewports'][0]['probes']if v['clear_with_own_mesh']])
    result=dict(contract_sha256=camera['digest'](ar.contract.read_bytes()),source_sha256=camera['digest'](data),camera_module_sha256=camera['digest']((P/'src/candidate-overview-camera.js').read_bytes()),compared_volumes=len(vol),asset_sha256=row['sha256'],cameras=results)
    ar.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,default=lambda v:v.item())+'\n')
    if not ar.explore:assert min(v['visible_detail_count']for v in results[0]['viewports'])>=9
if __name__=='__main__':main()
